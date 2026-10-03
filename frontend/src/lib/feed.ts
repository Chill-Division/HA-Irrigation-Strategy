import { createUuid } from "./uuid";

/** A room's nutrient batches, as the integration's feed services return them (feed.py, feed_api.py):
 * the reservoir's batch settings, the dosers' flow, and a feed recipe for each growth stage, with the
 * order its dosers dose in. The amounts: a recipe gives each doser's nutrient a number of parts, and a
 * strength in mL per litre per part; the fill's litres scale them, to the whole mL. A doser runs for
 * its mL at its flow (600 mL/min unless set). */

export interface FeedDose {
  label: string;
  parts: number;
}
export interface FeedRecipe {
  id: string;
  name: string;
  /** mL per litre per part. */
  strength: number;
  /** By doser number ("1" to "6"). */
  doses: Record<string, FeedDose>;
  /** The order its dosers dose in; any other doser follows, by number (feed.py recipe_order). */
  order: number[];
}
export interface PlannedDose {
  doser: number;
  label: string;
  ml: number;
  seconds: number;
}
export interface FeedSettings {
  fill_s: number;
  /** The litres the fill adds: what the doses are worked out for. */
  batch_l: number;
  /** The level sensor's distance to the water when full, and when empty; 0 = not set. */
  full_mm: number;
  empty_mm: number;
  /** The least the reservoir keeps, %: a refill comes before a shot that would take it lower. */
  min_pct: number;
  pause_s: number;
  mix_s: number;
}
export interface FeedPlan extends FeedSettings {
  stage: string | null;
  stage_id: string | null;
  doses: PlannedDose[];
  /** Why no batch can run, or null. */
  problem: string | null;
}
/** What the editor changes and feed_save takes. */
export interface FeedDraft extends FeedSettings {
  dosers: Record<string, { flow_ml_min: number }>;
  /** The room's dosing order from before each recipe had its own: a recipe without one takes it. */
  order: number[];
  recipes: FeedRecipe[];
  /** The id of the recipe in use. */
  stage: string | null;
}
export interface FeedDocument extends FeedDraft {
  schema_version: 1;
  room_id: string;
  revision: number;
  /** The room's doser switches from Rooms & hardware, by doser number. */
  mapped: Record<string, string>;
  plan: FeedPlan;
  max_dosers: number;
  max_recipes: number;
  error: string | null;
  /** feed_mix only: when the room's Mix a Batch Now button was pressed. */
  requested?: string | null;
}

/** The room's reservoir and dosers in Rooms & hardware (room.py RESERVOIR_KEYS). */
export const MAX_DOSERS = 6;
export const DOSER_KEYS = Array.from({ length: MAX_DOSERS }, (_, i) => `doser_${i + 1}_switch`);
export const BATCH_SWITCH_KEYS = ["fresh_water_switch", "recirc_switch", ...DOSER_KEYS];
export const RESERVOIR_KEYS = ["reservoir_distance_sensor", ...BATCH_SWITCH_KEYS];
export const DEFAULT_FLOW = 600;
export const MAX_ML_PER_L = 60;
export const NAME_LEN = 40;
/** field -> [label, unit, lowest, highest, whole number], as feed.py SETTINGS checks them. */
export const SETTINGS: Record<keyof FeedSettings, [string, string, number, number, boolean]> = {
  fill_s: ["Fresh-water fill", "s", 10, 7200, true],
  batch_l: ["Fill litres", "L", 1, 5000, false],
  full_mm: ["Distance when full", "mm", 0, 10000, false],
  empty_mm: ["Distance when empty", "mm", 0, 10000, false],
  min_pct: ["Minimum level", "%", 0, 50, false],
  pause_s: ["Pause between dosers", "s", 0, 600, true],
  mix_s: ["Recirculate after the last dose", "s", 0, 7200, true],
};
/** An integration older than the reservoir's level sends none of these: they start as feed.py's. */
const SETTING_DEFAULTS: Partial<FeedSettings> = { full_mm: 0, empty_mm: 0, min_pct: 5, mix_s: 10 };

/** How full the reservoir is, %, as the controller works it out (controller.py level_pct): 100 at
 * the distance when full, 0 at the distance when empty, clamped between. null without a reading or
 * without both distances in the right order. */
