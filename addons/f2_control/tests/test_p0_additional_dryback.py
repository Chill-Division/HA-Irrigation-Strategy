"""P0 ends on the zone's own additional dryback (Athena's 1-5% before the first shot), read from its
P0 Additional Dryback setting, number.crop_steering_<prefix>[zone_N_]p0_dryback_drop_percent. That
setting existed since 2025 and nothing read it: P0 waited for the P3 dryback target instead, which
the latest-first-shot time always beat."""
from test_controller import _build

ZONE = "number.crop_steering_zone_1_p0_dryback_drop_percent"
ROOM = "number.crop_steering_p0_dryback_drop_percent"
HARDWARE = {"pump": "switch.p", "mainline": "switch.m", "valves": {"1": "switch.v1"}}


def _params(states):
    c, _fake = _build({"num_zones": 1, "hardware": HARDWARE}, states=states)
    room = c.rooms[0]
    return c, room, c._params(room, 1)


def test_the_zones_own_value_wins_then_the_rooms():
    _c, _room, p = _params({ZONE: ("4", {}), ROOM: ("2", {})})
    assert p.additional_dryback == 4.0
    _c, _room, p = _params({ROOM: ("2", {})})
    assert p.additional_dryback == 2.0


def test_an_integration_without_it_leaves_3_and_holds_nothing():
    c, room, p = _params({})
    assert p.additional_dryback == 3.0
    assert ROOM not in c._defaulted_this_loop and ROOM not in getattr(room, "_settings_missing", set())
