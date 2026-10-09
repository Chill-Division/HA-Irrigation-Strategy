import { describe, expect, it } from "vitest";
import { draftErrors, partMl, type FeedDraft, type FeedRecipe } from "./feed";
import { sampleFeed } from "./feed-demo";
import {
  TEMPLATES,
  TEMPLATE_GROUPS,
  exportRecipe,
  importRecipe,
  placeRecipe,
  placedNote,
  uniqueName,
} from "./feed-library";

const DOSERS = [1, 2, 3, 4, 5, 6];
const recipe = (name: string, doses: Record<string, [string, number]>): FeedRecipe => ({
  id: name.toLowerCase(),
  name,
  strength: 1.655,
  doses: Object.fromEntries(
    Object.entries(doses).map(([n, [label, parts]]) => [n, { label, parts }]),
  ),
  order: [],
});
/** A room labelled as the owner's GR2: Grow on doser 1 in Vege (Empty otherwise), Cleanse on 2,
 * Balance on 3, Fade on 4, Core on 5 and Bloom on 6. */
const gr2 = (): FeedDraft => ({
  ...sampleFeed(),
  recipes: [
    recipe("Bloom", {
      "1": ["Empty", 0],
      "2": ["Cleanse", 0.5],
      "3": ["Balance", 1.05],
      "4": ["Fade", 0],
      "5": ["Core", 3],
      "6": ["Bloom", 5],
    }),
    recipe("Vege", {
      "1": ["Grow", 5],
      "2": ["Cleanse", 0.5],
      "3": ["Balance", 0.7],
      "4": ["Fade", 0],
      "5": ["Core", 3],
      "6": ["Bloom", 0],
    }),
    recipe("Fade", {
      "1": ["Empty", 0],
      "2": ["Cleanse", 0.5],
      "3": ["Balance", 1.1],
      "4": ["Fade", 3],
      "5": ["Core", 0],
      "6": ["Bloom", 5],
    }),
  ],
});
const byName = (name: string) => TEMPLATES.find((t) => t.name === name)!;
const parts = (r: FeedRecipe) =>
  Object.fromEntries(
    Object.entries(r.doses)
      .filter(([, d]) => d.parts > 0)
      .map(([n, d]) => [n, `${d.label} ${d.parts}`]),
  );

describe("feed recipe templates", () => {
  it("are Chill Division's Athena recipes, and Front Row's 3-2-2 chart at high strength", () => {
    expect(TEMPLATE_GROUPS.map((g) => [g.group, g.templates.length])).toEqual([
      ["Athena (Chill Division modified)", 3],
      ["Front Row 3-2-2, high strength", 5],
      ["Front Row 3-2-2, high strength + Triologic", 5],
      ["Front Row 3-2-2, high strength + BioFlo", 5],
    ]);
    expect(byName("Athena Bloom (Chill Division modified)")).toMatchObject({
      partMl: 240,
      doses: [
        { nutrient: "Balance", parts: 1.05 },
        { nutrient: "Bloom", parts: 5 },
        { nutrient: "Core", parts: 3 },
        { nutrient: "Cleanse", parts: 0.5 },
      ],
    });
    // One part is 1 mL of stock concentrate per litre: the chart's own numbers. Front Row Si, the pH
    // up, first in every stage; Veg has no Bloom.
    expect(byName("Front Row 3-2-2 High Swell").doses).toEqual([
      { nutrient: "Front Row Si", parts: 1.9 },
      { nutrient: "Part A", parts: 4.8 },
      { nutrient: "Part B", parts: 4.9 },
      { nutrient: "Bloom", parts: 8.6 },
      { nutrient: "PhosZyme", parts: 2.5 },
    ]);
    expect(byName("Front Row 3-2-2 High Veg").doses.map((d) => d.nutrient)).not.toContain("Bloom");
    expect(byName("Front Row 3-2-2 High Ripen + Triologic").doses.at(-1)).toEqual({
      nutrient: "Triologic",
      parts: 0.26,
    });
    expect(byName("Front Row 3-2-2 High Stack + BioFlo").doses.at(-1)).toEqual({
      nutrient: "BioFlo",
      parts: 8,
    });
  });

  it("each saves as feed_save would take it, on six dosers", () => {
    for (const template of TEMPLATES) {
      const draft = sampleFeed();
      const { recipe, unplaced } = placeRecipe(template, draft, DOSERS);
      expect(unplaced, template.name).toEqual([]);
      expect(draftErrors({ ...draft, recipes: [...draft.recipes, recipe] }), template.name).toEqual(
        [],
      );
    }
  });
});

