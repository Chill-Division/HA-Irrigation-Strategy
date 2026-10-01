import { describe, expect, it } from "vitest";
import { levelWarning, type ZoneLevels } from "./level-order";

// GR2 on 28 Sep: a peak target of 87 under a field capacity of 90, the trigger at 70, a 30% P3
// dryback and the rescue level at 50. Nothing in it works against the rest.
const GR2: ZoneLevels = { peak: 87, fieldCapacity: 90, trigger: 70, rescue: 50, dryback: 30 };
const PARAMS = [
  "p1_target_vwc",
  "p2_vwc_threshold",
  "p3_emergency_vwc_threshold",
  "vegetative_dryback_target",
  "generative_dryback_target",
];

describe("a zone's moisture levels against each other", () => {
  it("says nothing about levels that sit in order", () => {
    for (const param of PARAMS) expect(levelWarning(param, GR2)).toBeNull();
  });
  it("says where the ramp stops when the peak target is above field capacity", () => {
    expect(levelWarning("p1_target_vwc", { ...GR2, peak: 95 })).toBe(
      "the ramp stops at field capacity, 90%, below this target",
    );
  });
  it("says which trigger the controller uses when the typed one is out of order", () => {
    expect(levelWarning("p2_vwc_threshold", { ...GR2, trigger: 90 })).toBe(
      "the controller uses 86%: it keeps the trigger 1 point under the peak VWC target",
    );
    expect(levelWarning("p2_vwc_threshold", { ...GR2, trigger: 90, fieldCapacity: 80 })).toBe(
      "the controller uses 79%: it keeps the trigger 1 point under the field capacity",
    );
    expect(levelWarning("p2_vwc_threshold", { ...GR2, trigger: 51 })).toBe(
      "the controller uses 53%: it keeps the trigger at least 3 points above the rescue level",
    );
  });
  it("says when the day dries further than the night", () => {
    // (87 − 55) / 87 is 36.8% below the peak before a maintenance shot; overnight only 30%.
    expect(levelWarning("p2_vwc_threshold", { ...GR2, trigger: 55 })).toBe(
      "by day the substrate dries 36.8% below the 87% peak target before a maintenance shot, further than the 30% it dries back overnight, so P3 may water it back up to 60.9% after lights-off",
    );
  });
  it("says when the rescue level would stop tonight's dryback, from either setting", () => {
    // A 30% dryback from 87 ends at 60.9%: a rescue level of 65 fires first.
    const early = { ...GR2, rescue: 65, trigger: 70 };
    expect(levelWarning("p3_emergency_vwc_threshold", early)).toBe(
      "rescue shots would stop tonight's dryback at 65%: a 30% dryback from the 87% peak target ends at 60.9%",
    );
    expect(levelWarning("generative_dryback_target", early)).toBe(
      "from the 87% peak target this dryback ends at 60.9%, below the 65% rescue level, so rescue shots would stop it there",
    );
  });
  it("names field capacity as the peak when the ramp stops there, and says an 8% dryback", () => {
    expect(
      levelWarning("p3_emergency_vwc_threshold", {
        ...GR2,
        fieldCapacity: 80,
        dryback: 8,
        rescue: 75,
      }),
    ).toBe(
      "rescue shots would stop tonight's dryback at 75%: an 8% dryback from the 80% field capacity ends at 73.6%",
    );
  });
  it("says nothing it cannot work out", () => {
    for (const param of PARAMS) expect(levelWarning(param, {})).toBeNull();
    expect(levelWarning("p3_emergency_vwc_threshold", { rescue: 65, dryback: 30 })).toBeNull();
    expect(levelWarning("p2_shot_size", GR2)).toBeNull();
  });
});
