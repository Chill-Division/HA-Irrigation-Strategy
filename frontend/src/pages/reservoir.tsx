import { useEffect, useId, useLayoutEffect, useRef, useState, type PointerEvent } from "react";
import {
  ArrowDown,
  ArrowUp,
  Beaker,
  Check,
  GripVertical,
  LoaderCircle,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Empty, Heading, number, ReviewDialog, type Page } from "@/components/dashboard";
import { Pill } from "@/components/mini-visuals";
import {
  documentOf,
  doseOf,
  draftErrors,
  draftOf,
  duration,
  flowOf,
  mappedNumbers,
  moveTo,
  newRecipe,
  NUTRIENT_LINES,
  perLitre,
  planOf,
  RESERVOIR_KEYS,
  roomOrder,
  SETTINGS,
  STAGE_NAMES,
  type FeedDocument,
  type FeedDraft,
  type FeedPlan,
  type FeedRecipe,
  type FeedSettings,
} from "@/lib/feed";
import {
  almostEmpty,
  levelMm,
  readBatchStatus,
  STEP_LABELS,
  timeLeft,
  type BatchStatus,
} from "@/lib/feed-status";
import { descriptor } from "@/lib/model";
import type { Controller } from "@/lib/types";
import { errorText } from "@/lib/utils";
import "./reservoir.css";

const when = (at: number | null) =>
  at === null
    ? "Never"
    : new Date(at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
const mm = (value: number | null) => (value === null ? "No reading" : `${number(value, 0)} mm`);
const nutrientName = (recipe: FeedRecipe | undefined, doser: number) =>
  recipe?.doses[String(doser)]?.label || `Doser ${doser}`;
const HINTS: Record<keyof FeedSettings, string> = {
  fill_s: "How long the fresh-water solenoid runs to refill an almost empty reservoir.",
  batch_l: "The litres the doses are worked out for: what the fill leaves in the reservoir.",
  empty_mm:
    "The level sensor's distance to the water when the reservoir is almost empty. 0 means no automatic batches.",
  settle_s: "The pump and recirculation run this long before the first doser starts.",
  pause_s: "A gap between one doser and the next, so each mixes in before the next goes in.",
  mix_s: "The pump and recirculation keep running this long after the last dose.",
};

/** Seconds that tick while a step counts down. */
function useNow(active: boolean) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return now;
}

/** The reservoir drawn as a vessel below its level sensor: the water surface at the distance the
 * sensor reads, the almost-empty mark dashed across. Its depth is a little past the mark. */
function Vessel({ level, mark }: { level: number | null; mark: number | null }) {
  const clip = useId();
  const markSet = mark !== null && mark > 0;
  const depth = Math.max(markSet ? mark * 1.2 : 0, level !== null ? level * 1.15 : 0, 1);
  const y = (distance: number) => 1 + (98 * Math.min(distance, depth)) / depth;
  const low = almostEmpty(level, mark);
  return (
    <svg
      className="res-vessel"
      viewBox="0 0 60 100"
      role="img"
      aria-label={
        level === null
          ? "No level reading"
          : `The water is ${number(level, 0)} mm below the sensor${markSet ? `; almost empty at ${number(mark, 0)} mm` : ""}`
      }
      data-low={low ? "" : undefined}
    >
      <defs>
        <clipPath id={clip}>
          <rect x="1" y="1" width="58" height="98" rx="8" />
        </clipPath>
      </defs>
      <rect x="1" y="1" width="58" height="98" rx="8" className="res-shell" />
      {level !== null && (
        <g clipPath={`url(#${clip})`}>
          <rect x="1" y={y(level)} width="58" height={99 - y(level)} className="res-water" />
        </g>
      )}
      {markSet && <path d={`M1 ${y(mark)} H59`} className="res-mark" />}
    </svg>
  );
}

