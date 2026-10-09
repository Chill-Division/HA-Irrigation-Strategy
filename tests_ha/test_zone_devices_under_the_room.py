"""Each zone's device sits under its room's, without the parameter Home Assistant deprecated.

Home Assistant 2026.9 warns in its log, once for each of three platforms, that a device's
`via_device` stops working in 2027.8.0. The zones are put under their room in the device registry
instead (`via_device_id`), which every Home Assistant this supports has: on a fresh install, and on
an old one updated in place.
"""

import logging

from homeassistant.helpers import device_registry as dr
from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

DOMAIN = "crop_steering"


def _room_and_zones(hass, entry):
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    (room,) = [d for d in devices if (DOMAIN, entry.entry_id) in d.identifiers]
    zones = [
        d
        for d in devices
        if any(str(key).startswith(f"{entry.entry_id}_zone_") for _domain, key in d.identifiers)
    ]
    return room, zones


async def test_a_fresh_install_puts_its_zones_under_the_room_with_no_warning(hass, caplog):
    caplog.set_level(logging.WARNING)
    entry = await _install(hass)
    room, zones = _room_and_zones(hass, entry)
    assert zones and all(zone.via_device_id == room.id for zone in zones)
    assert "via_device" not in caplog.text


async def test_an_old_install_keeps_its_zones_under_the_room(hass, caplog):
    caplog.set_level(logging.WARNING)
    entry, seed = await _upgrade(hass, "entry_2_17_wizard.json")
    room, zones = _room_and_zones(hass, entry)
    assert len(zones) == len(seed["data"]["zones"])
    assert all(zone.via_device_id == room.id for zone in zones)
    assert "via_device" not in caplog.text
    # Loading it again changes nothing: a zone already under its room is left as it is.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert _room_and_zones(hass, entry)[1] == zones
