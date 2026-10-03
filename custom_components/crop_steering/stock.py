"""Stock tanks: the room's nutrient concentrates, each on the Reservoir doser its bottle feeds. Pure
(no Home Assistant import), so it is tested directly; stock_api.py stores it and counts the batches.

A tank needs only its name, capacity, level, low mark and doser: how much a batch takes from it is the
feed recipe's, week by week, not the tank's. Each batch the controller mixes takes from a tank on a
doser what that doser gave in it, as the controller recorded it. When bottles are swapped between
stages, several tanks can be on one doser; a batch then draws from the one named like the nutrient its
recipe puts on that doser. A tank on no doser changes only when its level is set or it is refilled.

The Reservoir's last batch the first time the store runs is only a starting point: counting it would
draw the stock down for a batch made before the tanks were set up.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, tzinfo

from .room import MAX_DOSERS

MAX_TANKS = 12
HISTORY = 30
_DEAD = ("unknown", "unavailable", "none", "")


class StockError(ValueError):
    """A stock tank change that cannot be saved; the message is shown to the operator."""


def empty() -> dict:
    return {
        "revision": 0,
        "tanks": [],
        # When the last Reservoir batch counted ended; None until the store first runs.
        "reservoir_batch": None,
        "history": [],
    }


def _number(raw: dict, key: str, low: float, high: float, default=None) -> float:
    value = raw.get(key, default)
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise StockError(f"{key.replace('_', ' ')} must be a number") from None
    if not low <= value <= high:
        raise StockError(
            f"{key.replace('_', ' ')} must be between {low:g} and {high:g}"
        )
    return value


def _slug(name: str, taken: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "stock"
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}_{n}", n + 1
    return slug


def clean_tanks(raw: list, current: list[dict], now: str) -> list[dict]:
    """The operator's full list of tanks, checked -> the list to store.

    A tank keeps its id (and so its sensor) across edits; a new one gets an id from its name. The
    level a new tank starts at is its capacity unless given; an edit that lowers the capacity
    below the level brings the level down with it.
    """
    if not isinstance(raw, list) or len(raw) > MAX_TANKS:
        raise StockError(f"send a list of at most {MAX_TANKS} stock tanks")
    known = {tank["id"]: tank for tank in current}
    kept = {
        str(item.get("id"))
        for item in raw
        if isinstance(item, dict) and item.get("id") in known
    }
    out, names = [], set()
    for item in raw:
        if not isinstance(item, dict):
            raise StockError("each stock tank must be an object")
        name = str(item.get("name") or "").strip()
        if not 1 <= len(name) <= 40:
            raise StockError("each stock tank needs a name of 1 to 40 characters")
        if name.lower() in names:
            raise StockError(f"two stock tanks are called {name}")
        names.add(name.lower())
        old = known.get(item.get("id"))
        # A field left out of an edit keeps its stored value.
        capacity = _number(
            item, "capacity_l", 0.1, 10000, old["capacity_l"] if old else None
        )
        level = _number(item, "level_l", 0, 10000, old["level_l"] if old else capacity)
        doser = _doser(item["doser"] if "doser" in item else (old or {}).get("doser"))
        tank_id = old["id"] if old else _slug(name, kept | {t["id"] for t in out})
        out.append(
            {
                "id": tank_id,
                "name": name,
                "capacity_l": capacity,
                "level_l": min(level, capacity),
                "doser": doser,
                "low_l": min(
                    _number(
                        item, "low_l", 0, 10000, old["low_l"] if old else capacity * 0.2
                    ),
                    capacity,
                ),
                "refilled_at": old.get("refilled_at") if old else None,
                "updated_at": (
                    now if old is None or _changed(old, item) else old["updated_at"]
                ),
            }
        )
    return out


def _doser(value) -> int | None:
    """The doser a tank is on (1 to MAX_DOSERS), or None for a tank on none."""
    if value is None or value == "":
        return None
    number = int(value) if isinstance(value, str) and value.isdigit() else value
    if (
        isinstance(number, bool)
        or not isinstance(number, int)
        or not 1 <= number <= MAX_DOSERS
    ):
        raise StockError(f"a stock tank's doser is numbered 1 to {MAX_DOSERS}")
    return number


def _changed(old: dict, item: dict) -> bool:
    return any(
        item.get(key) is not None and item.get(key) != old.get(key)
        for key in ("name", "capacity_l", "level_l", "doser", "low_l")
    )


def on_doser(tanks: list[dict], doser: int, nutrient: str | None) -> dict | None:
    """The tank a doser draws from: the one tank on it or, with bottles swapped between stages and
    several on it, the one named like the nutrient the recipe puts on it. None when there is none.
    """
    on = [tank for tank in tanks if tank.get("doser") == doser]
    if len(on) == 1:
        return on[0]
    wanted = (nutrient or "").strip().casefold()
    return next((tank for tank in on if tank["name"].casefold() == wanted), None)


def reservoir_draws(
    tanks: list[dict], dosed, nutrients: dict[int, str]
) -> dict[str, float]:
    """A Reservoir batch's draw from each tank on a doser, in mL: what its doser gave (`dosed`,
    doser -> mL, as the controller recorded it). `nutrients` is what the batch's recipe put on each
    doser, which picks between tanks sharing one."""
    draws: dict[str, float] = {}
    for key, value in (dosed if isinstance(dosed, dict) else {}).items():
        try:
            doser, ml = int(key), float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(ml) or ml <= 0:
            continue
        tank = on_doser(tanks, doser, nutrients.get(doser))
        if tank is not None:
            draws[tank["id"]] = draws.get(tank["id"], 0.0) + ml
    return draws


def draw(data: dict, doses: dict[str, float], at: str, source: str) -> dict:
    """One batch: every tank loses its dose (never below empty), and the batch is logged."""
    taken = {}
    for tank in data["tanks"]:
        ml = max(0.0, float(doses.get(tank["id"], 0)))
        before = tank["level_l"]
        tank["level_l"] = round(max(0.0, before - ml / 1000), 4)
        taken[tank["id"]] = round((before - tank["level_l"]) * 1000, 1)
    data["history"] = [
        {"at": at, "source": source, "draw_ml": taken},
        *data["history"],
    ][:HISTORY]
    return data


def refill(data: dict, tank_id: str, level_l: float | None, now: str) -> dict:
    """The operator refilled a tank (to capacity) or read its level off the side (`level_l`)."""
    tank = next((t for t in data["tanks"] if t["id"] == tank_id), None)
    if tank is None:
        raise StockError(f"there is no stock tank {tank_id}")
    if level_l is None:
        tank["level_l"], tank["refilled_at"] = tank["capacity_l"], now
    else:
        tank["level_l"] = _number(
            {"level_l": level_l}, "level_l", 0, tank["capacity_l"]
        )
    tank["updated_at"] = now
    return data


def batches_left(tank: dict, dose: float) -> int | None:
    """Whole batches the tank still covers at `dose` mL each; None when it doses nothing."""
    # Rounded first: 0.29 L is 289.99999999999997 mL in floating point, one batch short.
    return int(round(tank["level_l"] * 1000, 6) // dose) if dose > 0 else None


def low_tanks(data: dict) -> list[dict]:
    return [t for t in data["tanks"] if t["level_l"] <= t["low_l"]]


def parse_fill(state: str | None, zone: tzinfo) -> datetime | None:
    """A time as an aware datetime: an ISO string with its offset, or one without read in `zone` (the
    Reservoir's batch status gives the time its batch ended with its UTC offset)."""
    if state is None or str(state).strip().lower() in _DEAD:
        return None
    try:
        when = datetime.fromisoformat(str(state).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=zone)
