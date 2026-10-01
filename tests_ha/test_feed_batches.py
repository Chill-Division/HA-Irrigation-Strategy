"""Nutrient batches in a real Home Assistant: a room's reservoir and dosers, mapped in Rooms & hardware,
reach the controller's descriptor; the feed settings save through the real services and schemas;
the feed plan sensor and the feed stage select follow them; the room's Automatic batches switch
and Mix a Batch Now button exist, off and never pressed; and the dashboard's Mix a batch now presses
that button once the plan can run."""

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError
from test_setup_save_plumbing import _payload, _room, _service
from test_setup_entry import _install

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
        (4, 725.0),
        (3, 1208.3),
        (2, 241.7),
        (1, 120.8),
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
