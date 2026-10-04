import { describe, expect, it } from "vitest";
import {
  SIZING_BOUNDS,
  displayNumber,
  reviewValue,
  sizingError,
  sizingLabel,
  stateText,
} from "./units";

describe("sizing numbers", () => {
  it("rounds for display only, trimming trailing zeros", () => {
    expect(displayNumber(4.992851478)).toBe("4.993");
    expect(displayNumber(5)).toBe("5");
    expect(displayNumber(0.65)).toBe("0.65");
    expect(displayNumber(18.92705892, 2)).toBe("18.93");
    expect(displayNumber(NaN)).toBe("");
  });
  it("shows a reported reading to at most three decimals, and anything else as it is", () => {
    expect(stateText("0.639473676681519")).toBe("0.639"); // an estimated-pwEC probe, unrounded
    expect(stateText("83.5")).toBe("83.5");
    expect(stateText("525")).toBe("525");
    for (const state of ["on", "unavailable", "unknown", "", " ", "2026-09-28T03:15:00+13:00"])
      expect(stateText(state)).toBe(state);
  });
});

describe("sizing field text", () => {
  it("names the unit in each label: litres and L/h", () => {
    expect(sizingLabel("substrate_volume")).toBe("Pot volume · L per plant");
    expect(sizingLabel("dripper_flow_rate")).toBe("Dripper flow · L/h each");
  });
  it("reviews the value being saved", () => {
    expect(reviewValue(6, "substrate_volume")).toBe("6 L");
    expect(reviewValue(3.37, "substrate_volume")).toBe("3.37 L");
    expect(reviewValue(4, "dripper_flow_rate")).toBe("4 L/h");
  });
});

describe("sizing bounds", () => {
  it("mirrors the limits the integration enforces", () => {
    expect(SIZING_BOUNDS).toEqual({
      substrate_volume: { min: 0.1, max: 200 },
      dripper_flow_rate: { min: 0.1, max: 50 },
    });
  });
  it("accepts everything the integration accepts", () => {
    expect(sizingError(0.1, "substrate_volume")).toBe("");
    expect(sizingError(200, "substrate_volume")).toBe("");
    expect(sizingError(50, "dripper_flow_rate")).toBe("");
  });
  it("reports a bounds error in litres or L/h", () => {
    expect(sizingError(250, "substrate_volume")).toBe("Pot volume must be 0.1–200 L.");
    expect(sizingError(0, "dripper_flow_rate")).toBe("Dripper flow must be 0.1–50 L/h.");
  });
  it("asks for a number when the entry is blank or not a number", () => {
    expect(sizingError(NaN, "substrate_volume")).toBe("Enter the pot volume in L.");
    expect(sizingError(NaN, "dripper_flow_rate")).toBe("Enter the dripper flow in L/h.");
  });
});
