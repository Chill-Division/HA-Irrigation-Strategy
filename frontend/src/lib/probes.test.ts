import { describe, expect, it } from "vitest";
import { choiceLabel, readProbes } from "./probes";
import { buildRoom, discoverRooms, validateChange } from "./model";
import { createDemo, demoReact } from "./demo";
import type { EntityState, States } from "./types";

const DOOR = "sensor.thc_s_door_end_humidity",
  AC = "sensor.thc_s_ac_end_humidity";
const states: States = {
  [DOOR]: { entity_id: DOOR, state: "83.5", attributes: { friendly_name: "THC-S Door End" } },
  [AC]: { entity_id: AC, state: "87.7", attributes: { friendly_name: "THC-S AC End" } },
};
const sensor = (attributes: Record<string, unknown>): EntityState => ({
  entity_id: "sensor.crop_steering_vwc_zone_1",
  state: "83.5",
  attributes,
});
const select: EntityState = {
  entity_id: "select.crop_steering_zone_1_vwc_method",
  state: "Lowest",
  attributes: { options: ["Average", "Median", "Lowest", "Highest"] },
};
const GR2 = {
  method: "Lowest",
  probes: { [DOOR]: 83.5, [AC]: 87.7 },
  combined: { Average: 85.6, Median: 85.6, Lowest: 83.5, Highest: 87.7 },
};

describe("how a zone's probes are read", () => {
  it("reads each probe, what every choice gives, and the choice in use", () => {
    const choice = readProbes(states, sensor(GR2), select)!;
    expect(choice.entityId).toBe("select.crop_steering_zone_1_vwc_method");
    expect(choice.method).toBe("Lowest");
    expect(choice.readings).toEqual([
      { entityId: DOOR, name: "THC-S Door End", value: 83.5 },
      { entityId: AC, name: "THC-S AC End", value: 87.7 },
    ]);
    expect(choice.combined.Highest).toBe(87.7);
  });

  it("labels each choice with its reading now, and which probe the lowest and highest are", () => {
    const choice = readProbes(states, sensor(GR2), select)!;
    const label = (option: string) => choiceLabel(choice, option, "%", String);
    expect(label("Lowest")).toBe("Lowest — 83.5% (THC-S Door End)");
    expect(label("Highest")).toBe("Highest — 87.7% (THC-S AC End)");
    expect(label("Average")).toBe("Average — 85.6%");
  });

  it("is nothing on an integration whose sensor does not list its probes", () => {
    expect(readProbes(states, sensor({}), select)).toBeNull();
    expect(readProbes(states, undefined, select)).toBeNull();
    // A select not there yet: the sensor's own word for the choice.
    expect(readProbes(states, sensor(GR2), undefined)?.method).toBe("Lowest");
  });
});

describe("the demo's two-probe zone", () => {
  it("reads its probes, takes a new choice as a review would apply it, and refuses a wrong one", () => {
    let demo = createDemo();
    const room = discoverRooms(demo).find((r) => r.id === "room:")!;
    const zone = buildRoom(demo, room).zones.find((z) => z.id === 1)!;
    expect(zone.probes.vwc?.readings.map((r) => r.value)).toEqual([54, 58]);
    expect(zone.probes.vwc?.method).toBe("Average");
    const entityId = zone.probes.vwc!.entityId!;
    const view = buildRoom(demo, room);
    expect(validateChange(view, demo, { entityId, value: "Lowest" })).toBeNull();
    expect(validateChange(view, demo, { entityId, value: "Mode" })).toMatch(/Choose Average/);
    demo = demoReact(
      { ...demo, [entityId]: { ...demo[entityId], state: "Lowest" } },
      entityId,
      "Lowest",
    );
    const after = buildRoom(demo, room).zones.find((z) => z.id === 1)!;
    expect(after.vwc.value).toBe(54);
    expect(after.probes.vwc?.method).toBe("Lowest");
  });
});
