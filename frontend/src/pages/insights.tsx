import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Empty,
  Heading,
  HistoryChart,
  MetricValue,
  PhasePill,
  Status,
  time,
  type Page,
} from "@/components/dashboard";
import { Pill } from "@/components/mini-visuals";
import { ageText } from "@/lib/controller-health";
import type { Controller, Metric } from "@/lib/types";
import "./insights.css";

function Reference({ metric, controller }: { metric: Metric; controller: Controller }) {
  const entity = metric.entityId ? controller.states[metric.entityId] : undefined;
  return (
    <div className="insight-reference">
      <strong>{metric.label}</strong>
      <span>
        <MetricValue metric={metric} />
      </span>
      <small>{entity ? `Updated ${time(entity.last_updated)}` : "Entity not mapped"}</small>
    </div>
  );
}
/** Whether a zone's probe gives the controller a current reading, and how old its last one is. */
function Probe({ metric, controller }: { metric: Metric; controller: Controller }) {
  const entity = metric.entityId ? controller.states[metric.entityId] : undefined;
  const at = entity?.last_updated ? Date.parse(entity.last_updated) : NaN;
  return (
    <>
      <Pill dot tone={metric.value !== null ? "on" : "off"}>
        {metric.value !== null ? "Current" : "Unavailable / unverified"}
      </Pill>
      {Number.isFinite(at) && (
        <small className="muted"> Reading {ageText(Date.now() - at)} old</small>
      )}
    </>
  );
}
/** Insights › Zone: one zone's readings against its targets, their history, and every probe. */
export function Insights({
  controller,
  navigate,
}: {
  controller: Controller;
  navigate?: (page: Page, zoneId?: number) => void;
}) {
  const [zoneId, setZoneId] = useState<number | null>(controller.room.zones[0]?.id ?? null);
  useEffect(() => {
    setZoneId(controller.room.zones[0]?.id ?? null);
  }, [controller.roomId]);
  const zone = controller.room.zones.find((item) => item.id === zoneId) || controller.room.zones[0];
  const references = zone ? [zone.vwc, zone.target, zone.ec, zone.ecTarget] : [];
  const delta = (metric: Metric, target: Metric) =>
    metric.value !== null && target.value !== null ? metric.value - target.value : null;
  const vwcDelta = zone ? delta(zone.vwc, zone.target) : null,
    ecDelta = zone ? delta(zone.ec, zone.ecTarget) : null;
  const open = (page: Page) => {
    if (navigate) navigate(page, zone?.id);
    else window.location.hash = `/${page}`;
  };
  return (
    <div className="insights-page">
      <Heading title="Zone diagnostics" />
      {!zone ? (
        <section className="panel">
          <Empty
            title="Choose a configured room"
            detail="Diagnostics need a discovered zone and its controller entities."
            action={<Button onClick={() => open("setup")}>Open Rooms &amp; hardware</Button>}
          />
        </section>
      ) : (
        <>
          <div className="insight-zone-picker">
            <Label htmlFor="insights-zone">Inspect zone</Label>
            <select
              id="insights-zone"
              value={zone.id}
              onChange={(event) => setZoneId(Number(event.target.value))}
            >
              {controller.room.zones.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <Status enabled={zone.enabled} />
            <PhasePill phase={zone.phase} />
          </div>
          <div className="insight-references">
            {references.map((metric) => (
              <Reference key={metric.label} metric={metric} controller={controller} />
            ))}
          </div>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>What the readings show</h2>
                <p>{zone.name} · compared with the current phase references</p>
              </div>
              <Button variant="ghost" onClick={() => open("strategy")}>
                Review settings <ArrowRight size={16} />
              </Button>
            </div>
            <div className="insight-findings">
              <div>
                <strong>Moisture difference</strong>
                <p>
                  {vwcDelta === null
                    ? "A current VWC reading and phase reference are both needed for this comparison."
                    : `${Math.abs(vwcDelta).toFixed(1)} percentage points ${vwcDelta < 0 ? "below" : vwcDelta > 0 ? "above" : "from"} ${zone.target.label.toLowerCase()}.`}
                </p>
                <small>
                  {zone.phase === "P2"
                    ? "This is the base threshold. The controller may adjust it for EC."
                    : zone.phase === "P3"
                      ? "The emergency floor is a safety threshold, not a routine irrigation target."
                      : "A difference alone does not establish that an irrigation is due."}
                </small>
              </div>
              <div>
                <strong>EC difference</strong>
                <p>
                  {ecDelta === null
                    ? "A current EC reading and supported phase target are needed for this comparison."
                    : `${Math.abs(ecDelta).toFixed(2)} mS/cm ${ecDelta < 0 ? "below" : ecDelta > 0 ? "above" : "from"} the selected phase EC target.`}
                </p>
                <small>
                  Root-zone EC and feed-water EC describe different measurements. This comparison
                  does not prescribe a feed adjustment.
                </small>
              </div>
            </div>
            {controller.room.alerts
              .filter((notice) => notice.zoneId === undefined || notice.zoneId === zone.id)
              .map((notice) => (
                <div className="insight-notice" key={notice.id}>
                  <strong>{notice.title}</strong>
                  <p>{notice.detail}</p>
                </div>
              ))}
          </section>
          <HistoryChart controller={controller} zones={[zone]} />
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Probe coverage</h2>
                <p>Whether each zone's probes give the controller a current reading</p>
              </div>
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Zone</th>
                    <th>VWC</th>
                    <th>EC</th>
                    <th>Scheduling</th>
                  </tr>
                </thead>
                <tbody>
                  {controller.room.zones.map((item) => (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      {(["vwc", "ec"] as const).map((kind) => (
                        <td key={kind}>
                          <Probe metric={item[kind]} controller={controller} />
                        </td>
                      ))}
                      <td>
                        <Status enabled={item.enabled} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
