"""A room's settings that cannot be read yet are waited for, not guessed.

While Home Assistant starts, or the integration reloads, a room's numbers are missing for a moment.
The engine used to fill each one with its built-in value at once (a P2 trigger of 45 %, a 5 % shot)
and water on that, and only said so, with CS-402, three passes later. Now the zone waits those three
passes. A setting that reads again ends the wait at once; one still missing after them is watered
on its built-in value, as before, with CS-402 saying which.
"""
from datetime import datetime, timedelta, timezone

import pytest

import controller
from test_room_status import _room

pytestmark = pytest.mark.settings_wait

VWC = "sensor.crop_steering_vwc_zone_1"
STATUS = "sensor.crop_steering_zone_1_status_app"


class _Clock(datetime):
    current = None

    @classmethod
    def now(cls, tz=None):
        return cls.current if tz is None else cls.current.astimezone(tz)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    _Clock.current = _Clock(2026, 9, 25, 14, 0)  # lights are 10:00-22:00 in the rig
    monkeypatch.setattr(controller, "datetime", _Clock)
    seconds = {"now": 0.0}
    monkeypatch.setattr(controller.time, "monotonic", lambda: seconds["now"])
    monkeypatch.setattr(controller.time, "sleep", lambda dt: seconds.__setitem__("now", seconds["now"] + dt))


def _pass(c, fake):
    """One controller pass a minute after the last, with the probe reading 30 %: a P2 top-up is due."""
    _Clock.current += timedelta(minutes=1)
    fake.set_state(VWC, "30", {"unit_of_measurement": "%"}, last_updated=_Clock.now(timezone.utc).isoformat())
    c.loop_once(_Clock.now())


def _dry_p2_zone():
    """An armed room none of whose numbers exist in Home Assistant yet."""
    c, fake = _room("on")
    c.rooms[0].state[1].update(phase="P2", last_daily_reset=_Clock.now().date(),
                               last_shot=_Clock.now() - timedelta(hours=1))
    return c, fake


def _opened(fake):
    return [d["entity_id"] for dom, svc, d in fake.calls if (dom, svc) == ("switch", "turn_on")]


def _cs402(fake):
    return [d for dom, svc, d in fake.calls
            if (dom, svc) == ("persistent_notification", "create") and "(CS-402)" in d.get("title", "")]


def test_the_shipped_wait_is_as_long_as_cs402_waits():
    assert controller.SETTINGS_WAIT_PASSES == 3


def test_a_zone_waits_three_passes_for_its_settings_then_waters_on_the_built_in_values():
    c, fake = _dry_p2_zone()
    for _ in range(3):
        _pass(c, fake)
        assert _opened(fake) == []
        assert fake.sets[STATUS][0].startswith("Blocked: waiting for its settings to load (number.crop_steering_")
    assert _cs402(fake)  # said at the end of the third pass: from now on it is the built-in values
    _pass(c, fake)
    assert _opened(fake) == ["switch.p", "switch.m", "switch.v1"]


def test_settings_that_read_again_end_the_wait_at_once(monkeypatch):
    c, fake = _dry_p2_zone()
    used = {}
    real = c._zone_num

    def spy(room, zone, suffix, default, optional=False):
        value = used[f"number.crop_steering_{room.prefix}{suffix}"] = real(room, zone, suffix, default, optional)
        return value

    monkeypatch.setattr(c, "_zone_num", spy)
    _pass(c, fake)
    missing = sorted(c.rooms[0]._settings_missing)
    assert missing and fake.sets[STATUS][0].startswith("Blocked: waiting for its settings to load")
    for entity in missing:  # the integration has loaded: each reads the value the engine would have used
        fake.set_state(entity, str(used[entity]))
    _pass(c, fake)
    assert "waiting for its settings" not in fake.sets[STATUS][0]  # the next pass goes on to the shot
    assert _cs402(fake) == []


def test_the_wait_names_what_it_waits_for():
    c, fake = _dry_p2_zone()
    room = c.rooms[0]
    room._settings_missing = {"number.crop_steering_b", "number.crop_steering_a"}
    assert c._settings_loading(room) == "waiting for its settings to load (number.crop_steering_a, number.crop_steering_b)"
    room._settings_missing |= {"number.crop_steering_c", "number.crop_steering_d"}
    assert c._settings_loading(room).endswith("(number.crop_steering_a, number.crop_steering_b and 2 more)")
    c._defaulted = {e: 3 for e in room._settings_missing}  # missing for three passes already
    assert c._settings_loading(room) is None
