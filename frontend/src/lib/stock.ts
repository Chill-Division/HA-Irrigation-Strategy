import type { Tone } from "@/components/mini-visuals";

/** A room's stock tanks, as the integration's stock services return them (stock_api.py). */
export interface StockTank {
  id: string;
  name: string;
  capacity_l: number;
  level_l: number;
  /** The Reservoir doser its bottle feeds (1 to 6): each batch the controller mixes takes what that
   * doser gave, as the feed recipe in use says. null: on none, so only a refill or a level set by
   * hand changes it. */
  doser: number | null;
  low_l: number;
  refilled_at: string | null;
  updated_at: string;
}
export interface StockBatch {
  at: string;
  /** "reservoir"; a batch counted before 2.32 may also be "fill" or "manual". */
  source: "fill" | "manual" | "reservoir";
  draw_ml: Record<string, number>;
}
export interface StockDocument {
  schema_version: 1;
  room_id: string;
  revision: number;
  tanks: StockTank[];
  history: StockBatch[];
  /** The room's Reservoir dosers, each with the nutrient the feed stage in use puts on it. */
  dosers?: Record<string, { switch: string; nutrient: string | null }>;
  /** When the last Reservoir batch counted ended. */
  reservoir_batch?: string | null;
  /** What one batch takes from each tank right now, in mL: what the feed recipe in use gives from its
   * doser. */
  doses: Record<string, number>;
  low: string[];
  max_tanks: number;
  error: string | null;
}
/** What the editor sends for one tank; `id` is absent for a new one. */
export type StockTankDraft = Omit<StockTank, "id" | "refilled_at" | "updated_at"> & {
  id?: string;
};

export const stockShare = (tank: Pick<StockTank, "level_l" | "capacity_l">) =>
  tank.capacity_l > 0 ? Math.max(0, Math.min(100, (tank.level_l / tank.capacity_l) * 100)) : 0;

export const batchesLeft = (tank: Pick<StockTank, "level_l">, doseMl: number | undefined) =>
  doseMl && doseMl > 0 ? Math.floor(Math.round(tank.level_l * 1000 * 1e6) / 1e6 / doseMl) : null;

/** Red at or under the low mark, amber within half as much again, normal above. */
export function stockTone(tank: Pick<StockTank, "level_l" | "low_l">): Tone {
  if (tank.level_l <= tank.low_l) return "over";
  return tank.level_l <= tank.low_l * 1.5 ? "high" : "normal";
}

/** The checks the integration makes (stock.py clean_tanks), so the editor can say so first. */
export function draftErrors(drafts: StockTankDraft[], max = 12): string[] {
  const errors: string[] = [];
  if (drafts.length > max) errors.push(`At most ${max} stock tanks per room.`);
  const names = new Set<string>();
  for (const tank of drafts) {
    const name = tank.name.trim();
    const label = name || "A tank";
    if (!name || name.length > 40) errors.push("Each tank needs a name of 1 to 40 characters.");
    else if (names.has(name.toLowerCase())) errors.push(`Two tanks are called ${name}.`);
    names.add(name.toLowerCase());
    if (!(tank.capacity_l >= 0.1 && tank.capacity_l <= 10000))
      errors.push(`${label}: capacity must be between 0.1 and 10000 L.`);
    if (!(tank.level_l >= 0 && tank.level_l <= tank.capacity_l))
      errors.push(`${label}: the level must be between 0 L and its capacity.`);
    if (!(tank.low_l >= 0 && tank.low_l <= tank.capacity_l))
      errors.push(`${label}: the low mark must be between 0 L and its capacity.`);
    if (
      tank.doser !== null &&
      tank.doser !== undefined &&
      !(Number.isInteger(tank.doser) && tank.doser >= 1 && tank.doser <= 6)
    )
      errors.push(`${label}: a doser is numbered 1 to 6.`);
  }
  return errors;
}

/** As stock.py on_doser: the tank a doser draws from, the one on it or, when several share it
 * (bottles swapped between stages), the one named like the nutrient on it. */
export function onDoser<T extends Pick<StockTank, "name" | "doser">>(
  tanks: T[],
  doser: number,
  nutrient: string | null | undefined,
): T | undefined {
  const on = tanks.filter((tank) => tank.doser === doser);
  if (on.length === 1) return on[0];
  const wanted = (nutrient ?? "").trim().toLowerCase();
  return on.find((tank) => tank.name.trim().toLowerCase() === wanted);
}
