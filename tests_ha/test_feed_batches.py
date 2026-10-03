"""Nutrient batches in a real Home Assistant: a room's reservoir and dosers, mapped in Rooms & hardware,
reach the controller's descriptor; the feed settings save through the real services and schemas;
the feed plan sensor and the feed stage select follow them; the room's Automatic batches switch
and Mix a Batch Now button exist, off and never pressed; and the dashboard's Mix a batch now presses
that button once the plan can run."""

from datetime import datetime

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError
from test_setup_save_plumbing import _payload, _room, _service
from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

DESCRIPTOR = "sensor.crop_steering_engine_config"
PLAN = "sensor.crop_steering_feed_plan"
STAGE = "select.crop_steering_feed_stage"
AUTO = "switch.crop_steering_auto_batches"
MIX = "button.crop_steering_mix_batch"
RESERVOIR = {
    "reservoir_distance_sensor": "sensor.res_distance",
    "fresh_water_switch": "switch.mainswater",
    "recirc_switch": "switch.recirc",
    "doser_1_switch": "switch.doser_1_power",
    "doser_2_switch": "switch.doser_2_power",
    "doser_3_switch": "switch.doser_3_power",
    "doser_4_switch": "switch.doser_4_power",
}
FLOWER = {
    "id": "flower",
    "name": "Flower",
    "strength": 5 / 3,
    "doses": {
        "4": {"label": "Core", "parts": 3},
        "3": {"label": "Bloom", "parts": 5},
        "2": {"label": "Balance", "parts": 1},
        "1": {"label": "Cleanse", "parts": 0.5},
    },
}


async def test_a_new_room_has_its_batch_entities_and_nothing_to_run(
    hass, hass_admin_user
):
    await _install(hass)
    assert hass.states.get(AUTO).state == "off"  # automatic batches are opt-in
    assert hass.states.get(MIX).state == "unknown"  # never pressed
    plan = hass.states.get(PLAN)
    assert plan.state == "none"
    assert plan.attributes["problem"] == "No doser is mapped in Settings → Rooms & hardware."
    assert hass.states.get(STAGE).state == "unavailable"  # no feed recipe yet
    assert not set(RESERVOIR) & set(hass.states.get(DESCRIPTOR).attributes)
    with pytest.raises(HomeAssistantError, match="No doser is mapped"):
        await _service(hass, hass_admin_user, "feed_mix", {"room_id": "room:"})
    assert hass.states.get(MIX).state == "unknown"


async def test_a_mapped_reservoir_and_a_saved_recipe_become_the_controllers_plan(
    hass, hass_admin_user
):
    hass.states.async_set(
        "sensor.res_distance", "846.41", {"unit_of_measurement": "mm"}
    )
    for entity in list(RESERVOIR.values())[1:]:
        hass.states.async_set(entity, "off")
    await _install(hass)
    room = await _room(hass, hass_admin_user)
    await _service(
        hass, hass_admin_user, "setup_save", _payload(room, hardware=RESERVOIR)
    )
    await hass.async_block_till_done()
    descriptor = hass.states.get(DESCRIPTOR).attributes
    assert {key: descriptor.get(key) for key in RESERVOIR} == RESERVOIR

    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    assert doc["mapped"] == {str(n): f"switch.doser_{n}_power" for n in (1, 2, 3, 4)}
    doc = await _service(
        hass,
        hass_admin_user,
        "feed_save",
        {
            "room_id": "room:",
            "expected_revision": doc["revision"],
            "document": {
                "batch_l": 145,
                "fill_s": 621,
                "empty_mm": 800,
                "order": [4, 3, 2, 1],
                "recipes": [FLOWER, {**FLOWER, "id": "vege", "name": "Vege"}],
                "stage": "flower",
            },
        },
    )
    assert doc["plan"]["problem"] is None
    plan = hass.states.get(PLAN)
    assert plan.state == "Flower"
    assert [(d["doser"], d["ml"]) for d in plan.attributes["doses"]] == [
        (4, 725),  # to the whole mL, in the room's order the recipe was saved with
        (3, 1208),
        (2, 242),
        (1, 121),
    ]
    assert (plan.attributes["fill_s"], plan.attributes["empty_mm"]) == (621, 800.0)

    stage = hass.states.get(STAGE)
    assert stage.state == "Flower" and stage.attributes["options"] == ["Flower", "Vege"]
    await hass.services.async_call(
        "select", "select_option", {"entity_id": STAGE, "option": "Vege"}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get(PLAN).state == "Vege"

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": MIX},
        blocking=True,
        context=Context(user_id=hass_admin_user.id),
    )
    pressed = hass.states.get(MIX).state
    assert pressed not in ("unknown", "unavailable")  # when it was pressed

    mixed = await _service(hass, hass_admin_user, "feed_mix", {"room_id": "room:"})
    assert mixed["requested"] == hass.states.get(MIX).state != pressed


