"""The pump runs the room's Pump Prime Time before the main line opens, and the main line its Main
Line Lead Time before the zone valve. Both were fixed at 2 s and 1 s: a pump that takes 4 s to
reach pressure opened every zone valve onto a line still filling. Under an integration older than
the two settings, the controller keeps the 2 s and 1 s it always waited.
"""
import pytest

import controller
from test_controller import _build, _desc

KILL = "input_boolean.kill"
PUMP, MAIN, VALVE = "switch.pump", "switch.main", "switch.valve_1"
PRIME, LEAD = "number.crop_steering_pump_prime_time", "number.crop_steering_main_line_lead_time"


@pytest.fixture
def clock(monkeypatch):
    now = {"seconds": 0.0}
    monkeypatch.setattr(controller.time, "monotonic", lambda: now["seconds"])
    monkeypatch.setattr(controller.time, "sleep", lambda dt: now.__setitem__("seconds", now["seconds"] + dt))
    return now


def _opened(monkeypatch, clock, settings=None, pump=PUMP, mainline=MAIN):
    """Fire one 6 s shot in a room with these settings: when each switch was switched on."""
    states = {
        "sensor.crop_steering_engine_config": (
            "ok", _desc(pump=pump, mainline=mainline, valves={"1": VALVE}, enable_flag=KILL)),
        VALVE: ("off", {}),
        KILL: ("on", {}),
        "switch.crop_steering_zone_1_enabled": ("on", {}),
        **{entity: ("off", {}) for entity in (pump, mainline) if entity},
        **{entity: (str(value), {}) for entity, value in (settings or {}).items()},
    }
    c, _fake = _build({"num_zones": 1, "enable_flag": KILL}, states=states)
    opened = {}
    real = controller.ha_call  # the fake Home Assistant _build installed

    def stamped(domain, service, **data):
        if domain == "switch" and service == "turn_on":
            opened[data["entity_id"]] = clock["seconds"]
        return real(domain, service, **data)

    monkeypatch.setattr(controller, "ha_call", stamped)
    c._execute_shot(c.rooms[0], 1, 6, 2.0)
    assert c.rooms[0].state[1]["shots"] == 1  # the shot ran and was counted
    return opened


def test_the_pump_primes_and_the_main_line_leads_for_the_rooms_own_times(monkeypatch, clock):
    assert _opened(monkeypatch, clock, {PRIME: 4, LEAD: 0.5}) == {PUMP: 0.0, MAIN: 4.0, VALVE: 4.5}


def test_an_integration_without_the_settings_keeps_the_two_and_one_second_waits(monkeypatch, clock):
    assert _opened(monkeypatch, clock) == {PUMP: 0.0, MAIN: 2.0, VALVE: 3.0}


def test_a_value_past_what_the_setting_allows_waits_its_most(monkeypatch, clock):
    assert _opened(monkeypatch, clock, {PRIME: 90, LEAD: -3}) == {PUMP: 0.0, MAIN: 20.0, VALVE: 20.0}


def test_a_room_without_a_main_line_waits_only_the_pumps_prime(monkeypatch, clock):
    assert _opened(monkeypatch, clock, {PRIME: 4, LEAD: 5}, mainline=None) == {PUMP: 0.0, VALVE: 4.0}
