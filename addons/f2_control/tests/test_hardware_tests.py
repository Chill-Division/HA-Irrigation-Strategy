"""A zone's test shot, asked for from Settings → Rooms & hardware → Tests (or the zone's Test Shot button
in Home Assistant): the controller waters the zone for 10 seconds at its next pass, through every check a
shot passes but a held grow plan's. Its water counts toward the zone's day; it is not one of the day's
shots (a ramp shot, say), and Auto setpoints learns nothing from it.

The test refill, run anyway, is in test_nutrient_batch.py.
"""
from datetime import datetime, timedelta, timezone

import pytest

import controller
from test_room_status import _room

BUTTON = "button.crop_steering_zone_1_test_shot"
VWC = "sensor.crop_steering_vwc_zone_1"
STATUS = "sensor.crop_steering_zone_1_status_app"
PUMP, MAIN, VALVE = "switch.p", "switch.m", "switch.v1"
SIZING = {  # 40 plants of 3.2 L, one 2 L/h dripper each: 10 s gives 40 x 2 / 360 = 0.22 L
    "number.crop_steering_zone_1_plant_count": ("40", {}),
    "number.crop_steering_zone_1_substrate_volume": ("3.2", {}),
    "number.crop_steering_zone_1_drippers_per_plant": ("1", {}),
    "number.crop_steering_zone_1_dripper_flow_rate": ("2", {}),
    "number.crop_steering_zone_1_max_daily_volume": ("20", {}),
}


class _Clock(datetime):
    current = None

    @classmethod
    def now(cls, tz=None):
        return cls.current if tz is None else cls.current.astimezone(tz)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    _Clock.current = _Clock(2026, 9, 19, 14, 0)  # lights are 10:00-22:00 in the rig
    monkeypatch.setattr(controller, "datetime", _Clock)
    seconds = {"now": 0.0}

    def sleep(dt):
        seconds["now"] += dt
        _Clock.current += timedelta(seconds=dt)

    monkeypatch.setattr(controller.time, "monotonic", lambda: seconds["now"])
    monkeypatch.setattr(controller.time, "sleep", sleep)


def _zone(pressed="unknown", **state):
    """A zone in P2, well over its maintenance trigger, so nothing else is due: one pass has run, so
    the Test Shot button's state then is its starting point."""
    c, fake = _room("on", {**SIZING, BUTTON: (pressed, {})})
    _reading(fake)
    c.rooms[0].state[1].update(phase="P2", last_daily_reset=_Clock.now().date(), **state)
    c.loop_once(_Clock.now())
    fake.calls.clear()
    return c, fake, c.rooms[0]


def _reading(fake):
    fake.set_state(VWC, "60", {"unit_of_measurement": "%"}, last_updated=_Clock.now(timezone.utc).isoformat())


def _press(c, fake, ago=0):
    """Press the zone's Test Shot `ago` seconds before now (Home Assistant keeps it in UTC), then a pass."""
    _Clock.current += timedelta(seconds=30)
    _reading(fake)
    at = (_Clock.current - timedelta(seconds=ago)).astimezone(timezone.utc)
    fake.set_state(BUTTON, at.isoformat())
    c.loop_once(_Clock.now())


def _switched(fake):
    return [(d["entity_id"], svc) for dom, svc, d in fake.calls if dom == "switch"]


def test_a_test_shot_waters_the_zone_for_ten_seconds_and_is_not_one_of_the_days_shots(capsys):
    c, fake, room = _zone(shots=3, daily_vol=1.0)
    learned = dict(room.state[1]["learn"])
    _press(c, fake)
    assert _switched(fake) == [
        (PUMP, "turn_on"), (MAIN, "turn_on"), (VALVE, "turn_on"),
        (VALVE, "turn_off"), (MAIN, "turn_off"), (PUMP, "turn_off"),
    ]
    st = room.state[1]
    assert st["shots"] == 3  # not a shot of the day's: a ramp would not move on for it
    assert st["daily_vol"] == pytest.approx(1.0 + 10 * 40 * 2 / 3600, abs=0.01)  # its water is
    assert st["learn"] == learned  # Auto setpoints learns nothing from it
    assert st["last_shot"] is not None
    assert "P2 test shot 0.17% for 10 s (~0.2 L): 10 s asked for, to test the watering" in capsys.readouterr().out
    assert fake.sets[STATUS][0] == "Test shot"


def test_the_buttons_state_when_the_controller_starts_is_not_a_press():
    c, fake = _room("on", {**SIZING, BUTTON: (_Clock.now(timezone.utc).isoformat(), {})})
    _reading(fake)
    c.rooms[0].state[1].update(phase="P2", last_daily_reset=_Clock.now().date())
    c.loop_once(_Clock.now())
    assert _switched(fake) == []


def test_a_test_shot_asked_for_long_ago_is_not_run(capsys):
    c, fake, room = _zone()
    _press(c, fake, ago=20 * 60)
    assert _switched(fake) == []
    assert "Zone 1 · Test Shot pressed at 2026-09-19T" in capsys.readouterr().out
    _press(c, fake, ago=60)  # a minute ago: still wanted
    assert (VALVE, "turn_on") in _switched(fake)


def test_a_switched_off_zone_holds_a_test_shot_and_says_why(capsys):
    c, fake, room = _zone()
    fake.set_state("switch.crop_steering_zone_1_enabled", "off")
    _press(c, fake)
    assert _switched(fake) == []
    assert "held: zone disabled, instead of a test shot (10 s asked for, to test the watering)" in (
        capsys.readouterr().out
    )


def test_a_refill_in_progress_holds_a_test_shot(monkeypatch):
    c, fake, room = _zone()
    monkeypatch.setattr(c, "_batch_hold", lambda room: "refilling its reservoir (filling)")
    _press(c, fake)
    assert _switched(fake) == []


def test_a_test_shot_counts_toward_the_daily_water_limit(capsys):
    c, fake, room = _zone(daily_vol=20.0)  # the 20 L limit is spent
    _press(c, fake)
    assert _switched(fake) == []
    assert "held: the daily water limit is spent (0.00 L left), instead of a test shot" in capsys.readouterr().out


def test_a_held_grow_plan_does_not_stop_a_test_shot(monkeypatch, capsys):
    c, fake, room = _zone()
    monkeypatch.setattr(controller, "strategy_block", lambda snapshot, zone: "Strategy hold: plan starts 1 Oct")
    _press(c, fake)
    assert (VALVE, "turn_on") in _switched(fake)
    assert "Zone 1 · Strategy hold: plan starts 1 Oct, but a test shot still runs" in capsys.readouterr().out
