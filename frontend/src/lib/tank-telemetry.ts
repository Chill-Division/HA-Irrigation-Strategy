import type { Room, States } from "./types";
import { descriptor } from "./model";
import { levelPct } from "./feed";
import { levelMm } from "./feed-status";

export interface TankReading {
  entityId: string | null;
  value: number | null;
  unit: string;
  issue: string | null;
}

export function tankTelemetry(states: States, room: Room, now = Date.now()) {
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
  const fillId = mapped("tank_last_fill_sensor");
  const fillEntity = fillId ? states[fillId] : undefined;
  const raw = fillEntity?.state || "";
  const attrs = fillEntity?.attributes;
  const time =
    fillId?.startsWith("input_datetime.") &&
    attrs?.has_date === true &&
    attrs?.has_time === true &&
    typeof attrs.timestamp === "number" &&
    !["unknown", "unavailable", ""].includes(raw)
      ? attrs.timestamp * 1000
      : /^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/i.test(raw)
        ? Date.parse(raw)
        : NaN;
  const fillIssue = !fillId
    ? "Not mapped"
    : !Number.isFinite(time) || time <= 0 || Number.isNaN(new Date(time).getTime())
      ? "Unavailable"
      : time > now
        ? "Future timestamp"
        : null;
  // The reservoir's own level once its distances when full and when empty are set (Feed →
  // Reservoir): the distance sensor's reading as the controller works it out, so the card shows what
  // the controller acts on. Otherwise a mapped level sensor in %.
  const plan = states[`sensor.crop_steering_${room.prefix}feed_plan`]?.attributes;
  const distanceId = mapped("reservoir_distance_sensor");
  const full = Number(plan?.full_mm),
    empty = Number(plan?.empty_mm);
  const own = distanceId && full > 0 && full < empty;
  const pct = own ? levelPct(levelMm(states[distanceId]), full, empty) : null;
  const level: TankReading = own
    ? {
        entityId: distanceId,
        value: pct === null ? null : Math.round(pct * 10) / 10,
        unit: "%",
        issue: pct === null ? "Unavailable" : null,
      }
    : reading("water_level_sensor", ["%"], 0, 100);
  return {
    level,
    temperature: reading("tank_temperature_sensor", ["°c", "°f", "k"]),
    pump: binary("pump"),
    fill: binary("tank_fill_entity"),
    lastFill: {
      entityId: fillId,
      timestamp: fillIssue ? null : new Date(time).toISOString(),
      issue: fillIssue,
    },
  };
}
