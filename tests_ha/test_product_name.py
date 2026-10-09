"""PHASE Steering is the name Home Assistant shows, and nothing is found by it.

It was Crop Steering, and the room's device was "Crop Steering System" or "Crop Steering",
whichever platform registered it last. Now the sidebar, the room's device (one name, from every
platform) and the zones' entity names say PHASE Steering, on a fresh install and on an old one
updated in place. The controller and every dashboard find things by id: no id moves, and a name
the operator gave the device stays theirs.
"""

from homeassistant.components import frontend
from homeassistant.helpers import device_registry as dr, entity_registry as er
from test_setup_entry import PANEL, _install
from test_upgrade_in_place import _upgrade

DOMAIN = "crop_steering"
NAME = "PHASE Steering"
# A zone's entities, each as an old version registered it: id, unique key, the name it gave it.
ZONE_ENTITIES = (
    ("number.crop_steering_zone_1_plant_count", "zone_1_plant_count", "Crop Steering Zone 1 Plant Count"),
    (
        "number.crop_steering_zone_1_max_daily_volume",
        "zone_1_max_daily_volume",
        "Crop Steering Zone 1 Max Daily Volume",
    ),
    (
        "select.crop_steering_zone_1_steering_mode",
        "zone_1_steering_mode",
        "Crop Steering Zone 1 Steering Mode",
    ),
)


def _room_device(hass, entry):
    registry = dr.async_get(hass)
    (device,) = [
        device
        for device in dr.async_entries_for_config_entry(registry, entry.entry_id)
        if (DOMAIN, entry.entry_id) in device.identifiers
    ]
    return device


async def test_a_fresh_install_says_phase_steering_under_the_ids_it_always_had(hass):
    entry = await _install(hass)
    assert _room_device(hass, entry).name == NAME
    panel = hass.data[frontend.DATA_PANELS][PANEL]
    assert (panel.sidebar_title, panel.sidebar_icon) == (NAME, "mdi:water-circle")
    registry = er.async_get(hass)
    for entity_id, _key, _old in ZONE_ENTITIES:
        entity = registry.async_get(entity_id)
        assert entity is not None, entity_id
        assert entity.original_name.startswith(f"{NAME} Zone 1 "), entity_id
        # From 2026.9 Home Assistant puts the device's name (the zone's) in front of it.
        assert hass.states.get(entity_id).attributes["friendly_name"].endswith(entity.original_name)
    assert [e for e in registry.entities if "phase_steering" in e] == []


async def test_an_old_install_takes_the_new_names_and_keeps_every_id(hass):
    """Updated in place: the room's device and the zone's entities as the old version registered
    them, the device renamed by its operator, and the new code started on top."""

    def as_left(entry):
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name="Crop Steering System",
        )
        dr.async_get(hass).async_update_device(device.id, name_by_user="Veg tent")
        registry = er.async_get(hass)
        for entity_id, key, old_name in ZONE_ENTITIES:
            platform, object_id = entity_id.split(".", 1)
            registry.async_get_or_create(
                platform,
                DOMAIN,
                f"{DOMAIN}_{entry.entry_id}_{key}",
                suggested_object_id=object_id,
                config_entry=entry,
                original_name=old_name,
            )

    entry, seed = await _upgrade(hass, "entry_env_era.json", prepare=as_left)
    assert seed["data"]["name"] == "Crop Steering System"  # the name an old wizard gave the room
    device = _room_device(hass, entry)
    assert device.name == NAME
    assert device.name_by_user == "Veg tent"  # the operator's own name for it stays theirs
    registry = er.async_get(hass)
    for entity_id, _key, _old in ZONE_ENTITIES:
        entity = registry.async_get(entity_id)
        assert entity is not None, entity_id  # the same id, not a new entity beside it
        assert entity.original_name.startswith(f"{NAME} Zone 1 "), entity_id
        assert hass.states.get(entity_id).attributes["friendly_name"].endswith(entity.original_name)
    assert [e for e in registry.entities if "phase_steering" in e] == []
