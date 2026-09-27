"""A room's nutrient batch, run by the controller: the reservoir refilled for its fill time, the pump
and the recirculation line started, each doser run in the room's order for its planned seconds, the
mix kept going, and everything switched off in the right order. It starts when "Mix a Batch Now" is
pressed, or by itself when the reservoir has read almost empty for a few passes; it refuses to start,
and stops part-way, with a reason, whenever that is not safe."""
from datetime import datetime, timedelta, timezone

import pytest

import controller
from test_controller import _build, _desc

KILL = "input_boolean.kill"
DISTANCE = "sensor.res_distance"
FRESH, RECIRC = "switch.mainswater", "switch.recirc"
PUMP, MAIN, VALVE = "switch.p", "switch.m", "switch.v1"
DOSER = {1: "switch.doser_1_power", 2: "switch.doser_2_power"}
PLAN = "sensor.crop_steering_feed_plan"
BUTTON = "button.crop_steering_mix_batch"
AUTO = "switch.crop_steering_auto_batches"
STATUS = "sensor.crop_steering_batch_status"
FLOWER = {
    "stage": "Flower",
    "problem": None,
    "fill_s": 60,
    "batch_l": 145.0,
    "empty_mm": 800.0,
    "settle_s": 20,
    "pause_s": 10,
    "mix_s": 120,
    "doses": [
        {"doser": 2, "label": "Bloom", "ml": 100.0, "seconds": 10.0},
        {"doser": 1, "label": "Cleanse", "ml": 50.0, "seconds": 5.0},
    ],
}


class _Clock(datetime):
    current = None

    @classmethod
    def now(cls, tz=None):
        return cls.current if tz is None else cls.current.astimezone(tz)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    _Clock.current = _Clock(2026, 9, 27, 14, 0)
    monkeypatch.setattr(controller, "datetime", _Clock)
    seconds = {"now": 0.0}

    def sleep(dt):  # the switch read-backs wait on this: time passes on both clocks
        seconds["now"] += dt
        _Clock.current += timedelta(seconds=dt)

    monkeypatch.setattr(controller.time, "monotonic", lambda: seconds["now"])
    monkeypatch.setattr(controller.time, "sleep", sleep)


def _room(plan=FLOWER, level="820", auto="off", pressed="unknown", **extra):
    descriptor = _desc(
        enable_flag=KILL,
        pump=PUMP,
        mainline=MAIN,
        valves={"1": VALVE},
        reservoir_distance_sensor=DISTANCE,
        fresh_water_switch=FRESH,
        recirc_switch=RECIRC,
        doser_1_switch=DOSER[1],
        doser_2_switch=DOSER[2],
        **extra,
    )
    states = {
        "sensor.crop_steering_engine_config": ("ok", descriptor),
        KILL: ("on", {}),
        DISTANCE: (level, {"unit_of_measurement": "mm"}),
        PLAN: ((plan or {}).get("stage") or "none", dict(plan or {})),
        AUTO: (auto, {}),
        BUTTON: (pressed, {}),
        **{entity: ("off", {}) for entity in (FRESH, RECIRC, PUMP, MAIN, VALVE, *DOSER.values())},
    }
    c, fake = _build({"num_zones": 1, "enable_flag": KILL}, states=states)
    return c, fake, c.rooms[0]


def _tick(c, room):
    c._batch_tick(room, _Clock.now())


def _press(c, fake, room, ago=0):
    """Press Mix a Batch Now `ago` seconds before the clock's now: Home Assistant stores the time in
    UTC."""
    at = (_Clock.current - timedelta(seconds=ago)).astimezone(timezone.utc)
    fake.set_state(BUTTON, at.isoformat())
    _tick(c, room)


def _later(seconds):
    _Clock.current += timedelta(seconds=seconds)


def _switched(fake):
    return [(d["entity_id"], svc) for dom, svc, d in fake.calls if dom == "switch"]


