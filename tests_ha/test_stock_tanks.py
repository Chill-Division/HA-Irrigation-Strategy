"""Stock tanks in a real Home Assistant: the services through its registry and schemas, each batch
counted once from the tank's last-fill entity (a reload of the room included), the low-stock
Repairs card, the room's stock sensor an automation can push a phone alert from, and the tanks on
the Reservoir's dosers drawn by what each doser gave in a batch the controller mixed."""

from homeassistant.core import Context
from homeassistant.helpers import issue_registry as ir
from test_setup_entry import _install

DOMAIN = "crop_steering"
ROOM = "room:"
FILL = "sensor.batch_tank_last_fill"
DOSE = "number.doser_bloom_dose"
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


async def _fill(hass, when):
    hass.states.async_set(FILL, when, {"device_class": "timestamp"})
    await hass.async_block_till_done()


async def test_each_batch_draws_once_warns_when_low_and_a_refill_clears_it(
    hass, hass_admin_user
):
    # The tank was last filled before the stock tanks were set up: that fill is not counted.
    hass.states.async_set(
        FILL, "2026-09-24T07:16:08+00:00", {"device_class": "timestamp"}
    )
    hass.states.async_set(DOSE, "1800", {"unit_of_measurement": "mL"})
    entry = await _install(hass, {"tank_last_fill_sensor": FILL})

    doc = await _service(hass, hass_admin_user, "stock_get")
    assert (doc["tanks"], doc["fill_entity"]) == ([], FILL)
    doc = await _service(
        hass,
        hass_admin_user,
        "stock_save",
        expected_revision=doc["revision"],
        tanks=[
            {
                "name": "Bloom",
                "capacity_l": 10,
                "dose_ml": 500,
                "dose_entity": DOSE,
                "low_l": 7,
            }
        ],
    )
    assert doc["tanks"][0]["level_l"] == 10 and doc["doses"] == {"bloom": 1800.0}
    assert hass.states.get(SENSOR).state == "0"

    # A new fill is one batch; the same time coming back (a device reconnecting) is not.
    await _fill(hass, "2026-09-25T07:02:00+00:00")
    await _fill(hass, "unavailable")
    await _fill(hass, "2026-09-25T07:02:00+00:00")
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["tanks"][0]["level_l"] == 8.2
    assert doc["history"][0]["draw_ml"] == {"bloom": 1800.0}

    await _fill(hass, "2026-09-26T07:00:00+00:00")
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "stock_low")
    assert issue is not None and issue.translation_placeholders["count"] == "1"
    assert "about 3 batches left" in issue.translation_placeholders["tanks"]
    state = hass.states.get(SENSOR)
    assert state.state == "1"
    assert state.attributes["tanks"][0]["level_l"] == 6.4
    assert state.attributes["tanks"][0]["batches_left"] == 3

    # A setup change reloads the room: the level and the counted fill survive it.
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


async def test_a_room_without_a_fill_entity_records_batches_by_hand(
    hass, hass_admin_user
):
    await _install(hass)
    doc = await _service(hass, hass_admin_user, "stock_get")
    assert doc["fill_entity"] is None
    doc = await _service(
        hass,
        hass_admin_user,
        "stock_save",
        expected_revision=doc["revision"],
        tanks=[{"name": "Part A", "capacity_l": 5, "dose_ml": 250}],
    )
    doc = await _service(
        hass, hass_admin_user, "stock_record_batch", expected_revision=doc["revision"]
    )
    assert doc["tanks"][0]["level_l"] == 4.75
    assert doc["history"][0]["source"] == "manual"


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
            {"name": "pH down", "capacity_l": 5, "dose_ml": 60},
        ],
    )
    assert doc["dosers"]["4"] == {"switch": "switch.doser_4_power", "nutrient": "Core"}
    assert doc["doses"] == {"core": 725, "balance": 242, "ph_down": 60.0}  # whole mL

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
