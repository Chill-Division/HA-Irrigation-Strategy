"""Retired mappings (setup_api.RETIRED_HARDWARE): what an older setup stored goes on its next save,
nothing offers them any more, and a save that names one is refused. None was ever an actuator."""

import asyncio
from copy import deepcopy

import pytest

from custom_components.crop_steering import setup_api as api
from custom_components.crop_steering.room import build_engine_config
from .test_setup import payload, rig

RETIRED = {
    # 2.26.0, with the source-water gate: the feed and tank EC and pH probes
    "feed_ec_sensor": "sensor.feed_ec",
    "feed_ph_sensor": "sensor.feed_ph",
    "tank_ec_sensor": "sensor.tank_ec",
    "tank_ph_sensor": "sensor.tank_ph",
    # The tank's level in %, which the reservoir's distance sensor gives.
    "water_level_sensor": "sensor.tank_level",
    # The room's climate sensors and a notification service, which nothing read.
    "temperature_sensor": "sensor.air",
    "humidity_sensor": "sensor.rh",
    "vpd_sensor": "sensor.vpd",
    "notification_service": "notify.phone",
    # The tank's water temperature, which only the tank card showed.
    "tank_temperature_sensor": "sensor.tank_temp",
}


def test_an_older_setups_retired_mappings_go_on_its_next_save_and_nothing_else_moves():
    hass, entry, _states = rig()
    entry.data["hardware"].update(RETIRED)
    entry.options = {"keep_this_option": 42}
    before = deepcopy(entry.data)
    asyncio.run(api.save_setup(hass, payload()))
    assert not set(RETIRED) & set(entry.data["hardware"])
    assert entry.data["room_prefix"] == before["room_prefix"]
    assert entry.data["parameters"] == before["parameters"]
    assert entry.data["zones"]["1"]["special"] == 123
    assert entry.options == {"keep_this_option": 42}
    assert api.hardware_entities(entry.data) == {
        "switch.p",
        "switch.m",
        "switch.v1",
        "switch.v2",
    }


def test_the_room_descriptor_publishes_none_of_them():
    attrs = build_engine_config("veg_", "veg", 1, {}, dict(RETIRED))
    assert not set(RETIRED) & set(attrs)


@pytest.mark.parametrize("key", sorted(RETIRED))
def test_none_is_offered_and_a_save_that_names_one_is_refused(key):
    hass, entry, _states = rig()
    assert key not in api.HARDWARE_DOMAINS
    assert key not in api.read_setup(hass)["rooms"][0]["hardware"]
    data = payload()
    data["hardware"][key] = RETIRED[key]
    with pytest.raises(ValueError, match="Unknown hardware mapping field"):
        api.prepare_setup(hass, data, entry.data, entry.entry_id)
