"""Nutrient batches: the feed settings and recipes a room keeps, checked, and the plan the controller
runs from them (custom_components/crop_steering/feed.py, feed_api.py)."""

import asyncio
import copy
import sys
import types

import pytest

from . import ha_stubs

ha_stubs.install()

from custom_components.crop_steering import feed, feed_api  # noqa: E402
from custom_components.crop_steering.const import DOMAIN  # noqa: E402

DOSERS = {
    "doser_1_switch": "switch.doser_1",
    "doser_2_switch": "switch.doser_2",
    "doser_3_switch": "switch.doser_3",
    "doser_4_switch": "switch.doser_4",
}
MAPPED = {
    1: "switch.doser_1",
    2: "switch.doser_2",
    3: "switch.doser_3",
    4: "switch.doser_4",
}
# Athena Flower, as the owner runs it: 3 Core : 5 Bloom : 1 Balance : 0.5 Cleanse, one part being
# 1.667 mL per litre, on doser 4 (Core), 3 (Bloom), 2 (Balance) and 1 (Cleanse).
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


def settings(**changes):
    doc = {
        "batch_l": 145,
        "fill_s": 621,
        "order": [4, 3, 2, 1],
        "recipes": [copy.deepcopy(FLOWER)],
        "stage": "flower",
    }
    doc.update(changes)
    return feed.clean(doc)


def test_a_ratio_and_a_strength_become_each_dosers_ml_and_seconds():
    plan = feed.plan(settings(), MAPPED)
    assert plan["stage"] == "Flower" and plan["problem"] is None
    assert [(d["doser"], d["label"], d["ml"], d["seconds"]) for d in plan["doses"]] == [
        (4, "Core", 725.0, 72.5),  # 3 x 1.667 mL/L x 145 L, at 600 mL/min
        (3, "Bloom", 1208.3, 120.8),
        (2, "Balance", 241.7, 24.2),
        (1, "Cleanse", 120.8, 12.1),
    ]
    assert plan["fill_s"] == 621 and plan["batch_l"] == 145.0


def test_the_batch_size_scales_every_dose_and_a_calibrated_flow_its_time():
    plan = feed.plan(settings(batch_l=72.5, dosers={"3": {"flow_ml_min": 450}}), MAPPED)
    bloom = next(d for d in plan["doses"] if d["doser"] == 3)
    assert bloom["ml"] == 604.2 and bloom["seconds"] == pytest.approx(80.6, abs=0.05)


def test_dosers_run_in_the_rooms_order_then_any_other_by_number():
    plan = feed.plan(settings(order=[2]), MAPPED)
    assert [d["doser"] for d in plan["doses"]] == [2, 1, 3, 4]


def test_a_doser_without_parts_is_skipped_and_one_without_a_switch_stops_the_batch():
    doses = copy.deepcopy(FLOWER["doses"])
    doses["2"]["parts"] = 0
    plan = feed.plan(settings(recipes=[{**FLOWER, "doses": doses}]), MAPPED)
    assert [d["doser"] for d in plan["doses"]] == [4, 3, 1] and plan["problem"] is None
    plan = feed.plan(settings(), {n: e for n, e in MAPPED.items() if n != 3})
    assert (
        plan["problem"]
        == "Flower uses doser 3, which has no switch in Settings → Rooms & hardware."
    )


@pytest.mark.parametrize(
    "doc, mapped, problem",
    [
        ({}, MAPPED, "No feed stage is chosen."),
        ({"stage": "flower"}, {}, "No doser is mapped in Settings → Rooms & hardware."),
        (
            {"stage": "flower", "strength": 0},
            MAPPED,
            "Flower's strength is 0: nothing would be dosed.",
        ),
    ],
)
def test_it_says_why_no_batch_can_run(doc, mapped, problem):
    recipe = {**FLOWER, "strength": doc.get("strength", FLOWER["strength"])}
    chosen = settings(recipes=[recipe], stage=doc.get("stage"))
    assert feed.plan(chosen, mapped)["problem"] == problem