export function levelPct(mm: number | null, fullMm: number, emptyMm: number): number | null {
  if (mm === null || !Number.isFinite(mm) || !(fullMm > 0 && fullMm < emptyMm)) return null;
  const clamped = Math.min(Math.max(mm, fullMm), emptyMm);
  return 100 - ((clamped - fullMm) / (emptyMm - fullMm)) * 100;
}
/** The nutrient names the recipe editor offers; anything else can be typed. */
export const NUTRIENT_LINES: Record<string, string[]> = {
  Athena: ["Core", "Grow", "Bloom", "Fade", "Balance", "Cleanse"],
  "Front Row": ["Part A", "Part B", "Bloom", "PhosZyme", "Power Si"],
};
export const STAGE_NAMES = ["Vege", "Flower", "Bloom", "Fade"];

export const draftOf = (doc: FeedDocument): FeedDraft =>
  structuredClone({
    fill_s: doc.fill_s,
    batch_l: doc.batch_l,
    full_mm: doc.full_mm ?? SETTING_DEFAULTS.full_mm!,
    empty_mm: doc.empty_mm ?? SETTING_DEFAULTS.empty_mm!,
    min_pct: doc.min_pct ?? SETTING_DEFAULTS.min_pct!,
    pause_s: doc.pause_s,
    mix_s: doc.mix_s ?? SETTING_DEFAULTS.mix_s!,
    dosers: doc.dosers,
    order: doc.order,
    // An integration from before each recipe had its own order sends the room's.
    recipes: doc.recipes.map((recipe) => ({ ...recipe, order: recipe.order ?? doc.order ?? [] })),
    stage: doc.stage,
  });

export const mappedNumbers = (mapped: Record<string, string>) =>
  Object.keys(mapped)
    .map(Number)
    .filter((n) => Number.isInteger(n))
    .sort((a, b) => a - b);

/** The room's dosers in a recipe's order: those in `order` first, then any other by number. */
export function doserOrder(order: number[], mapped: number[]): number[] {
  const first = order.filter((n) => mapped.includes(n));
  return [...first, ...mapped.filter((n) => !first.includes(n)).sort((a, b) => a - b)];
}

/** `order` with the item at `from` moved to `to`. */
export function moveTo<T>(order: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || from >= order.length) return order;
  const next = [...order];
  const [item] = next.splice(from, 1);
  next.splice(Math.max(0, Math.min(to, next.length)), 0, item);
  return next;
}

export const flowOf = (draft: Pick<FeedDraft, "dosers">, doser: number) =>
  draft.dosers[String(doser)]?.flow_ml_min ?? DEFAULT_FLOW;

const round1 = (value: number) => Math.round(value * 10) / 10;

/** One part of a recipe in this fill, mL: its strength times the fill's litres. */
export const partMl = (draft: Pick<FeedDraft, "batch_l">, recipe: FeedRecipe) =>
  recipe.strength * draft.batch_l;

/** One doser's dose in a recipe at this batch size: mL, to the whole mL as feed.py doses it, and
 * seconds at the doser's flow. */
export function doseOf(draft: FeedDraft, recipe: FeedRecipe, doser: number) {
  const parts = recipe.doses[String(doser)]?.parts ?? 0;
  const ml = Math.round(parts * recipe.strength * draft.batch_l);
  const flow = flowOf(draft, doser);
  return { ml, seconds: flow > 0 ? round1((ml / flow) * 60) : 0 };
}

/** feed.py plan(): what the next batch would dose, in its recipe's order, or why none can run. */
export function planOf(draft: FeedDraft, mapped: number[]): FeedPlan {
  const stage = draft.recipes.find((r) => r.id === draft.stage) ?? null;
  const doses: PlannedDose[] = [];
  let problem: string | null = null;
  if (!mapped.length) problem = "No doser is mapped in Settings → Rooms & hardware.";
  else if (!stage) problem = "No feed stage is chosen.";
  else {
    const wanted = Object.entries(stage.doses)
      .filter(([, dose]) => dose.parts > 0)
      .map(([n]) => Number(n));
    const missing = wanted.filter((n) => !mapped.includes(n)).sort((a, b) => a - b);
    if (missing.length)
      problem = `${stage.name} uses doser ${missing[0]}, which has no switch in Settings → Rooms & hardware.`;
    else if (!wanted.length)
      problem = `${stage.name} doses nothing: give its nutrients some parts.`;
    for (const n of doserOrder(stage.order ?? draft.order, mapped))
      if (wanted.includes(n))
        doses.push({ doser: n, label: stage.doses[String(n)].label, ...doseOf(draft, stage, n) });
    if (!problem && !doses.some((d) => d.ml > 0))
      problem = `${stage.name}'s strength is 0: nothing would be dosed.`;
  }
  return {
    stage: stage?.name ?? null,
    stage_id: stage?.id ?? null,
    ...Object.fromEntries(Object.keys(SETTINGS).map((k) => [k, draft[k as keyof FeedSettings]])),
    doses,
    problem,
  } as FeedPlan;
}

