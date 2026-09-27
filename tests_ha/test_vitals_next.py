"""The vitals notification, from the real controller on a real install: no clock and no LIVE line,
and, under each zone, what it will do next while the room's "Include Predictions in Notifications"
switch is on (it is, until someone switches it off; an upgraded room gets it on too)."""

from datetime import datetime

from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

SWITCH = "switch.crop_steering_notify_predictions"


def _vitals(fake):
    (message,) = [
        d["message"]
        for dom, svc, d in fake.calls
        if (dom, svc) == ("persistent_notification", "create")
        and d.get("notification_id") == "f2_vitals"
    ]
    return message.splitlines()


async def test_the_vitals_say_what_comes_next_until_the_room_switches_it_off(
    hass, controller_for
):
    await _install(hass)
    assert hass.states.get(SWITCH).state == "on"
    c, fake, _clock = controller_for({})
    c.loop_once(datetime.now())  # the first pass sends the vitals
    lines = _vitals(fake)
    assert lines[0] == "Watering off"  # a new room starts with watering off
    assert not {"LIVE", "HELD"} & set(" ".join(lines).split())
    assert not lines[0][:2].isdigit()  # no clock
    zone = next(i for i, line in enumerate(lines) if line.startswith("Z1 "))
    assert lines[zone + 1].startswith("Next: ")

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH}, blocking=True
    )
    # What the controller reads over REST from now on (the fake is the REST view it was built on).
    fake.set_state(SWITCH, hass.states.get(SWITCH).state)
    fake.calls.clear()
    c._last_notify = None  # the next vitals are due
    c.loop_once(datetime.now())
    assert not [line for line in _vitals(fake) if line.startswith("Next: ")]


async def test_an_upgraded_room_gets_the_switch_on(hass):
    await _upgrade(hass, "entry_2_17_wizard.json")
    assert hass.states.get(SWITCH).state == "on"
