"""Optional tank telemetry mappings are explicit and do not become actuators."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace

import pytest

from custom_components.crop_steering import setup_api as api
from custom_components.crop_steering.room import build_engine_config
from .test_setup import payload, rig


MAPPINGS = {
    "tank_temperature_sensor": "sensor.tank_temp",
}


def tank_rig():
    hass, entry, states = rig()
    for entity, state, attrs in [
        ("sensor.tank_level", "65", {"unit_of_measurement": "%"}),
        ("sensor.tank_ec", "2.5", {"unit_of_measurement": "mS/cm"}),
        ("sensor.tank_ph", "5.8", {"unit_of_measurement": "pH"}),
        ("sensor.tank_temp", "21.5", {"unit_of_measurement": "°C"}),
    ]:
        states[entity] = SimpleNamespace(
            entity_id=entity, state=state, attributes=attrs
        )
    return hass, entry, states


def test_tank_mappings_roundtrip_without_changing_plumbing_identity_or_setpoints():
    hass, entry, _states = tank_rig()
    entry.data["hardware"]["temperature_sensor"] = "sensor.temp"
    # a setup from before 2.26.0: its feed and tank EC/pH probes are dropped on its next save
    entry.data["hardware"]["feed_ec_sensor"] = "sensor.ec"
    entry.data["hardware"]["tank_ph_sensor"] = "sensor.tank_ph"
    # and its tank level in %, which the reservoir's distance sensor now gives
    entry.data["hardware"]["water_level_sensor"] = "sensor.tank_level"
    entry.options = {"keep_this_option": 42}
    before = deepcopy(entry.data)
    data = payload()
    data["hardware"].update(MAPPINGS)
    result = asyncio.run(api.save_setup(hass, data))
    for key, value in MAPPINGS.items():
        assert result["hardware"][key] == value
        assert entry.data["hardware"][key] == value
    assert entry.data["hardware"]["temperature_sensor"] == "sensor.temp"
    assert not {"feed_ec_sensor", "tank_ph_sensor", "water_level_sensor"} & set(
        entry.data["hardware"]
    )
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
    assert not result["safety"]["blockers"]  # tank telemetry, not mapped plumbing
    assert (
        api.configuration_payload(entry.data)["hardware"]["tank_temperature_sensor"]
        == MAPPINGS["tank_temperature_sensor"]
    )
    candidates = api.read_setup(hass)["candidates"]
    assert any(
        row["entity_id"] == MAPPINGS["tank_temperature_sensor"] for row in candidates
    )


def test_descriptor_exposes_only_explicit_room_tank_mappings():
    hardware = {
        **MAPPINGS,
        "feed_ec_sensor": "sensor.feed_ec",
        "feed_ph_sensor": "sensor.feed_ph",
        "temperature_sensor": "sensor.air",
        "water_level_sensor": "sensor.tank_level",
    }
    attrs = build_engine_config("veg_", "veg", 1, {}, hardware)
    for key, value in MAPPINGS.items():
        assert attrs[key] == value
    retired = {
        "feed_ec_sensor",
        "feed_ph_sensor",
        "temperature_sensor",
        "water_level_sensor",
    }
    assert not retired & set(attrs)
    absent = build_engine_config(
        "", "default", 1, {}, {"temperature_sensor": "sensor.air"}
    )
    assert all(absent[key] == "" for key in MAPPINGS)


@pytest.mark.parametrize("unit", ["°C", "°F", "K"])
def test_tank_temperature_accepts_explicit_temperature_units(unit):
    hass, entry, states = tank_rig()
    states["sensor.tank_temp"].attributes["unit_of_measurement"] = unit
    data = payload()
    data["hardware"]["tank_temperature_sensor"] = "sensor.tank_temp"
    assert (
        api.prepare_setup(hass, data, entry.data, entry.entry_id)["hardware"][
            "tank_temperature_sensor"
        ]
        == "sensor.tank_temp"
    )


@pytest.mark.parametrize("unit", ["%", "mS/cm", "", None])
def test_tank_temperature_rejects_incompatible_or_missing_units(unit):
    hass, entry, states = tank_rig()
    states["sensor.tank_temp"].attributes["unit_of_measurement"] = unit
    data = payload()
    data["hardware"]["tank_temperature_sensor"] = "sensor.tank_temp"
    with pytest.raises(ValueError, match="unit"):
        api.prepare_setup(hass, data, entry.data, entry.entry_id)


def test_optional_telemetry_preserves_omissions_and_allows_explicit_clear():
    hass, entry, _states = tank_rig()
    entry.data["hardware"].update(MAPPINGS)
    result = api.prepare_setup(hass, payload(), entry.data, entry.entry_id)
    assert result["hardware"]["tank_temperature_sensor"] == "sensor.tank_temp"
    data = payload()
    data["hardware"].update({key: "" for key in MAPPINGS})
    result = api.prepare_setup(hass, data, entry.data, entry.entry_id)
    assert all(result["hardware"][key] == "" for key in MAPPINGS)


@pytest.mark.parametrize(
    "key,value",
    [
        ("tank_temperature_sensor", "sensor.missing"),
        ("tank_temperature_sensor", "switch.p"),
    ],
)
def test_tank_mappings_reject_missing_entities_or_wrong_domains(key, value):
    hass, entry, _states = tank_rig()
    data = payload()
    data["hardware"][key] = value
    with pytest.raises(ValueError):
        api.prepare_setup(hass, data, entry.data, entry.entry_id)


@pytest.mark.parametrize(
    "key", ["tank_ec_sensor", "tank_ph_sensor", "feed_ec_sensor", "feed_ph_sensor"]
)
def test_the_tank_and_feed_ec_ph_mappings_are_gone(key):
    """Removed in 2.26.0 with the source-water gate: a setup that names one is refused."""
    hass, entry, _states = tank_rig()
    data = payload()
    data["hardware"][key] = "sensor.tank_ec"
    with pytest.raises(ValueError, match="Unknown hardware mapping field"):
        api.prepare_setup(hass, data, entry.data, entry.entry_id)


def test_a_tank_level_in_percent_is_no_longer_a_mapping():
    """The reservoir's distance sensor gives the tank's level (the controller's level_pct): a
    separate level sensor in % is not offered, and a save that names one is refused."""
    hass, entry, _states = tank_rig()
    assert "water_level_sensor" not in api.HARDWARE_DOMAINS
    assert "water_level_sensor" not in api.read_setup(hass)["rooms"][0]["hardware"]
    data = payload()
    data["hardware"]["water_level_sensor"] = "sensor.tank_level"
    with pytest.raises(ValueError, match="Unknown hardware mapping field"):
        api.prepare_setup(hass, data, entry.data, entry.entry_id)