def _alerts(fake, code):
    return [d for dom, svc, d in fake.calls
            if (dom, svc) == ("persistent_notification", "create") and f"({code})" in d.get("title", "")]


def _to_end(c, fake, room, level="210"):
    """Run a started batch through every step (the level read after the fill is `level` mm)."""
    fake.set_state(DISTANCE, level, {"unit_of_measurement": "mm"})
    for _ in range(12):
        if room.batch["step"] == "idle":
            return
        until = datetime.fromisoformat(room.batch["until"])
        _Clock.current = max(_Clock.current, until)
        _tick(c, room)


def test_a_pressed_button_fills_mixes_doses_in_order_and_switches_off_in_order():
    c, fake, room = _room()
    _tick(c, room)  # the button as first seen: never pressed
    assert room.batch["step"] == "idle"
    _press(c, fake, room)
    assert room.batch["step"] == "filling" and fake.states[FRESH][0] == "on"
    fake.calls.clear()
    _to_end(c, fake, room)
    assert _switched(fake) == [
        (FRESH, "turn_off"),  # the fill ends
        (RECIRC, "turn_on"),  # the line opens before the pump starts
        (PUMP, "turn_on"),
        (DOSER[2], "turn_on"),  # the room's order: Bloom first
        (DOSER[2], "turn_off"),
        (DOSER[1], "turn_on"),
        (DOSER[1], "turn_off"),
        (PUMP, "turn_off"),  # the pump stops before its line closes
        (RECIRC, "turn_off"),
    ]
    last = room.batch["last"]
    assert (room.batch["step"], last["result"], last["stage"]) == ("idle", "done", "Flower")
    assert last["dosed"] == {"2": 100.0, "1": 50.0}
    assert all(fake.states[e][0] == "off" for e in (FRESH, RECIRC, PUMP, *DOSER.values()))


def test_each_step_lasts_what_the_plan_says():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    start = _Clock.now()
    seen = []
    fake.set_state(DISTANCE, "210", {"unit_of_measurement": "mm"})
    while room.batch["step"] != "idle":
        until = datetime.fromisoformat(room.batch["until"])
        seen.append((room.batch["step"], round((until - start).total_seconds())))
        _Clock.current = max(_Clock.current, until)
        _tick(c, room)
        start = _Clock.now()
    # fill 60 s, settle 20 s, Bloom 10 s, pause 10 s, Cleanse 5 s, mix 120 s; each measured from when
    # its step began (the switch read-backs take a second or so each)
    steps = [(step, seconds) for step, seconds in seen]
    assert [step for step, _ in steps] == ["filling", "settling", "dosing", "pausing", "dosing", "mixing"]
    assert [seconds for _, seconds in steps] == pytest.approx([60, 20, 10, 10, 5, 120], abs=3)


def test_the_first_press_seen_is_a_starting_point_but_a_first_press_ever_counts():
    c, fake, room = _room(pressed="2026-09-20T09:00:00+00:00")  # pressed before this controller knew
    _tick(c, room)
    assert room.batch["step"] == "idle"
    fresh, fake2, room2 = _room(pressed="unknown")  # never pressed: the first press is a request
    _tick(fresh, room2)
    _press(fresh, fake2, room2)
    assert room2.batch["step"] == "filling"


def test_a_press_that_waited_while_the_controller_was_stopped_is_not_acted_on():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room, ago=2 * 3600)
    assert room.batch["step"] == "idle" and _switched(fake) == []
    assert any("too long ago" in line for line in c._activity)
    _press(c, fake, room, ago=60)  # a minute ago: still wanted
    assert room.batch["step"] == "filling"


