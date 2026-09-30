"""Nutrient batches: a room's reservoir, its dosers, and a feed recipe for each growth stage.

Pure, no Home Assistant, so the rules are testable on their own (feed_api.py stores and serves them).

A batch refills the room's reservoir with fresh water for a set time, then runs the pump through the
recirculation line and, after a short settle, doses each doser in the room's order, one after the
other, then keeps mixing for a while. The controller app runs it; this module says what it runs.

The amounts: a feed recipe gives each nutrient a number of parts, and the stage a strength in mL per
litre per part. The batch size scales them: a doser gives parts x strength x batch litres, and runs
for that at its flow (600 mL/min unless calibrated otherwise). Athena Flower at 3 : 5 : 1 : 0.5 and
1.667 mL/L per part in 145 L is 725 mL Core, 1208 mL Bloom, 242 mL Balance and 121 mL Cleanse.
"""

from __future__ import annotations

import math
import re
import uuid

from .room import DOSER_KEYS, MAX_DOSERS, RESERVOIR_KEYS  # noqa: F401 (the one list)

MAX_RECIPES = 12
NAME_LEN = 40
DEFAULT_FLOW = 600.0  # mL/min, a doser's flow until it is calibrated
# field -> (lowest, highest, whole number)
SETTINGS = {
    "fill_s": (10, 7200, True),  # how long the fresh water runs
    "batch_l": (1, 5000, False),  # the litres the doses are worked out for
    "empty_mm": (
        0,
        10000,
        False,
    ),  # "almost empty" distance; 0 = not set, no automatic batch
    "settle_s": (0, 600, True),  # pump and recirc running before the first dose
    "pause_s": (0, 600, True),  # between one doser and the next
    "mix_s": (0, 7200, True),  # mixing after the last dose
}
DEFAULTS = {
    "fill_s": 600,
    "batch_l": 100.0,
    "empty_mm": 0.0,
    "settle_s": 20,
    "pause_s": 10,
    "mix_s": 600,
}
FLOW = (1.0, 10000.0)  # mL/min
STRENGTH = (0.0, 20.0)  # mL per litre per part
PARTS = (0.0, 100.0)
# A whole recipe's mL per litre. Nutrient lines run at 5-20; a strength typed ten times too big is
# refused rather than dosed.
MAX_ML_PER_L = 60.0


def empty() -> dict:
    return {
        "revision": 0,
        **DEFAULTS,
        "dosers": {},
        "order": [],
        "recipes": [],
        "stage": None,
    }


def _number(value, low, high, whole, what):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or not low <= value <= high
        or (whole and int(value) != value)
    ):
        raise ValueError(f"{what} must be a number from {low:g} to {high:g}")
    return int(value) if whole else float(value)


def _name(value, what) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} needs a name")
    name = re.sub(r"\s+", " ", value.strip())
    if len(name) > NAME_LEN:
        raise ValueError(f"{what} is longer than {NAME_LEN} characters")
    return name


def _doser(value) -> int:
    number = int(value) if isinstance(value, str) and value.isdigit() else value
    if (
        isinstance(number, bool)
        or not isinstance(number, int)
        or not 1 <= number <= MAX_DOSERS
    ):
        raise ValueError(f"A doser is numbered 1 to {MAX_DOSERS}")
    return number


