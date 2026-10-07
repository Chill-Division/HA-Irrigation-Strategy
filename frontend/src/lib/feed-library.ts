import { createUuid } from "./uuid";
import {
  FEED_EC,
  MAX_ML_PER_L,
  NAME_LEN,
  doserOrder,
  type FeedDraft,
  type FeedRecipe,
} from "./feed";

/** A feed recipe by nutrient rather than by doser, as a nutrient chart gives it: a template, or a
 * recipe file from another room. Adding one puts each nutrient on the doser that already carries it
 * (placeRecipe). */
export interface PortableRecipe {
  name: string;
  /** mL per litre per part. */
  strength: number;
  /** One part in mL whatever the fill, when the recipe is set that way: the strength is then worked
   * out from the room's fill litres. */
  partMl?: number;
  /** In dosing order. */
  doses: { nutrient: string; parts: number }[];
  /** What it mixes to, mS/cm, when its file gives it. */
  ec?: number;
}
export interface RecipeTemplate extends PortableRecipe {
  id: string;
  /** Its group in the list, e.g. "Athena (Chill Division modified)". */
  group: string;
  /** Its name within the group, e.g. "Bloom". */
  label: string;
}

const ATHENA = "Athena (Chill Division modified)";
// Athena's lines as Chill Division runs them, a little off Athena's own chart: 240 mL a part whatever
// the fill (1.655 mL per litre in their 145 L), Balance first.
const athena = (label: string, doses: [string, number][]): RecipeTemplate => ({
  id: `athena-cd-${label.toLowerCase()}`,
  group: ATHENA,
  label,
  name: `Athena ${label} (Chill Division modified)`,
  strength: 240 / 145,
  partMl: 240,
  doses: doses.map(([nutrient, parts]) => ({ nutrient, parts })),
});

// Front Row Ag's 3-2-2 stock concentrate feed chart, high strength (231226_FRA_Feed_Chart_322_Metric
// V3): mL of each stock concentrate per litre (Part A 180 g/L, Part B and Bloom 120 g/L, Front Row
// Si 53 mL/L, PhosZyme 42 g/L), so one part is 1 mL per litre. Front Row Si, the pH up, goes in first
// and in every stage. Triologic (0.26 mL/L, the low end: the chart has it once a week and a recipe
// doses every refill) or BioFlo (8 mL/L) go in last, undiluted from their own bottles.
const FRONT_ROW = "Front Row 3-2-2, high strength";
const STAGES: [string, string, number, number, number | null, number][] = [
  // stage, its weeks, Part A, Part B, Bloom, Front Row Si
  ["Veg", "Veg", 9.0, 9.0, null, 1.3],
  ["Stretch", "flower weeks 1-2", 7.5, 7.5, 5.3, 1.3],
  ["Stack", "flower weeks 3-5", 6.3, 6.3, 6.3, 1.3],
  ["Swell", "flower weeks 6-8/9", 4.8, 4.9, 8.6, 1.9],
  ["Ripen", "final 1-2 weeks", 2.9, 4.7, 6.9, 2.5],
];
const ADDITIVES: [string, [string, number] | null][] = [
  ["", null],
  [" + Triologic", ["Triologic", 0.26]],
  [" + BioFlo", ["BioFlo", 8]],
];
const frontRow = ADDITIVES.flatMap(([suffix, additive]) =>
  STAGES.map(([stage, weeks, a, b, bloom, si]): RecipeTemplate => {
    const doses: [string, number | null][] = [
      ["Front Row Si", si],
      ["Part A", a],
      ["Part B", b],
      ["Bloom", bloom],
      ["PhosZyme", 2.5],
      ...(additive ? [additive] : []),
    ];
    return {
      id: `front-row-322-high-${stage.toLowerCase()}${suffix ? `-${additive![0].toLowerCase()}` : ""}`,
      group: `${FRONT_ROW}${suffix}`,
      label: stage === "Veg" ? "Veg" : `${stage} (${weeks})`,
      name: `Front Row 3-2-2 High ${stage}${suffix}`,
      strength: 1,
      doses: doses.flatMap(([nutrient, parts]) => (parts === null ? [] : [{ nutrient, parts }])),
    };
  }),
);

export const TEMPLATES: RecipeTemplate[] = [
  athena("Grow", [
    ["Balance", 0.7],
    ["Grow", 5],
    ["Core", 3],
    ["Cleanse", 0.5],
  ]),
  athena("Bloom", [
    ["Balance", 1.05],
    ["Bloom", 5],
    ["Core", 3],
    ["Cleanse", 0.5],
  ]),
  athena("Fade", [
    ["Balance", 1.1],
    ["Bloom", 5],
    ["Fade", 3],
    ["Cleanse", 0.5],
  ]),
  ...frontRow,
];

/** The templates by group, in the order the list shows them. */
export const TEMPLATE_GROUPS = [...new Set(TEMPLATES.map((t) => t.group))].map((group) => ({
  group,
  templates: TEMPLATES.filter((t) => t.group === group),
}));

