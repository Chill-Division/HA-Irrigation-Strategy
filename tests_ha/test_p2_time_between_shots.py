"""A maintenance (P2) shot waits the room's "P2 Time Between Shots" after the last shot, in a real
Home Assistant with the real controller.

Seen live on 28 Sep 2026: the maintenance trigger was raised to 70 while a zone read 67, and a shot
fired every minute, three in four minutes, before the first had soaked down to the probes. The
setting is a number, room-wide and per zone like P1's, 5 minutes unless changed. An install
upgraded from before it has it at 5, and a controller whose integration is older than it uses 5
without holding the room for a missing setting.
"""

from datetime import datetime, timedelta

from crop_steering_engine import decide
from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

ROOM = "number.crop_steering_p2_time_between_shots"
ZONE = "number.crop_steering_zone_1_p2_time_between_shots"
WAITING = "sensor.crop_steering_zone_1_waiting_for_app"


async def _set(hass, entity_id, value):
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True
    )


async def _daytime(hass):
    """Lights around now, so the zone is mid-photoperiod whenever this runs."""
    now = datetime.now()
    await _set(hass, "number.crop_steering_lights_on_hour", (now.hour - 4) % 24)
    await _set(hass, "number.crop_steering_lights_off_hour", (now.hour + 8) % 24)


async def test_a_new_room_spaces_its_maintenance_shots_five_minutes_apart(hass):
    await _install(hass)
    for entity_id in (ROOM, ZONE):
        state = hass.states.get(entity_id)
        assert float(state.state) == 5
        assert (state.attributes["min"], state.attributes["max"]) == (0, 60)
        assert state.attributes["unit_of_measurement"] == "min"


async def test_an_upgraded_room_has_it_at_five_minutes(hass):
    await _upgrade(hass, "entry_2_17_wizard.json")
    assert float(hass.states.get(ROOM).state) == 5
    assert float(hass.states.get(ZONE).state) == 5


async def test_the_controller_waits_the_zones_own_time_and_says_when(
    hass, controller_for
):
    await _install(hass)
    await _daytime(hass)
    await _set(hass, ZONE, 8)  # the zone's own value wins over the room's 5
    c, fake, _clock = controller_for({})
    room = c.rooms[0]
    c.loop_once(datetime.now())  # the first pass starts the grow-day
    now = datetime.now()
    room.state[1].update(phase="P2", last_shot=now - timedelta(minutes=1))
    snap, p = c._snapshot(room, 1, now, True, False)
    assert p.p2_time_between_min == 8
    assert snap.vwc < p.p2_threshold  # a maintenance shot is wanted...
    assert decide(snap, p)[2] is False  # ...and waits
    later = snap.__class__(**{**snap.__dict__, "minutes_since_shot": 8})
    assert decide(later, p)[4].kind == "p2_topup"

    c.loop_once(now)
    for entity_id, (state, attributes) in fake.sets.items():  # its REST writes, into HA
        hass.states.async_set(entity_id, state, attributes)
    await hass.async_block_till_done()
    conditions = {c["rule"]: c for c in hass.states.get(WAITING).attributes["conditions"]}
    assert 6.5 <= conditions["p2_topup"]["in_min"] <= 7.0


async def test_an_integration_without_the_setting_leaves_the_controller_at_five_minutes(
    hass, controller_for
):
    await _install(hass)
    for entity_id in (ROOM, ZONE):  # as an integration from before this setting has none
        hass.states.async_remove(entity_id)
    c, _fake, _clock = controller_for({})
    room = c.rooms[0]
    assert c._params(room, 1).p2_time_between_min == 5
    missing = getattr(room, "_settings_missing", set())
    assert ROOM not in missing and ROOM not in c._defaulted_this_loop