/** A recipe's total mL per litre. */
export const perLitre = (recipe: FeedRecipe) =>
  recipe.strength * Object.values(recipe.doses).reduce((sum, dose) => sum + (dose.parts || 0), 0);

const inRange = (value: number, low: number, high: number, whole = false) =>
  Number.isFinite(value) && value >= low && value <= high && (!whole || Number.isInteger(value));

/** The checks feed.py clean() makes, so the editor can say so before saving. */
export function draftErrors(draft: FeedDraft, maxRecipes = 12): string[] {
  const errors: string[] = [];
  for (const [key, [label, unit, low, high, whole]] of Object.entries(SETTINGS))
    if (!inRange(draft[key as keyof FeedSettings], low, high, whole))
      errors.push(
        `${label} must be ${whole ? "a whole number" : "a number"} from ${low} to ${high} ${unit}.`,
      );
  if (draft.empty_mm > 0 && draft.full_mm >= draft.empty_mm)
    errors.push(
      "The distance when full must be less than the distance when empty: the level sensor is above the water, so it reads further as the reservoir empties.",
    );
  for (const [n, doser] of Object.entries(draft.dosers))
    if (!inRange(doser.flow_ml_min, 1, 10000))
      errors.push(`Doser ${n}'s flow must be from 1 to 10000 mL/min.`);
  if (draft.recipes.length > maxRecipes) errors.push(`Up to ${maxRecipes} feed recipes.`);
  const names = new Set<string>();
  for (const recipe of draft.recipes) {
    const name = recipe.name.trim().replace(/\s+/g, " ");
    const label = name || "A feed recipe";
    if (!name) errors.push("Each feed recipe needs a name.");
    else if (name.length > NAME_LEN)
      errors.push(`${name.slice(0, 20)}…: a name is at most ${NAME_LEN} characters.`);
    else if (names.has(name.toLowerCase())) errors.push(`Two feed recipes are called ${name}.`);
    names.add(name.toLowerCase());
    if (!inRange(recipe.strength, 0, 20))
      errors.push(`${label}: the strength must be from 0 to 20 mL per litre per part.`);
    for (const [n, dose] of Object.entries(recipe.doses)) {
      if (!inRange(dose.parts, 0, 100))
        errors.push(`${label}: doser ${n}'s parts must be from 0 to 100.`);
      else if (dose.parts > 0 && !dose.label.trim())
        errors.push(`${label}: doser ${n} has parts but no nutrient.`);
      if (dose.label.trim().length > NAME_LEN)
        errors.push(`${label}: doser ${n}'s nutrient is longer than ${NAME_LEN} characters.`);
    }
    const total = perLitre(recipe);
    if (Number.isFinite(total) && total > MAX_ML_PER_L)
      errors.push(
        `${label} comes to ${total.toFixed(1)} mL per litre; more than ${MAX_ML_PER_L} is refused as a likely typo in its strength or parts.`,
      );
  }
  return errors;
}

/** A new recipe: no parts, with the nutrients the last recipe had on each doser, since the bottles on
 * the dosers usually stay where they are between stages. */
export function newRecipe(draft: FeedDraft, mapped: number[], name = ""): FeedRecipe {
  const last = draft.recipes[draft.recipes.length - 1];
  return {
    // Its own id at once, so it can be the stage in use in the same save (feed.py keeps a valid id).
    id: createUuid().replaceAll("-", "").slice(0, 12),
    name,
    strength: last?.strength ?? 1,
    doses: Object.fromEntries(
      mapped.map((n) => [String(n), { label: last?.doses[String(n)]?.label ?? "", parts: 0 }]),
    ),
    order: [...(last?.order ?? draft.order)],
  };
}

/** What feed_save takes: names and nutrients as feed.py keeps them. */
export const documentOf = (draft: FeedDraft) => ({
  ...draft,
  recipes: draft.recipes.map((recipe) => ({
    ...recipe,
    name: recipe.name.trim().replace(/\s+/g, " "),
    doses: Object.fromEntries(
      Object.entries(recipe.doses).map(([n, dose]) => [
        n,
        { label: dose.label.trim().replace(/\s+/g, " "), parts: dose.parts },
      ]),
    ),
  })),
});

/** "10 min", "1 min 30 s", "45 s". */
export function duration(seconds: number): string {
  if (!Number.isFinite(seconds)) return "—";
  const whole = Math.round(seconds);
  if (whole < 60) return `${Number.isInteger(seconds) ? seconds : seconds.toFixed(1)} s`;
  const minutes = Math.floor(whole / 60),
    rest = whole % 60;
  return rest ? `${minutes} min ${rest} s` : `${minutes} min`;
}
