"""The stock-tank store: revisions, refills, each Reservoir batch counted once, what a batch takes
from each tank (the feed recipe in use), and the low-stock Repairs card."""

import asyncio
import copy
from datetime import timedelta, timezone
import sys
import types

import pytest

from . import ha_stubs

ha_stubs.install()

from custom_components.crop_steering import feed_api, stock_api  # noqa: E402
from custom_components.crop_steering.const import DOMAIN  # noqa: E402

NZ = timezone(timedelta(hours=12))
BLOOM = {"name": "Bloom", "capacity_l": 50, "low_l": 10}


class MemoryStore:
    def __init__(self, value=None):
        self.value, self.saves = value, 0

    async def async_load(self):
        return copy.deepcopy(self.value)

    async def async_save(self, value):
        self.value, self.saves = copy.deepcopy(value), self.saves + 1


@pytest.fixture(autouse=True)
def dispatcher(monkeypatch):
    module = types.ModuleType("homeassistant.helpers.dispatcher")
    module.sent = []
    module.async_dispatcher_send = lambda hass, signal, *a: module.sent.append(signal)
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.dispatcher", module)
    monkeypatch.setattr(
        sys.modules["homeassistant.util.dt"],
        "get_default_time_zone",
        lambda: NZ,
        raising=False,
    )
    return module


def rig(value=None, states=None):
    hass = ha_stubs.FakeHass(states=states, data={DOMAIN: {"entry": {"hardware": {}}}})
    store = stock_api.StockStore(
        hass, ha_stubs.FakeEntry(entry_id="entry"), MemoryStore(value)
    )
    asyncio.run(store.async_init())
    return hass, store


def mutate(store, action, **data):
    data.setdefault("expected_revision", store.data["revision"])
    return asyncio.run(store.mutate(action, data))


def test_a_fresh_room_has_no_tanks():
    _, store = rig()
    response = store.response()
    assert (response["room_id"], response["revision"], response["tanks"]) == (
        "room:",
        0,
        [],
    )
    assert response["error"] is None and "fill_entity" not in response


def test_a_batch_is_no_longer_recorded_by_hand():
    _, store = rig()
    mutate(store, "stock_save", tanks=[BLOOM])
    with pytest.raises(ValueError, match="Unsupported stock operation"):
        mutate(store, "stock_record_batch")
    assert "stock_record_batch" not in stock_api.SERVICES


def test_saving_refilling_and_a_stale_edit(dispatcher):
    _, store = rig()
    response = mutate(store, "stock_save", tanks=[{**BLOOM, "level_l": 20}])
    assert response["revision"] == 1 and response["tanks"][0]["level_l"] == 20
    assert store._store.saves == 1 and dispatcher.sent == [
        "crop_steering_stock_changed_entry"
    ]
    with pytest.raises(ValueError, match="changed elsewhere"):
        mutate(store, "stock_refill", id="bloom", expected_revision=0)
    assert mutate(store, "stock_refill", id="bloom")["tanks"][0]["level_l"] == 50
    assert (
        mutate(store, "stock_refill", id="bloom", level_l=31.5)["tanks"][0]["level_l"]
        == 31.5
    )


def test_a_corrupt_store_is_kept_and_every_change_refused():
    _, store = rig(value={"revision": "seven", "tanks": []})
    assert "not been overwritten" in store.error
    with pytest.raises(ValueError, match="not been overwritten"):
        mutate(store, "stock_save", tanks=[BLOOM])
    asyncio.run(store._reservoir(None))
    assert store._store.saves == 0 and store._store.value == {
        "revision": "seven",
        "tanks": [],
    }


def test_a_failed_save_changes_nothing():
    _, store = rig()
    mutate(store, "stock_save", tanks=[{**BLOOM, "level_l": 20}])

    async def broken(value):
        raise OSError("disk full")

    store._store.async_save = broken
    with pytest.raises(OSError):
        mutate(store, "stock_refill", id="bloom")
    assert store.data["tanks"][0]["level_l"] == 20 and store.data["revision"] == 1


# ------------------------------------------------------------ tanks on the Reservoir's dosers
DOSERS = {f"doser_{n}_switch": f"switch.doser_{n}" for n in (1, 2, 3, 4)}
FLOWER = {
    "id": "flower",
    "name": "Flower",
    "strength": 1,
    "doses": {
        "1": {"label": "Core", "parts": 3},
        "2": {"label": "Bloom", "parts": 5},
        "3": {"label": "Balance", "parts": 1},
        "4": {"label": "Cleanse", "parts": 0.5},
    },
}
BATCH = "sensor.crop_steering_batch_status"


