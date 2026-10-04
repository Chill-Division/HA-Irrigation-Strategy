import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  SUBSTRATE_PRESETS,
  SUBSTRATE_PRESET_GROUPS,
  matchPreset,
  presetLabel,
} from "@/lib/substrate-presets";
import {
  SIZING_BOUNDS,
  displayNumber,
  sizingError,
  sizingLabel,
  type SizingKey,
} from "@/lib/units";

/** A zone's pot volume (L) or dripper flow (L/h), as the draft holds it. Only the setup draft
 * changes here; saving still goes through "Review configuration". */
export function SizingField({
  id,
  sizingKey,
  value,
  disabled,
  onChange,
}: {
  id: string;
  sizingKey: SizingKey;
  value: number;
  disabled: boolean;
  onChange: (value: number) => void;
}) {
  const [entry, setEntry] = useState({ value, text: displayNumber(value) });
  let text = entry.text;
  // The draft moved without this field being typed in (preset, discard, reload): show the draft
  // again instead of the stale keystrokes.
  if (!Object.is(entry.value, value)) {
    text = displayNumber(value);
    setEntry({ value, text });
  }
  const error = sizingError(value, sizingKey),
    { min, max } = SIZING_BOUNDS[sizingKey];
  return (
    <div>
      <Label htmlFor={id}>{sizingLabel(sizingKey)}</Label>
      <Input
        id={id}
        type="number"
        min={min}
        max={max}
        step={0.1}
        disabled={disabled}
        value={text}
        aria-invalid={Boolean(error)}
        aria-describedby={id + "-note"}
        onChange={(event) => {
          const typed = event.target.value;
          const number = typed === "" ? NaN : Number(typed);
          const next = Number.isFinite(number) ? number : NaN;
          setEntry({ value: next, text: typed });
          onChange(next);
        }}
      />
      <p id={id + "-note"} className={error ? "field-error" : "small muted"}>
        {error}
      </p>
    </div>
  );
}

export function SubstratePresetPicker({
  id,
  volumeFieldId,
  litres,
  disabled,
  onPick,
}: {
  id: string;
  volumeFieldId: string;
  litres: number;
  disabled: boolean;
  onPick: (litres: number) => void;
}) {
  // A zone keeps its pot volume, not what fills the pot, and the volume cannot say: a 3.2 L coco
  // bag holds what a Rockwool Hugo block does. So a preset shows only while the volume is the one
  // it filled in here; any other volume, typed or saved, reads Custom.
  const [picked, setPicked] = useState<string | null>(null);
  return (
    <div>
      <Label htmlFor={id}>Substrate preset</Label>
      <select
        id={id}
        disabled={disabled}
        value={picked !== null && matchPreset(litres)?.id === picked ? picked : "custom"}
        aria-describedby={id + "-note"}
        onChange={(event) => {
          const preset = SUBSTRATE_PRESETS.find((item) => item.id === event.target.value);
          setPicked(preset?.id ?? null);
          if (preset) onPick(preset.litres);
          else document.getElementById(volumeFieldId)?.focus();
        }}
      >
        <option value="custom">Custom · type the pot volume</option>
        {SUBSTRATE_PRESET_GROUPS.map((group) => (
          <optgroup key={group.id} label={group.label}>
            {SUBSTRATE_PRESETS.filter((item) => item.group === group.id).map((item) => (
              <option key={item.id} value={item.id}>
                {presetLabel(item)}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <p id={id + "-note"} className="small muted">
        Nursery “trade” pots often hold less than their nominal gallons, and shot sizes are a
        percentage of this volume, so measure it if unsure.
      </p>
    </div>
  );
}
