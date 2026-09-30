"""The dashboard's grow day says who changed a room's setting, from Home Assistant's logbook: a
person by the user behind the change, Auto setpoints by the Supervisor's user (the controller writes
through it, and it is nobody's person), an automation by its name.

These change a real room's maintenance trigger those three ways, then read the logbook back the two
ways the dashboard does: over the websocket inside Home Assistant (`logbook/get_events`) and over
REST standalone (`/api/logbook`). What they rely on is Home Assistant's, so it is proven on each
Home Assistant this tier runs."""

from datetime import timedelta

import pytest
from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.core import Context
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from test_setup_entry import _install

pytestmark = pytest.mark.web_server
TRIGGER = "number.crop_steering_zone_1_p2_vwc_threshold"


@pytest.fixture
def mock_recorder_before_hass(async_test_recorder):
    """The recorder's database is made before Home Assistant is: the test plugin's rule, which
    this repository's own autouse fixtures (they need `hass`) would otherwise break."""


async def test_the_logbook_says_who_changed_a_setting(
    recorder_mock, hass, hass_admin_user, hass_ws_client, hass_client
):
    assert await async_setup_component(hass, "logbook", {})
    # The person the dashboard names the signed-in user by.
    assert await async_setup_component(
        hass,
        "person",
        {"person": [{"id": "sam", "name": "Sam", "user_id": hass_admin_user.id}]},
    )
    await _install(hass)
    assert hass.states.get(TRIGGER) is not None
    start = dt_util.utcnow() - timedelta(seconds=1)

    # As the dashboard changes it: number.set_value over the websocket, as the signed-in user.
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "number",
            "service": "set_value",
            "service_data": {"entity_id": TRIGGER, "value": 58},
        }
    )
    assert (await ws.receive_json())["success"]
    # As Auto setpoints does: the controller calls Home Assistant as the Supervisor's user.
    supervisor = await hass.auth.async_create_system_user(
        "Supervisor", group_ids=[GROUP_ID_ADMIN]
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": TRIGGER, "value": 57},
        blocking=True,
        context=Context(user_id=supervisor.id),
    )
    # As an automation does.
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "alias": "Morning tweak",
                "triggers": [{"trigger": "event", "event_type": "tweak"}],
                "actions": [
                    {
                        "action": "number.set_value",
                        "target": {"entity_id": TRIGGER},
                        "data": {"value": 56},
                    }
                ],
            }
        },
    )
    hass.bus.async_fire("tweak")
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    end = dt_util.utcnow() + timedelta(seconds=1)

    person = hass.states.get("person.sam")
    assert person.attributes["user_id"] == hass_admin_user.id
    assert hass.states.get(TRIGGER).state == "56.0"

    def by_value(entries):
        return {
            float(entry["state"]): entry
            for entry in entries
            if entry.get("entity_id") == TRIGGER
            and entry["state"] not in ("unknown", "unavailable")
        }

    await ws.send_json_auto_id(
        {
            "type": "logbook/get_events",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "entity_ids": [TRIGGER],
        }
    )
    reply = await ws.receive_json()
    assert reply["success"], reply
    over_websocket = by_value(reply["result"])

    client = await hass_client()
    response = await client.get(
        f"/api/logbook/{start.isoformat()}",
        params={"end_time": end.isoformat(), "entity": TRIGGER},
    )
    assert response.status == 200
    over_rest = by_value(await response.json())

    for entries in (over_websocket, over_rest):
        assert entries[58]["context_user_id"] == hass_admin_user.id
        assert entries[57]["context_user_id"] == supervisor.id
        assert entries[56]["context_event_type"] == "automation_triggered"
        assert entries[56]["context_name"] == "Morning tweak"
    # The websocket gives the time in epoch seconds, REST as an ISO time: the dashboard reads both.
    assert isinstance(over_websocket[58]["when"], float)
    assert dt_util.parse_datetime(over_rest[58]["when"]) is not None