describe("putting a recipe on the room's dosers", () => {
  it("makes an Athena part 240 mL, whatever the fill", () => {
    for (const batch_l of [145, 150, 300]) {
      const draft = { ...gr2(), batch_l };
      const { recipe } = placeRecipe(
        byName("Athena Grow (Chill Division modified)"),
        draft,
        DOSERS,
      );
      expect(partMl(draft, recipe)).toBeCloseTo(240, 9);
    }
    // Front Row's chart is per litre: 1 mL a part per litre, whatever the fill.
    const { recipe } = placeRecipe(byName("Front Row 3-2-2 High Veg"), gr2(), DOSERS);
    expect(recipe.strength).toBe(1);
  });

  it("puts each nutrient on the doser the room's recipes give it, in the template's order", () => {
    const { recipe, placed, unplaced } = placeRecipe(
      byName("Athena Bloom (Chill Division modified)"),
      gr2(),
      DOSERS,
    );
    expect(parts(recipe)).toEqual({
      "2": "Cleanse 0.5",
      "3": "Balance 1.05",
      "5": "Core 3",
      "6": "Bloom 5",
    });
    expect(recipe.order).toEqual([3, 6, 5, 2, 1, 4]);
    // The others keep the nutrient most recipes give them, at 0 parts.
    expect(recipe.doses["1"]).toEqual({ label: "Empty", parts: 0 });
    expect(recipe.doses["4"]).toEqual({ label: "Fade", parts: 0 });
    expect(placed.every((p) => p.matched) && unplaced.length === 0).toBe(true);
    expect(placedNote(recipe.name, placed, unplaced)).toBe(
      "Added Athena Bloom (Chill Division modified). Each nutrient went on the doser that carries it.",
    );
  });

  it("puts a nutrient no recipe names on a free doser, one without a nutrient first", () => {
    const draft = gr2();
    draft.recipes = draft.recipes.map((r) => ({
      ...r,
      doses: { ...r.doses, "4": { label: "", parts: 0 } },
    }));
    const { recipe, placed } = placeRecipe(byName("Front Row 3-2-2 High Stack"), draft, DOSERS);
    // Bloom is on 6 here; Front Row Si takes doser 4, which no recipe gives a nutrient, then 1
    // (only ever Grow or Empty), 2, 3 by number.
    expect(placed.map((p) => [p.nutrient, p.doser, p.matched])).toEqual([
      ["Bloom", 6, true],
      ["Front Row Si", 4, false],
      ["Part A", 1, false],
      ["Part B", 2, false],
      ["PhosZyme", 3, false],
    ]);
    expect(recipe.order.slice(0, 5)).toEqual([4, 1, 2, 6, 3]);
    expect(placedNote(recipe.name, placed, [])).toBe(
      "Added Front Row 3-2-2 High Stack. No recipe here names Front Row Si, Part A, Part B and PhosZyme: they went on doser 4, doser 1, doser 2 and doser 3. Check those bottles before saving.",
    );
  });

  it("knows Front Row's silica by its other names, and leaves out what finds no doser", () => {
    const draft = sampleFeed();
    draft.recipes[0].doses["4"] = { label: "Power Si", parts: 0 };
    const four = placeRecipe(byName("Front Row 3-2-2 High Stretch + BioFlo"), draft, [1, 2, 3, 4]);
    expect(four.placed.find((p) => p.nutrient === "Front Row Si")).toEqual({
      nutrient: "Front Row Si",
      doser: 4,
      matched: true,
    });
    // Six nutrients, four dosers: the last two find none.
    expect(four.unplaced).toEqual(["PhosZyme", "BioFlo"]);
    expect(placedNote("X", four.placed, four.unplaced)).toMatch(
      /PhosZyme and BioFlo found no free doser and were left out\.$/,
    );
  });

  it("names it apart from a recipe already called that, within 40 characters", () => {
    const draft = gr2();
    const first = placeRecipe(byName("Front Row 3-2-2 High Stretch + Triologic"), draft, DOSERS);
    expect(first.recipe.name).toBe("Front Row 3-2-2 High Stretch + Triologic");
    draft.recipes.push(first.recipe);
    const second = placeRecipe(byName("Front Row 3-2-2 High Stretch + Triologic"), draft, DOSERS);
    expect(second.recipe.name).toBe("Front Row 3-2-2 High Stretch + Triolog 2");
    expect(second.recipe.name.length).toBe(40);
    expect(uniqueName("bloom", gr2().recipes)).toBe("bloom 2");
  });
});

