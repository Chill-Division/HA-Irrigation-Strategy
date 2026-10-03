import { useId } from "react";
import { Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Controller } from "@/lib/types";
import { tankTelemetry, type TankReading } from "@/lib/tank-telemetry";
import { TankLevelChart } from "./tank-level-chart";
import "./tank-status.css";

export function TankStatus({
  controller,
  onConfigure,
}: {
  controller: Controller;
  onConfigure: () => void;
}) {
  const tank = tankTelemetry(controller.states, controller.room.room);
  const refill = tank.refill;
  const clipId = useId();
  const connected = ["live", "demo"].includes(controller.connection);
  const value = (r: TankReading, digits = 1) =>
    r.value === null
      ? r.issue
      : `${r.value.toLocaleString(undefined, { maximumFractionDigits: digits })} ${r.unit}`;
  const pump = tank.pump.on === null ? tank.pump.issue : tank.pump.on ? "On" : "Off";
  // The water's temperature, a line in the tank under how full it is: only where a sensor is mapped.
  const temperature = tank.temperature.entityId ? value(tank.temperature, 1) : null;
  const lastKnown = connected ? "" : " · last known";
  const level = tank.level.value;
  // The drawing's inside runs from y=119 (empty) to y=1 (full): 1.18 units per percent.
  const surface = level === null ? null : 119 - level * 1.18;
  return (
    <section className="panel tank-panel" aria-label="Tank and pump status" data-tank-status>
      <div className="panel-heading">
        <h2>Tank & pump</h2>
        {!connected && <span className="tank-stale">Disconnected · last received</span>}
        <div className="tank-actions">
          <Button variant="ghost" onClick={onConfigure}>
            <Settings2 size={16} /> Map sensors
          </Button>
        </div>
      </div>
      <div className="tank-layout">
        <div
          className="tank-vessel"
          data-tank-level={level ?? "unknown"}
          title={tank.level.entityId || undefined}
        >
          <svg
            viewBox="0 0 100 120"
            role="img"
            aria-label={`Tank level: ${value(tank.level)}${temperature ? `, water ${temperature}` : ""}`}
          >
            <defs>
              <clipPath id={clipId}>
                <rect x="1" y="1" width="98" height="118" rx="12" />
              </clipPath>
            </defs>
            <rect x="1" y="1" width="98" height="118" rx="12" className="tank-shell" />
            {surface !== null && (
              <g clipPath={`url(#${clipId})`}>
                <rect x="1" y={surface} width="98" height={119 - surface} className="tank-water" />
                <path d={`M1 ${surface} H99`} className="tank-waterline" />
              </g>
            )}
            {[25, 50, 75].map((p) => (
              <path key={p} d={`M86 ${119 - p * 1.18}h13`} className="tank-tick" />
            ))}
            <text x="50" y={temperature ? 52 : 58} textAnchor="middle" className="tank-percent">
              {level === null ? "—" : `${Math.round(level)}%`}
            </text>
            <text x="50" y={temperature ? 69 : 76} textAnchor="middle" className="tank-caption">
              {tank.level.issue || "full"}
            </text>
            {temperature && (
              <text x="50" y="88" textAnchor="middle" className="tank-temperature">
                {temperature}
              </text>
            )}
          </svg>
        </div>
        <TankLevelChart controller={controller} source={tank.source} current={level} />
        <dl className="tank-equipment">
          <div
            className={connected && tank.pump.on ? "is-on" : undefined}
            data-pump-state={tank.pump.on === null ? "unknown" : tank.pump.on ? "on" : "off"}
          >
            <dt>Pump{lastKnown}</dt>
            <dd>{pump}</dd>
          </div>
          {refill && (
            <>
              <div
                className={connected && refill.running ? "is-on" : undefined}
                data-refill-state={refill.running ? "running" : refill.now ? "idle" : "unknown"}
              >
                <dt>Refill{lastKnown}</dt>
                <dd>{refill.now ?? refill.issue}</dd>
              </div>
              <div>
                <dt>Last refill</dt>
                <dd>
                  {refill.lastAt ? (
                    <>
                      <time dateTime={refill.lastAt}>
                        {new Date(refill.lastAt).toLocaleString([], {
                          dateStyle: "short",
                          timeStyle: "short",
                        })}
                      </time>
                      {refill.lastStopped && " · stopped"}
                    </>
                  ) : (
                    (refill.issue ?? "None yet")
                  )}
                </dd>
              </div>
            </>
          )}
        </dl>
        <p className="tank-note">
          Pump is the switch’s report, not measured flow.
          {refill && " Refills are the controller’s own record."}
        </p>
      </div>
    </section>
  );
}
