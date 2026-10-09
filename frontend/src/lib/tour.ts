import type { Page } from "@/components/dashboard";

/** One stop of the first-run tour: the page it shows and what on it the words are about. */
export interface TourStep {
  id: string;
  /** The page it opens; null stays where it is. */
  page: Page | null;
  title: string;
  /** Plain words; **two asterisks** around a name the page shows. */
  text: string;
  /** What it points at: every element the first of these selectors finds, as one. None: nothing. */
  target: string[];
}

/** The tour: where things are, then how to switch the room on. A room without a reservoir has no
 * Reservoir page: Feed opens on its stock tanks, as the menu does. */
export function tourSteps(reservoir: boolean): TourStep[] {
  return [
    {
      id: "welcome",
      page: null,
      title: "Welcome to PHASE Steering",
      text: "It waters this room by itself, from your probes and your setpoints. Here is where everything is, in five stops. Skip it at any time: **Help** starts it again.",
      target: [],
    },
    {
      id: "overview",
      page: "overview",
      title: "Overview",
      text: "The room today: each zone's moisture against its targets through the grow day, every shot and why, the zones and the tank. Come here to see what the room is doing.",
      target: ["[data-day-timeline]"],
    },
    {
      id: "plan",
      page: "strategy",
      title: "Irrigation strategy",
      text: "Where you steer. **Today** sets each zone's targets for the four phases, from the morning dryback to the overnight one. **Schedule** moves them through the grow, more vegetative or more generative, week by week.",
      target: [".section-tabs button", ".page-heading h1"],
    },
    {
      id: "feed",
      page: reservoir ? "reservoir" : "stock",
      title: "Feed",
      text: reservoir
        ? "For a batch tank the controller looks after: its level and minimum, the feed recipes and when each is used, and the refills it mixes. **Stock tanks** keeps track of the concentrates that feed the dosers."
        : "For a batch tank the controller looks after: map its level sensor, solenoids and dosers in **Settings**, and its **Reservoir** page appears here. **Stock tanks** keeps track of the concentrates that feed the dosers.",
      target: [".section-tabs button", ".page-heading h1"],
    },
    {
      id: "settings",
      page: "setup",
      title: "Settings",
      text: "**Rooms & hardware** holds what this room is wired to: its valves, pump, probes and pot sizes. Its **Tests** give a zone a 10-second test shot, so you can see the water reach the drippers.",
      target: [".section-tabs button", ".page-heading h1"],
    },
    {
      id: "switch",
      page: "overview",
      title: "Switch it on",
      text: "When the probes read right and a test shot reaches the drippers, switch it on here. **Room** on means it is growing; **Watering** on lets the controller water it. Each switch shows what changes before it applies, and you can switch watering off again at any time.",
      target: [".page-heading .room-power"],
    },
  ];
}

/** `text` in pieces, every other one inside two asterisks: [plain, bold, plain, …]. */
export const textPieces = (text: string) => text.split("**");
