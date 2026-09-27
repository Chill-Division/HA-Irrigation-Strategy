"""Pure calculation helpers for crop steering."""

from __future__ import annotations

import statistics

from .const import PERCENTAGE_TO_RATIO, PROBE_METHODS, SECONDS_PER_HOUR


class ShotCalculator:
    """Helper class for irrigation shot calculations."""

    @staticmethod
    def calculate_shot_duration(
        dripper_flow: float, substrate_vol: float, shot_size: float
    ) -> float:
        """Calculate irrigation shot duration in seconds."""
        try:
            if dripper_flow and dripper_flow > 0:
                volume_to_add = substrate_vol * (shot_size * PERCENTAGE_TO_RATIO)
                duration_hours = volume_to_add / dripper_flow
                return round(duration_hours * SECONDS_PER_HOUR, 1)
            return 0.0
        except Exception:
            return 0.0


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