type StepState = "done" | "now" | "next";
interface Stage {
  key: string;
  label: string;
  detail: string;
  state: StepState;
}
/** A batch's steps in order: fill, mix, each dose, mix. Running, each is done, now or next. */
function stepsOf(plan: FeedPlan, status: BatchStatus | null): Stage[] {
  const running = status?.step && status.step !== "idle" ? status : null;
  const doses = running?.doses.length
    ? running.doses
    : plan.doses.map((d) => ({ ...d, dosed: null }));
  const order = ["filling", "settling", "dosing", "mixing"];
  const at = running ? order.indexOf(running.step === "pausing" ? "dosing" : running.step!) : -1;
  const phase = (index: number): StepState =>
    at < 0 ? "next" : index < at ? "done" : index === at ? "now" : "next";
  return [
    { key: "fill", label: "Fill", detail: duration(plan.fill_s), state: phase(0) },
    { key: "settle", label: "Circulate", detail: duration(plan.settle_s), state: phase(1) },
    ...doses.map((dose) => ({
      key: `dose-${dose.doser}`,
      label: dose.label,
      detail: `${number(dose.ml, 1)} mL · ${duration(dose.seconds)}`,
      state: (at > 2
        ? "done"
        : at < 2
          ? "next"
          : running?.step === "dosing" && running.doser === dose.doser
            ? "now"
            : dose.dosed !== null
              ? "done"
              : "next") as StepState,
    })),
    { key: "mix", label: "Mix", detail: duration(plan.mix_s), state: phase(3) },
  ];
}

