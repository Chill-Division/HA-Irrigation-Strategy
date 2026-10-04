/** The zone sizing fields: pot volume in litres and dripper flow in L/h, as the setup draft holds
 * them and the integration saves them. */
export type SizingKey = "substrate_volume" | "dripper_flow_rate";
/** Mirrors SIZING in custom_components/crop_steering/setup_api.py, in litres and L/h. */
export const SIZING_BOUNDS: Record<SizingKey, { min: number; max: number }> = {
  substrate_volume: { min: 0.1, max: 200 },
  dripper_flow_rate: { min: 0.1, max: 50 },
};
const FIELDS: Record<SizingKey, { name: string; per: string; unit: string }> = {
  substrate_volume: { name: "Pot volume", per: "per plant", unit: "L" },
  dripper_flow_rate: { name: "Dripper flow", per: "each", unit: "L/h" },
};

/** Display rounding only; never feed the result back into a draft. */
export const displayNumber = (value: number, digits = 3): string =>
  Number.isFinite(value) ? String(Number(value.toFixed(digits))) : "";
/** An entity's state as shown: a number to at most three decimals (an estimated-pwEC probe's
 * 0.639473676681519 reads 0.639), anything else as Home Assistant has it. Display only. */
export const stateText = (state: string, digits = 3): string => {
  const value = state.trim() ? Number(state) : NaN;
  return Number.isFinite(value) ? displayNumber(value, digits) : state;
};

export const sizingLabel = (key: SizingKey) =>
  `${FIELDS[key].name} · ${FIELDS[key].unit} ${FIELDS[key].per}`;
/** Review line: the value being saved. */
export const reviewValue = (value: number, key: SizingKey): string =>
  `${displayNumber(value)} ${FIELDS[key].unit}`;
/** Empty when the integration would accept the value. */
export function sizingError(value: number, key: SizingKey): string {
  const field = FIELDS[key],
    { min, max } = SIZING_BOUNDS[key];
  if (!Number.isFinite(value)) return `Enter the ${field.name.toLowerCase()} in ${field.unit}.`;
  return value >= min && value <= max ? "" : `${field.name} must be ${min}–${max} ${field.unit}.`;
}
