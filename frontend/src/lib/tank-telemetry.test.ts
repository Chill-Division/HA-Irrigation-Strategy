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
    expect(tankTelemetry(states, room).pump.on).toBe(true);
  });
  it("reads isolated mappings, the pump and the controller's refills", () => {
    const states = createDemo(now);
    const tank = tankTelemetry(states, room);
    // Flower 2's reservoir has its distances set: 640 mm between 125 (full) and 850 (empty) is 29%,
    // what the controller acts on, ahead of its mapped level sensor's 42%.
    expect(tank.level).toMatchObject({
      value: 29,
      unit: "%",
      entityId: "sensor.demo_reservoir_distance",
    });
    expect(tank.pump.on).toBe(true);
    // Flower 2's last refill as the controller recorded it: done, 20 hours ago; none running now.
    expect(tank.refill).toEqual({
      now: "Not running",
      running: false,
      lastAt: "2026-09-07T12:24:10.000Z",
      lastStopped: false,
      issue: null,
    });
    // Flower 1 has no reservoir level: its mapped level sensor in %. Nothing refills it.
    const flower1 = tankTelemetry(states, { ...room, prefix: "f1_" });
    expect(flower1.level.value).toBe(72);
    expect(flower1.refill).toBeNull();
    // The controller's reading is the one: when it reads no level, the card says so, whatever the
    // sensor shows now.
    const status = states["sensor.crop_steering_batch_status"];
    states[status.entity_id] = {
      ...status,
      attributes: { ...status.attributes, level_mm: null, level_pct: null },
    };
    expect(tankTelemetry(states, room).level).toMatchObject({
      value: null,
      issue: "Unavailable",
    });
    // Before the controller reports, the sensor's own reading, worked out the same way.
    delete states[status.entity_id];
    expect(tankTelemetry(states, room).level.value).toBe(29);
    states["sensor.demo_reservoir_distance"] = {
      ...states["sensor.demo_reservoir_distance"],
      state: "unavailable",
    };
    expect(tankTelemetry(states, room).level).toMatchObject({
      value: null,
      issue: "Unavailable",
    });
  });
  it("shows a refill running, and one that stopped part-way", () => {
    const states = createDemo(now);
    const status = states["sensor.crop_steering_batch_status"];
    const last = status.attributes.last as Record<string, unknown>;
    states[status.entity_id] = {
      ...status,
      state: "dosing",
      attributes: {
        ...status.attributes,
        last: { ...last, result: "stopped: the reservoir's level sensor read nothing" },
      },
    };
    expect(tankTelemetry(states, room).refill).toMatchObject({
      now: "Dosing",
      running: true,
      lastStopped: true,
    });
    // A reservoir whose controller has not reported: not "not running", but unknown.
    delete states[status.entity_id];
    expect(tankTelemetry(states, room).refill).toEqual({
      now: null,
      running: false,
      lastAt: null,
      lastStopped: false,
      issue: "Unavailable",
    });
  });
  it("does not guess ambient temperature or other-room mappings", () => {
    const states = createDemo(now);
    states["sensor.crop_steering_engine_config"].attributes = {
      temperature_sensor: "sensor.demo_tank_temperature",
    };
    const tank = tankTelemetry(states, room);
    expect(tank.temperature.value).toBeNull();
    expect(tank.pump.on).toBeNull();
  });
  it.each(["unknown", "unavailable", "", "NaN", "101", "-1"])(
    "does not draw an invalid tank percentage: %s",
    (state) => {
      const states = withoutLevel(createDemo(now));
      states["sensor.demo_tank_level"].state = state;
      expect(tankTelemetry(states, room).level.value).toBeNull();
    },
  );
  it("requires percentage units and keeps temperature source units", () => {
    const states = withoutLevel(createDemo(now));
    states["sensor.demo_tank_level"].attributes.unit_of_measurement = "L";
    states["sensor.demo_tank_temperature"].attributes.unit_of_measurement = "°F";
    expect(tankTelemetry(states, room).level.issue).toBe("Check units");
    expect(tankTelemetry(states, room).temperature.unit).toBe("°F");
  });
  it("distinguishes unknown from off", () => {
    const states = createDemo(now);
    states["switch.demo_pump"].state = "unavailable";
    expect(tankTelemetry(states, room).pump.on).toBeNull();
    states["switch.demo_pump"].state = "off";
    expect(tankTelemetry(states, room).pump.on).toBe(false);
  });
});
