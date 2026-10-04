import type { EntityState, States } from "./types";

/** How a zone's probes become its one moisture reading, and separately its one EC reading: the
 * zone's select (select.crop_steering_<prefix>zone_N_vwc_method / _ec_method) and what the zone's
 * sensor publishes from its probes (sensor.py: `probes`, `combined`, `method`). */
export const PROBE_METHODS = ["Average", "Median", "Lowest", "Highest"];

export interface ProbeReading {
  entityId: string;
  name: string;
  value: number;
}
export interface ProbeChoice {
  /** The zone's select; null on an integration without it (the zone then reads the average). */
  entityId: string | null;
  /** The choice in use. */
  method: string;
  options: string[];
  /** Each probe's reading, as the zone's sensor took it (in % or mS/cm). */
  readings: ProbeReading[];
  /** What each choice gives from those readings right now. */
  combined: Record<string, number | null>;
}

const finite = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

/** A zone's probes for one reading, or null when its sensor does not list them (an integration
 * from before the choice existed). */
export function readProbes(
  states: States,
  sensor: EntityState | undefined,
  select: EntityState | undefined,
): ProbeChoice | null {
  const probes = sensor?.attributes.probes;
  if (!sensor || !probes || typeof probes !== "object" || Array.isArray(probes)) return null;
  const readings = Object.entries(probes as Record<string, unknown>).flatMap(([entityId, value]) =>
    finite(value)
      ? [{ entityId, name: String(states[entityId]?.attributes.friendly_name || entityId), value }]
      : [],
  );
  const raw = sensor.attributes.combined;
  const combined: Record<string, number | null> = {};
  if (raw && typeof raw === "object" && !Array.isArray(raw))
    for (const [method, value] of Object.entries(raw as Record<string, unknown>))
      combined[method] = finite(value) ? value : null;
  const listed = select?.attributes.options;
  const options = Array.isArray(listed) ? listed.map(String) : PROBE_METHODS;
  const method =
    select && options.includes(select.state)
      ? select.state
      : String(sensor.attributes.method || "Average");
  return { entityId: select?.entity_id ?? null, method, options, readings, combined };
}

/** "Lowest — 83.5% (THC-S Door End)": a choice, what it gives now and, for the lowest or the
 * highest, which probe that is. */
export function choiceLabel(
  choice: ProbeChoice,
  option: string,
  unit: string,
  format: (value: number) => string,
): string {
  const value = choice.combined[option];
  if (value === null || value === undefined) return option;
  const probe =
    option === "Lowest" || option === "Highest"
      ? choice.readings.find((reading) => Math.abs(reading.value - value) < 0.005)
      : undefined;
  return `${option} — ${format(value)}${unit}${probe ? ` (${probe.name})` : ""}`;
}

/** What the room's tile for a reading from probes is called. One zone's is that zone's reading,
 * named for its choice ("Lowest VWC"); several zones' is their average, named for the choice they
 * share ("Average lowest VWC"). Only a zone with two or more probes has a choice to make. */
export function readingTile(reading: "VWC" | "EC", choices: (ProbeChoice | null)[]): string {
  const methods = new Set(
    choices.flatMap((choice) => (choice && choice.readings.length > 1 ? [choice.method] : [])),
  );
  const [method = "Average"] = methods.size === 1 ? methods : [];
  if (choices.length === 1) return `${method} ${reading}`;
  return method === "Average" ? `Average ${reading}` : `Average ${method.toLowerCase()} ${reading}`;
}
