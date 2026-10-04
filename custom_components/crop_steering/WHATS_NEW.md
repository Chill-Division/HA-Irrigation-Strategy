# What's new

The dashboard's **What's new** window shows these to the first person who opens the dashboard after
an update: every release since the last one it showed there, newest first, at most five. A new
installation has nothing to catch up on and shows none. **Help → What's new** opens it again at
any time.

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

- Rooms & hardware is simpler: litres only, and no catch-test calculator.
- Two Nutrifield sizes are in the substrate presets.

## 2.35.2 - 2026-10-04

- Water per plant shows litres to two decimal places, such as 1.04 L, and whole millilitres below a litre.

## 2.35.1 - 2026-10-04

- The Overview's VWC and EC tiles are named for your probe choice, such as Lowest VWC.

## 2.35.0 - 2026-10-04

- A tidier Overview: each zone's predictions and the chart's key are a tap away, under the grow day.
- The dashboard opens in light mode; Settings → Appearance can still follow Home Assistant or go dark.
- No more Home Assistant title bar above the dashboard: the page starts at the top.
- Feed recipes can start from Athena or Front Row charts, and be saved to a file and imported.

## 2.34.0 - 2026-10-04

- The nutrients go in while the reservoir fills, so a refill is done when its fill time ends.

## 2.33.1 - 2026-10-04

- The Tank & pump card charts how full the reservoir has been over the last 12 or 24 hours.

## 2.33.0 - 2026-10-03

- The Tank & pump card shows the reservoir's refill and when it last refilled, straight from the controller, with nothing to map.

## 2.32.2 - 2026-10-03

- The reservoir level reads while the reservoir holds still, however long.

## 2.32.1 - 2026-10-03

- The reservoir level reads again when it holds steady for a while.

## 2.32.0 - 2026-10-03

- On a laptop, each zone's line on Today's grow day now wraps, so you can read all of it without pointing at it.
- A reservoir level sensor that stops reporting for 10 minutes counts as not reading, so no refill starts on an old reading.
- Each feed recipe sets the order its dosers run in, doses are whole millilitres, and 1 part can be set in mL.
- A feed schedule gives each week of the grow its own recipe, from the day Week 1 starts, and changes the stage by itself.
- Stock tanks need only a name, size, level, low mark and doser: each week's recipe says what a refill takes.

## 2.31.0 - 2026-10-03

- The reservoir never runs dry: a refill starts before the next shots would take it under its minimum, or watering waits there.
- Set the reservoir sensor's distances when full and empty, and the Reservoir page and the Overview show how full it is.
- A refill starts the pump half-way through the fresh water, doses as soon as it stops, and recirculates 10 seconds after.
- New Tests in Rooms & hardware: water one zone for 10 seconds, or run a refill (anyway, once you have checked it fits).

## 2.30.1 - 2026-10-01

- With Auto setpoints on, the morning dryback before the first shot is no longer skipped after a night that reached its dryback target.
- Today's grow day shows "Maintenance stopped" for the hours when Auto setpoints stops maintenance shots before lights-off.
- Bug fixes and improvements.

## 2.30.0 - 2026-10-01

- Overnight, a zone stops drying at your dryback target: a rescue-sized shot holds it there, where it used to dry on to the rescue level.
- Bug fixes and improvements.

## 2.29.2 - 2026-10-01

- Bug fixes and improvements.

## 2.29.1 - 2026-10-01

- Today's events say who changed a setting (you, Auto setpoints or an automation) and what it was before.
- The controller app's log is dated, names your rooms and zones, says what each zone is waiting for, and who changed a setting.

## 2.29.0 - 2026-09-30

- Set how long your pump runs before a zone's valve opens, for a pump that takes a few seconds to reach pressure.
- A shorter menu of six: pages that belong together are tabs, and the room and watering switches are on the Overview.
- Today's grow day chart is twice as tall, and how to read it is behind the ? beside its title.

## 2.28.0 - 2026-09-29

- The peak VWC target, maintenance trigger, field capacity and rescue level are used exactly as you set them, up to 100% (the rescue level up to 65%).
- Overnight, each zone's line on the Overview shows how far it has dried back from today's peak.
- The Irrigation plan points out moisture levels that work against each other, such as a rescue level that would cut the overnight dryback short.
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
