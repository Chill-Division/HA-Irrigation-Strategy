import type { Room, States } from "./types";
import { descriptor } from "./model";
import { RESERVOIR_KEYS, levelPct } from "./feed";
import { STEP_LABELS, levelMm, readBatchStatus } from "./feed-status";

export interface TankReading {
  entityId: string | null;
  value: number | null;
  unit: string;
  issue: string | null;
}

/** The refills the controller runs for the room's reservoir, as it records them. */
export interface RefillRecord {
  /** What its refill is doing now: "Not running", "Filling", "Dosing"…; null before it reports. */
  now: string | null;
  running: boolean;
  /** When its last refill ended (ISO); null before the first. */
  lastAt: string | null;
  /** That refill stopped part-way. */
  lastStopped: boolean;
  issue: string | null;
}

export function tankTelemetry(states: States, room: Room) {
  const config = descriptor(states, room)?.attributes || {};
  const mapped = (key: string) =>
    typeof config[key] === "string" && config[key] ? String(config[key]) : null;
  const reading = (key: string, units: string[], min = -Infinity, max = Infinity): TankReading => {
    const entityId = mapped(key),
      entity = entityId ? states[entityId] : undefined;
    const unit = String(entity?.attributes.unit_of_measurement || "");
    const value = entity?.state.trim() ? Number(entity.state) : NaN;
    const issue = !entityId
      ? "Not mapped"
      : !Number.isFinite(value)
        ? "Unavailable"
        : !units.includes(unit.toLowerCase())
          ? "Check units"
          : value < min || value > max
            ? "Out of range"
            : null;
    return { entityId, value: issue ? null : value, unit, issue };
  };
  const binary = (key: string) => {
    const entityId = mapped(key),
      state = entityId ? states[entityId]?.state : undefined;
    return {
      entityId,
      on: state === "on" ? true : state === "off" ? false : null,
      issue: !entityId ? "Not mapped" : !["on", "off"].includes(state || "") ? "Unavailable" : null,
    };
  };
  // The reservoir's own level once its distances when full and when empty are set (Feed →
  // Reservoir): the controller's, once it reports one, so the card shows what it acts on (none when
  // the sensor reads nothing to it, whatever that shows now); before that, the distance sensor's
  // reading worked out the same way. Otherwise a mapped level sensor in %.
  const plan = states[`sensor.crop_steering_${room.prefix}feed_plan`]?.attributes;
  const distanceId = mapped("reservoir_distance_sensor");
  const full = Number(plan?.full_mm),
    empty = Number(plan?.empty_mm);
  const own = distanceId && full > 0 && full < empty;
  const status = readBatchStatus(states, room.prefix);
  const pct = !own
    ? null
    : status
      ? status.levelPct
      : levelPct(levelMm(states[distanceId]), full, empty);
  const level: TankReading = own
    ? {
        entityId: distanceId,
        value: pct === null ? null : Math.round(pct * 10) / 10,
        unit: "%",
        issue: pct === null ? "Unavailable" : null,
      }
    : reading("water_level_sensor", ["%"], 0, 100);
  // A room with a reservoir: the controller's record of the refills it runs (batch_status). None for
  // a room without one, which nothing refills.
  const step = status?.step ?? null;
  const refill: RefillRecord | null =
    status || RESERVOIR_KEYS.some((key) => mapped(key))
      ? {
          now: step === null ? null : step === "idle" ? "Not running" : STEP_LABELS[step],
          running: step !== null && step !== "idle",
          lastAt: status?.last?.at ? new Date(status.last.at).toISOString() : null,
          lastStopped: !!status?.last && status.last.result !== "done",
          issue: step === null ? "Unavailable" : null,
        }
      : null;
  return {
    level,
    temperature: reading("tank_temperature_sensor", ["°c", "°f", "k"]),
    pump: binary("pump"),
    refill,
  };
}