function BatchPanel({
  controller,
  doc,
  status,
  level,
  mapped,
  dirty,
  onMix,
}: {
  controller: Controller;
  doc: FeedDocument;
  status: BatchStatus | null;
  /** The level sensor's reading in mm: the controller's, or the sensor's own before it reports. */
  level: number | null;
  mapped: boolean;
  dirty: boolean;
  onMix: () => void;
}) {
  const [review, setReview] = useState(false);
  const running = !!status?.step && status.step !== "idle";
  const now = useNow(running);
  const left = running ? timeLeft(status!.until, now) : null;
  const plan = doc.plan;
  const { entityId: autoId, enabled: auto } = controller.room.autoBatches;
  const low = almostEmpty(level, status?.emptyMm ?? plan.empty_mm);
  const steps = stepsOf(plan, status);
  const why = !mapped
    ? "Map the reservoir in Settings → Rooms & hardware first."
    : dirty
      ? "Save or discard your changes first."
      : running
        ? "A batch is running."
        : plan.problem
          ? plan.problem
          : status?.blocked
            ? `A batch cannot start: ${status.blocked}.`
            : null;
  return (
    <section className="panel res-batch" data-batch-status={status?.step ?? "none"}>
      <div className="res-batch-head">
        <div>
          <span className="eyebrow">Nutrient batch</span>
          <div className="res-step">
            <strong>{status?.step ? STEP_LABELS[status.step] : "Not reported"}</strong>
            {running && status?.step === "dosing" && status.nutrient && (
              <span>
                {status.nutrient} <span className="muted">(doser {status.doser})</span>
              </span>
            )}
            {left && <Pill tone="water">{left}</Pill>}
          </div>
          <p className="muted small">
            {running
              ? `${status!.stage ?? "No stage"} batch. Watering in this room waits until it finishes.`
              : plan.stage
                ? `Next batch: ${plan.stage}, ${number(plan.batch_l, 1)} L.`
                : "No feed stage is chosen."}
          </p>
        </div>
        <div className="res-batch-actions">
          <Button onClick={onMix} disabled={!!why}>
            <Beaker size={16} /> Mix a batch now
          </Button>
          {why && !running && <small className="muted">{why}</small>}
        </div>
      </div>
      <ol className="res-steps" aria-label={running ? "This batch's steps" : "What a batch does"}>
        {steps.map((step) => (
          <li key={step.key} data-state={step.state}>
            <span className="res-step-dot" aria-hidden="true">
              {step.state === "done" ? <Check size={12} /> : null}
            </span>
            <span className="res-step-label">
              {step.label}
              {step.state === "now" && <span className="sr-only"> (now)</span>}
              {step.state === "done" && <span className="sr-only"> (done)</span>}
            </span>
            <span className="res-step-detail">{step.detail}</span>
          </li>
        ))}
      </ol>
      <div className="res-batch-body">
        <div className="res-level">
          <Vessel level={level} mark={status?.emptyMm ?? plan.empty_mm} />
          <dl className="res-facts">
            <div>
              <dt>Level sensor</dt>
              <dd>
                {mm(level)}
                <span className="unit"> to the water</span>
              </dd>
            </div>
            <div>
              <dt>Almost empty at</dt>
              <dd>{plan.empty_mm > 0 ? `${number(plan.empty_mm, 0)} mm` : "Not set"}</dd>
            </div>
            <div>
              <dt>Now</dt>
              <dd>
                {low === null ? (
                  <Pill tone="unknown">Unknown</Pill>
                ) : low ? (
                  <Pill tone="warn" dot>
                    Almost empty
                  </Pill>
                ) : (
                  <Pill tone="on" dot>
                    Has water
                  </Pill>
                )}
              </dd>
            </div>
          </dl>
        </div>
        <div className="res-auto">
          <span className="eyebrow">Automatic batches</span>
          <p>
            {auto === true
              ? plan.empty_mm > 0
                ? `On: a batch starts by itself once the reservoir reads almost empty for three passes in a row.${status && !status.armed ? " Waiting for the reservoir to read fuller after the last one." : ""}`
                : "On, but no almost-empty mark is set, so none starts by itself."
              : auto === false
                ? "Off: batches start only when you ask for one."
                : "Unavailable: update the Crop Steering integration."}
          </p>
          {autoId && (
            <Button
              variant="outline"
              size="sm"
              disabled={
                auto === null || !["live", "demo"].includes(controller.connection) || !mapped
              }
              onClick={() => setReview(true)}
            >
              <Sparkles size={15} /> {auto ? "Turn automatic off…" : "Turn automatic on…"}
            </Button>
          )}
        </div>
        <div className="res-last">
          <span className="eyebrow">Last batch</span>
          {status?.last ? (
            <>
              <p>
                <strong>{status.last.stage ?? "No stage"}</strong>, {when(status.last.at)}{" "}
                <Pill tone={status.last.result === "done" ? "on" : "warn"}>
                  {status.last.result === "done" ? "Done" : "Stopped"}
                </Pill>
              </p>
              {status.last.result !== "done" && (
                <p className="muted small">{status.last.result.replace(/^stopped: /, "")}</p>
              )}
              <p className="muted small">
                {Object.entries(status.last.dosed)
                  .map(([n, ml]) => `doser ${n} ${number(ml, 1)} mL`)
                  .join(" · ") || "Nothing dosed"}
              </p>
            </>
          ) : (
            <p className="muted">{status ? "None yet" : "Not reported"}</p>
          )}
        </div>
      </div>
      {!status && mapped && (
        <p className="workspace-message res-note">
          The controller app has not reported on this reservoir yet. It does once it runs a version
          with nutrient batches and sees the reservoir mapped here.
        </p>
      )}
      {autoId && (
        <ReviewDialog
          open={review}
          onOpenChange={setReview}
          controller={controller}
          title={auto ? "Turn automatic batches off?" : "Turn automatic batches on?"}
          items={[
            {
              change: { entityId: autoId, value: !auto },
              label: `${controller.room.room.name} automatic batches`,
              before: auto ? "On" : "Off",
              after: auto ? "Off" : "On",
            },
          ]}
          note={
            auto
              ? "Batches then start only when you ask for one."
              : "The controller app then fills, mixes and doses a batch by itself whenever the reservoir reads almost empty. Check the fill time and the almost-empty mark first."
          }
        />
      )}
    </section>
  );
}

