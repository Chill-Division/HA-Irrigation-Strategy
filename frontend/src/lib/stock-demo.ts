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

/** Sample stock for a demo room: one tank getting low, so the colours have something to show. */
function sample(roomId: string, fillEntity: string | null): StockDocument {
  const tank = (
    id: string,
    name: string,
    capacity: number,
    level: number,
    dose: number,
    low: number,
  ): StockTank => ({
    id,
    name,
    capacity_l: capacity,
    level_l: level,
    dose_ml: dose,
    dose_entity: null,
    doser: null,
    low_l: low,
    refilled_at: hoursAgo(24 * 9),
    updated_at: hoursAgo(20),
  });
  const tanks = [
    tank("part_a", "Part A", 20, 13.6, 400, 4),
    tank("part_b", "Part B", 20, 12.9, 400, 4),
    tank("cal_mag", "Cal-Mag", 10, 3.2, 250, 2.5),
    tank("ph_down", "pH down", 5, 3.9, 60, 1),
  ];
  const draw = Object.fromEntries(tanks.map((t) => [t.id, t.dose_ml]));
  return {
    schema_version: 1,
    room_id: roomId,
    revision: 1,
    tanks,
    last_batch: hoursAgo(20),
    history: [20, 44, 68].map((hours) => ({ at: hoursAgo(hours), source: "fill", draw_ml: draw })),
    fill_entity: fillEntity,
    dosers: {},
    reservoir_batch: null,
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
    if (!this.docs.has(roomId)) {
      const fill = descriptor?.attributes.tank_last_fill_sensor;
      this.docs.set(roomId, sample(roomId, typeof fill === "string" && fill ? fill : null));
    }
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

  /** stock_api doses: a tank on a doser takes what the stage in use gives from it; any other its
   * fixed dose. */
  private doses(doc: StockDocument) {
    const doses = Object.fromEntries(doc.tanks.map((t) => [t.id, t.doser ? 0 : t.dose_ml]));
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
          const base = draft.name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "stock";
          id = base;
          for (let n = 2; taken.has(id); n++) id = `${base}_${n}`;
          taken.add(id);
        }
        return {
          id,
          name: draft.name.trim(),
          capacity_l: draft.capacity_l,
          level_l: Math.min(draft.level_l, draft.capacity_l),
          dose_ml: draft.dose_ml,
          dose_entity: draft.doser ? null : draft.dose_entity || null,
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
    } else if (action === "stock_record_batch") {
      const draw: Record<string, number> = {};
      // A batch made by hand leaves the tanks on dosers alone: they lose what their doser gives.
      for (const tank of doc.tanks.filter((t) => !t.doser)) {
        const before = tank.level_l;
        tank.level_l = Math.round(Math.max(0, before - tank.dose_ml / 1000) * 1e4) / 1e4;
        draw[tank.id] = Math.round((before - tank.level_l) * 1e4) / 10;
      }
      doc.history = [{ at: now, source: "manual" as const, draw_ml: draw }, ...doc.history].slice(0, 30);
    } else throw new Error("Unsupported demo action.");
    return this.finish(doc);
  }
}
