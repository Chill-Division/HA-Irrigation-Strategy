"""P0 ends on the zone's own additional dryback, in a real Home Assistant with the real controller.

Athena's additional dryback is the 1-5% the substrate dries after lights-on, before the first shot
(p. 33, p. 39). A "P0 Dryback Drop Percent" setting has existed since 2025, per room and per zone, and
nothing read it: P0 ended on the P3 dryback target instead, which the latest-first-shot time always
beat. The setting is now P0 Additional Dryback, 3% unless changed, and the controller ends P0 on it.
A value saved while nothing read it (the old 15% default, a recipe's 12-30%) starts at 3%; one set
since is kept.
"""

import copy

import test_upgrade_in_place as upgrade
from conftest import fixture
from test_setup_entry import _install

ROOM = "number.crop_steering_p0_dryback_drop_percent"
ZONE = "number.crop_steering_zone_1_p0_dryback_drop_percent"


async def test_a_new_room_ends_p0_at_3_percent_and_the_controller_reads_the_zones_own(
    hass, controller_for
):
    await _install(hass)
    for entity_id in (ROOM, ZONE):
        state = hass.states.get(entity_id)
        assert float(state.state) == 3
        assert (state.attributes["min"], state.attributes["max"]) == (1, 40)
        assert state.attributes["read_by_controller"] is True
    await hass.services.async_call(
        "number", "set_value", {"entity_id": ZONE, "value": 4.5}, blocking=True
    )
    c, _fake, _clock = controller_for({})
    assert c._params(c.rooms[0], 1).additional_dryback == 4.5


def _seeded(monkeypatch, saved):
    seed = copy.deepcopy(fixture("entry_2_17_wizard.json"))
    seed["operator_tuned_numbers"].update(saved)
    monkeypatch.setattr(upgrade, "fixture", lambda _name: seed)


async def test_a_value_saved_while_nothing_read_it_starts_at_3(hass, monkeypatch):
    # The old 15% default on the room, a recipe's 24% on the zone: neither ever did anything.
    _seeded(monkeypatch, {ROOM: "15", ZONE: "24"})
    await upgrade._upgrade(hass, "entry_2_17_wizard.json")
    assert float(hass.states.get(ROOM).state) == 3
    assert float(hass.states.get(ZONE).state) == 3
    # Everything else the operator tuned comes back as it was.
    assert float(hass.states.get("number.crop_steering_zone_1_p1_target_vwc").state) == 61.5


async def test_a_value_set_since_the_controller_reads_it_is_kept(hass, monkeypatch):
    _seeded(monkeypatch, {ZONE: ["4.5", {"read_by_controller": True}]})
    await upgrade._upgrade(hass, "entry_2_17_wizard.json")
    assert float(hass.states.get(ZONE).state) == 4.5
