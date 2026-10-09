// How a schedule and Today share a room's targets, in the words both pages use. The rules are the
// integration's (strategy.py) and the controller's (strategy_runtime.py): an armed schedule takes
// over at the first lights-on after it is armed; while it runs, its targets for the day replace
// Today's for the zones it manages, and Today's numbers are never written; disarming hands back at
// the next lights-on, or at once when the schedule never started. A new schedule copies Today's
// targets once, when it is first made (_seed_plan); nothing flows between them after that.

/** The strategy's status, as the integration reports it; "manual" where there is no strategy. */
export type ScheduleStatus = "draft" | "armed" | "active" | "disarming" | "error" | "manual";

export const STATUS_NAMES: Record<ScheduleStatus, string> = {
  draft: "Not armed",
  manual: "Not armed",
  armed: "Armed",
  active: "Running",
  disarming: "Disarming",
  error: "Held",
};

export function scheduleStatus(value: string | null | undefined): ScheduleStatus {
  return value && value in STATUS_NAMES ? (value as ScheduleStatus) : "manual";
}

/** When a pending arm or disarm takes effect, as the integration reports it: "at Sat 07:00", or
 * "at the next lights-on" where it says nothing (an older integration, the demo). */
export function lightsOnText(iso: string | null | undefined): string {
  const time = iso ? new Date(iso) : null;
  if (!time || Number.isNaN(time.getTime())) return "at the next lights-on";
  const when = time.toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" });
  return `at the next lights-on, ${when}`;
}

/** What the status means for the room, on Schedule. */
export function scheduleMeaning(status: ScheduleStatus, at?: string | null): string {
  switch (status) {
    case "armed":
      return `Takes over from Today’s targets ${lightsOnText(at)}. Until then Today’s targets run the room.`;
    case "active":
      return "Running: its targets for the day replace Today’s. Today’s targets are kept, and run again once it’s disarmed.";
    case "disarming":
      return `Hands back ${lightsOnText(at)}. From then the room runs on Today’s targets again.`;
    case "error":
      return "Held: until the cause is cleared, its zones get only emergency and watchdog shots. Disarm and arm again once it’s fixed.";
    default:
      return "Today’s targets run the room. Saving this schedule changes nothing until you arm it.";
  }
}

/** Today's description while no schedule is armed or running. */
export const TODAY_IDLE =
  "The targets the room runs on, and their daily curve. A schedule takes over only once it’s armed.";

/** What an armed, running or held schedule means for Today's targets; null when there is none. */
export function todayMeaning(status: ScheduleStatus): string | null {
  switch (status) {
    case "armed":
      return "A schedule is armed. It takes over from these targets at the next lights-on; until then, changes here apply as usual.";
    case "active":
      return "A schedule is running, so the room follows its targets, shown below, not the ones set here. Yours are kept, and run again from the first lights-on after you disarm it.";
    case "disarming":
      return "The schedule hands back at the next lights-on. From then the room runs on the targets set here.";
    case "error":
      return "The schedule is holding its zones: until it’s cleared they get only emergency and watchdog shots.";
    default:
      return null;
  }
}

/** The four states in order, for the steps on Schedule. */
export const HOW_IT_WORKS: { status: ScheduleStatus[]; title: string; text: string }[] = [
  {
    status: ["draft", "manual"],
    title: "Not armed",
    text: "The room runs on Today’s targets. Saving the schedule changes nothing.",
  },
  {
    status: ["armed"],
    title: "Armed",
    text: "It takes over at the next lights-on. Until then Today’s targets run.",
  },
  {
    status: ["active", "error"],
    title: "Running",
    text: "From each lights-on, its targets for the day replace Today’s. Today is read-only.",
  },
  {
    status: ["disarming"],
    title: "Disarmed",
    text: "From the next lights-on the room runs on Today’s targets again, unchanged.",
  },
];

/** What takes priority, and what moves between them. */
export const PRIORITY_NOTES = [
  "While a schedule runs, it wins: for every zone it manages, the controller uses the schedule’s targets and its steering balance instead of Today’s targets and steering mode. Auto setpoints pauses.",
  "The schedule never changes Today’s targets. They stay as they are underneath, and run again once it’s disarmed.",
  "Changes made on Today never reach the schedule. A new schedule copies Today’s targets once, when it’s first made.",
  "A schedule sets the zones’ moisture levels, shot sizes, dryback, rescue level, EC targets and daily limits. Lights hours, P0’s additional dryback and the time between P2 shots stay as set on Today.",
];
