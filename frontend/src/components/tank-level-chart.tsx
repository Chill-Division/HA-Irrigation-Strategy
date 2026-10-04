import { useEffect, useId, useState } from "react";
import {
  Area,
  AreaChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Controller, Series } from "@/lib/types";
import { levelSeries, type LevelSource } from "@/lib/tank-telemetry";
import { whileVisible } from "@/lib/live";
import { errorText } from "@/lib/utils";

const WINDOWS = [12, 24] as const;
/** How often the chart reads the level sensor's history again while the page is open. */
const REFRESH_MS = 10 * 60_000;

/** The tank's level over the last 12 or 24 hours, from Home Assistant's recorded history of the
 * level sensor the card reads, ending on the level it shows now. */
export function TankLevelChart({
  controller,
  source,
  current,
}: {
  controller: Controller;
  source: LevelSource | null;
  current: number | null;
}) {
  const titleId = useId();
  const [hours, setHours] = useState<(typeof WINDOWS)[number]>(24);
  const [loaded, setLoaded] = useState<{ entityId: string; points: Series["points"] } | null>(null);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);
  const entityId = source?.entityId ?? "";
  useEffect(() => whileVisible(() => setTick((value) => value + 1), REFRESH_MS), []);
  useEffect(() => {
    if (!entityId) return;
    let live = true;
    const abort = new AbortController();
    setError("");
    controller
      .history([entityId], hours, abort.signal)
      .then(([series]) => {
        if (live) setLoaded({ entityId, points: series?.points ?? [] });
      })
      .catch((reason) => {
        if (live) setError(errorText(reason));
      });
    return () => {
      live = false;
      abort.abort();
    };
  }, [controller.roomId, controller.connection, entityId, hours, tick]);
  const now = Date.now();
  const points = loaded?.entityId === entityId ? loaded.points : null;
  const series = source && points ? levelSeries(points, source, hours, current, now) : [];
  const shown = series.flatMap((step) => (step.pct === null ? [] : [step.pct]));
  const start = now - hours * 3_600_000;
  const clock = (at: number) =>
    at >= now - 60_000
      ? "Now"
      : new Date(at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const summary = shown.length
    ? `Tank level over the last ${hours} hours: ${Math.round(shown[0])}% then, ` +
      `${Math.round(shown[shown.length - 1])}% now, lowest ${Math.round(Math.min(...shown))}%, ` +
      `highest ${Math.round(Math.max(...shown))}%` +
      (source?.minPct ? `; the dashed line is the ${source.minPct}% minimum` : "")
    : "";
  return (
    <div className="tank-history" aria-labelledby={titleId} role="group">
      <div className="tank-history-head">
        <span id={titleId}>Level, last {hours} h</span>
        <div className="tank-range" role="group" aria-label="Level history window">
          {WINDOWS.map((option) => (
            <button
              type="button"
              key={option}
              aria-pressed={hours === option}
              onClick={() => setHours(option)}
            >
              {option} h
            </button>
          ))}
        </div>
      </div>
      {!source ? (
        <p className="tank-history-note">Map the reservoir's level sensor to chart it.</p>
      ) : error && !points ? (
        <p className="tank-history-note">{error}</p>
      ) : !points ? (
        <p className="tank-history-note" role="status">
          Loading the recorded level…
        </p>
      ) : !shown.length ? (
        <p className="tank-history-note">No level recorded in the last {hours} hours.</p>
      ) : (
        <div className="tank-history-chart" role="img" aria-label={summary} data-tank-history>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={series} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="at"
                type="number"
                scale="time"
                domain={[start, now]}
                ticks={[start, start + (now - start) / 2, now]}
                interval={0}
                tickLine={false}
                axisLine={false}
                stroke="var(--muted-foreground)"
                // The window's start and Now sit inside the chart's edges, not centred on them.
                tick={(props) => {
                  const at = Number(props.payload?.value);
                  return (
                    <text
                      x={props.x}
                      y={props.y}
                      dy={10}
                      textAnchor={at <= start ? "start" : at >= now ? "end" : "middle"}
                      fill="var(--muted-foreground)"
                      fontSize={12}
                    >
                      {clock(at)}
                    </text>
                  );
                }}
              />
              <YAxis
                domain={[0, 100]}
                ticks={[0, 50, 100]}
                unit="%"
                width={36}
                tickLine={false}
                axisLine={false}
                stroke="var(--muted-foreground)"
                fontSize={12}
              />
              {source.minPct !== null && (
                <ReferenceLine
                  y={source.minPct}
                  stroke="var(--warning)"
                  strokeDasharray="4 3"
                  ifOverflow="extendDomain"
                />
              )}
              <Tooltip
                labelFormatter={(value) =>
                  new Date(Number(value)).toLocaleString([], {
                    dateStyle: "short",
                    timeStyle: "short",
                  })
                }
                formatter={(value) => [`${Math.round(Number(value))}%`, "Level"]}
                contentStyle={{
                  background: "var(--surface)",
                  color: "var(--foreground)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Area
                dataKey="pct"
                type="linear"
                stroke="var(--primary)"
                strokeWidth={2}
                fill="var(--primary)"
                fillOpacity={0.23}
                connectNulls={false}
                dot={false}
                activeDot={{ r: 3 }}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
