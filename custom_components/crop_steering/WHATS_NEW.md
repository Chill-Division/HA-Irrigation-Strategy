# What's new

The dashboard's **What's new** window shows these to the first person who opens the dashboard after
an update: every release since the last one it showed there, newest first, at most five. A new
installation has nothing to catch up on and shows none. **Help & tools → What's new** opens it
again at any time.

A change a grower would notice adds one line under `## Unreleased` at the top, in its own pull
request, and `scripts/release.py` dates them as the release. Write it for growers, not for the
people who build the system:

- **At most five short lines a release**, one for each change a grower would notice: what they can
  now do or see, in plain words, not how it was built.
- **No entity ids, error codes, file names, pull request numbers or code.** The release notes and
  the changelog keep the detail, and the window links to them.
- **Put the small things together** as one last line: `Bug fixes and improvements.` A release with
  nothing a grower would notice has only that line.
- Each line starts with `- `. The release command writes the heading,
  `## <version> - <release date, YYYY-MM-DD>`, and puts the small things last.

`tests/test_whats_new.py` checks the shape and the plain words, and that the newest section is the
version being released.

## Unreleased

- The first shot of the day now waits for the plants to drink a little after lights-on (3% unless you change it), not just for the clock.

## 2.27.2 - 2026-09-29

- Auto setpoints keeps a vegetative zone's maintenance shots going until 3 hours before lights-off, and says when the overnight dryback target is out of reach.

## 2.27.1 - 2026-09-28

- Maintenance shots now wait at least 5 minutes after the last shot so each can soak in; Time between P2 shots changes that.
- Bug fixes and improvements.

## 2.27.0 - 2026-09-28

- When Home Assistant refuses a change, the dashboard now says why.
- Each saved change to a room's setup now shows in Home Assistant's Activity, with who made it and what changed.
- Bug fixes and improvements.

## 2.26.3 - 2026-09-28

- A zone with more than one probe can read its moisture, and separately its EC, as their average, median, lowest or highest.

## 2.26.2 - 2026-09-28

- The vitals notification is shorter and says what each zone will do next; Settings can leave that out.

## 2.26.1 - 2026-09-28

- Put each stock tank on the doser its bottle feeds, and every batch the Reservoir mixes takes what that doser gave from it, by itself.
- A dryback target now reads "% below peak", so it is clear the substrate dries back by that much, not to it.

## 2.26.0 - 2026-09-27

- When the controller app stops for an update or a restart, the dashboard says so, and that it starts again by itself.
- The tank's EC and pH, and the feed-water limits that could hold watering, are gone.
- A new Reservoir page mixes your nutrient batches: it refills the reservoir, then runs each doser in turn, in the order you drag them into.
- Keep a feed recipe for each growth stage, with its ratio off the nutrient chart, and pick the stage each room is on.
- Bug fixes and improvements.

## 2.25.0 - 2026-09-27

- Each zone shows what it is waiting for next: the moisture or EC level that starts its next shot or phase.
- One switch in the zones heading turns every zone on or off, and switching a zone off now stops a shot already running.
- Water today can show per plant instead of per zone, on the dashboard and in the vitals notification: choose it in Settings.
- One watering switch per room: two older switches that did the same job are retired.
- Bug fixes and improvements.

## 2.24.0 - 2026-09-26

- Nothing is watered while the pump, main line or a zone's valve is offline: the zone waits, and says which switch is missing.
- A room switched back on within a day carries on where it left off.
- Move a zone to any phase by hand, from its details.
- Every irrigation setting has a plain name, and a ? that explains it.
- Bug fixes and improvements.

## 2.23.0 - 2026-09-25

- The grow-day chart shows how today is tracking: each phase's target, yesterday or a typical day, and the rest of today.
- Repairs cards link straight to what their message means and what to do.
- Bug fixes and improvements.

## 2.22.0 - 2026-09-25

- A Stock tanks page counts your nutrient concentrates down batch by batch, and warns before they run low.
- The Overview reads at a glance: how fast each zone is drying, water against its daily limit, and valves in colour.
- Water use for each zone: today, this week and the whole grow.
- The tank card graphs its EC and pH.

## 2.21.0 - 2026-09-25

- The Overview opens on today's grow day: every zone's phases, shots and holds on one chart, with the next shot estimated.
- A calmer look, with bigger text, and colour only where it means something.
