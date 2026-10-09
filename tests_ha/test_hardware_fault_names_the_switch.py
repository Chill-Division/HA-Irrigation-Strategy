"""A hardware fault names the switch that did not read OFF, as Home Assistant names it.

At the end of a shot the real controller switches off the valve the integration mapped, and reads
it back. Here it stays ON. The fault, its notification (CS-301) and the zone's status used to say
only "zone 1 valve/pump/mainline close not confirmed", which left the operator searching the
history of every switch the zone uses. Now they name it: its name in Home Assistant, its entity id
and what it read.
"""

import controller
from test_real_flow import VALVE
from test_recreated_room_controller import ARMED, KILL, _see
from test_setup_entry import _install


async def test_a_valve_left_on_is_named_as_home_assistant_names_it(
    hass, controller_for, monkeypatch
):
    await _install(hass)
    hass.states.async_set(VALVE, "off", {"friendly_name": "GT1 irrigation"})
    c, fake, _clock = controller_for({"enable_flag": KILL})
    _see(hass, fake)
    for switch in ARMED:
        fake.set_state(switch, "on")
    room = c.rooms[0]
    assert room.hw["valves"] == {1: VALVE}
    assert c._blocked(room, 1) is None

    switched = controller.ha_call

    def stuck(domain, service, **data):
        if (service, data.get("entity_id")) == ("turn_off", VALVE):
            fake.calls.append((domain, service, data))
            return True  # Home Assistant took the command; the relay never let go
        return switched(domain, service, **data)

    monkeypatch.setattr(controller, "ha_call", stuck)
    c._execute_shot(room, 1, 6, 2.0)

    assert room.hardware_fault["switches"] == [
        {"entity_id": VALVE, "problem": "on", "name": "GT1 irrigation"}
    ]
    named = f"GT1 irrigation ({VALVE}) still read ON 6 s after it was switched off"
    (notification,) = [
        data
        for domain, service, data in fake.calls
        if (domain, service) == ("persistent_notification", "create")
        and data["notification_id"] == f"f2_hardware_fault_{room.slug}"
    ]
    assert notification["message"].startswith(f"zone 1 shot end: {named}.")
    assert "Code CS-301" in notification["message"]
    assert c._blocked(room, 1) == f"hardware fault (CS-301): zone 1 shot end: {named}"
