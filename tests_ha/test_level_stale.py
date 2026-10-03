"""The reservoir's level counts as no reading once its sensor has not reported for 10 minutes, in a real
Home Assistant read the way the controller reads it.

An ultrasonic that filters out its failed echoes stops sending, and Home Assistant keeps showing its
last value. What tells a sensor that has gone from one that is steady is `last_reported`, which Home
Assistant moves at every report even when the value is the same. But the JSON its REST API serves is
the state's cached copy, which a same-value report does not renew: 2.32.0 read that copy, and a level
that held steady for 10 minutes read as gone. The controller now reads last_reported live, through
the template API. Here its own `ha_get` and `ha_reported` get what Home Assistant would send: the
cached JSON, and the template rendered by Home Assistant's own template engine.
"""

import json
from datetime import datetime, timedelta
from types import SimpleNamespace

DISTANCE = "sensor.res_distance"


def _rest(hass, monkeypatch, controller):
    """The controller's REST session, answered by this Home Assistant as its API would answer."""
    from homeassistant.helpers.template import Template

    def get(url, headers=None, timeout=None):
        state = hass.states.get(url.rsplit("/", 1)[1])
        body = json.loads(state.as_dict_json)  # the copy the REST API serves
        return SimpleNamespace(status_code=200, json=lambda: body)

    def post(url, headers=None, timeout=None, **request):
        assert url.endswith("/template")
        text = Template(request["json"]["template"], hass).async_render(parse_result=False)
        return SimpleNamespace(status_code=200, text=str(text))

    monkeypatch.setattr(controller, "_S", SimpleNamespace(get=get, post=post))


async def test_a_sensor_reporting_the_same_value_is_read_and_one_that_has_gone_is_not(
    hass, freezer, monkeypatch
):
    import controller

    _rest(hass, monkeypatch, controller)
    level_now = controller.Controller._level_now  # uses nothing of the controller's but its reads
    hass.states.async_set(DISTANCE, "300", {"unit_of_measurement": "mm"})
    served = controller.ha_get(DISTANCE)  # served once over REST: Home Assistant keeps that copy
    freezer.tick(timedelta(minutes=9))
    hass.states.async_set(DISTANCE, "300", {"unit_of_measurement": "mm"})  # the same value, again

    # The REST copy still says when it was first served; the template says when it last reported.
    assert controller.ha_get(DISTANCE).last_reported == served.last_reported
    live = controller.ha_reported(DISTANCE)
    assert live == hass.states.get(DISTANCE).last_reported
    assert live - datetime.fromisoformat(served.last_reported) == timedelta(minutes=9)

    freezer.tick(timedelta(minutes=9))  # 18 minutes unchanged, but reported 9 minutes ago
    assert level_now(None, DISTANCE) == 300.0
    freezer.tick(timedelta(minutes=2))  # 11 minutes since it last reported: it has gone
    assert level_now(None, DISTANCE) is None
    hass.states.async_set(DISTANCE, "310", {"unit_of_measurement": "mm"})
    assert level_now(None, DISTANCE) == 310.0
    assert controller.ha_reported("sensor.not_there") is None
