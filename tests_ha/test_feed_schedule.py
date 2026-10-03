"""The feed schedule in a real Home Assistant: each week of the grow doses its own recipe from the day
Week 1 starts, the feed plan sensor (which the controller reads) and the feed stage select follow it,
and at Home Assistant's midnight that starts a new week they move on by themselves. A stage picked in
Home Assistant while the schedule runs holds until the schedule's next week starts. A feed document
stored before the schedule loads in place with none.
"""

from datetime import datetime

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from test_feed_batches import FLOWER, PLAN, STAGE
from test_setup_entry import _install
from test_setup_save_plumbing import _service
from test_upgrade_in_place import _upgrade

VEGE = {**FLOWER, "id": "vege", "name": "Vege"}
FADE = {**FLOWER, "id": "fade", "name": "Fade"}


def _local(hass, *parts):
    return datetime(*parts, tzinfo=dt_util.get_time_zone(hass.config.time_zone))


async def test_the_schedule_moves_the_stage_at_midnight_and_a_pick_holds_until_next_week(
    hass, hass_admin_user, freezer
):
    freezer.move_to(_local(hass, 2026, 10, 7, 12, 0))  # Wednesday of week 1
    await _install(hass)
    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    await _service(
        hass,
        hass_admin_user,
        "feed_save",
        {
            "room_id": "room:",
            "expected_revision": doc["revision"],
            "document": {
                "recipes": [VEGE, FLOWER, FADE],
                "stage": "vege",
                # Week 1 from Monday 5 October: Vege, then Flower, Flower, Fade
                "schedule": {
                    "start": "2026-10-05",
                    "weeks": ["vege", "flower", "flower", "fade"],
                },
            },
        },
    )
    plan = hass.states.get(PLAN)
    assert (plan.state, plan.attributes["week"], plan.attributes["source"]) == (
        "Vege",
        1,
        "schedule",
    )

    # Picked in Home Assistant: it holds until week 2 starts, Monday 12 October.
    await hass.services.async_call(
        "select", "select_option", {"entity_id": STAGE, "option": "Fade"}, blocking=True
    )
    await hass.async_block_till_done()
    plan = hass.states.get(PLAN)
    assert (plan.state, plan.attributes["source"], plan.attributes["held_until"]) == (
        "Fade",
        "held",
        "2026-10-12",
    )
    assert hass.states.get(STAGE).state == "Fade"

    # Home Assistant's midnight that starts week 2: Flower, the hold over, with nobody touching it.
    midnight = _local(hass, 2026, 10, 12, 0, 0, 1)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, dt_util.as_utc(midnight))
    await hass.async_block_till_done()
    plan = hass.states.get(PLAN)
    assert (plan.state, plan.attributes["week"], plan.attributes["source"]) == (
        "Flower",
        2,
        "schedule",
    )
    assert plan.attributes["held_until"] is None
    assert hass.states.get(STAGE).state == "Flower"


async def test_a_feed_document_stored_before_the_schedule_loads_with_none(
    hass, hass_storage, hass_admin_user
):
    stored = {
        "revision": 4,
        "fill_s": 690,
        "batch_l": 145.0,
        "full_mm": 125.0,
        "empty_mm": 850.0,
        "min_pct": 5.0,
        "pause_s": 10,
        "mix_s": 10,
        "dosers": {},
        "order": [],
        "recipes": [{**FLOWER, "order": [4, 3, 2, 1]}],
        "stage": "flower",
    }
    key = "crop_steering.feed.seeded2x17wizard0000000000000001"
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": stored}
    await _upgrade(hass, "entry_2_17_wizard.json")
    plan = hass.states.get(PLAN)
    assert (plan.state, plan.attributes["source"], plan.attributes["week"]) == (
        "Flower",
        "hand",
        None,
    )
    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    assert doc["schedule"] == {"start": None, "weeks": []} and doc["revision"] == 4