@pytest.mark.parametrize(
    "level, reason",
    [
        ("450", "reads 450 mm from the top, short of its almost-empty mark (800 mm)"),
        ("unavailable", f"the reservoir level ({DISTANCE}) reads nothing"),
    ],
)
def test_asked_for_by_hand_it_waits_for_the_reservoir_to_read_almost_empty(level, reason):
    c, fake, room = _room(level=level)
    _tick(c, room)
    _press(c, fake, room)
    assert room.batch["step"] == "idle" and _switched(fake) == []
    (note,) = _alerts(fake, "CS-703")
    assert reason in note["message"]


def test_without_an_almost_empty_mark_a_batch_asked_for_by_hand_goes_ahead():
    c, fake, room = _room(plan={**FLOWER, "empty_mm": 0.0}, level="450")
    _tick(c, room)
    _press(c, fake, room)
    assert room.batch["step"] == "filling"


def test_automatic_batches_start_after_three_low_readings_and_wait_for_the_tank_to_read_fuller():
    c, fake, room = _room(level="850", auto="on")
    for _ in range(2):
        _tick(c, room)
    assert room.batch["step"] == "idle" and room.batch["low_seen"] == 2
    _tick(c, room)
    assert room.batch["step"] == "filling"
    _to_end(c, fake, room, level="850")  # the level never rose: it stops, and does not start again
    assert room.batch["last"]["result"] == "stopped: the reservoir did not fill"
    for _ in range(5):
        _tick(c, room)
    assert room.batch["step"] == "idle" and not room.batch["armed"]
    fake.set_state(DISTANCE, "300", {"unit_of_measurement": "mm"})  # refilled by hand: re-armed
    _tick(c, room)
    assert room.batch["armed"]


def test_with_automatic_batches_off_a_low_reservoir_starts_nothing():
    c, fake, room = _room(level="900", auto="off")
    for _ in range(5):
        _tick(c, room)
    assert room.batch["step"] == "idle" and _switched(fake) == []


def test_a_tank_that_did_not_fill_gets_no_nutrients():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    _to_end(c, fake, room, level="810")
    switched = _switched(fake)
    assert not any(entity in DOSER.values() for entity, _ in switched)
    assert fake.states[PUMP][0] == "off" and fake.states[RECIRC][0] == "off"
    (note,) = _alerts(fake, "CS-702")
    assert "810 mm" in note["message"] and "no nutrient was dosed" in note["message"]


@pytest.mark.parametrize(
    "change, reason",
    [
        ({KILL: "off"}, f"the room's watering switch ({KILL}) is off"),
        ({PUMP: "on"}, f"{PUMP} reads on, not off"),
        ({VALVE: "on"}, f"{VALVE} reads on, not off"),
        ({DOSER[2]: "unavailable"}, f"{DOSER[2]} reads unavailable, not off"),
    ],
)
def test_it_refuses_to_start_with_a_reason_and_switches_nothing_on(change, reason):
    c, fake, room = _room()
    _tick(c, room)
    for entity, state in change.items():
        fake.set_state(entity, state)
    _press(c, fake, room)
    assert room.batch["step"] == "idle"
    assert not [call for call in _switched(fake) if call[1] == "turn_on"]
    (note,) = _alerts(fake, "CS-703")
    assert reason in note["message"]
    assert fake.sets[STATUS][1]["blocked"] == reason


def test_a_plan_the_integration_cannot_run_is_refused_in_its_own_words():
    plan = {**FLOWER, "stage": None, "problem": "No feed stage is chosen.", "doses": []}
    c, fake, room = _room(plan=plan)
    _tick(c, room)
    _press(c, fake, room)
    (note,) = _alerts(fake, "CS-703")
    assert "could not start: No feed stage is chosen." in note["message"]


