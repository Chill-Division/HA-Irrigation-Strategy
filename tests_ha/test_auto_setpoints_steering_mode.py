"""Auto Setpoints never spends a vegetative zone's afternoon on a dryback its nights cannot reach, in a
real Home Assistant with the real controller.

GR2 on 28 Sep: flower week 3, steering Vegetative, a 30% P3 dryback target and nights that dry about
12 points. Auto Setpoints stopped the maintenance shots the moment the ramp ended, and the zone dried
from 85% to 60% by lights-off: a generative day nobody asked for. A day now keeps its maintenance
shots until its last 3 hours when the zone steers Vegetative, or the middle of the day when it
steers Generative (the zone's own select), and the zone's auto setpoints sensor says what it gets.
"""

from datetime import datetime
from types import SimpleNamespace

import auto_setpoints as au
import pytest
from test_setup_entry import _install

ZONE = "number.crop_steering_zone_1_"
MODE = "select.crop_steering_zone_1_steering_mode"
STATUS = "sensor.crop_steering_zone_1_auto_setpoints"


@pytest.mark.parametrize("mode, stop", [("Vegetative", "19:00"), ("Generative", "16:00")])
async def test_the_zones_steering_mode_keeps_its_afternoon_and_the_sensor_says_why(
    hass, controller_for, mode, stop
):
    await _install(hass)
    await hass.services.async_call(
        "select", "select_option", {"entity_id": MODE, "option": mode}, blocking=True
    )
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.crop_steering_auto_setpoints"},
        blocking=True,
    )
    # The zone as Auto Setpoints left it this morning, so one step reaches where it goes next.
    for key, value in (
        ("p1_target_vwc", 36),
        ("field_capacity", 40),
        ("p2_vwc_threshold", 34),
        ("p3_emergency_vwc_threshold", 22),
    ):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": f"{ZONE}{key}", "value": value},
            blocking=True,
        )
    c, fake, _clock = controller_for({})
    room = c.rooms[0]
    room.lights_on_hour, room.lights_off_hour = 10.0, 22.0
    room.state[1]["learn"] = dict(
        au.fresh(),
        peak=36.0,
        gain=0.6,
        day_rate=0.72,
        night_rate=0.37,
        day_n=au.MIN_RATE_DAYS,
        night_n=au.MIN_RATE_DAYS,
        outcome="reached",
        hold_days=2,
    )
    room.state[1]["phase"], room.state[1]["shots"] = "P2", 6
    at_five = datetime(2026, 9, 28, 17, 0)
    p = c._params(room, 1)
    c._auto_tick(
        room,
        1,
        SimpleNamespace(vwc=35.0, ec=0.6, dryback_rate=0.0),
        SimpleNamespace(**{**vars(p), "dryback_target": 30.0}),
        True,
        at_five,
    )
    written = {
        d["entity_id"]: d["value"]
        for dom, svc, d in fake.calls
        if (dom, svc) == ("number", "set_value")
    }
    band = round(36.0 - 0.6 * p.p2_shot_size, 1)  # one maintenance shot under the peak
    # A generative day stops its maintenance shots at 16:00, and the trigger goes 2 points under where
    # the 30% dryback target ends, 36 x 0.7 - 2 = 23.2 (not under the 24.3% its nights can reach:
    # P3 holds a night at the target, and a trigger above that skipped P0), at most 10 points a pass.
    drying = max(34 - 10.0, round(36.0 * (1 - 0.30) - 2.0, 1))
    assert written[f"{ZONE}p2_vwc_threshold"] == (band if mode == "Vegetative" else drying)
    note = fake.sets[STATUS][1]["dryback_note"]
    assert note.startswith("30% dryback unreachable at this zone's uptake: about ")
    assert note.endswith(f"with maintenance shots until {stop}")
    assert fake.sets[STATUS][1]["p2_stop"] == stop  # the dashboard's "Maintenance stopped" from here
