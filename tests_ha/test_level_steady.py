"""A still reservoir's level reads, however long since it last changed, in a real Home Assistant read the
way the controller reads it: its REST state.

GR2, 3 October: the reservoir held at 664.56 mm for hours. Its ESPHome ultrasonic read it every 5
seconds, but Home Assistant's ESPHome integration drops a reading that repeats the last, so the state in
Home Assistant was hours old, and 2.32.0 and 2.32.1 read the level as gone. A level is no reading only
when Home Assistant has none: unavailable, or unknown, which ESPHome's timeout filter sends for a sensor
whose readings have failed.
"""

import json
from datetime import timedelta
from types import SimpleNamespace

DISTANCE = "sensor.res_distance"


def _rest(hass, monkeypatch, controller):
    """The controller's REST session, answered by this Home Assistant as its API would answer."""

    def get(url, headers=None, timeout=None):
        state = hass.states.get(url.rsplit("/", 1)[1])
        body = json.loads(state.as_dict_json)  # the copy the REST API serves
        return SimpleNamespace(status_code=200, json=lambda: body)

    monkeypatch.setattr(controller, "_S", SimpleNamespace(get=get))


async def test_a_still_reservoir_reads_and_a_sensor_reading_unknown_does_not(
    hass, freezer, monkeypatch
):
    import controller

    _rest(hass, monkeypatch, controller)
    level_now = controller.Controller._level_now  # uses nothing of the controller's but its reads
    hass.states.async_set(DISTANCE, "664.564", {"unit_of_measurement": "mm"})
    assert level_now(None, DISTANCE) == 664.564
    freezer.tick(timedelta(hours=3))  # nothing new for hours: the reservoir is still
    assert level_now(None, DISTANCE) == 664.564
    hass.states.async_set(DISTANCE, "unknown", {"unit_of_measurement": "mm"})  # a timeout filter
    assert level_now(None, DISTANCE) is None
    hass.states.async_set(DISTANCE, "unavailable")  # the device offline
    assert level_now(None, DISTANCE) is None