def test_switching_watering_off_mid_dose_stops_it_and_counts_what_went_in():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    fake.set_state(DISTANCE, "210", {"unit_of_measurement": "mm"})
    while room.batch["step"] != "dosing":
        _Clock.current = max(_Clock.current, datetime.fromisoformat(room.batch["until"]))
        _tick(c, room)
    _later(4)  # Bloom has run about 4 of its 10 s
    fake.set_state(KILL, "off")
    _tick(c, room)
    assert room.batch["step"] == "idle"
    assert all(fake.states[e][0] == "off" for e in (DOSER[2], PUMP, RECIRC))
    assert 30 <= room.batch["last"]["dosed"]["2"] <= 70  # 100 mL in 10 s, stopped part-way
    (note,) = _alerts(fake, "CS-701")
    assert "while dosing" in note["message"] and "was switched off" in note["message"]


def test_a_doser_that_will_not_switch_off_latches_the_hardware_hold():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    fake.set_state(DISTANCE, "210", {"unit_of_measurement": "mm"})
    while room.batch["step"] != "dosing":
        _Clock.current = max(_Clock.current, datetime.fromisoformat(room.batch["until"]))
        _tick(c, room)
    plain = controller.ha_call

    def stuck(domain, service, **data):  # the doser's relay reports on whatever it is told
        if data.get("entity_id") == DOSER[2] and service == "turn_off":
            fake.calls.append((domain, service, data))
            return True
        return plain(domain, service, **data)

    controller.ha_call = stuck
    try:
        _Clock.current = datetime.fromisoformat(room.batch["until"])
        _tick(c, room)
    finally:
        controller.ha_call = plain
    assert room.batch["step"] == "idle" and room.hardware_fault
    assert DOSER[2] in room.hardware_fault["reason"]
    assert _alerts(fake, "CS-301") and _alerts(fake, "CS-701")


def test_while_it_runs_the_rooms_shots_wait_and_other_rooms_only_during_a_fill_or_a_dose():
    c, fake, room = _room()
    other = controller.Room("veg", "veg_", {1: {}}, {"pump": None, "mainline": None, "valves": {1: "switch.veg_v1"}},
                            "input_boolean.veg", 10, 22)
    c.rooms.append(other)
    _tick(c, room)
    _press(c, fake, room)
    assert c._batch_hold(room) == "mixing a nutrient batch (filling)"
    assert c._batch_hold(other).startswith("waiting for ") and "(filling)" in c._batch_hold(other)
    fake.set_state(DISTANCE, "210", {"unit_of_measurement": "mm"})
    _Clock.current = datetime.fromisoformat(room.batch["until"])
    _tick(c, room)  # settling: the fill is over, nothing timed runs
    assert c._batch_hold(room) == "mixing a nutrient batch (settling)"
    assert c._batch_hold(other) is None


def test_between_passes_switching_watering_off_stops_the_fill_within_seconds():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    start = _Clock.now()
    fake.set_state(KILL, "off")
    c._wait_for_next_pass()  # the pass would come after the whole 60 s fill
    assert room.batch["step"] == "idle" and fake.states[FRESH][0] == "off"
    stopped = datetime.fromisoformat(room.batch["last"]["at"])
    assert (stopped - start).total_seconds() <= controller.BATCH_WATCH_S + 1
    (note,) = _alerts(fake, "CS-701")
    assert "while filling" in note["message"] and fake.sets[STATUS][0] == "idle"


def test_with_no_batch_filling_or_dosing_the_loop_sleeps_its_whole_interval():
    c, fake, room = _room()
    _tick(c, room)
    start = _Clock.now()
    c._wait_for_next_pass()
    assert (_Clock.now() - start).total_seconds() == pytest.approx(c.loop_seconds)
    assert not [call for call in fake.calls if call[0] != "persistent_notification"]


def test_the_loop_wakes_when_a_step_is_due():
    c, fake, room = _room()
    assert c._sleep_for(_Clock.now()) == c.loop_seconds
    _tick(c, room)
    _press(c, fake, room)
    assert c._sleep_for(_Clock.now()) == pytest.approx(60, abs=2)  # the fill's end