/** The room's dosers in their order: drag by the handle (mouse or touch), or move with the arrows. */
function DoserOrder({
  draft,
  mapped,
  entities,
  stage,
  onChange,
}: {
  draft: FeedDraft;
  mapped: number[];
  entities: Record<string, string>;
  stage: FeedRecipe | undefined;
  onChange: (next: FeedDraft) => void;
}) {
  const id = useId();
  const list = useRef<HTMLOListElement>(null);
  const [dragging, setDragging] = useState<number | null>(null);
  const [said, setSaid] = useState("");
  const order = roomOrder(draft.order, mapped);
  const place = (next: number[], moved: number) => {
    onChange({ ...draft, order: next });
    setSaid(`Doser ${moved} moved to position ${next.indexOf(moved) + 1} of ${next.length}.`);
  };
  const move = (event: PointerEvent) => {
    if (dragging === null || !list.current) return;
    const rows = [...list.current.querySelectorAll<HTMLElement>("[data-doser]")];
    const to = rows.filter((row) => {
      if (Number(row.dataset.doser) === dragging) return false;
      const box = row.getBoundingClientRect();
      return event.clientY > box.top + box.height / 2;
    }).length;
    const next = moveTo(order, order.indexOf(dragging), to);
    if (next.join() !== order.join()) place(next, dragging);
  };
  const drop = () => setDragging(null);
  return (
    <>
      {/* The list, not the handle, holds the pointer while a doser is dragged: reordering moves the
          dragged row in the page, which would let go of a pointer its handle held. */}
      <ol
        ref={list}
        className="res-dosers"
        aria-describedby={`${id}-help`}
        onPointerMove={move}
        onPointerUp={drop}
        onPointerCancel={drop}
        onLostPointerCapture={drop}
      >
        {order.map((doser, index) => (
          <li
            key={doser}
            data-doser={doser}
            data-dragging={dragging === doser ? "" : undefined}
            className="res-doser"
          >
            <span
              className="res-grip"
              aria-hidden="true"
              title="Drag to reorder"
              onPointerDown={(event) => {
                if (event.button !== 0 || !list.current) return;
                event.preventDefault();
                list.current.setPointerCapture(event.pointerId);
                setDragging(doser);
              }}
            >
              <GripVertical size={18} />
            </span>
            <span className="res-doser-position">{index + 1}</span>
            <span className="res-doser-name">
              <strong>Doser {doser}</strong>
              <span className="muted small">
                {stage?.doses[String(doser)]?.label
                  ? `${stage.doses[String(doser)].label} in ${stage.name}`
                  : "Not in the stage in use"}
              </span>
              <code className="res-entity">{entities[String(doser)]}</code>
            </span>
            <span className="res-flow">
              <Label htmlFor={`${id}-flow-${doser}`}>Flow (mL/min)</Label>
              <Input
                id={`${id}-flow-${doser}`}
                type="number"
                min={1}
                max={10000}
                step={1}
                value={Number.isFinite(flowOf(draft, doser)) ? String(flowOf(draft, doser)) : ""}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    dosers: {
                      ...draft.dosers,
                      [String(doser)]: {
                        flow_ml_min: event.target.value === "" ? NaN : Number(event.target.value),
                      },
                    },
                  })
                }
              />
            </span>
            <span className="res-doser-move">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Move doser ${doser} earlier`}
                disabled={index === 0}
                onClick={() => place(moveTo(order, index, index - 1), doser)}
              >
                <ArrowUp size={16} />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Move doser ${doser} later`}
                disabled={index === order.length - 1}
                onClick={() => place(moveTo(order, index, index + 1), doser)}
              >
                <ArrowDown size={16} />
              </Button>
            </span>
          </li>
        ))}
      </ol>
      <p id={`${id}-help`} className="muted small">
        Dosers run one after another in this order, whatever the stage. Drag a doser by its handle,
        or use the arrows. The flow is what the doser pumps, set on the doser itself.
      </p>
      <p className="sr-only" aria-live="polite">
        {said}
      </p>
    </>
  );
}

