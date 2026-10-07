"""Pure calculation helpers for crop steering."""

from __future__ import annotations

import math
import statistics

from .const import PERCENTAGE_TO_RATIO, PROBE_METHODS, SECONDS_PER_HOUR

# The shortest shot the controller runs, in seconds (MIN_SHOT_S in the controller app).
MIN_SHOT_S = 5


class ShotCalculator:
    """Helper class for irrigation shot calculations."""

    @staticmethod
    def calculate_shot_duration(
        dripper_flow: float,
        substrate_vol: float,
        shot_size: float,
        drippers_per_plant: float = 1,
    ) -> float:
        """Seconds a shot of `shot_size`% of `substrate_vol` litres per plant takes through each
        plant's `drippers_per_plant` drippers of `dripper_flow` L/hr. Plant count cancels: every
        plant gets its own shot through its own drippers at once."""
        try:
            flow = dripper_flow * drippers_per_plant
            if flow and flow > 0:
                volume_to_add = substrate_vol * (shot_size * PERCENTAGE_TO_RATIO)
                duration_hours = volume_to_add / flow
                return round(duration_hours * SECONDS_PER_HOUR, 1)
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def capped_shot_seconds(seconds: float, max_shot_seconds: float | None) -> int:
        """What the controller runs a shot of `seconds` for: whole seconds, at least MIN_SHOT_S,
        and no longer than the room's maximum shot length when that reads as one (5 s or more).
        """
        whole = int(seconds)
        if (
            max_shot_seconds is not None
            and math.isfinite(max_shot_seconds)
            and max_shot_seconds >= MIN_SHOT_S
        ):
            whole = min(int(max_shot_seconds), whole)
        return max(MIN_SHOT_S, whole)


def combine_probes(values, method: str = "Average") -> float | None:
    """A zone's one reading from its probes' readings: their average (also for a method this does
    not know), median, lowest or highest. None when no probe gives a reading."""
    values = [float(v) for v in values]
    if not values:
        return None
    if method == "Median":
        value = statistics.median(values)
    elif method == "Lowest":
        value = min(values)
    elif method == "Highest":
        value = max(values)
    else:
        value = sum(values) / len(values)
    return round(value, 2)


def combined_readings(values) -> dict[str, float | None]:
    """What each way of combining a zone's probes gives right now, by method."""
    values = list(values)
    return {method: combine_probes(values, method) for method in PROBE_METHODS}