def reservoir_rig(value=None):
    """A room with four dosers and Athena Flower in use (150 L), its stock store started."""
    hass = ha_stubs.FakeHass(data={DOMAIN: {"entry": {"hardware": dict(DOSERS)}}})
    entry = ha_stubs.FakeEntry(entry_id="entry")
    feed = feed_api.FeedStore(hass, entry, MemoryStore())
    asyncio.run(feed.async_init())
    asyncio.run(
        feed.save(
            {
                "expected_revision": 0,
                "document": {"batch_l": 150, "recipes": [FLOWER], "stage": "flower"},
            }
        )
    )
    hass.data[DOMAIN]["_feed"] = {"entry": feed}
    store = stock_api.StockStore(hass, entry, MemoryStore(value))
    asyncio.run(store.async_init())
    asyncio.run(store._reservoir(None))  # the first run: a starting point
    return hass, store


def ended(store, at, dosed, stage="Flower", result="done"):
    last = {"at": at, "result": result, "stage": stage, "dosed": dosed}
    asyncio.run(store._reservoir(ha_stubs.FakeState("idle", {"last": last})))


def test_a_reservoir_batch_draws_what_each_doser_gave_once():
    hass, store = reservoir_rig()
    mutate(
        store,
        "stock_save",
        tanks=[
            {"name": "Core", "capacity_l": 20, "doser": 1},
            {"name": "Balance", "capacity_l": 20, "doser": 3},
            {"name": "pH down", "capacity_l": 5},
        ],
    )
    response = store.response()
    assert response["dosers"]["3"] == {
        "switch": "switch.doser_3",
        "nutrient": "Balance",
    }
    # Per batch: what Flower gives from its doser; a tank on no doser takes nothing.
    assert response["doses"] == {"core": 450.0, "balance": 150.0, "ph_down": 0.0}

    ended(store, "2999-01-01T10:00:00+12:00", {"1": 450.0, "2": 750.0, "3": 150.0})
    levels = {t["id"]: t["level_l"] for t in store.data["tanks"]}
    assert levels == {"core": 19.55, "balance": 19.85, "ph_down": 5}
    assert store.data["history"][0]["source"] == "reservoir"
    ended(
        store, "2999-01-01T10:00:00+12:00", {"1": 450.0}
    )  # reported again: counted once
    assert store.data["tanks"][0]["level_l"] == 19.55
    # Stopped part-way: only what went in.
    ended(store, "2999-01-02T10:00:00+12:00", {"1": 200.0}, result="stopped: x")
    assert store.data["tanks"][0]["level_l"] == 19.35


def test_the_reservoirs_batch_before_this_is_a_starting_point_and_a_restart_counts_nothing_twice():
    hass, store = reservoir_rig()
    mutate(store, "stock_save", tanks=[{"name": "Core", "capacity_l": 20, "doser": 1}])
    ended(store, "2000-01-01T10:00:00+00:00", {"1": 450.0})  # ended before this ran
    assert store.data["tanks"][0]["level_l"] == 20
    ended(store, "2999-01-01T10:00:00+00:00", {"1": 450.0})
    _, again = reservoir_rig(value=store._store.value)
    ended(again, "2999-01-01T10:00:00+00:00", {"1": 450.0})
    assert again.data["tanks"][0]["level_l"] == 19.55


def test_the_low_card_comes_with_the_batches_left_and_goes_on_refill():
    """What a batch takes is the feed recipe's: Flower gives 750 mL of Bloom from doser 2, so 8 L
    is about 10 batches."""
    hass, store = reservoir_rig()
    mutate(store, "stock_save", tanks=[{**BLOOM, "level_l": 8, "doser": 2}])
    card = hass._issues["stock_low"]
    assert card["translation_key"] == "stock_low"
    assert card["translation_placeholders"]["count"] == "1"
    assert (
        "Bloom: 8 L of 50 L, about 10 batches left"
        in card["translation_placeholders"]["tanks"]
    )
    assert store.response()["low"] == ["bloom"]
    mutate(store, "stock_refill", id="bloom")
    assert "stock_low" not in hass._issues


def test_a_tank_whose_doser_the_stage_does_not_use_takes_nothing_per_batch():
    hass, store = reservoir_rig()
    mutate(
        store,
        "stock_save",
        tanks=[
            {"name": "Grow", "capacity_l": 20, "doser": 2},
            {"name": "Bloom", "capacity_l": 20, "doser": 2},
        ],
    )
    assert store.doses() == {
        "grow": 0.0,
        "bloom": 750.0,
    }  # Flower puts Bloom on doser 2


def test_stock_tanks_stored_before_dosers_load_on_none():
    old = {
        "revision": 4,
        "tanks": [
            {
                "id": "bloom",
                "name": "Bloom",
                "capacity_l": 50,
                "level_l": 20,
                "dose_ml": 1800,
                "dose_entity": None,
                "low_l": 10,
                "refilled_at": None,
                "updated_at": "2026-09-25T08:00:00+12:00",
            }
        ],
        "last_batch": None,
        "history": [],
    }
    _, store = rig(value=old)
    assert store.error is None
    tank = store.data["tanks"][0]
    assert (tank["doser"], tank["level_l"], tank["low_l"]) == (None, 20, 10)
    assert "dose_ml" not in tank and "last_batch" not in store.data  # retired in 2.32
    assert store.data["reservoir_batch"] is None and store.data["revision"] == 4
