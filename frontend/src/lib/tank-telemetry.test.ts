import { describe, expect, it } from "vitest";
import { createDemo } from "./demo";
import { tankTelemetry } from "./tank-telemetry";
const room = { id: "room:", name: "Flower 2", prefix: "" };
const now = Date.parse("2026-09-08T08:00:00Z");
/** The demo without Flower 2's reservoir distances: its tank card falls back to the level sensor in %. */
const withoutLevel = (states: ReturnType<typeof createDemo>) => {
  states["sensor.crop_steering_feed_plan"].attributes.full_mm = 0;
  return states;
};
describe("room tank telemetry", () => {
  it("finds renamed HA descriptors by room prefix", () => {
    const states = createDemo(now);
    states["sensor.crop_steering_system_engine_config"] = {
      ...states["sensor.crop_steering_engine_config"],
      entity_id: "sensor.crop_steering_system_engine_config",
    };
    delete states["sensor.crop_steering_engine_config"];
    expect(tankTelemetry(states, room, now).pump.on).toBe(true);
  });
  it("uses a full native datetime helper's epoch timestamp, not browser timezone", () => {
    const states = createDemo(now);
    states["sensor.crop_steering_engine_config"].attributes.tank_last_fill_sensor =
      "input_datetime.filled";
    states["input_datetime.filled"] = {
      entity_id: "input_datetime.filled",
      state: "2026-09-08 18:00:00",
      attributes: { has_date: true, has_time: true, timestamp: (now - 7200000) / 1000 },
    };
    expect(tankTelemetry(states, room, now).lastFill.timestamp).toBe("2026-09-08T06:00:00.000Z");
    states["input_datetime.filled"].attributes.has_date = false;
    expect(tankTelemetry(states, room, now).lastFill.timestamp).toBeNull();
  });
  it("reads isolated mappings, including pump and recorded fill", () => {
    const states = createDemo(now);
    const tank = tankTelemetry(states, room, now);
    // Flower 2's reservoir has its distances set: 640 mm between 125 (full) and 850 (empty) is 29%,
    // what the controller acts on, ahead of its mapped level sensor's 42%.
    expect(tank.level).toMatchObject({
      value: 29,
      unit: "%",
      entityId: "sensor.demo_reservoir_distance",
    });
    expect(tank.pump.on).toBe(true);
    expect(tank.lastFill.timestamp).toBe("2026-09-08T06:00:00.000Z");
    // Flower 1 has no reservoir level: its mapped level sensor in %.
    expect(tankTelemetry(states, { ...room, prefix: "f1_" }, now).level.value).toBe(72);
    // The controller's reading is the one: a sensor it no longer reads (stopped reporting) still shows
    // its last value in Home Assistant, but the card says it is not reading.
    const status = states["sensor.crop_steering_batch_status"];
    states[status.entity_id] = {
      ...status,
      attributes: { ...status.attributes, level_mm: null, level_pct: null },
    };
    expect(tankTelemetry(states, room, now).level).toMatchObject({
      value: null,
      issue: "Unavailable",
    });
    // Before the controller reports, the sensor's own reading, worked out the same way.
    delete states[status.entity_id];
    expect(tankTelemetry(states, room, now).level.value).toBe(29);
    states["sensor.demo_reservoir_distance"] = {
      ...states["sensor.demo_reservoir_distance"],
      state: "unavailable",
    };
    expect(tankTelemetry(states, room, now).level).toMatchObject({
      value: null,
      issue: "Unavailable",
    });
  });
  it("does not guess ambient temperature or other-room mappings", () => {
    const states = createDemo(now);
    states["sensor.crop_steering_engine_config"].attributes = {
      temperature_sensor: "sensor.demo_tank_temperature",
    };
    const tank = tankTelemetry(states, room, now);
    expect(tank.temperature.value).toBeNull();
    expect(tank.pump.on).toBeNull();
    expect(tank.lastFill.timestamp).toBeNull();
  });
  it.each(["unknown", "unavailable", "", "NaN", "101", "-1"])(
    "does not draw an invalid tank percentage: %s",
    (state) => {
      const states = withoutLevel(createDemo(now));
      states["sensor.demo_tank_level"].state = state;
      expect(tankTelemetry(states, room, now).level.value).toBeNull();
    },
  );
  it("requires percentage units and keeps temperature source units", () => {
    const states = withoutLevel(createDemo(now));
    states["sensor.demo_tank_level"].attributes.unit_of_measurement = "L";
    states["sensor.demo_tank_temperature"].attributes.unit_of_measurement = "°F";
    expect(tankTelemetry(states, room, now).level.issue).toBe("Check units");
    expect(tankTelemetry(states, room, now).temperature.unit).toBe("°F");
  });
  it.each(["unavailable", "2026-09-08", "2026-09-08T06:00:00", "2027-01-01T00:00:00Z"])(
    "never substitutes last_changed for invalid fill timestamp: %s",
    (state) => {
      const states = createDemo(now);
      states["sensor.demo_tank_last_fill"].state = state;
      expect(tankTelemetry(states, room, now).lastFill.timestamp).toBeNull();
    },
  );
  it("distinguishes unknown from off", () => {
    const states = createDemo(now);
    states["switch.demo_pump"].state = "unavailable";
    expect(tankTelemetry(states, room, now).pump.on).toBeNull();
    expect(tankTelemetry(states, room, now).fill.on).toBe(false);
  });
});