def clean(payload, old: dict | None = None) -> dict:
    """An edited document, checked, with the revision it replaces. Anything malformed is refused
    with a reason a person can act on."""
    if not isinstance(payload, dict):
        raise ValueError("Feed settings must be an object")
    old = old or empty()
    doc = empty()
    doc["revision"] = old.get("revision", 0)
    for key, (low, high, whole) in SETTINGS.items():
        value = payload.get(key, old.get(key, DEFAULTS[key]))
        doc[key] = _number(value, low, high, whole, key.replace("_", " "))
    dosers = payload.get("dosers", old.get("dosers", {}))
    if not isinstance(dosers, dict):
        raise ValueError("Dosers must be an object")
    for key, value in dosers.items():
        number = _doser(key)
        flow = (
            value.get("flow_ml_min", DEFAULT_FLOW) if isinstance(value, dict) else value
        )
        doc["dosers"][str(number)] = {
            "flow_ml_min": _number(flow, *FLOW, False, f"Doser {number}'s flow")
        }
    order = payload.get("order", old.get("order", []))
    if not isinstance(order, list):
        raise ValueError("The dosing order must be a list of dosers")
    numbers = [_doser(value) for value in order]
    if len(set(numbers)) != len(numbers):
        raise ValueError("A doser appears twice in the dosing order")
    doc["order"] = numbers
    recipes = payload.get("recipes", old.get("recipes", []))
    if not isinstance(recipes, list) or len(recipes) > MAX_RECIPES:
        raise ValueError(f"Up to {MAX_RECIPES} feed recipes")
    names, ids = set(), set()
    for raw in recipes:
        if not isinstance(raw, dict):
            raise ValueError("A feed recipe must be an object")
        name = _name(raw.get("name"), "A feed recipe")
        if name.casefold() in names:
            raise ValueError(f"Two feed recipes are called {name}")
        names.add(name.casefold())
        recipe_id = raw.get("id")
        if not isinstance(recipe_id, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,40}", recipe_id
        ):
            recipe_id = uuid.uuid4().hex[:12]
        if recipe_id in ids:
            raise ValueError(f"Two feed recipes share the id {recipe_id}")
        ids.add(recipe_id)
        strength = _number(
            raw.get("strength", 0), *STRENGTH, False, f"{name}'s strength"
        )
        doses = raw.get("doses", {})
        if not isinstance(doses, dict):
            raise ValueError(f"{name}'s doses must be an object")
        clean_doses = {}
        for key, dose in doses.items():
            number = _doser(key)
            if not isinstance(dose, dict):
                raise ValueError(
                    f"{name}: doser {number} needs a nutrient and its parts"
                )
            label = dose.get("label") or ""
            if not isinstance(label, str):
                raise ValueError(f"{name}: doser {number}'s nutrient must be text")
            label = (
                _name(label, f"{name}: doser {number}'s nutrient")
                if label.strip()
                else ""
            )
            parts = _number(
                dose.get("parts", 0), *PARTS, False, f"{name}: doser {number}'s parts"
            )
            if parts and not label:
                raise ValueError(f"{name}: doser {number} has parts but no nutrient")
            clean_doses[str(number)] = {"label": label, "parts": parts}
        per_litre = strength * sum(dose["parts"] for dose in clean_doses.values())
        if per_litre > MAX_ML_PER_L:
            raise ValueError(
                f"{name} comes to {per_litre:.1f} mL per litre; more than {MAX_ML_PER_L:g} "
                "is refused as a likely typo in its strength or parts"
            )
        doc["recipes"].append(
            {"id": recipe_id, "name": name, "strength": strength, "doses": clean_doses}
        )
    stage = payload.get("stage", old.get("stage"))
    doc["stage"] = stage if stage in ids else None
    return doc


def room_order(doc: dict, mapped: dict[int, str]) -> list[int]:
    """The dosers the room has, in its order: those in the saved order first, then any other
    mapped doser by number."""
    order = [number for number in doc.get("order", []) if number in mapped]
    return order + sorted(number for number in mapped if number not in order)


def flow(doc: dict, number: int) -> float:
    return float(
        (doc.get("dosers", {}).get(str(number)) or {}).get("flow_ml_min", DEFAULT_FLOW)
    )


def recipe(doc: dict, recipe_id=None) -> dict | None:
    wanted = doc.get("stage") if recipe_id is None else recipe_id
    return next((item for item in doc.get("recipes", []) if item["id"] == wanted), None)


def plan(doc: dict, mapped: dict[int, str]) -> dict:
    """What the controller runs for this room's next batch: the batch settings and, in the room's
    order, each doser's nutrient, mL and seconds for the stage in use. `problem` says why no batch
    can run, or is None. `mapped` is the room's doser switches by number (Rooms & hardware).
    """
    stage = recipe(doc)
    doses, problem = [], None
    if not mapped:
        problem = "No doser is mapped in Settings → Rooms & hardware."
    elif stage is None:
        problem = "No feed stage is chosen."
    else:
        wanted = {
            int(key): dose for key, dose in stage["doses"].items() if dose["parts"] > 0
        }
        missing = sorted(number for number in wanted if number not in mapped)
        if missing:
            problem = f"{stage['name']} uses doser {missing[0]}, which has no switch in Settings → Rooms & hardware."
        elif not wanted:
            problem = f"{stage['name']} doses nothing: give its nutrients some parts."
        for number in room_order(doc, mapped):
            if number not in wanted:
                continue
            ml = round(wanted[number]["parts"] * stage["strength"] * doc["batch_l"], 1)
            doses.append(
                {
                    "doser": number,
                    "label": wanted[number]["label"],
                    "ml": ml,
                    "seconds": round(ml / flow(doc, number) * 60.0, 1),
                }
            )
        if not problem and not any(dose["ml"] > 0 for dose in doses):
            problem = f"{stage['name']}'s strength is 0: nothing would be dosed."
    return {
        "stage": stage["name"] if stage else None,
        "stage_id": stage["id"] if stage else None,
        **{key: doc[key] for key in SETTINGS},
        "doses": doses,
        "problem": problem,
    }
