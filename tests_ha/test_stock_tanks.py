"""Stock tanks in a real Home Assistant: the services through its registry and schemas, a tank as its
name, capacity, level, low mark and doser (what a batch takes is the feed recipe's), the low-stock
Repairs card, the room's stock sensor an automation can push a phone alert from, the tanks on the
Reservoir's dosers drawn by what each doser gave in a batch the controller mixed, and tanks stored
with a fixed dose per batch (before 2.32) loading in place."""

from homeassistant.core import Context
from homeassistant.helpers import issue_registry as ir
from test_setup_entry import _install
from test_upgrade_in_place import _upgrade

DOMAIN = "crop_steering"
ROOM = "room:"
SENSOR = "sensor.crop_steering_stock_low"
BATCH = "sensor.crop_steering_batch_status"


async def _service(hass, admin, name, **data):
    return await hass.services.async_call(
        DOMAIN,
        name,
        {"room_id": ROOM, **data},
        blocking=True,
        return_response=True,
        context=Context(user_id=admin.id),
    )


async def test_a_tank_warns_when_low_a_refill_clears_it_and_a_reload_keeps_its_level(
    hass, hass_admin_user
):
    entry = await _install(hass)
    assert not hass.services.has_service(DOMAIN, "stock_record_batch")  # retired in 2.32
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["tanks"] == [] and "fill_entity" not in doc
    doc = await _service(
        hass,
        hass_admin_user,
        "stock_save",
        expected_revision=doc["revision"],
        tanks=[{"name": "Bloom", "capacity_l": 10, "level_l": 6.4, "low_l": 7}],
    )
    assert "dose_ml" not in doc["tanks"][0]
    assert doc["doses"] == {"bloom": 0.0}  # on no doser: no batch takes from it
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "stock_low")
    assert issue is not None and issue.translation_placeholders["count"] == "1"
    state = hass.states.get(SENSOR)
    assert state.state == "1" and state.attributes["tanks"][0]["level_l"] == 6.4

    # A setup change reloads the room: the level survives it.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["tanks"][0]["level_l"] == 6.4

    doc = await _service(
        hass,
        hass_admin_user,
        "stock_refill",
        expected_revision=doc["revision"],
        id="bloom",
    )
    assert doc["tanks"][0]["level_l"] == 10
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, "stock_low") is None
    assert hass.states.get(SENSOR).state == "0"


async def test_stock_tanks_stored_with_a_dose_per_batch_load_in_place_with_the_rest(
    hass, hass_storage, hass_admin_user
):
    """In place: 2.31 kept a fixed dose per batch (or a dose entity) on each tank, and counted the
    tank last-fill entity's times. They load with their levels, low marks and dosers; the feed recipe
    in use says what a batch takes now."""
    stored = {
        "revision": 9,
        "tanks": [
            {
                "id": "bloom",
                "name": "Bloom",
                "capacity_l": 20,
                "level_l": 12.5,
                "dose_ml": 1200,
                "dose_entity": None,
                "doser": 3,
                "low_l": 4,
                "refilled_at": "2026-09-30T08:00:00+13:00",
                "updated_at": "2026-09-30T08:00:00+13:00",
            },
            {
                "id": "ph_down",
                "name": "pH down",
                "capacity_l": 5,
                "level_l": 2,
                "dose_ml": 60,
                "dose_entity": "number.doser_ph_dose",
                "doser": None,
                "low_l": 1,
                "refilled_at": None,
                "updated_at": "2026-09-30T08:00:00+13:00",
            },
        ],
        "last_batch": "2026-10-01T07:00:00+13:00",
        "reservoir_batch": "2026-10-02T07:00:00+13:00",
        "history": [
            {"at": "2026-10-01T07:00:00+13:00", "source": "fill", "draw_ml": {"bloom": 1200.0}}
        ],
    }
    key = "crop_steering.stock.seeded2x17wizard0000000000000001"
    hass_storage[key] = {"version": 1, "minor_version": 1, "key": key, "data": stored}
    await _upgrade(hass, "entry_2_17_wizard.json")
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["error"] is None and doc["revision"] == 9
    assert [
        (tank["name"], tank["level_l"], tank["low_l"], tank["doser"], tank["refilled_at"])
        for tank in doc["tanks"]
    ] == [
        ("Bloom", 12.5, 4, 3, "2026-09-30T08:00:00+13:00"),
        ("pH down", 2, 1, None, None),
    ]
    assert not any("dose_ml" in tank or "dose_entity" in tank for tank in doc["tanks"])
    assert doc["history"][0]["source"] == "fill"  # the record of what was counted stays
    state = hass.states.get(SENSOR)
    assert state.attributes["last_batch"] == "2026-10-01T07:00:00+13:00"