function RecipeCard({
  draft,
  recipe,
  index,
  rows,
  mapped,
  onChange,
  onRemove,
  listId,
}: {
  draft: FeedDraft;
  recipe: FeedRecipe;
  index: number;
  rows: number[];
  mapped: number[];
  onChange: (recipe: FeedRecipe) => void;
  onRemove: () => void;
  listId: string;
}) {
  const id = useId();
  const total = perLitre(recipe);
  const batch = rows.reduce((sum, n) => sum + doseOf(draft, recipe, n).ml, 0);
  const inUse = draft.stage === recipe.id;
  const dose = (n: number) => recipe.doses[String(n)] ?? { label: "", parts: 0 };
  const setDose = (n: number, change: Partial<{ label: string; parts: number }>) =>
    onChange({ ...recipe, doses: { ...recipe.doses, [String(n)]: { ...dose(n), ...change } } });
  return (
    <fieldset className="panel res-recipe" data-recipe={recipe.name || `recipe-${index + 1}`}>
      <legend className="sr-only">{recipe.name || `Feed recipe ${index + 1}`}</legend>
      <div className="res-recipe-head">
        <div>
          <Label htmlFor={`${id}-name`}>Stage name</Label>
          <Input
            id={`${id}-name`}
            list={`${listId}-stages`}
            value={recipe.name}
            maxLength={40}
            placeholder="Vege, Flower, Fade…"
            onChange={(event) => onChange({ ...recipe, name: event.target.value })}
          />
        </div>
        <div>
          <Label htmlFor={`${id}-strength`}>mL per litre per part</Label>
          <Input
            id={`${id}-strength`}
            type="number"
            min={0}
            max={20}
            step={0.001}
            value={Number.isFinite(recipe.strength) ? String(recipe.strength) : ""}
            onChange={(event) =>
              onChange({
                ...recipe,
                strength: event.target.value === "" ? NaN : Number(event.target.value),
              })
            }
          />
        </div>
        {inUse && (
          <Pill tone="on" dot>
            In use
          </Pill>
        )}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={`Remove ${recipe.name || `feed recipe ${index + 1}`}`}
          onClick={onRemove}
        >
          <Trash2 size={16} />
        </Button>
      </div>
      <div className="table-scroll" tabIndex={0} aria-label={`${recipe.name || "Recipe"} doses`}>
        <table className="data-table res-recipe-table">
          <thead>
            <tr>
              <th>Doser</th>
              <th>Nutrient</th>
              <th>Parts</th>
              <th className="numeric">Per batch</th>
              <th className="numeric">Runs</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((n) => {
              const amount = doseOf(draft, recipe, n);
              return (
                <tr key={n} data-dose={n}>
                  <td>
                    {n}
                    {!mapped.includes(n) && (
                      <Pill tone="warn" className="pill res-unmapped">
                        No switch
                      </Pill>
                    )}
                  </td>
                  <td>
                    <Input
                      aria-label={`Doser ${n} nutrient`}
                      list={`${listId}-nutrients`}
                      value={dose(n).label}
                      maxLength={40}
                      placeholder="Nothing"
                      onChange={(event) => setDose(n, { label: event.target.value })}
                    />
                  </td>
                  <td>
                    <Input
                      aria-label={`Doser ${n} parts`}
                      type="number"
                      min={0}
                      max={100}
                      step={0.1}
                      value={Number.isFinite(dose(n).parts) ? String(dose(n).parts) : ""}
                      onChange={(event) =>
                        setDose(n, {
                          parts: event.target.value === "" ? NaN : Number(event.target.value),
                        })
                      }
                    />
                  </td>
                  <td className="numeric">
                    {amount.ml > 0 ? number(amount.ml, 1) : "—"}
                    {amount.ml > 0 && <span className="unit"> mL</span>}
                  </td>
                  <td className="numeric">{amount.ml > 0 ? duration(amount.seconds) : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="muted small res-recipe-total">
        {Number.isFinite(total) ? number(total, 2) : "—"} mL per litre · {number(batch, 1)} mL in a{" "}
        {number(draft.batch_l, 1)} L batch
      </p>
    </fieldset>
  );
}

export function Reservoir({
  controller,
  navigate,
  onDirtyChange,
}: {
  controller: Controller;
  navigate: (page: Page) => void;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const [doc, setDoc] = useState<FeedDocument | null>(null);
  const [draft, setDraft] = useState<FeedDraft | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const listId = useId();
  useEffect(() => {
    let current = true;
    setDoc(null);
    setDraft(null);
    setError("");
    controller
      .operator<FeedDocument>("feed_get")
      .then((result) => {
        if (!current) return;
        setDoc(result);
        setDraft(draftOf(result));
      })
      .catch((err) => current && setError(errorText(err)));
    return () => {
      current = false;
    };
  }, [controller.roomId, controller.connection]);
  const dirty = !!doc && !!draft && JSON.stringify(draft) !== JSON.stringify(draftOf(doc));
  useLayoutEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);

  const attributes = descriptor(controller.states, controller.room.room)?.attributes ?? {};
  const reservoir = RESERVOIR_KEYS.some((key) => attributes[key]);
  const status = readBatchStatus(controller.states, controller.room.room.prefix);
  const sensor = attributes.reservoir_distance_sensor;
  const level =
    status?.levelMm ??
    (typeof sensor === "string" && sensor ? levelMm(controller.states[sensor]) : null);
  const mapped = doc ? mappedNumbers(doc.mapped) : [];
  const errors = draft && doc ? draftErrors(draft, doc.max_recipes) : [];
  const preview = draft ? planOf(draft, mapped) : null;
  const stage = draft?.recipes.find((r) => r.id === draft.stage);

  async function save() {
    if (!doc || !draft) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await controller.operator<FeedDocument>("feed_save", {
        expected_revision: doc.revision,
        document: documentOf(draft),
      });
      setDoc(result);
      setDraft(draftOf(result));
      setNotice("Saved. The controller app runs the next batch with these settings.");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  async function mix() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await controller.operator<FeedDocument>("feed_mix");
      setDoc(result);
      setConfirm(false);
      const at = result.requested ? Date.parse(result.requested) : NaN;
      setNotice(
        `Batch asked for${Number.isFinite(at) ? ` at ${new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}. The controller app starts it at its next pass, within a minute, or says why it cannot.`,
      );
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  const setting = (key: keyof FeedSettings) => {
    const [label, unit, low, high, whole] = SETTINGS[key];
    const value = draft![key];
    return (
      <div key={key} className="res-setting">
        <Label htmlFor={`${listId}-${key}`}>
          {label} ({unit})
        </Label>
        <Input
          id={`${listId}-${key}`}
          type="number"
          min={low}
          max={high}
          step={whole ? 1 : 0.1}
          value={Number.isFinite(value) ? String(value) : ""}
          onChange={(event) =>
            setDraft({
              ...draft!,
              [key]: event.target.value === "" ? NaN : Number(event.target.value),
            })
          }
        />
        <small className="muted">
          {unit === "s" && Number.isFinite(value) && value >= 60 ? `${duration(value)}. ` : ""}
          {HINTS[key]}
        </small>
        {key === "empty_mm" && level !== null && (
          <Button
            type="button"
            variant="link"
            className="inline-link"
            onClick={() => setDraft({ ...draft!, empty_mm: Math.round(level) })}
          >
            Use the reading now ({number(level, 0)} mm)
          </Button>
        )}
      </div>
    );
  };
  const rows = (recipe: FeedRecipe) => {
    const used = Object.entries(recipe.doses)
      .filter(([n, dose]) => !mapped.includes(Number(n)) && (dose.parts > 0 || dose.label))
      .map(([n]) => Number(n));
    return [...roomOrder(draft!.order, mapped), ...used.sort((a, b) => a - b)];
  };
  const low = almostEmpty(level, status?.emptyMm ?? doc?.plan.empty_mm ?? null);
  // What the controller checks before a batch asked for by hand: an almost empty reservoir, when it
  // has a level sensor and a mark; without either nothing is checked.
  const checked = !!attributes.reservoir_distance_sensor && !!doc && doc.plan.empty_mm > 0;

  return (
    <>
      <Heading title="Reservoir" />
      {error && (
        <p className="workspace-message error" role="alert">
          {error}
        </p>
      )}
      {doc?.error && (
        <p className="workspace-message error" role="alert">
          {doc.error}
        </p>
      )}
      {notice && (
        <p className="workspace-message" role="status">
          {notice}
        </p>
      )}
      {!doc && !error && <p className="muted">Loading the reservoir…</p>}
      {doc && !reservoir && !mapped.length && (
        <Empty
          title="No reservoir mapped"
          detail="Map this room's reservoir level sensor, its fresh-water and recirculation solenoids and up to six dosers in Settings → Rooms & hardware. The controller app then refills the reservoir, mixes and doses each batch."
          action={<Button onClick={() => navigate("setup")}>Map them in Rooms & hardware</Button>}
        />
      )}
      {doc && draft && (reservoir || !!mapped.length) && (
        <>
          <BatchPanel
            controller={controller}
            doc={doc}
            status={status}
            level={level}
            mapped={reservoir}
            dirty={dirty}
            onMix={() => setConfirm(true)}
          />
          <div className="res-columns">
            <section className="panel workspace-card res-stage">
              <h2>Feed stage</h2>
              <p className="muted small">
                The recipe the next batch mixes. Change it when the room moves to its next stage,
                and swap the bottles on the dosers if that stage uses other nutrients.
              </p>
              <Label htmlFor={`${listId}-stage`}>Stage in use</Label>
              <select
                id={`${listId}-stage`}
                className="res-select"
                value={draft.stage ?? ""}
                onChange={(event) => setDraft({ ...draft, stage: event.target.value || null })}
              >
                <option value="">None: no batches</option>
                {draft.recipes.map((recipe, index) => (
                  <option key={recipe.id} value={recipe.id}>
                    {recipe.name || `Recipe ${index + 1}`}
                  </option>
                ))}
              </select>
              {preview?.problem ? (
                <p className="workspace-message" data-feed-problem>
                  {preview.problem}
                </p>
              ) : (
                preview && (
                  <table className="data-table res-plan" aria-label="The next batch's doses">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Nutrient</th>
                        <th className="numeric">Dose</th>
                        <th className="numeric">Runs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.doses.map((dose, index) => (
                        <tr key={dose.doser}>
                          <td>{index + 1}</td>
                          <td>
                            {dose.label} <span className="muted small">doser {dose.doser}</span>
                          </td>
                          <td className="numeric">
                            {number(dose.ml, 1)}
                            <span className="unit"> mL</span>
                          </td>
                          <td className="numeric">{duration(dose.seconds)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )
              )}
            </section>
            <section className="panel workspace-card res-settings">
              <h2>Batch</h2>
              <div className="res-setting-grid">
                {(Object.keys(SETTINGS) as (keyof FeedSettings)[]).map(setting)}
              </div>
            </section>
          </div>
          <section className="panel workspace-card">
            <h2>Dosers</h2>
            {mapped.length ? (
              <DoserOrder
                draft={draft}
                mapped={mapped}
                entities={doc.mapped}
                stage={stage}
                onChange={setDraft}
              />
            ) : (
              <p className="muted">
                No doser is mapped.{" "}
                <Button variant="link" className="inline-link" onClick={() => navigate("setup")}>
                  Map them in Rooms & hardware
                </Button>
                .
              </p>
            )}
          </section>
          <section className="res-recipes" aria-labelledby={`${listId}-recipes`}>
            <div className="workspace-section-heading">
              <div>
                <h2 id={`${listId}-recipes`}>Feed recipes</h2>
                <p className="muted small">
                  One per growth stage. Parts are the ratio, as on the nutrient chart (Athena Flower
                  is 3 Core : 5 Bloom : 1 Balance : 0.5 Cleanse); the strength is how many mL per
                  litre one part is. Each nutrient is the bottle on that doser in that stage.
                </p>
              </div>
              <Button
                variant="outline"
                disabled={draft.recipes.length >= doc.max_recipes}
                onClick={() =>
                  setDraft({
                    ...draft,
                    recipes: [
                      ...draft.recipes,
                      newRecipe(
                        draft,
                        mapped,
                        STAGE_NAMES.find(
                          (name) =>
                            !draft.recipes.some(
                              (r) => r.name.trim().toLowerCase() === name.toLowerCase(),
                            ),
                        ) ?? "",
                      ),
                    ],
                  })
                }
              >
                <Plus size={16} /> Add a feed recipe
              </Button>
            </div>
            <datalist id={`${listId}-stages`}>
              {STAGE_NAMES.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
            <datalist id={`${listId}-nutrients`}>
              {[...new Set(Object.values(NUTRIENT_LINES).flat())].map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
            {!draft.recipes.length && (
              <p className="muted">No feed recipes yet: add one for each stage you feed.</p>
            )}
            {draft.recipes.map((recipe, index) => (
              <RecipeCard
                key={recipe.id || index}
                draft={draft}
                recipe={recipe}
                index={index}
                rows={rows(recipe)}
                mapped={mapped}
                listId={listId}
                onChange={(next) =>
                  setDraft({
                    ...draft,
                    recipes: draft.recipes.map((r, i) => (i === index ? next : r)),
                  })
                }
                onRemove={() =>
                  setDraft({
                    ...draft,
                    recipes: draft.recipes.filter((_, i) => i !== index),
                    stage: draft.stage === recipe.id ? null : draft.stage,
                  })
                }
              />
            ))}
          </section>
          {dirty && (
            <div className="res-savebar" role="region" aria-label="Unsaved changes">
              {!!errors.length && (
                <ul className="workspace-message error" role="alert">
                  {errors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
              <div className="res-savebar-row">
                <span>Unsaved changes</span>
                <Button variant="ghost" disabled={busy} onClick={() => setDraft(draftOf(doc))}>
                  Discard
                </Button>
                <Button disabled={busy || !!errors.length || !!doc.error} onClick={save}>
                  {busy && <LoaderCircle className="spin" size={16} />} Save
                </Button>
              </div>
            </div>
          )}
        </>
      )}
      {confirm && doc && (
        <Dialog open onOpenChange={(open) => !open && !busy && setConfirm(false)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Mix a {doc.plan.stage} batch now?</DialogTitle>
              <DialogDescription>
                The fresh water runs for {duration(doc.plan.fill_s)}, then the pump and
                recirculation start; after {duration(doc.plan.settle_s)} the dosers run one after
                another, then it mixes for {duration(doc.plan.mix_s)}. Watering in this room waits
                until it finishes.
              </DialogDescription>
            </DialogHeader>
            <table className="data-table res-plan" aria-label="This batch's doses">
              <tbody>
                {doc.plan.doses.map((dose) => (
                  <tr key={dose.doser}>
                    <td>
                      {dose.label} <span className="muted small">doser {dose.doser}</span>
                    </td>
                    <td className="numeric">
                      {number(dose.ml, 1)}
                      <span className="unit"> mL</span>
                    </td>
                    <td className="numeric">{duration(dose.seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {checked && low === false && (
              <p className="workspace-message error" role="alert">
                The reservoir reads {mm(level)} from the top, short of its almost-empty mark (
                {number(doc.plan.empty_mm, 0)} mm). The controller app mixes a batch only in an
                almost empty reservoir, so the fill cannot overflow it.
              </p>
            )}
            {checked && low === null && (
              <p className="workspace-message error" role="alert">
                The level sensor has no reading, so the controller app will not start a batch.
              </p>
            )}
            {!checked && (
              <p className="workspace-message">
                {attributes.reservoir_distance_sensor
                  ? "No almost-empty mark is set"
                  : "No level sensor is mapped"}
                , so nothing checks the level first: make sure the reservoir is almost empty, or the
                fill may overflow it.
              </p>
            )}
            <DialogFooter>
              <Button variant="ghost" disabled={busy} onClick={() => setConfirm(false)}>
                Cancel
              </Button>
              <Button disabled={busy || (checked && low !== true)} onClick={mix}>
                {busy && <LoaderCircle className="spin" size={16} />} Mix a batch
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