def test_a_batch_saved_in_progress_is_switched_off_at_the_next_start(tmp_path):
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    c._save_state()
    again = controller.Controller.__new__(controller.Controller)
    again.__dict__.update(c.__dict__)
    again.rooms = [controller.Room("default", "", room.zones, room.hw, KILL, 10, 22)]
    again._load_state()  # the process died filling
    assert again.rooms[0]._batch_crashed
    _tick(again, again.rooms[0])
    assert again.rooms[0].batch["step"] == "idle"
    assert fake.states[FRESH][0] == "off"
    (note,) = _alerts(fake, "CS-701")
    assert "the controller app stopped without finishing it" in note["message"]


def test_stopping_the_app_mid_batch_switches_it_off_and_says_so_once_at_the_next_start():
    c, fake, room = _room()
    _tick(c, room)
    _press(c, fake, room)
    c._safe_off()
    assert fake.states[FRESH][0] == "off" and room.batch["step"] == "idle"
    assert room.batch["interrupted"]["step"] == "filling"
    _tick(c, room)
    _tick(c, room)
    assert len(_alerts(fake, "CS-701")) == 1 and room.batch["interrupted"] is None


def test_the_status_sensor_says_what_runs_and_what_went_in():
    c, fake, room = _room()
    _tick(c, room)
    state, attrs = fake.sets[STATUS]
    assert state == "idle" and attrs["stage"] == "Flower" and attrs["level_mm"] == 820.0
    assert attrs["blocked"] is None and attrs["auto"] is False
    _press(c, fake, room)
    state, attrs = fake.sets[STATUS]
    # the times carry their UTC offset, so a browser in another time zone reads the same moment
    until = datetime.fromisoformat(attrs["until"])
    assert state == "filling" and until.utcoffset() is not None
    assert abs((until - datetime.fromisoformat(room.batch["until"]).astimezone()).total_seconds()) < 1
    _to_end(c, fake, room)
    last = fake.sets[STATUS][1]["last"]
    assert last["result"] == "done" and datetime.fromisoformat(last["at"]).utcoffset() is not None
    assert last["dosed"] == {"2": 100.0, "1": 50.0}


def test_an_old_state_file_or_a_damaged_batch_record_loads_as_no_batch():
    assert controller.restore_batch(None) == controller.fresh_batch()
    damaged = controller.restore_batch({"step": "flooding", "index": "two", "armed": "yes", "plan": 5})
    assert damaged["step"] == "idle" and damaged["index"] == 0 and damaged["armed"] is True
    assert damaged["plan"] is None


def test_a_plan_with_a_dose_it_cannot_read_is_not_run():
    assert controller.feed_plan({**FLOWER, "doses": [{"doser": 9, "ml": 1, "seconds": 1}]}) is None
    assert controller.feed_plan({**FLOWER, "doses": [{"doser": 1, "ml": 1, "seconds": 99999}]}) is None
    assert controller.feed_plan({**FLOWER, "fill_s": "soon"}) is None
    assert controller.feed_plan(FLOWER)["doses"][0]["label"] == "Bloom"


def test_a_distance_in_cm_or_m_reads_in_mm():
    assert controller.level_mm(("84.6", {"unit_of_measurement": "cm"})) == pytest.approx(846.0)
    assert controller.level_mm(("0.85", {"unit_of_measurement": "m"})) == pytest.approx(850.0)
    assert controller.level_mm(("850", {"unit_of_measurement": "in"})) is None
    assert controller.level_mm(("unavailable", {})) is None


def test_a_room_without_a_reservoir_keeps_its_fingerprint_and_one_with_it_names_it():
    plain = _desc(enable_flag=KILL)
    room = type("R", (), {"enable_flag": KILL})()
    assert "reservoir" not in controller.Controller._setup_fingerprint(plain, room)
    mapped = controller.Controller._setup_fingerprint({**plain, "fresh_water_switch": FRESH}, room)
    assert FRESH in mapped