// A nutrient's name as two recipes might spell it: case and spaces aside, and Front Row's silica by
// any of its names.
const ALIASES: Record<string, string> = {
  "power si": "front row si",
  si: "front row si",
  "fr si": "front row si",
};
const key = (name: string) => {
  const plain = name.trim().replace(/\s+/g, " ").toLowerCase();
  return ALIASES[plain] ?? plain;
};
const empty = (label: string) => !label.trim() || key(label) === "empty";

/** `name`, or with a number after it when a recipe here is already called that, within NAME_LEN. */
export function uniqueName(name: string, recipes: FeedRecipe[]): string {
  const taken = new Set(recipes.map((r) => r.name.trim().toLowerCase()));
  const base = name.trim().replace(/\s+/g, " ").slice(0, NAME_LEN);
  if (!taken.has(base.toLowerCase())) return base;
  for (let n = 2; ; n++) {
    const suffix = ` ${n}`;
    const next = `${base.slice(0, NAME_LEN - suffix.length).trimEnd()}${suffix}`;
    if (!taken.has(next.toLowerCase())) return next;
  }
}

/** A portable recipe put on this room's dosers. Each nutrient goes on the doser the room's recipes
 * already give it (the one most of them do); one no recipe names goes on a free doser, one no recipe
 * gives a nutrient first; with none free, it is left out. Every other doser keeps its nutrient's name
 * at 0 parts, as the room's recipes list them. */
export function placeRecipe(source: PortableRecipe, draft: FeedDraft, mapped: number[]) {
  const counts = new Map<number, Map<string, number>>();
  for (const recipe of draft.recipes)
    for (const [n, dose] of Object.entries(recipe.doses)) {
      const doser = Number(n);
      if (!mapped.includes(doser) || !dose.label.trim()) continue;
      const labels = counts.get(doser) ?? new Map<string, number>();
      labels.set(dose.label.trim(), (labels.get(dose.label.trim()) ?? 0) + 1);
      counts.set(doser, labels);
    }
  // What each doser carries in the room's recipes, the name most of them give it first.
  const carries = (doser: number) =>
    [...(counts.get(doser) ?? new Map<string, number>())].sort((a, b) => b[1] - a[1]);
  const usual = (nutrient: string) => {
    let best: { doser: number; times: number } | null = null;
    for (const doser of mapped)
      for (const [label, times] of carries(doser))
        if (key(label) === key(nutrient) && (!best || times > best.times)) best = { doser, times };
    return best?.doser ?? null;
  };
  const taken = new Map<number, { nutrient: string; parts: number }>();
  const placed: { nutrient: string; doser: number; matched: boolean }[] = [];
  const waiting: { nutrient: string; parts: number }[] = [];
  for (const dose of source.doses) {
    const doser = usual(dose.nutrient);
    if (doser !== null && !taken.has(doser)) {
      taken.set(doser, dose);
      placed.push({ nutrient: dose.nutrient, doser, matched: true });
    } else waiting.push(dose);
  }
  // A free doser: first one no recipe gives a nutrient (or calls Empty), then any other.
  const free = mapped
    .filter((doser) => !taken.has(doser))
    .sort(
      (a, b) =>
        Number(!carries(a).every(([label]) => empty(label))) -
          Number(!carries(b).every(([label]) => empty(label))) || a - b,
    );
  const unplaced: string[] = [];
  for (const dose of waiting) {
    const doser = free.shift();
    if (doser === undefined) {
      unplaced.push(dose.nutrient);
      continue;
    }
    taken.set(doser, dose);
    placed.push({ nutrient: dose.nutrient, doser, matched: false });
  }
  const ordered = source.doses.flatMap((dose) => {
    const at = [...taken].find(([, given]) => given === dose);
    return at ? [at[0]] : [];
  });
  const recipe: FeedRecipe = {
    id: createUuid().replaceAll("-", "").slice(0, 12),
    name: uniqueName(source.name, draft.recipes),
    strength: source.partMl && draft.batch_l > 0 ? source.partMl / draft.batch_l : source.strength,
    doses: Object.fromEntries(
      mapped.map((doser) => {
        const given = taken.get(doser);
        return [
          String(doser),
          given
            ? { label: given.nutrient, parts: given.parts }
            : { label: carries(doser)[0]?.[0] ?? "", parts: 0 },
        ];
      }),
    ),
    order: doserOrder(ordered, mapped),
    ec: source.ec ?? null,
  };
  return { recipe, placed, unplaced };
}

/** What adding a recipe did, in a sentence or two: where any nutrient no recipe named went, and any
 * that found no doser. */