def test_a_recipe_that_doses_nothing_says_so():
    empty = {**FLOWER, "doses": {"4": {"label": "Core", "parts": 0}}}
    assert (
        feed.plan(settings(recipes=[empty]), MAPPED)["problem"]
        == "Flower doses nothing: give its nutrients some parts."
    )


@pytest.mark.parametrize(
    "changes, reason",
    [
        ({"batch_l": 0}, "batch l must be a number from 1 to 5000"),
        ({"fill_s": 12.5}, "fill s must be a number from 10 to 7200"),
        ({"mix_s": True}, "mix s must be a number"),
        ({"min_pct": 60}, "min pct must be a number from 0 to 50"),
        (
            {"full_mm": 850, "empty_mm": 125},
            "The distance when full must be less than the distance when empty",
        ),
        ({"order": [1, 1]}, "A doser appears twice in the dosing order"),
        ({"order": [7]}, "A doser is numbered 1 to 6"),
        ({"dosers": {"2": {"flow_ml_min": 0}}}, "Doser 2's flow must be a number"),
        (
            {"recipes": [FLOWER, {**FLOWER, "id": "b"}]},
            "Two feed recipes are called Flower",
        ),
        ({"recipes": [{**FLOWER, "strength": 7}]}, "comes to 66.5 mL per litre"),
        (
            {"recipes": [{**FLOWER, "doses": {"4": {"label": "", "parts": 3}}}]},
            "Flower: doser 4 has parts but no nutrient",
        ),
        (
            {"recipes": [{**FLOWER, "doses": {"4": {"label": 5, "parts": 3}}}]},
            "nutrient must be text",
        ),
        (
            {"recipes": [{**FLOWER, "name": "x" * 41}]},
            "A feed recipe is longer than 40 characters",
        ),
        (
            {"recipes": [{**FLOWER, "id": str(n), "name": str(n)} for n in range(13)]},
            "Up to 12 feed recipes",
        ),
    ],
)
def test_a_setting_or_recipe_that_does_not_make_sense_is_refused(changes, reason):
    with pytest.raises(ValueError, match=reason):
        settings(**changes)


def test_a_stage_whose_recipe_is_gone_is_no_stage():
    assert settings(stage="nothing")["stage"] is None
    kept = settings(recipes=[{**FLOWER, "id": "?? not an id"}], stage="flower")
    assert kept["recipes"][0]["id"] != "?? not an id" and kept["stage"] is None


def test_a_fresh_room_has_the_defaults_and_nothing_to_run():
    doc = feed.empty()
    assert (doc["fill_s"], doc["pause_s"], doc["mix_s"], doc["min_pct"]) == (
        600,
        10,
        10,
        5.0,
    )
    assert (doc["full_mm"], doc["empty_mm"]) == (
        0.0,
        0.0,
    )  # no level until both are set
    assert feed.plan(doc, MAPPED)["problem"] == "No feed stage is chosen."
    assert feed.flow(doc, 1) == 600.0


# ------------------------------------------------------------------ the store
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
    return module


def rig(value=None, hardware=DOSERS):
    hass = ha_stubs.FakeHass(data={DOMAIN: {"entry": {"hardware": dict(hardware)}}})
    store = feed_api.FeedStore(
        hass, ha_stubs.FakeEntry(entry_id="entry"), MemoryStore(value)
    )
    asyncio.run(store.async_init())
    return store


def save(store, **document):
    return asyncio.run(
        store.save({"expected_revision": store.data["revision"], "document": document})
    )


def test_saving_takes_the_next_revision_and_tells_the_entities(dispatcher):
    store = rig()
    response = save(
        store, recipes=[FLOWER], stage="flower", batch_l=145, order=[4, 3, 2, 1]
    )
    assert response["revision"] == 1 and store._store.saves == 1
    assert response["mapped"] == {"1": "switch.doser_1", "2": "switch.doser_2",
                                  "3": "switch.doser_3", "4": "switch.doser_4"}  # fmt: skip
    assert response["plan"]["doses"][0]["ml"] == 725.0
    assert dispatcher.sent == [f"{feed_api.SIGNAL}_entry"]


