/**
 * Where a zone's moisture levels, taken together, do not do what each one says alone. Every probe
 * reads on its own scale, so no fixed number says a level is risky; what does is how the levels
 * sit against each other, as the controller uses them:
 *
 * - the ramp stops at the lower of the peak VWC target and field capacity (decide()'s ceiling);
 * - the maintenance trigger is kept at least 3 points above the rescue level and 1 point under
 *   that ceiling (controller._params), whatever is typed;
 * - overnight the substrate dries toward the P3 dryback target, a % below the day's peak, and a
 *   rescue level above where that ends stops the dryback early;
 * - by day it dries from the peak to the trigger before a maintenance shot.
 *
 * Advisory only: nothing here stops a value being saved.
 */

export interface ZoneLevels {
  /** p1_target_vwc */
  peak?: number;
  /** field_capacity */
  fieldCapacity?: number;
  /** p2_vwc_threshold */
  trigger?: number;
  /** p3_emergency_vwc_threshold */
  rescue?: number;
  /** The steering mode's P3 dryback target, % below the day's peak. */
  dryback?: number;
}

const known = (value: number | undefined): value is number =>
  value !== undefined && Number.isFinite(value);
const pct = (value: number) => `${Number(value.toFixed(1))}%`;
/** "a 30% dryback", "an 8% dryback": said aloud, 8, 11 and 18 start with a vowel. */
const a = (value: number) => (/^(8|11(?!\d)|18(?!\d))/.test(pct(value)) ? "an" : "a");

/** The warning for one setting (`param`, as its entity names it; a dryback target by either
 * mode's name), or null. */
export function levelWarning(param: string, levels: ZoneLevels): string | null {
  const { peak, fieldCapacity, trigger, rescue, dryback } = levels;
  const ceiling =
    known(peak) && known(fieldCapacity)
      ? Math.min(peak, fieldCapacity)
      : known(peak)
        ? peak
        : known(fieldCapacity)
          ? fieldCapacity
          : undefined;
  const ends = known(ceiling) && known(dryback) ? ceiling * (1 - dryback / 100) : undefined;
  // The peak the ramp aims for, named apart from the probe's own typical peak shown beside it.
  const top = `the ${known(ceiling) ? pct(ceiling) : ""} ${known(peak) && known(fieldCapacity) && fieldCapacity < peak ? "field capacity" : "peak target"}`;
  if (param === "p1_target_vwc")
    return known(peak) && known(fieldCapacity) && peak > fieldCapacity
      ? `the ramp stops at field capacity, ${pct(fieldCapacity)}, below this target`
      : null;
  if (param === "p2_vwc_threshold") {
    if (!known(trigger)) return null;
    const highest = known(ceiling) ? ceiling - 1 : Infinity;
    const bottom = known(rescue) ? rescue + 3 : -Infinity;
    const used = Math.max(bottom, Math.min(highest, trigger));
    if (used !== trigger) {
      const why =
        used === bottom
          ? "at least 3 points above the rescue level"
          : `1 point under the ${known(peak) && known(fieldCapacity) && fieldCapacity < peak ? "field capacity" : "peak VWC target"}`;
      return `the controller uses ${pct(used)}: it keeps the trigger ${why}`;
    }
    if (known(ceiling) && known(dryback) && ceiling > 0) {
      const daytime = ((ceiling - trigger) / ceiling) * 100;
      if (daytime > dryback)
        return `by day the substrate dries ${pct(daytime)} below ${top} before a maintenance shot, further than the ${pct(dryback)} it dries back overnight`;
    }
    return null;
  }
  if (param === "p3_emergency_vwc_threshold")
    return known(rescue) && known(ends) && rescue > ends
      ? `rescue shots would stop tonight's dryback at ${pct(rescue)}: ${a(dryback!)} ${pct(dryback!)} dryback from ${top} ends at ${pct(ends)}`
      : null;
  if (/(^|_)dryback_target$/.test(param))
    return known(rescue) && known(ends) && rescue > ends
      ? `from ${top} this dryback ends at ${pct(ends)}, below the ${pct(rescue)} rescue level, so rescue shots would stop it there`
      : null;
  return null;
}