async def test_a_doser_cannot_share_a_switch_with_the_pump_or_another_doser(
    hass, hass_admin_user
):
    for entity in ("switch.doser_1_power", "switch.recirc"):
        hass.states.async_set(entity, "off")
    await _install(hass)
    room = await _room(hass, hass_admin_user)
    same = {
        "doser_1_switch": "switch.doser_1_power",
        "doser_2_switch": "switch.doser_1_power",
    }
    with pytest.raises(HomeAssistantError, match="need a switch of their own"):
        await _service(
            hass, hass_admin_user, "setup_save", _payload(room, hardware=same)
        )


async def test_a_recipe_saved_before_the_dosers_are_mapped_runs_once_they_are(
    hass, hass_admin_user
):
    await _install(hass)
    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    await _service(
        hass,
        hass_admin_user,
        "feed_save",
        {
            "room_id": "room:",
            "expected_revision": doc["revision"],
            "document": {"batch_l": 145, "recipes": [FLOWER], "stage": "flower"},
        },
    )
    assert (
        hass.states.get(PLAN).attributes["problem"]
        == "No doser is mapped in Settings → Rooms & hardware."
    )
    for entity in list(RESERVOIR.values())[1:]:
        hass.states.async_set(entity, "off")
    hass.states.async_set("sensor.res_distance", "300", {"unit_of_measurement": "cm"})
    room = await _room(hass, hass_admin_user)
    await _service(
        hass, hass_admin_user, "setup_save", _payload(room, hardware=RESERVOIR)
    )
    await hass.async_block_till_done()  # the room reloads with its new mapping
    plan = hass.states.get(PLAN)
    assert plan.state == "Flower" and plan.attributes["problem"] is None
    assert [d["doser"] for d in plan.attributes["doses"]] == [
        1,
        2,
        3,
        4,
    ]  # no order: by number
    assert plan.attributes["revision"] == 1  # the saved settings survived the reload


async def test_the_reservoirs_distances_and_minimum_reach_the_real_controller_as_a_level(
    hass, hass_admin_user, controller_for
):
    """Saved through the real feed_save, the distances when full and when empty and the minimum are on
    the feed plan sensor; the real controller reads the level sensor through them as a percentage,
    sees a refill due, and publishes the level for the dashboard."""
    hass.states.async_set(
        "sensor.res_distance", "846.41", {"unit_of_measurement": "mm"}
    )
    for entity in list(RESERVOIR.values())[1:]:
        hass.states.async_set(entity, "off")
    await _install(hass)
    room = await _room(hass, hass_admin_user)
    await _service(
        hass, hass_admin_user, "setup_save", _payload(room, hardware=RESERVOIR)
    )
    await hass.async_block_till_done()
    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    settings = {"batch_l": 145, "fill_s": 690, "full_mm": 125, "empty_mm": 850}
    with pytest.raises(HomeAssistantError, match="distance when full must be less"):
        await _service(
            hass,
            hass_admin_user,
            "feed_save",
            {
                "room_id": "room:",
                "expected_revision": doc["revision"],
                "document": {**settings, "full_mm": 850, "empty_mm": 125},
            },
        )
    doc = await _service(
        hass,
        hass_admin_user,
        "feed_save",
        {
            "room_id": "room:",
            "expected_revision": doc["revision"],
            "document": {
                **settings,
                "order": [4, 3, 2, 1],
                "recipes": [FLOWER],
                "stage": "flower",
            },
        },
    )
    plan = hass.states.get(PLAN).attributes
    assert (plan["full_mm"], plan["empty_mm"], plan["min_pct"], plan["mix_s"]) == (
        125.0,
        850.0,
        5.0,
        10,
    )
    assert "settle_s" not in plan

    c, fake, _clock = controller_for({})
    controller_room = c.rooms[0]
    c._batch_tick(controller_room, datetime.now())
    assert controller_room._res["pct"] == pytest.approx(
        (850 - 846.41) / 725 * 100
    )
    assert c._refill_due(controller_room) is True  # under 5%: a refill is due
    status = fake.sets["sensor.crop_steering_batch_status"][1]
    assert (status["level_pct"], status["min_pct"], status["due"]) == (0.5, 5.0, True)