async def test_tanks_on_dosers_lose_what_each_doser_gave_in_the_reservoirs_batches(
    hass, hass_admin_user
):
    """The owner's room: Athena's bottles on the Reservoir's four dosers, each stock tank naming its
    doser. A batch the controller reports it finished draws what each doser gave, once.
    """
    from datetime import timedelta

    from homeassistant.util import dt as dt_util
    from test_feed_batches import FLOWER, RESERVOIR
    from test_setup_save_plumbing import _payload, _room

    hass.states.async_set("sensor.res_distance", "812", {"unit_of_measurement": "mm"})
    for entity in list(RESERVOIR.values())[1:]:
        hass.states.async_set(entity, "off")
    entry = await _install(hass)
    room = await _room(hass, hass_admin_user)
    await hass.services.async_call(
        DOMAIN,
        "setup_save",
        _payload(room, hardware=RESERVOIR),
        blocking=True,
        return_response=True,
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    feed = await _service(hass, hass_admin_user, "feed_get")
    # FLOWER puts Core on doser 4, Bloom on 3, Balance on 2 and Cleanse on 1.
    await _service(
        hass,
        hass_admin_user,
        "feed_save",
        expected_revision=feed["revision"],
        document={"batch_l": 145, "recipes": [FLOWER], "stage": "flower"},
    )
    doc = await _service(hass, hass_admin_user, "stock_get")
    doc = await _service(
        hass,
        hass_admin_user,
        "stock_save",
        expected_revision=doc["revision"],
        tanks=[
            {"name": "Core", "capacity_l": 20, "doser": 4},
            {"name": "Balance", "capacity_l": 20, "doser": 2},
            {"name": "pH down", "capacity_l": 5},
        ],
    )
    assert doc["dosers"]["4"] == {"switch": "switch.doser_4_power", "nutrient": "Core"}
    # What the recipe in use gives from each tank's doser, whole mL; on no doser, nothing.
    assert doc["doses"] == {"core": 725, "balance": 242, "ph_down": 0.0}

    # The controller reports the batch that just ended, as it does every pass.
    ended = (dt_util.utcnow() + timedelta(minutes=1)).isoformat(timespec="seconds")
    last = {"at": ended, "result": "done", "stage": "Flower",
            "dosed": {"4": 725.0, "3": 1208.3, "2": 241.7, "1": 120.8}}  # fmt: skip
    for _ in range(2):  # reported again the next pass: counted once
        hass.states.async_set(BATCH, "idle", {"last": last})
        await hass.async_block_till_done()
    doc = await _service(hass, hass_admin_user, "stock_get")
    levels = {tank["id"]: tank["level_l"] for tank in doc["tanks"]}
    assert levels == {"core": 19.275, "balance": 19.7583, "ph_down": 5}
    assert doc["history"][0]["source"] == "reservoir"

    # A reload of the room (a setup change) counts nothing twice.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set(BATCH, "mixing", {"last": last})
    await hass.async_block_till_done()
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["tanks"][0]["level_l"] == 19.275
    state = hass.states.get(SENSOR)
    assert state.attributes["tanks"][0]["doser"] == 4
    # 19.275 L at the 725 mL Flower takes from Core is about 26 batches.
    assert state.attributes["tanks"][0]["dose_ml"] == 725
    assert state.attributes["tanks"][0]["batches_left"] == 26
