"""Stock tanks: checked edits, the draw of each Reservoir batch, and refills. A tank is its name,
capacity, level, low mark and doser; what a batch takes is the feed recipe's."""

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.crop_steering import stock

NZ = timezone(timedelta(hours=12))
NOW = "2026-09-25T08:00:00+12:00"


def tanks(*items):
    return stock.clean_tanks(list(items), [], NOW)


def test_a_new_tank_starts_full_with_a_low_mark_at_a_fifth():
    [bloom] = tanks({"name": "Bloom", "capacity_l": 50, "doser": 2})
    assert bloom["id"] == "bloom"
    assert bloom["level_l"] == 50
    assert bloom["low_l"] == 10
    assert set(bloom) == {
        "id",
        "name",
        "capacity_l",
        "level_l",
        "doser",
        "low_l",
        "refilled_at",
        "updated_at",
    }


def test_a_tank_saved_with_a_dose_per_batch_or_a_dose_entity_keeps_the_rest():
    """Before 2.32 a tank had a fixed dose per batch, or a dose entity: the recipe says it now."""
    [bloom] = tanks(
        {
            "name": "Bloom",
            "capacity_l": 20,
            "level_l": 12,
            "low_l": 4,
            "doser": 2,
            "dose_ml": 1200,
            "dose_entity": "number.doser_bloom_dose",
        }
    )
    assert (bloom["level_l"], bloom["low_l"], bloom["doser"]) == (12, 4, 2)
    assert "dose_ml" not in bloom and "dose_entity" not in bloom


def test_edits_keep_the_id_and_a_smaller_capacity_brings_the_level_down():
    [bloom] = tanks({"name": "Bloom", "capacity_l": 50})
    [edited] = stock.clean_tanks(
        [{"id": "bloom", "name": "Bloom A", "capacity_l": 20}],
        [bloom],
        NOW,
    )
    assert edited["id"] == "bloom"
    assert edited["level_l"] == 20
    assert edited["low_l"] == 10


def test_names_ids_and_numbers_are_checked():
    with pytest.raises(stock.StockError, match="name"):
        tanks({"name": "", "capacity_l": 5})
    with pytest.raises(stock.StockError, match="capacity l"):
        tanks({"name": "A", "capacity_l": 0})
    with pytest.raises(stock.StockError, match="two stock tanks"):
        tanks({"name": "A", "capacity_l": 5}, {"name": "a", "capacity_l": 5})
    # Two names that slug alike still get distinct ids.
    first, second = tanks(
        {"name": "Part A", "capacity_l": 5}, {"name": "Part-A!", "capacity_l": 5}
    )
    assert (first["id"], second["id"]) == ("part_a", "part_a_2")


def test_a_batch_draws_each_dose_and_never_below_empty():
    data = stock.empty()
    data["tanks"] = tanks(
        {"name": "Bloom", "capacity_l": 50, "doser": 2},
        {"name": "Cal", "capacity_l": 1, "level_l": 0.1, "doser": 3},
    )
    stock.draw(data, {"bloom": 1800, "cal": 250}, NOW, "reservoir")
    assert [t["level_l"] for t in data["tanks"]] == [48.2, 0]
    assert data["history"][0]["draw_ml"] == {"bloom": 1800.0, "cal": 100.0}


def test_refilled_and_set_level():
    data = stock.empty()
    data["tanks"] = tanks({"name": "Bloom", "capacity_l": 50, "level_l": 4})
    stock.refill(data, "bloom", None, NOW)
    assert (data["tanks"][0]["level_l"], data["tanks"][0]["refilled_at"]) == (50, NOW)
    stock.refill(data, "bloom", 12.5, NOW)
    assert data["tanks"][0]["level_l"] == 12.5
    with pytest.raises(stock.StockError):
        stock.refill(data, "bloom", 60, NOW)
    with pytest.raises(stock.StockError):
        stock.refill(data, "nope", None, NOW)


def test_low_and_batches_left():
    data = stock.empty()
    data["tanks"] = tanks({"name": "Bloom", "capacity_l": 50, "level_l": 9.9})
    assert [t["id"] for t in stock.low_tanks(data)] == ["bloom"]
    assert stock.batches_left(data["tanks"][0], 1800) == 5
    assert stock.batches_left(data["tanks"][0], 0) is None
    assert stock.batches_left({"level_l": 0.29}, 290) == 1  # not 0: float rounding


def test_the_time_a_reservoir_batch_ended_is_read_with_its_offset():
    assert stock.parse_fill("2026-09-24T07:16:08+00:00", NZ) == datetime(
        2026, 9, 24, 7, 16, 8, tzinfo=timezone.utc
    )
    # One without an offset is read in the zone given.
    assert stock.parse_fill("2026-09-24 19:16:08", NZ) == datetime(
        2026, 9, 24, 19, 16, 8, tzinfo=NZ
    )
    assert stock.parse_fill("unavailable", NZ) is None
    assert stock.parse_fill("yesterday", NZ) is None


def test_the_doser_is_checked():
    [balance] = tanks({"name": "Balance", "capacity_l": 20, "doser": "3"})
    assert balance["doser"] == 3
    assert tanks({"name": "pH down", "capacity_l": 5})[0]["doser"] is None
    with pytest.raises(stock.StockError, match="numbered 1 to 6"):
        tanks({"name": "Balance", "capacity_l": 20, "doser": 7})


def test_a_batch_draws_what_each_doser_gave_from_the_tank_on_it():
    stock_tanks = tanks(
        {"name": "Core", "capacity_l": 20, "doser": 1},
        {"name": "Balance", "capacity_l": 20, "doser": 3},
        {"name": "pH down", "capacity_l": 5},
    )
    draws = stock.reservoir_draws(
        stock_tanks, {"1": 450.0, "3": 150.0, "4": 75.0, "2": 0}, {}
    )
    # Doser 4 has no tank here; pH down is on no doser: neither is drawn.
    assert draws == {"core": 450.0, "balance": 150.0}


def test_with_bottles_swapped_the_recipes_nutrient_picks_the_tank():
    stock_tanks = tanks(
        {"name": "Grow", "capacity_l": 20, "doser": 2},
        {"name": "Bloom", "capacity_l": 20, "doser": 2},
    )
    assert stock.reservoir_draws(stock_tanks, {"2": 750}, {2: "bloom"}) == {
        "bloom": 750.0
    }
    assert stock.reservoir_draws(stock_tanks, {"2": 600}, {2: "Grow"}) == {
        "grow": 600.0
    }
    # Two tanks on the doser and no nutrient to tell them apart: neither is guessed at.
    assert stock.reservoir_draws(stock_tanks, {"2": 600}, {}) == {}
