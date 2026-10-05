"""The overnight dryback targets a new room starts with: the middle of Athena's ranges, vegetative
35% (30-40%) and generative 45% (40-50%), % below the day's peak. They were 50% and 40%, the wrong
way round. A room that was already running keeps what it had, the old defaults included: Home
Assistant restores a number's last value over the default."""

from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

TARGETS = {
    "number.crop_steering_vegetative_dryback_target": 35.0,
    "number.crop_steering_generative_dryback_target": 45.0,
    "number.crop_steering_zone_1_vegetative_dryback_target": 35.0,
    "number.crop_steering_zone_1_generative_dryback_target": 45.0,
}


async def test_a_new_room_starts_at_the_middle_of_athenas_dryback_ranges(hass):
    await _install(hass)
    for entity_id, value in TARGETS.items():
        assert float(hass.states.get(entity_id).state) == value, entity_id


async def test_a_room_already_running_keeps_its_dryback_targets_the_old_defaults_included(hass):
    old = {
        entity_id: "50.0" if "vegetative" in entity_id else "40.0" for entity_id in TARGETS
    }
    await _upgrade(hass, "entry_2_17_wizard.json", restored=old)
    for entity_id, value in old.items():
        assert float(hass.states.get(entity_id).state) == float(value), entity_id