def test_a_save_on_an_old_revision_is_refused():
    store = rig()
    save(store, batch_l=100)
    with pytest.raises(ValueError, match="changed elsewhere"):
        asyncio.run(store.save({"expected_revision": 0, "document": {"batch_l": 90}}))


def test_the_stage_is_chosen_by_its_recipes_name():
    store = rig()
    save(
        store, recipes=[FLOWER, {**FLOWER, "id": "veg", "name": "Vege"}], stage="flower"
    )
    asyncio.run(store.set_stage("Vege"))
    assert store.data["stage"] == "veg" and store.data["revision"] == 2
    with pytest.raises(ValueError, match="No feed recipe is called Fade"):
        asyncio.run(store.set_stage("Fade"))


def test_a_stored_document_that_cannot_be_read_is_kept_and_named():
    store = rig({"revision": "one"})
    assert store.error and "have not been overwritten" in store.error
    with pytest.raises(ValueError, match="have not been overwritten"):
        save(store, batch_l=100)
    assert store._store.value == {"revision": "one"}


def test_the_reservoirs_distances_and_minimum_reach_the_controllers_plan():
    plan = feed.plan(
        settings(full_mm=125, empty_mm=850, min_pct=5, batch_l=145), MAPPED
    )
    assert (plan["full_mm"], plan["empty_mm"], plan["min_pct"], plan["batch_l"]) == (
        125,
        850,
        5,
        145,
    )
    assert "settle_s" not in plan  # the pump starts half-way through the fill instead
    assert (
        feed.plan(settings(empty_mm=850), MAPPED)["full_mm"] == 0.0
    )  # one alone: no level yet


def test_a_document_saved_before_the_reservoirs_level_loads_with_its_mark_as_the_empty_distance():
    """Until 2.30 a room had an "almost empty at" distance and a settle before the first dose; its
    stored document still loads: the mark is the distance when empty, the settle is gone, and the
    minimum and the distance when full start at their defaults."""
    old = {
        "revision": 3,
        "fill_s": 690,
        "batch_l": 145,
        "empty_mm": 800,
        "settle_s": 20,
        "pause_s": 10,
        "mix_s": 600,
        "dosers": {},
        "order": [],
        "recipes": [],
        "stage": None,
    }
    store = rig(old)
    assert store.error is None
    data = store.data
    assert (data["empty_mm"], data["full_mm"], data["min_pct"], data["mix_s"]) == (
        800,
        0.0,
        5.0,
        600,
    )
    assert "settle_s" not in data and data["revision"] == 3


def test_a_stored_document_loads_as_it_was_saved():
    first = rig()
    save(first, recipes=[FLOWER], stage="flower", order=[4, 3, 2, 1])
    again = rig(first._store.value)
    assert again.data == first.data and again.error is None


def test_only_the_rooms_mapped_dosers_count():
    assert feed_api.mapped_dosers(
        {"doser_2_switch": "switch.b", "doser_5_switch": ""}
    ) == {2: "switch.b"}
    assert (
        rig(hardware={}).response()["plan"]["problem"]
        == "No doser is mapped in Settings → Rooms & hardware."
    )


def test_mixing_a_batch_presses_the_rooms_button_once_the_plan_can_run():
    store = rig()
    button = "button.crop_steering_mix_batch"
    with pytest.raises(ValueError, match="is not available"):
        asyncio.run(store.mix())
    store.hass.states.set(button, "unknown")
    with pytest.raises(ValueError, match="No feed stage is chosen"):
        asyncio.run(store.mix())
    assert store.hass.services.calls == []
    save(store, recipes=[FLOWER], stage="flower", order=[4, 3, 2, 1])
    response = asyncio.run(store.mix())
    assert store.hass.services.calls == [("button", "press", {"entity_id": button})]
    assert response["plan"]["stage"] == "Flower" and "requested" in response