describe("recipe files", () => {
  it("carry a recipe by nutrient, in its dosing order, to another room's dosers", () => {
    const vege = gr2().recipes[1];
    vege.order = [3, 1, 5, 2];
    const file = exportRecipe(vege);
    expect(JSON.parse(file)).toEqual({
      format: "crop-steering-feed-recipe",
      version: 1,
      recipe: {
        name: "Vege",
        strength: 1.655,
        doses: [
          { nutrient: "Balance", parts: 0.7 },
          { nutrient: "Grow", parts: 5 },
          { nutrient: "Core", parts: 3 },
          { nutrient: "Cleanse", parts: 0.5 },
        ],
      },
    });
    // Back into the same room: the same doses on the same dosers, under a name of its own.
    const { recipe } = placeRecipe(importRecipe(file), gr2(), DOSERS);
    expect(parts(recipe)).toEqual(parts(vege));
    expect(recipe.name).toBe("Vege 2");
    // No feed EC given, none carried: a file from before recipes had one reads the same.
    expect(recipe.ec).toBeNull();
  });

  it("carry the feed EC a recipe mixes to, when it gives one", () => {
    const vege = { ...gr2().recipes[1], ec: 1.6 };
    const file = exportRecipe(vege);
    expect(JSON.parse(file).recipe.ec).toBe(1.6);
    const { recipe } = placeRecipe(importRecipe(file), gr2(), DOSERS);
    expect(recipe.ec).toBe(1.6);
    expect(draftErrors({ ...gr2(), recipes: [...gr2().recipes, recipe] })).toEqual([]);
  });

  it.each([
    ["not json", "isn't JSON"],
    [
      JSON.stringify({ format: "crop-steering-plan", version: 1, recipe: {} }),
      "isn't a PHASE Steering",
    ],
    [
      JSON.stringify({
        format: "crop-steering-feed-recipe",
        version: 1,
        recipe: { name: "X", strength: 25, doses: [{ nutrient: "A", parts: 1 }] },
      }),
      "strength must be from 0 to 20",
    ],
    [
      JSON.stringify({
        format: "crop-steering-feed-recipe",
        version: 1,
        recipe: { name: "X", strength: 1, doses: [{ nutrient: "A", parts: 61 }] },
      }),
      "61.0 mL per litre",
    ],
    [
      JSON.stringify({
        format: "crop-steering-feed-recipe",
        version: 1,
        recipe: {
          name: "X",
          strength: 1,
          doses: [
            { nutrient: "Power Si", parts: 1 },
            { nutrient: "Front Row Si", parts: 1 },
          ],
        },
      }),
      "Front Row Si is in it twice",
    ],
    [
      JSON.stringify({
        format: "crop-steering-feed-recipe",
        version: 1,
        recipe: { name: "X", strength: 1, ec: 25, doses: [{ nutrient: "A", parts: 1 }] },
      }),
      "feed EC must be from 0.1 to 10 mS/cm",
    ],
  ])("refuses a file that isn't a recipe it can add: %s", (raw, why) => {
    expect(() => importRecipe(raw)).toThrow(why);
  });
});