export function placedNote(
  name: string,
  placed: { nutrient: string; doser: number; matched: boolean }[],
  unplaced: string[],
): string {
  const guessed = placed.filter((p) => !p.matched);
  const list = (items: string[]) =>
    items.length < 2 ? items.join("") : `${items.slice(0, -1).join(", ")} and ${items.at(-1)}`;
  return [
    `Added ${name}.`,
    guessed.length
      ? `No recipe here names ${list(guessed.map((p) => p.nutrient))}: ${guessed.length > 1 ? "they went" : "it went"} on ${list(guessed.map((p) => `doser ${p.doser}`))}. Check those bottles before saving.`
      : unplaced.length
        ? ""
        : "Each nutrient went on the doser that carries it.",
    unplaced.length
      ? `${list(unplaced)} found no free doser and ${unplaced.length > 1 ? "were" : "was"} left out.`
      : "",
  ]
    .filter(Boolean)
    .join(" ");
}

export const FILE_FORMAT = "crop-steering-feed-recipe";
const MAX_FILE_BYTES = 100_000;

/** A recipe file: the recipe by nutrient, in its dosing order, nutrients at 0 parts left out. */
export function exportRecipe(recipe: FeedRecipe): string {
  const dosers = doserOrder(
    recipe.order,
    Object.keys(recipe.doses)
      .map(Number)
      .sort((a, b) => a - b),
  );
  return JSON.stringify(
    {
      format: FILE_FORMAT,
      version: 1,
      recipe: {
        name: recipe.name,
        strength: recipe.strength,
        ...(recipe.ec != null ? { ec: recipe.ec } : {}),
        doses: dosers.flatMap((doser) => {
          const dose = recipe.doses[String(doser)];
          return dose && dose.parts > 0 && dose.label.trim()
            ? [{ nutrient: dose.label.trim(), parts: dose.parts }]
            : [];
        }),
      },
    },
    null,
    2,
  );
}
/** A recipe file's name: the recipe's, as a file name. */
export const exportName = (recipe: FeedRecipe) =>
  `feed-recipe-${
    recipe.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "recipe"
  }.json`;

/** A recipe file's recipe, checked as feed_save would check it, or why it can't be read. */
export function importRecipe(raw: string): PortableRecipe {
  if (new Blob([raw]).size > MAX_FILE_BYTES)
    throw new Error("That file is too large for a recipe.");
  let file: unknown;
  try {
    file = JSON.parse(raw);
  } catch {
    throw new Error("That file isn't a feed recipe: it isn't JSON.");
  }
  const f = file as { format?: unknown; version?: unknown; recipe?: unknown };
  if (f?.format !== FILE_FORMAT || f.version !== 1 || typeof f.recipe !== "object" || !f.recipe)
    throw new Error("That file isn't a Crop Steering feed recipe.");
  const r = f.recipe as { name?: unknown; strength?: unknown; doses?: unknown; ec?: unknown };
  const name = typeof r.name === "string" ? r.name.trim().replace(/\s+/g, " ") : "";
  if (!name || name.length > NAME_LEN)
    throw new Error(`The recipe needs a name of up to ${NAME_LEN} characters.`);
  const strength = Number(r.strength);
  if (typeof r.strength !== "number" || !(strength >= 0 && strength <= 20))
    throw new Error(`${name}: the strength must be from 0 to 20 mL per litre per part.`);
  if (!Array.isArray(r.doses) || !r.doses.length || r.doses.length > 6)
    throw new Error(`${name}: it needs one to six nutrients.`);
  const seen = new Set<string>();
  const doses = r.doses.map((raw: unknown) => {
    const d = raw as { nutrient?: unknown; parts?: unknown };
    const nutrient = typeof d?.nutrient === "string" ? d.nutrient.trim().replace(/\s+/g, " ") : "";
    if (!nutrient || nutrient.length > NAME_LEN)
      throw new Error(`${name}: each nutrient needs a name of up to ${NAME_LEN} characters.`);
    if (seen.has(key(nutrient))) throw new Error(`${name}: ${nutrient} is in it twice.`);
    seen.add(key(nutrient));
    if (typeof d.parts !== "number" || !(d.parts >= 0 && d.parts <= 100))
      throw new Error(`${name}: ${nutrient}'s parts must be from 0 to 100.`);
    return { nutrient, parts: d.parts };
  });
  const perLitre = strength * doses.reduce((sum, d) => sum + d.parts, 0);
  if (perLitre > MAX_ML_PER_L)
    throw new Error(
      `${name} comes to ${perLitre.toFixed(1)} mL per litre; more than ${MAX_ML_PER_L} is refused as a likely typo.`,
    );
  // A file from before recipes gave their feed EC has none.
  if (r.ec === undefined || r.ec === null) return { name, strength, doses };
  if (typeof r.ec !== "number" || !(r.ec >= FEED_EC[0] && r.ec <= FEED_EC[1]))
    throw new Error(`${name}: its feed EC must be from ${FEED_EC[0]} to ${FEED_EC[1]} mS/cm.`);
  return { name, strength, doses, ec: r.ec };
}
