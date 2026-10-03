"""The reservoir's level counts as no reading once its sensor has not reported for 10 minutes, in a real
Home Assistant read the way the controller reads it.

An ultrasonic that filters out its failed echoes stops sending, and Home Assistant keeps showing its
last value. What tells a sensor that has gone from one that is steady is `last_reported`, which Home
Assistant moves at every report even when the value is the same (`last_updated` does not). The
controller reads the state over REST; here its own `ha_get` reads Home Assistant's own state object,
as REST would send it, so the field it relies on is the one Home Assistant gives.
"""

import json
from datetime import timedelta
from types import SimpleNamespace

DISTANCE = "sensor.res_distance"


def _rest(hass, monkeypatch, controller):
    """The controller's REST session, answered from this Home Assistant's state machine."""

    def get(url, headers=None, timeout=None):
        state = hass.states.get(url.rsplit("/", 1)[1])
        body = json.loads(json.dumps(state.as_dict(), default=str))
        return SimpleNamespace(status_code=200, json=lambda: body)

    monkeypatch.setattr(controller, "_S", SimpleNamespace(get=get))


async def test_a_sensor_that_reports_the_same_value_is_read_and_one_that_has_gone_is_not(
    hass, freezer, monkeypatch
):
    import controller

    _rest(hass, monkeypatch, controller)
    level_now = controller.Controller._level_now  # uses nothing of the controller's but ha_get
    hass.states.async_set(DISTANCE, "300", {"unit_of_measurement": "mm"})
    first = hass.states.get(DISTANCE)
    updated, reported = first.last_updated, first.last_reported
    freezer.tick(timedelta(minutes=9))
    hass.states.async_set(DISTANCE, "300", {"unit_of_measurement": "mm"})  # the same value, again
    again = hass.states.get(DISTANCE)
    assert again.last_updated == updated and again.last_reported - reported == timedelta(minutes=9)
    read = controller.ha_get(DISTANCE)
    assert read.last_reported == again.last_reported.isoformat()

    freezer.tick(timedelta(minutes=9))  # 18 minutes unchanged, but reported 9 minutes ago
    assert level_now(None, DISTANCE) == 300.0
    freezer.tick(timedelta(minutes=2))  # 11 minutes since it last reported: it has gone
    assert level_now(None, DISTANCE) is None
    hass.states.async_set(DISTANCE, "310", {"unit_of_measurement": "mm"})
    assert level_now(None, DISTANCE) == 310.0
