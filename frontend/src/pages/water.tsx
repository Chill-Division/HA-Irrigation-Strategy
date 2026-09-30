import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Heading } from "@/components/dashboard";
import { WaterDelivery } from "@/components/water-delivery";
import { WaterUsePanel } from "@/components/water-use";
import type { Controller } from "@/lib/types";
import "./insights.css";

/** Insights › Water: what each zone has been given, and what a shot of a given length delivers. */
export function Water({ controller }: { controller: Controller }) {
  const zones = controller.room.zones;
  const [zoneId, setZoneId] = useState<number | null>(zones[0]?.id ?? null);
  const zone = zones.find((item) => item.id === zoneId) ?? zones[0];
  return (
    <>
      <Heading title="Water" />
      <WaterUsePanel controller={controller} zones={zones} />
      {zone && (
        <>
          <div className="insight-zone-picker">
            <Label htmlFor="water-zone">Shot calculator for</Label>
            <select
              id="water-zone"
              value={zone.id}
              onChange={(event) => setZoneId(Number(event.target.value))}
            >
              {zones.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>
          <WaterDelivery controller={controller} zoneId={zone.id} />
        </>
      )}
    </>
  );
}
