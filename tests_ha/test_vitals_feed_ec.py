"""The vitals notification, from the real controller looking at a real install, says nothing about feed EC:
the source-water gate and its probes were removed in 2.26.0."""

from datetime import datetime

from test_setup_entry import _install


async def test_a_room_with_no_feed_ec_probe_says_nothing_about_feed_ec(hass, controller_for):
    await _install(hass)
    c, fake, _clock = controller_for({"feed_ec_sensor": "sensor.tank_ec"})  # an old option: ignored
    c.loop_once(datetime.now())  # the first pass sends the vitals
    (message,) = [
        d["message"]
        for dom, svc, d in fake.calls
        if (dom, svc) == ("persistent_notification", "create") and d.get("notification_id") == "f2_vitals"
    ]
    assert "LIVE" in message or "HELD" in message
    assert "feed EC" not in message