async def test_a_feed_document_stored_by_2_30_loads_with_its_mark_as_the_empty_distance(
    hass, hass_storage
):
    """In place: a room's feed settings as 2.30.1 stored them (made by its own feed.clean), with an
    "almost empty at" mark of 800 mm and a 20 s settle. They load: the mark is the distance when
    empty, the settle is gone, and the distance when full and the minimum start at their defaults;
    nothing else changes, its recipe and revision included."""
    stored = {
        "revision": 5,
        "fill_s": 690,
        "batch_l": 145.0,
        "empty_mm": 800.0,
        "settle_s": 20,
        "pause_s": 10,
        "mix_s": 600,
        "dosers": {"1": {"flow_ml_min": 600.0}},
        "order": [2, 1],
        "recipes": [
            {
                "id": "flower",
                "name": "Flower",
                "strength": 1.667,
                "doses": {
                    "2": {"label": "Bloom", "parts": 5.0},
                    "1": {"label": "Core", "parts": 3.0},
                },
            }
        ],
        "stage": "flower",
    }
    key = "crop_steering.feed.seeded2x17wizard0000000000000001"
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": stored}
    await _upgrade(hass, "entry_2_17_wizard.json")
    plan = hass.states.get(PLAN)
    assert plan.state == "Flower"
    assert (
        plan.attributes["empty_mm"],
        plan.attributes["full_mm"],
        plan.attributes["min_pct"],
        plan.attributes["mix_s"],
        plan.attributes["fill_s"],
        plan.attributes["batch_l"],
    ) == (800.0, 0.0, 5.0, 600, 690, 145.0)
    assert "settle_s" not in plan.attributes and plan.attributes["revision"] == 5


async def test_a_feed_document_stored_by_2_31_gives_each_recipe_the_rooms_order(
    hass, hass_storage, hass_admin_user
):
    """In place: 2.31 kept one dosing order for the room. Each recipe has its own now, and one stored
    before that takes the room's, so nothing doses in another order after the update; a recipe saved
    with its own order doses in it, as the plan sensor the controller reads says. Doses are whole mL.
    """
    stored = {
        "revision": 7,
        "fill_s": 690,
        "batch_l": 145.0,
        "full_mm": 125.0,
        "empty_mm": 850.0,
        "min_pct": 5.0,
        "pause_s": 10,
        "mix_s": 10,
        "dosers": {},
        "order": [4, 3, 2, 1],
        "recipes": [
            {
                "id": "bloom",
                "name": "Bloom",
                "strength": 1.655,
                "doses": {
                    "4": {"label": "Core", "parts": 3},
                    "3": {"label": "Bloom", "parts": 5},
                    "2": {"label": "Balance", "parts": 1},
                    "1": {"label": "Cleanse", "parts": 0.5},
                },
            }
        ],
        "stage": "bloom",
    }
    key = "crop_steering.feed.seeded2x17wizard0000000000000001"
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": stored}
    hass.states.async_set("sensor.res_distance", "300", {"unit_of_measurement": "mm"})
    for entity in list(RESERVOIR.values())[1:]:
        hass.states.async_set(entity, "off")
    await _upgrade(hass, "entry_2_17_wizard.json")
    room = await _room(hass, hass_admin_user)
    await _service(
        hass, hass_admin_user, "setup_save", _payload(room, hardware=RESERVOIR)
    )
    await hass.async_block_till_done()
    doses = lambda: [  # noqa: E731
        (d["doser"], d["ml"]) for d in hass.states.get(PLAN).attributes["doses"]
    ]
    assert doses() == [(4, 720), (3, 1200), (2, 240), (1, 120)]

    doc = await _service(hass, hass_admin_user, "feed_get", {"room_id": "room:"})
    assert doc["recipes"][0]["order"] == [4, 3, 2, 1] and doc["revision"] == 7
    recipe = {**doc["recipes"][0], "order": [1, 2, 3, 4]}
    await _service(
        hass,
        hass_admin_user,
        "feed_save",
        {
            "room_id": "room:",
            "expected_revision": doc["revision"],
            "document": {"recipes": [recipe]},
        },
    )
    assert doses() == [(1, 120), (2, 240), (3, 1200), (4, 720)]
