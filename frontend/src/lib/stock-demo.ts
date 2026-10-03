import type { OperatorAction } from "./operator-types";
import {
  draftErrors,
  onDoser,
  type StockDocument,
  type StockTank,
  type StockTankDraft,
} from "./stock";
import { mappedNumbers, planOf } from "./feed";
import { sampleFeed } from "./feed-demo";
import type { States } from "./types";

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value));
const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000).toISOString();

/** Sample stock for a demo room: Athena's bottles on its four dosers, as the demo's Flower uses them,
 * one getting low, so the colours have something to show. */
function sample(roomId: string): StockDocument {
  const tank = (
    id: string,
    name: string,
    doser: number,
    capacity: number,
    level: number,
    low: number,
  ): StockTank => ({
    id,
    name,
    capacity_l: capacity,
    level_l: level,
    doser,
    low_l: low,
    refilled_at: hoursAgo(24 * 9),
    updated_at: hoursAgo(20),
  });
  const tanks = [
    tank("core", "Core", 1, 20, 13.6, 4),
    tank("bloom", "Bloom", 2, 20, 12.9, 4),
    tank("balance", "Balance", 3, 10, 3.2, 2.5),
    tank("cleanse", "Cleanse", 4, 5, 3.9, 1),
  ];
  // What the demo's Flower doses from each, in each of the last three refills.
  const draw = { core: 450, bloom: 750, balance: 150, cleanse: 75 };
  return {
    schema_version: 1,
    room_id: roomId,
    revision: 1,
    tanks,
    history: [20, 44, 68].map((hours) => ({
      at: hoursAgo(hours),
      source: "reservoir",
      draw_ml: draw,
    })),
    dosers: {},
    reservoir_batch: hoursAgo(20),
    doses: draw,
    low: [],
    max_tanks: 12,
    error: null,
  };
}

/** The integration's stock services in memory (stock.py / stock_api.py), for demo mode. */
export class StockDemo {
  private docs = new Map<string, StockDocument>();
  constructor(private getStates: () => States) {}

  private doc(roomId: string) {
    const prefix = roomId.startsWith("room:") ? roomId.slice(5) : "";
    const descriptor = this.getStates()[`sensor.crop_steering_${prefix}engine_config`];
    if (!this.docs.has(roomId)) this.docs.set(roomId, sample(roomId));
    const doc = this.docs.get(roomId)!;
    // The room's Reservoir dosers, with what the demo's feed stage puts on each (stock_api dosers).
    const mapped: Record<string, string> = {};
    for (let n = 1; n <= 6; n++) {
      const entity = descriptor?.attributes[`doser_${n}_switch`];
      if (typeof entity === "string" && entity) mapped[String(n)] = entity;
    }
    const feed = sampleFeed();
    const nutrients = feed.recipes.find((r) => r.id === feed.stage)?.doses ?? {};
    doc.dosers = Object.fromEntries(
      Object.entries(mapped).map(([n, entity]) => [
        n,
        { switch: entity, nutrient: nutrients[n]?.label || null },
      ]),
    );
    this.plan = planOf(feed, mappedNumbers(mapped)).doses;
    doc.doses = this.doses(doc);
    return doc;
  }

  private plan: { doser: number; label: string; ml: number }[] = [];

  /** stock_api doses: what the stage in use gives from each tank's doser; nothing from a tank on
   * none. */
  private doses(doc: StockDocument) {
    const doses: Record<string, number> = Object.fromEntries(doc.tanks.map((t) => [t.id, 0]));
    for (const dose of this.plan) {
      const owner = onDoser(doc.tanks, dose.doser, dose.label);
      if (owner) doses[owner.id] = dose.ml;
    }
    return doses;
  }

  private finish(doc: StockDocument) {
    doc.revision++;
    doc.doses = this.doses(doc);
    doc.low = doc.tanks.filter((t) => t.level_l <= t.low_l).map((t) => t.id);
    return clone(doc);
  }

  call(action: OperatorAction, data: Record<string, unknown>): StockDocument {
    const doc = this.doc(String(data.room_id));
    if (action === "stock_get") {
      doc.low = doc.tanks.filter((t) => t.level_l <= t.low_l).map((t) => t.id);
      return clone(doc);
    }
    if (data.expected_revision !== doc.revision)
      throw new Error("Stock tanks changed elsewhere. Reload before saving.");
    const now = new Date().toISOString();
    if (action === "stock_save") {
      const drafts = data.tanks as StockTankDraft[];
      const errors = draftErrors(drafts, doc.max_tanks);
      if (errors.length) throw new Error(errors.join(" "));
      const known = new Map(doc.tanks.map((t) => [t.id, t]));
      const taken = new Set(drafts.flatMap((d) => (d.id && known.has(d.id) ? [d.id] : [])));
      doc.tanks = drafts.map((draft) => {
        const old = draft.id ? known.get(draft.id) : undefined;
        let id = old?.id;
        if (!id) {
          const base =
            draft.name
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, "_")
              .replace(/^_|_$/g, "") || "stock";
          id = base;
          for (let n = 2; taken.has(id); n++) id = `${base}_${n}`;
          taken.add(id);
        }
        return {
          id,
          name: draft.name.trim(),
          capacity_l: draft.capacity_l,
          level_l: Math.min(draft.level_l, draft.capacity_l),
          doser: draft.doser ?? null,
          low_l: Math.min(draft.low_l, draft.capacity_l),
          refilled_at: old?.refilled_at ?? null,
          updated_at: now,
        };
      });
    } else if (action === "stock_refill") {
      const tank = doc.tanks.find((t) => t.id === data.id);
      if (!tank) throw new Error(`There is no stock tank ${String(data.id)}.`);
      const level = data.level_l;
      if (level === undefined || level === null) {
        tank.level_l = tank.capacity_l;
        tank.refilled_at = now;
      } else if (typeof level === "number" && level >= 0 && level <= tank.capacity_l) {
        tank.level_l = level;
      } else throw new Error("The level must be between 0 L and the tank's capacity.");
      tank.updated_at = now;
    } else throw new Error("Unsupported demo action.");
    return this.finish(doc);
  }
}
