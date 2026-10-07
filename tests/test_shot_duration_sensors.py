"""The P1, P2 and P3 shot-duration sensors time a shot as the controller runs it.

They used to divide by one dripper's flow and read the room-wide sizing only, so a room with two
drippers per plant, or zones sized apart in Settings → Rooms & hardware, read the wrong time. Each
zone now gets its own: its pot size, drippers per plant and dripper flow (the room's where the zone
has none), in whole seconds within the room's shot limits, as the controller's shot sequence does.
The sensor shows the longest, and every zone's in its `zones` attribute.
"""

import ast
import logging
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.crop_steering.calculations import ShotCalculator

SOURCE = (
    Path(__file__).resolve().parents[1] / "custom_components/crop_steering/sensor.py"
)
METHODS = {
    "native_value",
    "extra_state_attributes",
    "_zone_setting",
    "_shot_seconds_by_zone",
}


def _module_constant(tree, name):
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", "") == name for t in n.targets)
    )
    return ast.literal_eval(node.value)


def sensor(key, numbers, zones=None, prefix=""):
    """The real sensor methods, on a room whose number entities read `numbers` (suffix -> state)."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    original = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "CropSteeringSensor"
    )
    body = [
        n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in METHODS
    ]
    cls = ast.ClassDef(
        name="SensorMethods", bases=[], keywords=[], body=body, decorator_list=[]
    )
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {
        "Any": Any,
        "math": math,
        "_LOGGER": logging.getLogger(__name__),
        "ShotCalculator": ShotCalculator,
        "SHOT_SIZE_KEYS": _module_constant(tree, "SHOT_SIZE_KEYS"),
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    entity = namespace["SensorMethods"]()
    states = {
        f"number.crop_steering_{prefix}{suffix}": SimpleNamespace(state=str(value))
        for suffix, value in numbers.items()
    }
    entity.hass = SimpleNamespace(states=SimpleNamespace(get=states.get))
    entity._prefix = prefix
    entity._zone_number = None
    entity._zones_config = zones if zones is not None else {"1": {}}
    entity.entity_description = SimpleNamespace(key=key)
    return entity


ROOM = {
    "substrate_volume": 3.2,
    "dripper_flow_rate": 4,
    "drippers_per_plant": 1,
    "p1_initial_shot_size": 2,
    "p2_shot_size": 5,
    "p3_emergency_shot_size": 2,
    "max_shot_duration": 900,
}


def test_one_dripper_per_plant_times_the_shot_through_it():
    # 2% of 3.2 L is 64 mL; one 4 L/hr dripper gives it in 57.6 s; the controller runs 57.
    entity = sensor("p1_shot_duration_seconds", ROOM)
    assert entity.native_value == 57
    assert entity.extra_state_attributes == {"zones": {"1": 57}}


def test_two_drippers_per_plant_halve_it():
    entity = sensor("p1_shot_duration_seconds", {**ROOM, "drippers_per_plant": 2})
    assert entity.native_value == 28


@pytest.mark.parametrize(
    ("key", "seconds"),
    [
        ("p1_shot_duration_seconds", 57),
        ("p2_shot_duration_seconds", 144),
        ("p3_shot_duration_seconds", 57),
    ],
)
def test_each_sensor_times_its_own_shot(key, seconds):
    assert sensor(key, ROOM).native_value == seconds


def test_the_room_limit_caps_it_and_five_seconds_is_the_least():
    assert (
        sensor(
            "p2_shot_duration_seconds", {**ROOM, "max_shot_duration": 60}
        ).native_value
        == 60
    )
    tiny = {**ROOM, "p1_initial_shot_size": 0.1, "drippers_per_plant": 20}
    assert sensor("p1_shot_duration_seconds", tiny).native_value == 5
    # A limit that isn't one (under 5 s, or not a number) caps nothing, as the controller holds
    # such a room rather than shortening its shots.
    for limit in (3, "unavailable"):
        assert (
            sensor(
                "p2_shot_duration_seconds", {**ROOM, "max_shot_duration": limit}
            ).native_value
            == 144
        )


def test_the_older_limit_entity_still_counts():
    room = {k: v for k, v in ROOM.items() if k != "max_shot_duration"}
    entity = sensor("p2_shot_duration_seconds", {**room, "maximum_shot_duration": 100})
    assert entity.native_value == 100


def test_zones_sized_apart_each_get_their_own_and_the_sensor_shows_the_longest():
    numbers = {
        **ROOM,
        # Zone 1: a 5.8 L pot on two 2 L/hr drippers; zone 2 uses the room's sizing.
        "zone_1_substrate_volume": 5.8,
        "zone_1_drippers_per_plant": 2,
        "zone_1_dripper_flow_rate": 2,
        "zone_2_p2_shot_size": 4,
    }
    entity = sensor("p2_shot_duration_seconds", numbers, zones={"1": {}, "2": {}})
    # Zone 1: 5% of 5.8 L = 290 mL at 4 L/hr: 261 s. Zone 2: 4% of 3.2 L at 4 L/hr: 115.2 s.
    assert entity.extra_state_attributes == {"zones": {"1": 261, "2": 115}}
    assert entity.native_value == 261


def test_an_archived_zone_is_left_out():
    numbers = {**ROOM, "zone_2_substrate_volume": 50}
    zones = {"1": {}, "2": {"active": False}}
    entity = sensor("p1_shot_duration_seconds", numbers, zones=zones)
    assert entity.extra_state_attributes == {"zones": {"1": 57}}


@pytest.mark.parametrize(
    "broken",
    [
        {"dripper_flow_rate": 0},
        {"drippers_per_plant": "unavailable"},
        {"substrate_volume": "not a number"},
        {"p2_shot_size": "nan"},
    ],
)
def test_a_zone_whose_sizing_gives_no_flow_reads_unknown_not_zero(broken):
    entity = sensor("p2_shot_duration_seconds", {**ROOM, **broken})
    assert entity.native_value is None
    assert entity.extra_state_attributes == {"zones": {}}


def test_each_room_reads_its_own_numbers():
    entity = sensor(
        "p1_shot_duration_seconds", {**ROOM, "drippers_per_plant": 2}, prefix="veg_"
    )
    assert entity.native_value == 28


def test_the_calculator_counts_drippers_and_caps_like_the_controller():
    assert ShotCalculator.calculate_shot_duration(4, 3.2, 2, 2) == 28.8
    assert ShotCalculator.capped_shot_seconds(28.8, 900) == 28
    assert ShotCalculator.capped_shot_seconds(1000.4, 900) == 900
    assert ShotCalculator.capped_shot_seconds(2.0, 900) == 5
    assert ShotCalculator.capped_shot_seconds(1000.4, None) == 1000
    assert ShotCalculator.capped_shot_seconds(1000.4, float("nan")) == 1000
