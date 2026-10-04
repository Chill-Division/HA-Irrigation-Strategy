import { describe, expect, it } from "vitest";
import { choiceLabel, readProbes, readingTile, type ProbeChoice } from "./probes";
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

describe("the room's tiles for readings from probes", () => {
  const choice = (method: string, probes = 2) =>
    ({ method, readings: Array.from({ length: probes }, () => ({})) }) as ProbeChoice;
  it("name one zone's reading for its choice: Lowest VWC for its lowest probe", () => {
    expect(readingTile("VWC", [choice("Lowest")])).toBe("Lowest VWC");
    expect(readingTile("EC", [choice("Average")])).toBe("Average EC");
    // One probe has no choice to make; an integration from before the choice reads the average.
    expect(readingTile("VWC", [choice("Lowest", 1)])).toBe("Average VWC");
    expect(readingTile("VWC", [null])).toBe("Average VWC");
  });
  it("name several zones' average for the choice their zones with two or more probes share", () => {
    expect(readingTile("VWC", [choice("Lowest"), choice("Lowest")])).toBe("Average lowest VWC");
    // A zone with one probe reads that probe whatever its choice.
    expect(readingTile("EC", [choice("Median"), choice("Average", 1), null])).toBe(
      "Average median EC",
    );
    // Zones that choose differently: their average, with no one choice to name.
    expect(readingTile("VWC", [choice("Lowest"), choice("Highest")])).toBe("Average VWC");
    expect(readingTile("VWC", [choice("Average"), choice("Average")])).toBe("Average VWC");
  });
  it("are the Overview's: a room of one zone reading its lowest probe says Lowest VWC", () => {
    const demo = createDemo();
    demo["select.crop_steering_zone_1_vwc_method"].state = "Lowest";
    const room = discoverRooms(demo).find((r) => r.id === "room:")!;
    // Three zones; zone 1, the one with two probes, reads its lowest for moisture.
    const labels = () => {
      const [vwc, ec] = buildRoom(demo, room).metrics;
      return [vwc.label, ec.label];
    };
    expect(labels()).toEqual(["Average lowest VWC", "Average EC"]);
    // The same room with only its first zone: its tiles are that zone's readings, named for them.
    const config = demo["sensor.crop_steering_engine_config"];
    demo[config.entity_id] = {
      ...config,
      attributes: { ...config.attributes, num_zones: 1, active_zone_ids: [1] },
    };
    expect(buildRoom(demo, room).zones.map((z) => z.id)).toEqual([1]);
    expect(labels()).toEqual(["Lowest VWC", "Average EC"]);
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
