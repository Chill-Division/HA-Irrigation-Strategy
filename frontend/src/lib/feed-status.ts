import type { PlannedDose } from "./feed";
import type { EntityState, States } from "./types";

/** A room's nutrient batch as the controller app reports it: sensor.crop_steering_<prefix>batch_status
 * (controller.py _batch_publish). The state is the step; idle while no batch runs. */
export const BATCH_STEPS = ["filling", "settling", "dosing", "pausing", "mixing"] as const;
export type BatchStep = "idle" | (typeof BATCH_STEPS)[number];
export interface BatchDose extends PlannedDose {
  /** mL it gave in the batch running now; null before its turn. */
  dosed: number | null;
}
export interface LastBatch {
  at: number | null;
  /** "done", or "stopped: <why>". */
  result: string;
  stage: string | null;
  dosed: Record<string, number>;
}
export interface BatchStatus {
  entityId: string;
  /** null: the sensor reads something else (unavailable). */
  step: BatchStep | null;
  stage: string | null;
  /** When the step in progress ends (epoch ms). */
  until: number | null;
  doser: number | null;
  nutrient: string | null;
  doses: BatchDose[];
  levelMm: number | null;
  emptyMm: number | null;
  auto: boolean;
  armed: boolean;
  last: LastBatch | null;
  /** Why no batch could start now, or null. */
  blocked: string | null;
  updated: number | null;
}

export const STEP_LABELS: Record<BatchStep, string> = {
  idle: "Idle",
  filling: "Filling",
  settling: "Circulating before dosing",
  dosing: "Dosing",
  pausing: "Between dosers",
  mixing: "Mixing",
};

const finite = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value) ? value : null;
const text = (value: unknown) => (typeof value === "string" && value ? value : null);
const time = (value: unknown) => {
  const at = typeof value === "string" ? Date.parse(value) : NaN;
  return Number.isFinite(at) ? at : null;
};

export const batchStatusId = (prefix: string) => `sensor.crop_steering_${prefix}batch_status`;

/** The room's batch status, or null when the controller has not reported one (no reservoir mapped,
 * the controller app not running, or a version without nutrient batches). */
export function readBatchStatus(states: States, prefix: string): BatchStatus | null {
  const entityId = batchStatusId(prefix);
  const entity = states[entityId];
  if (!entity) return null;
  const a = entity.attributes;
  const step = (["idle", ...BATCH_STEPS] as string[]).includes(entity.state)
    ? (entity.state as BatchStep)
    : null;
  const last = a.last && typeof a.last === "object" ? (a.last as Record<string, unknown>) : null;
  return {
    entityId,
    step,
    stage: text(a.stage),
    until: time(a.until),
    doser: finite(a.doser),
    nutrient: text(a.nutrient),
    doses: Array.isArray(a.doses)
      ? a.doses.flatMap((dose) => {
          const d = dose as Record<string, unknown>;
          const doser = finite(d.doser);
          return doser === null
            ? []
            : [
                {
                  doser,
                  label: text(d.label) ?? `Doser ${doser}`,
                  ml: finite(d.ml) ?? 0,
                  seconds: finite(d.seconds) ?? 0,
                  dosed: finite(d.dosed),
                },
              ];
        })
      : [],
    levelMm: finite(a.level_mm),
    emptyMm: finite(a.empty_mm),
    auto: a.auto === true,
    armed: a.armed !== false,
    last: last
      ? {
          at: time(last.at),
          result: text(last.result) ?? "unknown",
          stage: text(last.stage),
          dosed:
            last.dosed && typeof last.dosed === "object"
              ? Object.fromEntries(
                  Object.entries(last.dosed as Record<string, unknown>).flatMap(([n, ml]) =>
                    finite(ml) === null ? [] : [[n, finite(ml)!]],
                  ),
                )
              : {},
        }
      : null,
    blocked: text(a.blocked),
    updated: time(a.updated),
  };
}

/** A distance sensor's reading in mm, as the controller reads it (controller.py level_mm): it may
 * report mm, cm or m; no unit is mm. null when it reads no number or another unit. */
export function levelMm(entity: EntityState | undefined): number | null {
  if (!entity || !entity.state.trim()) return null;
  const value = Number(entity.state);
  const unit = String(entity.attributes.unit_of_measurement ?? "")
    .trim()
    .toLowerCase();
  const factor = ({ mm: 1, cm: 10, m: 1000, "": 1 } as Record<string, number>)[unit];
  return Number.isFinite(value) && factor !== undefined ? value * factor : null;
}

/** Is the reservoir almost empty: its sensor reads at or past the mark (distances grow as it empties).
 * null when there is no reading or no mark. */
export function almostEmpty(levelMm: number | null, emptyMm: number | null): boolean | null {
  if (levelMm === null || emptyMm === null || emptyMm <= 0) return null;
  return levelMm >= emptyMm;
}

/** "3 min 20 s left", counted to `until`; null once it has passed or when unknown. */
export function timeLeft(until: number | null, now = Date.now()): string | null {
  if (until === null) return null;
  const seconds = Math.ceil((until - now) / 1000);
  if (seconds <= 0) return null;
  const minutes = Math.floor(seconds / 60),
    rest = seconds % 60;
  return minutes ? `${minutes} min${rest ? ` ${rest} s` : ""} left` : `${rest} s left`;
}
