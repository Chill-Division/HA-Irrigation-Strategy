# Changelog

All notable changes to the Advanced Automated Crop Steering System will be documented in this file.

**Two views per release.** Each version leads with what changed and why it matters, written so
anyone can follow it without knowing the internals, followed by **🔧 Technical notes**, the entity-
and code-level detail for developers and AI agents working on the repo.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- **Pull requests start with what they change.** The pull request template's first section is
  "What", without the "In plain English" title the changelog dropped in 2.36.0.
- **Exports named for what they hold.** A plan exported from the Schedule saves as, for example,
  `crop-steering-plan-gr2-chill1.json` (the room and its profiles), and a recipe from the library
  as `crop-steering-plan-chill1.json`, where every file was `crop-steering-plan.json`.
- **No refill where none can run.** A room without a fresh-water solenoid, a recirculation solenoid,
  its pump and a doser no longer offers a refill by hand or a test refill. Its Reservoir page shows
  the tank's level, its minimum and whether watering would wait, without a refill's steps or
  automatic refills.

### 🔧 Technical notes

- CI: `.github/pull_request_template.md` opens with `## What` and its checklist asks for the
  changelog's summary, then its technical notes.
- Dashboard: `planFileName` (`frontend/src/lib/recipe-library.ts`) names the Schedule's export
  after the room and its profiles and a library recipe's after the recipe, each name once, cut at
  a word after 100 characters. The recipe-library browser check reads both names.
- Dashboard: `canRefill` (`frontend/src/lib/feed.ts`) mirrors the hardware the controller's
  `_batch_refusal` needs: `fresh_water_switch`, `recirc_switch`, `pump` and a doser. Without it the
  Reservoir page's batch panel drops Refill by hand and its note, the blocked line, the steps,
  Automatic refills, Last batch (with no record) and 1% holds (while unknown), and Settings →
  Rooms & hardware → Tests drops Test refill. A new browser check unmaps Flower 2's recirculation
  solenoid and checks both pages.

## [2.36.0] - 2026-10-04

Integration and controller **2.36.0**.

- **One branch.** Changes are merged into `main` and released from it; the separate `testing`
  branch is retired. Rooms are still offered an update only at a release.
- **Release notes start with what changed.** The heading that sat over each release's summary is
  gone, here and on the release page; the summary and the technical notes are as before.
- **No catch-test calculator.** Rooms & hardware no longer works out dripper flow from a catch
  test. Pressure-compensating drippers give a fixed flow: type the number on the dripper.
- **Litres only.** Pot volume is typed in litres and dripper flow in litres per hour; the US gallon
  and GPH choices are gone. Nothing saved changes: it was always kept in litres.
- **Two Nutrifield sizes in the substrate presets.** 0.9 gal (15 × 15 × 16 cm, 3.37 L) and 1.5 gal
  (18 × 18 × 18 cm, 5.8 L), under their own heading.
- **No separate tank level sensor.** The tank's level comes from the reservoir's level sensor, as
  the controller works it out, so the "Tank fill level (%)" mapping is gone. A room that had one
  mapped drops it the next time its setup is saved. Watering is not affected: the controller never
  read it.
- **The last batch names each nutrient, in the order it went in.** The Reservoir page reads, for
  example, "Balance 252 mL · Bloom 1,200 mL · Core 720 mL · Cleanse 120 mL" instead of doser
  numbers, at the amounts the recipe asked for. A dose that runs its time is recorded as exactly
  that amount: the moment the controller takes to switch a doser no longer reads as 1 mL more. A
  batch stopped part-way says what each nutrient gave and which never went in.
- **Fill and mix on one line on a computer.** On the Reservoir page the doses sit beside "Fill and
  mix" instead of under it, and "Fill" is as tall as it. A phone keeps them underneath.

### 🔧 Technical notes

- Docs: `CONTRIBUTING.md`, `docs/RELEASING.md` and `CLAUDE.md` describe one long-lived branch,
  `main`. Pull requests target it, and `release.py` releases it once Validate has passed on the
  last merge, with no fast-forward from `testing` and no push back to it. A controller built
  between releases (a fresh install, a Rebuild) builds what is merged on `main` then, under the last
  released number, so merges are made close to releasing. An assistant merges a pull request or
  runs the release command only when the owner asks, each time.
- CI: the pull request template says a pull request goes into `main`, and the comment on
  Validate's `main` trigger no longer mentions `testing`.
- Docs and release tooling: the changelog's summary has no heading of its own, taken out of every
  entry. `scripts/release.py` refuses an Unreleased section with no `- ` line before
  `### 🔧 Technical notes`, and `scripts/release_notes.py` publishes an entry up to that heading.
  `CLAUDE.md` and `docs/RELEASING.md` say so.
- Dashboard: `CatchTestCalculator` and `frontend/src/lib/catch-test.ts` are removed, with their
  styles, unit tests, browser check and the user guide's paragraph. The substrate-preset browser
  check now runs the accessibility scan of the zone's sizing helpers that the catch-test check ran.
- Dashboard: the sizing unit pickers, their US gallon and GPH conversions and the per-browser
  choice are removed (`crop-steering-unit-volume` and `-flow` in local storage are no longer
  read). `SizingField`, `sizingError` and `reviewValue` take litres and L/h only, with their unit
  tests and two browser checks trimmed to match.
- Dashboard: `SUBSTRATE_PRESETS` gains a Nutrifield group, each size at its stated volume (3.37 L
  and 5.8 L) beside its outer dimensions, which alone would make the smaller one 3.6 L.
- Integration: `water_level_sensor` leaves `HARDWARE_DOMAINS`, the wizard, Configure and the room
  descriptor; it joins `RETIRED_HARDWARE`, so a stored value goes on the room's next save, and a save
  naming it is refused as an unknown field. The controller's setup fingerprint never read it.
  Dashboard: the tank card's level and chart come only from `reservoir_distance_sensor` with the
  feed plan's `full_mm` and `empty_mm` (the level reads "Not set up" without them, "Not mapped"
  without the sensor); history is allowed for that sensor alone, and the demo loses its % sensors.
- Controller: `_batch_given` records a dose that has run its planned time as the recipe's mL; it
  had counted from just before the doser switched on to when it switched off, up to 5 s over. One
  stopped sooner gives its share. `batch_status.last` gains `doses` (each `doser`, `label`, `ml`
  and `given`, null when not reached, in dosing order) from `_batch_doses`; `dosed` stays for the
  stock tanks. CS-701 names what was given by nutrient. Dashboard: `lastBatchWords` words it, with
  doser numbers for a record from an older controller.
- Dashboard: above 900 px the Reservoir page's steps (`.res-steps`) keep to one line, stretched to
  the tallest, and the mixing half (`.res-steps-group`) puts its doses in a third grid column beside
  its name; only the doses give way, wrapping inside it. At 900 px and under nothing changes.

## [2.35.2] - 2026-10-04

Integration and controller **2.35.2**.

- **Water per plant in litres to two decimal places.** From a litre up, water per plant reads in
  litres to two places, so 1.04 L reads **1.04 L**, not 1 L; below a litre it stays in whole
  millilitres (**980 mL**). The Overview, a zone's details, the Water page and the controller's
  notification all show it the same way, and 999.6 mL now reads 1.00 L instead of "1,000 mL".
  Zone totals are unchanged.

### 🔧 Technical notes

- Dashboard: `plantAmount` (`frontend/src/lib/water-view.ts`) returns the figure as text, whole mL
  below a litre and litres with exactly two decimals from one up, choosing by `Math.round(ml)` so
  the mL as shown decide; `plantText` is the same in words, shared by the Overview, zone details
  and the Water page's per-plant note, which showed whole mL even above a litre.
- Controller: the vitals notification's water per plant reads as the dashboard does,
  `1.26 L/plant day` from `round(ml)` of 1000 up. Tests: `water-view.test.ts`,
  `verify-dashboard.mjs` and `test_vitals_water.py`.

## [2.35.1] - 2026-10-04

Integration and controller **2.35.1**.

- **Light screenshots.** The README's and the screenshots page's pictures are light, as the
  dashboard now opens, with three from a phone: the Overview, the Reservoir and today's targets.
- **The Overview's VWC and EC tiles say how they are read.** A room of one zone shows that zone's
  reading named for its probe choice: a zone reading its lowest probe shows **Lowest VWC**, where
  it said Average VWC. Several zones show their average, named for the choice they share
  (**Average lowest VWC**). A zone with one probe has no choice to make, and zones that choose
  differently show **Average VWC** as before. Moisture and EC each follow their own choice.

### 🔧 Technical notes

- Docs: every README and `docs/SCREENSHOTS.md` image is retaken light. The browser checks that run
  dark take their README images through `frontend/scripts/light-shot.mjs` (the device made light
  for the screenshot, then dark again); `verify-workspace.mjs`'s Overview, Schedule and Rooms &
  hardware images, and the new `mobile-reservoir.png` and `mobile-plan.png`, come from a light check
  of their own, its Home Assistant dark-palette pages now only in `output/`. The README's images
  load from `ChillingSilence/HA-Irrigation-Strategy` until the public repository exists.
- Dashboard: `readingTile` (`frontend/src/lib/probes.ts`) names the room's VWC and EC tiles from
  each zone's `ProbeChoice`. One zone's is `<method> VWC`; several zones' is
  `Average <method> VWC` when every zone with two or more probe readings uses that method, else
  `Average VWC`. `buildRoom` builds both tiles with it; their values and Range captions are
  unchanged. Tests: `probes.test.ts` (the names, and the demo's room with three zones and with
  one) and `verify-dashboard.mjs` (the tiles once zone 1's moisture reads its lowest probe).

## [2.35.0] - 2026-10-04

Integration and controller **2.35.0**.

- **A tidier Overview.** On Today's grow day, each zone's chart has just its phase and moisture now
  above it; how it is tracking against yesterday, its targets, the water so far and what comes next
  are behind **Predictions**, and the chart's key is behind the **?**, both at the right of Today's
  events. A zone's last irrigation reads on one line: how long ago, and the time.
- **Compact dosers.** On the Reservoir page each doser is a small card, like the schedule's weeks:
  what it pumps in the stage in use and its flow, side by side instead of a row each across the
  page, with what they mean behind a **?**.
- **Light by default.** The dashboard opens light, whatever the device is set to. **Settings →
  Appearance** can still follow Home Assistant's theme (or the device's, outside Home Assistant) or
  stay dark: each browser keeps its own choice, and one already made is kept.
- **No Home Assistant title bar above the dashboard.** The dashboard is now a custom panel, so Home
  Assistant no longer draws its black "Crop Steering" bar above it, and the page starts at the top.
  The house button in the dashboard's top bar opens Home Assistant's sidebar, as before.
- **Feed recipes to start from, and recipe files.** A new feed recipe can start from Athena's Grow,
  Bloom or Fade as Chill Division runs them (240 mL a part), or from Front Row's 3-2-2 stock
  concentrate chart at high strength (Veg, Stretch, Stack, Swell and Ripen, each also with Triologic
  or with BioFlo, and Front Row Si as the pH up). Each nutrient goes on the doser your recipes
  already give it, and a note says where any went that no recipe names. Each recipe can be saved to
  a file and imported, in this room or another, as strategies can.

### 🔧 Technical notes

- Dashboard: `tracking` returns the zone line's phase and VWC now (shown above its chart, with the
  whole line as its tooltip) and the rest, which a Predictions popover lists a paragraph per zone.
  The key (`TimelineKey`, with its layer switches) and the "how to read this chart" note move from
  under the chart and beside the title into a popover behind a **?**; both popovers carry the
  `day-timeline` class so the key keeps its colours outside the panel. `LastIrrigation` shows the
  relative time and the time (or day and time) on one line, the full timestamp as its tooltip.
- Dashboard: the Reservoir page's dosers are small cards in a wrapping grid (each its number, what it
  pumps in the stage in use, and its flow in mL/min, with its switch's entity id as its tooltip); the
  note under them is a **?** popover beside the heading, reworded. Popovers space their paragraphs.
- Dashboard: with no appearance saved in the browser (`irrigation-theme`), the dashboard is light
  (`themePreference` defaults to `light`, not `auto`); Appearance's options are Home Assistant, Light
  and Dark, in one row on a laptop. The browser checks that emulate a dark device save `auto` first
  where nothing is saved, so they still check the dark theme and the README's dark screenshots stay.
- Integration: `setup_panel` registers the sidebar panel as a custom panel (component `custom`, its
  `_panel_custom` the module `/crop_steering/panel.js?v=<version>` and the element
  `crop-steering-panel`, not embedded in a frame of its own) instead of the built-in iframe panel,
  whose `hass-subpage` draws a title bar. Its URL path, `/crop-steering`, is the same. The element
  (`www/panel.js`) holds the dashboard in a frame the size of the panel, less the safe-area padding
  Home Assistant puts around a custom panel, so the dashboard finds Home Assistant through its frame
  as before: its kiosk event and its house button work unchanged.
- Dashboard: `feed-library.ts` holds the templates (Athena, Chill Division modified: `partMl` 240,
  the strength worked out from the room's fill litres; Front Row 3-2-2 high strength from its
  231226 metric V3 chart at 1 mL per litre a part, Triologic 0.26 and BioFlo 8 mL/L variants),
  `placeRecipe` (each nutrient on the doser the room's recipes most give it, Front Row Si also by
  Power Si or Si; others on free dosers, an unnamed or Empty one first; none free, left out;
  `uniqueName` within 40 characters) and the recipe file (`crop-steering-feed-recipe` version 1:
  name, strength and nutrients by name in dosing order; `importRecipe` checks it as `feed_save`
  would). The Reservoir page's Feed recipes have a "Start from" list beside Add a feed recipe,
  Import recipe file, a note on where the nutrients went, and an export button on each recipe. The
  nutrient suggestions add Front Row Si, Triologic and BioFlo. No change to the integration: a
  recipe saves as before.
- Docs: the user guide's Overview; the Overview screenshot.
- Docs: the user guide's feed recipes, their templates and recipe files.
- Tests: the grow-day browser checks read the zone lines and the key through their popovers, and
  check the key's popover on a dark theme.
- Tests: the templates (each saves as `feed_save` takes it; Athena 240 mL a part at any fill),
  placing a recipe on a room labelled as GR2, unique names, and the recipe file's round trip and
  refusals; a browser check adds a template, exports it and imports the file.

## [2.34.0] - 2026-10-04

Integration and controller **2.34.0**.

- **The nutrients go in while the reservoir fills.** A refill used to run its fresh water for the
  whole fill time and only then dose each nutrient, so it took the fill time and the doses on top.
  Now, half-way through the fill, once the pump and recirculation are running, the doses go in one
  after another while the fresh water still runs, and the tank keeps circulating until the fill ends:
  a refill is done when its fill time is (11 min 30 s for a 690 s fill). If a recipe's doses take
  longer than the fill's second half, the rest go in after the fresh water stops, and the Reservoir
  page says so. On the Reservoir page the doses now sit inside Fill and mix.

### 🔧 Technical notes

- Controller: `_batch_step` switches the fresh water off at the fill's end (`fill_end`, cleared once
  it reads off) whatever the step. At half-way, `filling_mixing` lasts one `pause_s` before the first
  dose, and after the last dose `mixing` runs until the fill's end and at least `mix_s`.
  `batch_timed` (a timed step, or any step while the fresh water runs) decides what holds other
  rooms' shots and what the between-pass watch checks, and `_sleep_for` also wakes at the fill's end.
  `_batch_interrupted` and `_batch_stop` keep and switch off the fresh water while it runs, so a
  refill stopped mid-dose stops it too. `batch_status` gains `fill_until`. No new options; no change
  to the state file (a refill saved in progress is switched off at the next start, as before).
- Integration: `feed.py`'s description of a refill.
- Dashboard: the Reservoir page shows the doses inside Fill and mix, and Recirculate only when the
  doses outlast the fill, with a line saying so; the settings' help says when the doses go in. The
  demo's refill starts with the fill's first half.
- Docs: the user guide's refill; `batch_status` in the entities; the Reservoir screenshot.
- Tests: the doses go in while the fresh water runs and the refill ends with the fill; doses that
  outlast the fill go on after the fresh water stops on time, and the loop wakes for it; a refill
  stopped mid-dose stops the fresh water too; other rooms wait while the fresh water runs, not once
  the fill has ended; `fill_until` on the status sensor.

## [2.33.1] - 2026-10-04

Integration and controller **2.33.1**.

- **The tank card charts the reservoir's level.** Beside the tank, the Tank & pump card shows how
  full it has been over the last 24 hours, or 12: a refill as a jump, each round of shots as a step
  down, and the reservoir's minimum as a dashed line. The tank's temperature, where a sensor is
  mapped for it, moves into the tank as a small line under how full it is, and is left out where
  none is, instead of reading "Not mapped".
- **Less text on the tank card.** Its footnote ("Pump is the switch's report, not measured flow…")
  is gone.

### 🔧 Technical notes

- Dashboard: `TankLevelChart` (`tank-level-chart.tsx`) reads `controller.history` for the level
  sensor the card reads (`reservoir_distance_sensor`, worked out with the feed plan's full and empty
  distances as `level_pct` is, or `water_level_sensor` in %), 12 or 24 hours, and again every 10
  minutes while the page is visible. `levelSeries` draws it in 144 steps, each the middle reading
  recorded in it or the level held (Home Assistant records changes), ending on the card's level now.
  `controller.history` also allows the room's own mapped level sensors (its descriptor's
  `reservoir_distance_sensor` and `water_level_sensor`), not another room's. The temperature is a
  line in the tank drawing, whose words have a halo so the waterline passes behind them. The demo
  records a reservoir level with a refill and rounds of shots. No change to the integration or the
  controller.
- Dashboard: the tank card's footnote (`.tank-note`) is removed.
- Docs: the user guide's tank section; the screenshot.
- Tests: `levelSeries` (distance and % sensors, a step's middle reading, the level held through
  steps with no reading, the level now at the end), the card's level source, and history limited to
  the room's own level sensors; the tank browser check covers the chart, its 12 h and 24 h buttons,
  Flower 1's % sensor, and the Overview staying within two screens at 1440×800.

## [2.33.0] - 2026-10-03

Integration and controller **2.33.0**.

- **The tank card's refills come from the controller.** The Overview's Tank & pump card showed
  "Filling" and "Last fill" only from two Home Assistant sensors you had to map, so most rooms read
  "Not mapped" there. It now shows the controller's own record of the reservoir refills it runs:
  **Refill** says what the refill is doing now (not running, filling, dosing, mixing), and **Last
  refill** when the last one ended, and whether it stopped part-way. A room without a reservoir has
  neither row. The two mappings are gone from Rooms & hardware and from Configure.

### 🔧 Technical notes

- Integration: `tank_fill_entity` and `tank_last_fill_sensor` are removed from the setup API
  (`HARDWARE_DOMAINS`, `HARDWARE_WORDS`, the last-fill timestamp check), the wizard and Configure
  (`_hardware_schema`, `_build_hardware`, strings) and the room descriptor (`build_engine_config`).
  Setup candidates no longer list `binary_sensor` and `input_datetime` entities, which only those two
  used. A value an older setup stored stays in its config entry, unread; the controller's setup
  fingerprint never read either.
- Dashboard: the tank card's **Refill** and **Last refill** read
  `sensor.crop_steering_<prefix>batch_status` (its step, and `last.at` and `last.result`), for a
  room with a reservoir mapped or a batch status reported; "Unavailable" until the controller
  reports. The demo drops its two fill entities. Two code comments that still described 2.32.0's
  10-minute level rule are corrected.
- Docs: the user guide's tank section (and its paragraph on the tank and feed EC/pH mappings that
  2.26.0 removed), the install guide, and the screenshot.
- Tests: the lean setup and Configure tests drop the two mappings; the tank telemetry tests and the
  tank browser check cover the refill rows, and that a room without a reservoir has none.

## [2.32.2] - 2026-10-03

Integration and controller **2.32.2**.

- **The reservoir's level reads while it holds still, for real this time.** 2.32.0 counted a level
  sensor that had not reported for 10 minutes as reading nothing, and 2.32.1 only fixed how that
  was read. But Home Assistant's ESPHome integration drops a reading that repeats the last one, so
  an ultrasonic over a still reservoir, reading the same distance every few seconds, looks to Home
  Assistant as if it had stopped: GR2's level read "No reading" for hours. That rule is gone. The
  level reads nothing only when Home Assistant has no reading at all (unavailable or unknown). To
  have an ultrasonic whose echoes fail show as unknown, give it ESPHome's `timeout` filter (the user
  guide says how).

### 🔧 Technical notes

- Controller: `_level_now` is `level_mm(ha_get(...))` again: `LEVEL_STALE_S`, `ha_reported` (the
  template API call) and `HAState.last_reported` are removed. Home Assistant's ESPHome integration
  ignores a state that repeats the last unless the sensor has `force_update`, so neither
  `last_updated` nor `last_reported` tells a steady sensor from a silent one. CS-705's text is as it
  was before 2.32.0. No new options; no change to the state file.
- Dashboard: CS-705's help (Help page) names a timeout filter's unknown as a cause and says to add
  one; the Reservoir page, the Tests dialog and the tank card still take the controller's level.
- Docs: the user guide on still reservoirs and ESPHome's `timeout` filter; entities.
- Tests: a reservoir whose level has not changed for three hours reads, through the cached REST
  JSON of a real Home Assistant and in the add-on suite, and one reading unknown or unavailable does
  not.

## [2.32.1] - 2026-10-03

Integration and controller **2.32.1**.

- **The reservoir's level reads again while it holds steady.** 2.32.0 counted a level sensor that
  had not reported for 10 minutes as reading nothing, but it judged that from a copy Home Assistant
  does not renew while a sensor keeps reporting the same value: a level that held steady for 10
  minutes (no shots drawing on it) read "No reading", a refill asked for by hand was refused, and
  the next shot was not held at the minimum. The controller now asks Home Assistant when the sensor
  last reported, so only one that has really stopped counts as reading nothing.

### 🔧 Technical notes

- Controller: `ha_reported(entity)` reads `last_reported` live, rendering
  `states.<entity>.last_reported` through Home Assistant's template API (`POST /template`), for the
  level sensor's id only. The REST state's `last_reported` cannot be used: Home Assistant serves a
  state's cached JSON (`as_dict_json`), and a same-value report moves `last_reported` on the state
  without renewing it. `_level_now` uses `ha_reported`; when it can't be told (the template API
  refused, or no such entity), the reading stands, as before 2.32.0. No new options; no change to
  the state file.
- Tests: in a real Home Assistant, the controller is served the cached REST JSON and the template
  rendered by Home Assistant's own engine: after a same-value report the REST copy keeps the old
  `last_reported` while `ha_reported` gives the new one, and a sensor unchanged for 18 minutes but
  reported 9 minutes ago still reads. The add-on suite covers the template call, its refusals and
  the reading standing when the last report can't be told.

## [2.32.0] - 2026-10-03

Integration and controller **2.32.0**.

- **Each zone's line on Today's grow day wraps on a laptop too.** On a wide screen it stopped at
  the edge with "…", and the rest was only in its tooltip; now all of it shows, as on a phone. A
  room with several zones can make the Overview a little taller.
- **A level sensor that stops reporting is not trusted.** An ultrasonic that filters out its
  failed echoes keeps showing its last good value in Home Assistant. Once the reservoir's level
  sensor has not reported for 10 minutes it counts as reading nothing: no refill starts on that old
  value, by itself or asked for; a refill already filling stops half-way, before the pump runs; and
  after 5 more minutes a notice says so. The Overview and the Reservoir page show no reading too.
- **Each feed recipe doses in its own order.** A stage can use a doser the others leave out (the
  Fade bottle's doser in place of Core's, in the Fade weeks): drag a recipe's rows into the order
  they dose. The Dosers section keeps only each doser's flow. A recipe saved before this keeps the
  order the room had.
- **Whole millilitres, and what 1 part is.** Doses are to the whole mL, which is as fine as a doser
  gives, so 3 and 5 parts of 240 mL read 720 and 1,200 rather than 719.9 and 1,199.9. Beside a
  recipe's mL per litre per part, **1 part** sets the same as mL of nutrient in each fill, and the
  recipe says what that gives (Bloom: 5 × 240 = 1,200 mL).
- **A feed schedule by week.** Strains differ (a week or three of veg, eight or ten of flower), so
  each grow gets its own: the day Week 1 starts, its number of weeks and each week's recipe (Week 1
  Vege, Weeks 2–6 Bloom, Weeks 7–8 Fade). The stage in use changes by itself at midnight as each week
  starts, and the next refill doses that week's recipe; after the last week, its recipe carries on. A
  stage picked by hand while it runs holds only until the next week starts, and the page says so;
  removing the schedule keeps the stage in use as it was.
- **Stock tanks are just the bottles.** A stock tank is its name, capacity, level, low mark and the
  doser it feeds: how much a refill takes from it is the recipe's, week by week, so it is no longer
  set on the tank. Each refill the Reservoir mixes takes what that doser gave; the card shows what
  this week's recipe takes and about how many refills are left. "Record a batch", the dose per batch,
  the dose entity and counting batches from the tank's fill time are gone: every batch is the
  Reservoir's.

### 🔧 Technical notes

- Dashboard: `.timeline-zone-line` is no longer `nowrap` with an ellipsis at 1024 px and wider.
  The Overview's two-screen browser checks (`verify-dashboard.mjs`, `verify-tank-status.mjs`) leave
  what the zone lines add by wrapping out of the height they measure.
- Controller: `ha_get` keeps Home Assistant's `last_reported` (`HAState.last_reported`).
  `_level_now` reads the level sensor as nothing once its `last_reported` (else `last_updated`) is
  older than `LEVEL_STALE_S` (600 s), for the pass's reading (`_reservoir_reading`), the half-way
  check and learning what 1% holds. CS-705's text says it. `batch_status`'s `level_mm` and
  `level_pct` are then null.
- Dashboard: once the controller publishes `batch_status`, the Reservoir page, the Tests dialog and
  the Overview's tank card take its level (null = no reading) rather than the sensor's own state.
- Error codes: CS-705's meaning and causes name a sensor that stopped reporting.
- Integration (`feed.py`): each recipe has `order`, its dosers in the order they dose, checked like
  the room's; one stored or sent without it takes the room's `order`, which is kept for that.
  `plan()` doses in `recipe_order(stage, mapped)` and gives each dose's `ml` to the whole mL
  (`whole_ml`, halves up). No change to the controller: it doses in the plan's order.
- Dashboard: a recipe's rows drag (or move with arrows) into its order, each with its turn; the
  Dosers section keeps each doser's flow. **1 part (mL)** beside the strength sets the strength from
  mL of nutrient per fill (`partMl`); doses and totals show whole mL. `doseOf` and `planOf` round as
  `feed.py` does.
- Tests: whole mL (the owner's 1.655 mL/L per part in 145 L gives 720 and 1,200), a recipe's own
  order (Fade's doser in place of Core's), a recipe without an order taking the room's; in a real
  Home Assistant, a feed document stored by 2.31 loading in place with each recipe in the room's
  order, and a recipe saved with its own order changing the plan sensor's order.
- Integration (`feed.py`, `feed_api.py`): the feed document gains `schedule` (`start`, the day Week 1
  starts, and `weeks`, a recipe id each, at most `MAX_WEEKS` = 52, each a recipe the room has) and
  `held_until`; one stored before them loads with no schedule. `schedule_week`, `held`, `in_use` and
  `pick` give the stage in use; `plan(doc, mapped, today)` doses it and adds `week`, `weeks`,
  `schedule_start`, `held_until` and `source`. The store's `today()` is Home Assistant's date;
  `start()` rewrites the plan sensor and the stage select at its midnight
  (`async_track_time_change`), and the select picks through `pick`. Stock tanks read the stage in
  use. No change to the controller: it doses the plan's stage, as before.
- Dashboard: the Reservoir page's Feed schedule (the day Week 1 starts, the number of weeks, a recipe
  for each week, this week marked); the stage in use follows it, and one picked by hand says until
  when it holds. `scheduleWeek`, `inUse`, `pickStage` and `removeSchedule` mirror `feed.py`.
- Tests: the schedule's weeks (the owner's example), a pick held until the next week, the checks, an
  old document with none; in a real Home Assistant, the plan sensor and the select moving on at the
  midnight that starts a week, a pick in the select holding until then, and a document stored before
  the schedule loading with none; the dashboard's helpers and a browser check.
- Integration (`stock.py`, `stock_api.py`): a tank is `name`, `capacity_l`, `level_l`, `doser` and
  `low_l` (with its id and times); `dose_ml` and `dose_entity` are gone, and a tank stored with them
  loads with the rest. `doses()` is what the feed plan in use gives from each tank's doser (0 on
  none). The store counts only the Reservoir's batches (`batch_status`'s `last`): `_fill`,
  `new_batch`, `dose_ml()`, `last_batch` and the `stock_record_batch` service are removed. The
  stock sensor's `last_batch` is the newest batch in the history.
- Dashboard: the stock tank editor has no dose per batch or dose entity, and the page no "Record a
  batch"; a card says "On no doser" when it is on none. The demo's tanks are Athena's on its four
  dosers.
- Tests: the model and the store without the per-batch amount (an old tank loading with the rest,
  the batches left from the recipe, no batch by hand); in a real Home Assistant, the low card and a
  refill, the service gone, the Reservoir's draws with the sensor's dose and batches left, and stock
  tanks stored by 2.31 loading in place.

## [2.31.0] - 2026-10-03

Integration and controller **2.31.0**.

- **The reservoir never runs dry.** A pump that does not prime itself stops working once its
  reservoir runs dry, so the reservoir now keeps a minimum (5% unless you change it; 0 turns it
  off). The controller plans ahead: once the room's next round of shots would take the reservoir
  under it, a refill starts, between shots. In the middle of a P1 ramp that is right after the shot
  before, since the next is bigger; once the ramp is done it plans for P2's shot. A shot that still
  would not fit waits for the refill. With automatic refills off, watering waits at the minimum and
  a notice says so until the reservoir reads enough again.
- **The level is a percentage.** Set the level sensor's distance to the water when the reservoir is
  full and when it is empty (an ultrasonic sensor on the lid reads further as it empties), and the
  Reservoir page and the Overview's tank card show how full it is, worked out as an ESPHome template
  would. Each refill shows how much 1% holds: its fill litres over how far the level rose.
- **A refill runs the way it should.** The fresh water runs for its fill time; half-way through,
  once the level shows it is filling, the pump starts through the recirculation line; as soon as
  the fresh water stops each doser runs in turn, 10 s apart, and it recirculates 10 s more before
  the pump stops. A refill that is not filling half-way stops before the pump runs from it. "Batch
  size" is now "Fill litres": the litres the fill adds, which the doses are worked out for.
- **Safer by hand.** A refill asked for by hand runs only when its fill fits under 100%, and the
  controller app's log says which room's refill other rooms are waiting for. If the level sensor
  reads nothing for 5 minutes, watering carries on and a notice says so.
- **Tests.** At the bottom of Settings → Rooms & hardware, **Tests** checks a room's hardware: a
  **test shot** waters one zone for 10 seconds, and a **test refill** refills and mixes the
  reservoir. Each goes through the controller app's usual checks, and its log says how it went. A
  test shot's water counts toward the zone's day, but it is not one of the day's shots, so a ramp
  does not move on for it. A refill the controller would refuse as one that could overflow can be
  **run anyway** by someone who has checked that it fits. The Reservoir page's "Mix a batch now"
  moved there: **Refill by hand…** opens it.

### 🔧 Technical notes

- Integration (`feed.py`): the feed settings gain `full_mm` and `min_pct` (5); `empty_mm` is the
  distance when empty (a stored "almost empty at" mark loads as that); `settle_s` is gone (a stored
  one is dropped); `mix_s` defaults to 10. `full_mm` must be less than `empty_mm`. The feed plan
  sensor carries them.
- Engine: `next_shot_size(s, p)`, the size of a zone's next routine shot as `decide()` would size
  it now (P0/P1 the next ramp shot, or P2's once the ramp is done; P2 maintenance; P3 rescue-sized).
  The vendored copy follows.
- Controller: `level_pct` from the distance sensor and the plan's distances. `_plan_next_round`
  (end of each pass: every zone's `next_shot_size` in litres of its substrate) and `_refill_due`
  (the level less that round, or what waits, in % once `litres_per_pct` is known; the level alone
  before) start an automatic refill after `BATCH_LOW_PASSES`. `_reservoir_block` holds a shot that
  would take the reservoir under `min_pct` (with this pass's `_drawn_l`): it waits for a refill, or,
  with none coming, raises CS-704. The fill runs in two steps, `filling` and `filling_mixing` (the
  line, then the pump, at half-way once the level rose `FILL_RISE_PCT`, else CS-702), then doses
  with no settle; `settling` is still known in a saved record. `_learn_litres` averages each full
  refill's `batch_l` over its rise (at least `LEARN_RISE_PCT`) into `litres_per_pct`, saved with
  the batch record (`restore_batch` tolerates its absence). `_fill_overflow` refuses a fill that
  would not fit (`UNLEARNED_FILL_FROM_PCT` before one is learned). CS-705 after
  `LEVEL_MISSING_PASSES` without a reading. `batch_status` adds `level_pct`, `full_mm`, `min_pct`,
  `litres_per_pct`, `due` and `next_round_l`. Hold text: "refilling its reservoir (…)" and
  "waiting for <room>'s reservoir refill (…)".
- Error codes: CS-701 to CS-703 reworded, CS-704 (watering held, reservoir too low) and CS-705
  (reservoir level not reading) added; `docs/error-codes.json`, `docs/ERROR_CODES.md`, Help.
- Dashboard: the Reservoir page shows the level, the minimum and what 1% holds, the steps Fill,
  Fill and mix, each dose, Recirculate, and checks a refill asked for by hand as the controller
  does (`fillRefusal`); the settings take both distances (each with "Use the reading now") and the
  minimum. The tank card shows the reservoir's own level once its distances are set.
- Docs: `docs/USER_GUIDE.md`, `docs/ENTITIES.md`, `docs/SYSTEM_OVERVIEW.md`, `README.md`,
  `CLAUDE.md`, the Reservoir screenshot.
- Tests: the add-on's batch suite rewritten for the new sequence, the level, learning, the
  overflow guard, planning ahead (mid-P1, the P1 to P2 handover, P2, P3, no probe), the shot
  backstop and both notices, with a whole-pass test; `next_shot_size` against `decide()`; the feed
  settings; in a real Home Assistant, the settings reaching the real controller as a level, and a
  feed document stored by 2.30.1 loading in place; dashboard tests and browser checks.
- Integration (tests): a Test Shot button per zone, on the zone's device,
  `button.crop_steering_<prefix>zone_N_test_shot`; `crop_steering.test_shot` (`room_id`, `zone`;
  administrator, response-only, `selftest.py`) presses it. `feed_mix` takes `force`: for `FORCE_S`
  (120 s) the feed plan sensor carries `mix_force_until`, written before the press. An upgraded room
  gains the buttons, unpressed.
- Controller: `_test_shot` turns a new press into this pass's decision for the zone, a `TEST_SHOT_S`
  (10 s) shot of kind `test_shot` (in `PLAN_HOLD_EXEMPT`), through `_blocked`, `_reservoir_block`
  and the daily limit; the first state seen is a starting point (kept in memory, not in the state
  file), and a press older than `TEST_REQUEST_S` is not run. `_advance_shot_counters(steering=False)`
  counts its water (`daily_vol`, `last_shot`) but not `shots`, and skips `auto_setpoints.shot`. Its
  status label is `Test shot`; `log_words` names it. `_mix_forced`: a Mix a Batch Now press up to
  `MIX_FORCE_S` before the plan's `mix_force_until` skips `_fill_overflow`'s fit checks ("asked for,
  run anyway"), not its refusal of a level that reads nothing, which the half-way check would stop. CS-702, CS-703 and CS-704 point to the test refill.
- Dashboard: the Tests section (`room-tests.tsx`) on Rooms & hardware, for the room in use and a
  saved configuration; the Reservoir page's "Refill by hand…" opens it (`#/setup?tests`). `test_shot`
  is a room-scoped action, in the demo too, and a fired test shot is labelled "Test shot".
- Docs: `docs/USER_GUIDE.md` (Tests), `docs/ENTITIES.md`, `docs/ERROR_CODES.md`, `CLAUDE.md`.
- Tests: the add-on's test shot (sized, counted, held, stale, plan-held) and run anyway (its window,
  its refusals); the force window and the admin matrices in the lean suite; in a real Home
  Assistant, the buttons' ids and devices (a named room too), a test shot and a refill run anyway
  through the real controller, and the buttons on an upgraded 2.17 room; browser checks.

## [2.30.1] - 2026-10-01

Integration and controller **2.30.1**.

- **With Auto setpoints, mornings keep their P0.** When Auto setpoints stops the maintenance shots
  for the dryback, it moves the maintenance trigger under the zone, and it stays there through the
  night and P0. It used to sit 2 points under where its plan expected the night to end. When that
  plan expected a shallower night than your dryback target, a night that reached the target (P3
  now holds the zone there) left the zone under the trigger at lights-on, and P0 was skipped: no
  morning dryback, the ramp at once (GR2, 1 Oct: "P0 bypass VWC 61<=rewater 63"). It now sits 2
  points under where your dryback target ends: for GR2, 57.8% instead of 62.2%.
- **Today's grow day says when the maintenance shots stopped.** From that time the trigger's line
  reads "Maintenance stopped" instead of a trigger; hover it to see the level a top-up would still
  fire under. The maintenance trigger's ? says what Auto setpoints does with it through the day.
- **Today's grow day starts the day at P0 for a zone still in last night's P3.** In the minute or so
  after lights-on before the controller's next check moves a zone to P0, the chart projected the
  rest of the day as P3, and since 2.30.0 it drew no target line for it.

### 🔧 Technical notes

- Controller: `setpoint_supervisor.desired` sets the post-stop, overnight and P0
  `p2_vwc_threshold` to `peak × (1 − dryback_pct / 100) − 2` (was `plan.floor − 2`, the floor being
  the achievable dryback), and its own rescue 3 under that. `auto_setpoints.status` publishes
  `p2_stop` (`HH:MM`, `auto_setpoints.clock(plan.p2_stop_h)`) beside `dryback_note`. No new options
  or state fields.
- Dashboard: `parseAutoSetpoints` reads `p2Stop`; `stoppedTargets` marks the P2 target steps from
  the stop on, for a tracking zone; the day chart labels them `Maintenance stopped`. The demo's
  tracking zone publishes `p2_stop` with its dryback note.
- Docs: `docs/ENTITIES.md` lists the auto setpoints sensor's `dryback_note` and `p2_stop`.
- Tests: GR2's day in `test_auto_setpoints.py` (its plan gives the old 62.2% and the new 57.8%, and
  `decide()` keeps P0 for a zone held at 60.6% under the new one, skipped it under the old);
  `p2_stop` published and parsed; the stopped marking.
- Dashboard: `projectFrom` projects from P0 now for a zone whose P3 began before lights-on while the
  lights are on (`since <= 0`, before the P3 cutoff); a P3 begun today, P2's early move, stays. Seen
  in CI: the Overview's "targets layer is drawn" check failed between the demo's 10:00 lights-on and
  its zones' move to P0.

## [2.30.0] - 2026-10-01

Integration and controller **2.30.0**.

- **The overnight dryback stops at your dryback target.** Overnight a zone used to be watered only
  below its rescue level, so a night that dried faster than the day went straight past the target:
  a 30% dryback from an 86.5% peak should end at 60.6%, but a zone drying 2.3 points an hour from
  74.2% at 9 pm was on course for about 51% by lights-on, with its next shot at the 50% rescue
  level. Now, each time a zone dries to where its dryback target ends, it gets a shot the size of
  its rescue shot, no sooner than the time between P2 shots after the last one, and the rescue level
  stays the floor beneath it. These shots stop when the daily water limit is spent, and a held plan
  stops them, as it does other routine shots. A zone's "Next:", the controller's log and Today's
  grow day show the level it is held at.
- **Today's grow day draws P0's line where P0 really ends.** It was drawn from the overnight dryback
  target, so a 30% dryback put it far below the zone, while the controller ends P0 on its own
  additional dryback: 3% below the morning's highest reading unless you change it. The line is
  there now.

### 🔧 Technical notes

- Engine: in P3, after the `p3_emergency` check, `decide()` fires `p3_hold` below
  `p3_hold_level()` = `peak_vwc × (1 − dryback_target / 100)` (None until a peak is seen), sized
  `p3_emergency_shot`, once `minutes_since_shot ≥ p2_time_between_min`, never while `steering_held`;
  `CAP_EXEMPT["p3_hold"] = False`. Its reason reads `P3 hold dryback VWC 60.4<60.5 (30% of peak
  86.5)`. `waiting_for()` lists `p3_hold` (with `in_min` while the P2 gap runs, and `dryback`), and
  `zone_status_label` says `Holding dryback` for it. The predictive move to P3 is unchanged: it only
  ever starts the dryback sooner. The vendored copy follows.
- Controller: `next_text` and `log_words` say the hold (`shot when VWC < 60.55%, the 30% dryback
  (now 74.2%) · rescue shot if VWC < 50% · P0 at 07:00`; `P3 dryback hold shot 2% for 57 s (~0.3 L):
  VWC 41.0% under 49.0%, the 30% P3 dryback from today's 70.0% peak`). A rescue level at or over the
  hold level fires first, so it is said alone. No new options or state fields.
- Dashboard: `waitingText` mirrors `next_text`, and `controllerZoneLabel` says `Holding dryback`.
  Today's grow day draws P3's target at the hold level (`Held at`), from the day's peak, and none
  for last night's P3 carried into the morning; its projected night (`runPhases`, and `projectFrom`
  with the day's peak) holds there with rescue-sized shots. The plan graph counts hold and rescue
  shots apart and warns of a short dryback from the night's lowest point, not the lights-on reading.
  The trigger-below-the-dryback warning adds that P3 may water the zone back up, and the dryback
  target, rescue level, rescue shot and P2 time-between-shots explainers say what the hold does.
- Docs: `README.md`, `CLAUDE.md`, `docs/ENTITIES.md`, `docs/SYSTEM_OVERVIEW.md`,
  `docs/GROW_PLANS.md`, and the daily-limit code's "Watering meanwhile" in `docs/error-codes.json`
  and `docs/ERROR_CODES.md`.
- Tests: `crop-steering-engine/tests/test_p3_hold.py`, with the `waiting_for` and kind tables;
  `addons/f2_control/tests` (`next_text`, `log_words`, the published conditions);
  `tests_ha/test_p3_hold.py`, in a real Home Assistant: an armed fresh room at night, a zone under
  its dryback target gets the shot through its valve, with its label and conditions published, and
  one above it gets nothing; the dashboard's unit tests.
- Dashboard: `phaseTargets` draws P0's target from `p0_dryback_drop_percent` (`PHASE_TARGET.P0`, the
  zone's or room's P0 Additional Dryback, 3% when missing, as the controller reads it), below the
  highest reading since P0 began, where `decide()` ends P0; it was the steering mode's
  `dryback_target`. `TargetKey` drops the rescue level, which no phase's line uses since the hold.

## [2.29.2] - 2026-10-01

Integration and controller **2.29.2**.

- **The README says what Crop Steering does and how to install it, and little else.** It is half as
  long, and it says plainly that no AI makes any decision: the controller waters by your setpoints
  and fixed arithmetic, so the same readings and settings, at the same point in the day, give the
  same decision every time. It no longer says Crop Steering doses no nutrients (it has mixed
  nutrient batches since 2.26.0), and no longer points at the online demo or the AI-assistant
  connector.
- **The online demo is gone.** It showed the dashboard with sample data on a github.io page; the
  screenshots show it instead. The sample data stays inside the dashboard, where its tests and the
  screenshots use it.
- **The AI-assistant connector is gone.** The optional connector that let an assistant such as
  Claude read a room and prepare setup or plan changes is removed, with its guide. Nothing in Crop
  Steering talks to an AI; the dashboard and the controller work exactly as before.

### 🔧 Technical notes

- `README.md`: features, *What you need*, install and updating, documentation.
- `.github/workflows/pages.yml` and the root `www/` it published are removed, and
  `frontend/scripts/package.mjs` writes the dashboard to the integration and the app only. The
  dashboard opens its demo workspace only with `?demo` (`isDemoLocation`), no longer by itself on
  any `*.github.io` address. The browser checks load the app's copy
  (`addons/f2_control/www/public`), the same `dashboard.html` with the `index.html` that opens it;
  `tests/test_dashboard_layout.py`, CI's committed-build check and both hygiene checks follow.
- Removed: `mcp-server/` (the stdio MCP server, its tests and its lockfile), `docs/MCP.md`, CI's
  *MCP protocol and reviewed configuration workflows* job, and the source zip each GitHub release
  attached (`crop_steering_mcp_source.zip`). The README, user guide, install guide, testing guide,
  repository map and troubleshooting no longer mention it, nor does `health.py`.
  `tests_ha/test_mcp_setup_contract.py` is now `test_setup_save_plumbing.py`: the same two real
  Home Assistant checks of `setup_save` and declared plumbing, as the payload Rooms & hardware
  sends. `tests/test_requirements_stated.py` no longer checks a Node.js version.

## [2.29.1] - 2026-10-01

Integration and controller **2.29.1**.

- **Today's events say who changed a setting, and what it was.** A change reads "Sam raised Most
  P1 shots to 10 (was 6)" or "Auto setpoints lowered Maintenance trigger to 63.3% (was 71.3%)",
  under the zone's own name. It said "Zone 1 · Maintenance shot when below 71.3 → 63.3 %", whoever
  made it and whatever the zone is called. A person is named as Home Assistant knows them, an
  automation or a script by its name, and the controller's own adjustments as Auto setpoints.
- **The controller's log says what it is doing, when, and in plain words.** Every line starts with
  the date and time and names the room and zone as you named them. Each zone writes a line a minute
  with its moisture, EC and water today and what it is waiting for; a phase change says why ("P3 →
  P0: lights on"); a shot says what kind it is, how long it runs, about how much water it gives and
  why; and a setting change says who made it ("Sam raised Most P1 shots to 10 (was 6)"). It said
  "[controller] [default] Z1 P3 hold —", with no time, every minute.

### 🔧 Technical notes

- The grow day reads who made each setting change from Home Assistant's logbook, which records the
  user behind every state change: `logbook/get_events` over the websocket inside Home Assistant,
  `/api/logbook` over REST standalone (`Controller.logbook`, the selected room's entities only).
  `changedBy` (`day-timeline.ts`) names an entry's `context_event_type` `automation_triggered` /
  `script_started` by its `context_name`, a `context_user_id` by that user's person (`person.*`'s
  `user_id`) or, for an account without one, the signed-in user (`hass.user`, as
  `Controller.viewer`), and any other user on a zone's `p1_target_vwc`, `field_capacity`,
  `p2_vwc_threshold` or `p3_emergency_vwc_threshold` as Auto setpoints, which writes only those and
  through the Supervisor's user. It is read once the day's changes are known and again when one
  more appears; a failed read shows the changes without a name. `changeSentence` words it, with a
  setting's `short` name (new on `Setting`). The demo has a grower, `person.alex`, and
  `demoLogbook`. `tests_ha/test_logbook_names_who.py` changes a real room's trigger as a signed-in
  user, as the Supervisor and from an automation, and reads all three back both ways.
- `log()` starts each line with the local date and time (the `[controller]` tag it had is gone), and
  `_say` names the room and zone as the notifications do (`_where`). The words are `log_words.py`'s:
  decide()'s transition, shot and hold texts said for a person by `Reason.kind`, anything unknown
  logged as it is, and each setting's short name as the dashboard's `setting-words.ts` has it. What
  the engine decides and publishes is unchanged.
- Each minute a zone that does not fire logs its readings (`_readings`), what holds it, and
  `next_text` of the conditions it published. A phase change has its own line.
- Every number read (`_num`, `_num_or_none`) is noted; a value that differs from its last read is
  logged with who changed it, from Home Assistant's logbook (`/api/logbook` for that entity since
  the last read): an automation or script by its `context_name`, a `context_user_id` by its
  person's name (`person.*`, read at most every ten minutes). Auto setpoints' own writes are logged
  where they are made, "Auto setpoints lowered Maintenance trigger to 63.3% (was 71.3%)", and not
  again. The first read after a start only notes. No state file, option or entity changes.
- `addons/f2_control/tests/test_log_words.py` runs decide() for each transition, shot and hold it
  words, holds the names to `setting-words.ts`, and drives a named room through a minute's line and
  a setting change.

## [2.29.0] - 2026-09-30

Integration and controller **2.29.0**.

- **Home Assistant 2026.5 or newer is required.** It was 2024.10, two years old. On an older Home
  Assistant, HACS and the app store offer no update to Crop Steering or its controller until Home
  Assistant itself is updated, and what is installed keeps working. The code and the extra test
  run that only the older versions needed are gone.
- **HACS and the app store name Chill-Division as the maintainer.** They named JakeTheRabbit, who
  started Crop Steering, so an installation from this repository looked like one of theirs.
  Nothing else changes.
- **Messages name the controller, not "f2-control".** It was named after the room it was first
  written for. When a room is switched off, the "hasn't been watered" notification and the zone's
  line on the dashboard now say "room off (kill switch)", not "f2-control disabled (kill switch
  off)", and the controller's log lines start with "[controller]".
- **The EC PID option is gone.** Only Home Assistant helpers from the original author's own setup
  could switch it on, so it never ran anywhere else, and the maintenance trigger's explanation no
  longer mentions it. EC Stacking works as before, moving the maintenance trigger 1 point at a time.
- **Setup's examples and the entity reference describe any room, not the first one.** Setup's
  hints for pot size and dripper flow gave a 6 L rockwool block and a 4 L/hr emitter, the room
  Crop Steering was first written for; they now say a 10 L pot and a 2 L/hr emitter. The entity
  reference listed that room's own settings as the defaults (6 L pots, 4 L/hr drippers, lights
  10:00 to 22:00, a 200 L daily budget and more); it now lists what a new room starts at.
- **A new room starts at a 3.2 L (0.9 gal) pot with one 4 L/hr dripper per plant**, in setup and
  in its settings. Each place used to start somewhere different: 5, 6 or 10 L, 1.2 to 2 L/hr, one
  or two drippers. A room already set up keeps its own numbers.
- **The "What has been tested" page is gone.** It logged the original author's own live checks
  on their installation, not anything a grower can use.
- **Links go to Chill-Division, Crop Steering's public home.** The README (its demo, screenshots
  and install buttons), the integration's documentation and issue links, **Learn more** on
  Repairs cards, the app store and the release notes link in What's new all pointed at
  JakeTheRabbit's or the maintainer's own repository. The GitHub Sponsor button, which went to
  JakeTheRabbit, is gone.
- **Setup no longer imports a `crop_steering.env` file, and Configure no longer reloads one.** A
  room set up from one keeps working exactly as before: after setup it only ever ran on what was
  stored then. Change it in Configure or in Rooms & hardware.
- **The original author's old page addresses are gone.** `f2.html`, `office.html` and a dozen
  others only redirected old bookmarks; so did the old room and page names in dashboard links
  (`?room=f2`, `?view=climate`). The app's sidebar entry, the dashboard in the sidebar and the demo
  site open as before.
- **How long the pump runs before a zone opens is a setting.** *Pump prime time* (how long the
  pump runs before the main line and a zone's valve open) and *Main line lead time* (how long the
  main line is open before the zone's valve) were fixed at 2 and 1 seconds, so a pump that takes 4
  seconds to reach pressure opened each valve onto a line still filling. Both are on the Irrigation
  plan's room settings, under Pump and valves. Until they are changed, nothing is different.
- **The per-plant daily minimum is gone.** Like the EC PID option, only a Home Assistant helper
  from the original author's own setup could switch it on, so it never ran anywhere else. The
  watchdog is still the backstop that waters a zone left dry by day.
- **A shorter menu: six entries instead of thirteen.** Overview, Irrigation plan, Insights, Feed,
  Settings and Help. Pages that belong together are tabs of one entry: Insights holds Zone, Water,
  Compare runs and Activity; Feed holds Reservoir (once the room has one mapped) and Stock tanks;
  Settings holds General and Rooms & hardware (was Rooms & setup). Bookmarks keep working, and one
  to a page that is gone opens the Overview.
- **The room's switches are on the Overview.** Switching the room off, and watering off, moved from
  Settings to the Overview's heading, beside the pills that say whether each is on, and the status
  line's link for watering switched off opens the Overview. With the room off, the Overview's
  banner leaves the switch to the heading; on every other page the banner keeps its own.
- **The Zones and Sensors pages are gone.** The Overview's zone table has what the Zones page
  showed, and a zone's name opens its details. Water use over the grow is under Insights, Water,
  which also shares each zone's water today across its plants. The Sensors page repeated the
  probes: Insights, Zone shows whether each zone's probes give a current reading and how old the
  last one is.
- **Less said twice.** The shot calculator is in one place, Insights, Water, not on Today, Schedule
  and Insights. A setting's range, step and key are behind its **?**. Pot size, plants and
  drippers are set only in Rooms & hardware. Help keeps the terms, the error codes and What's new:
  its daily routine and tool links repeated the menu. Rooms & hardware drops its Installation tab,
  which repeated the README's install buttons, and inside Home Assistant, Settings no longer shows
  a connection form: the session is the connection.
- **Today's grow day is twice as tall**, and how to read it is behind a **?** beside its title.

### 🔧 Technical notes

- **Minimum Home Assistant 2026.5.0** (was 2024.10.0):
  - `hacs.json` `homeassistant` is `2026.5.0`. The controller app's `config.yaml` sets
    `homeassistant: "2026.5.0"` too, and the Supervisor checks it on install and on every update,
    so on an older Home Assistant the controller cannot move ahead of the integration.
  - `setup_panel` calls `frontend.async_panel_exists` (2026.5.0+) without the panel-table fallback,
    and registers its static path through `async_register_static_paths` only.
  - `stock_api` takes the time zone from `dt_util.get_default_time_zone`.
  - The oldest-supported Real Home Assistant leg runs 2026.5.0 on Python 3.14 (plugin 0.13.329),
    without the `josepy` and `pycares` pins. `tests/test_requirements_stated.py` checks the app's
    minimum as well.
- `manifest.json` `codeowners` is `["@Chill-Division"]`: HACS shows it as the author, reading the
  manifest of the latest release. `repository.yaml` `maintainer` is `Chill-Division`, which the app
  store lists for the repository. The manifest's `documentation` and `issue_tracker` links and
  `repository.yaml`'s `url` are unchanged.
- The controller's own name in what it says: the blocked reason is `room off (kill switch)`, the
  `engine` attribute on the sensors it publishes is `crop-steering-controller` (was `f2-control`;
  nothing shipped reads it), its log prefix is `[controller]` (also in `run.sh`), and it starts
  with `Crop Steering Controller X.Y.Z starting`. Ids are unchanged: the app slug `f2_control`,
  `input_boolean.f2_control_enabled`, `sensor.f2_control_vitals` and the notification ids.
- The EC PID loop is removed: `crop_steering_engine.ec_pid`, the controller's branch that read
  `input_boolean.crop_steering_ec_pid_enabled` and `input_number.crop_steering_ec_pid_kp` / `_ki` /
  `_kd`, and the per-zone `ec_integral` / `ec_prev_err` it kept. EC Stacking always takes
  `_step_ec_offset`'s 1-point step. A state file holding those two keys still loads
  (`test_state_migration`); they are dropped and not written back. The EC Stacking line of the
  P2 trigger's explainer (`setting-words.ts`) drops "The PID option can move it up to 20%."
- `strings.json` / `translations/en.json`: the `substrate_volume` and `dripper_flow_rate` hints,
  in setup and Configure, use a 10 L pot and a 2 L/hr emitter. `docs/ENTITIES.md` follows
  `number.py`: `p1_target_vwc` 65, `p1_time_between_shots` 15, `p2_vwc_threshold` 60,
  `substrate_volume` 10 (range 0.1-200), `dripper_flow_rate` 1.2, `drippers_per_plant` 2 (range
  1-20), `field_capacity` 70, `lights_on_hour` 12, `lights_off_hour` 0, `zone_N_plant_count` 4
  (range 1-1000) and `zone_N_max_daily_volume` 20.
- Sizing defaults are 3.2 L, 4 L/hr and 1 dripper per plant: the wizard's schema and
  `_build_parameters`, the Configure form's fallbacks, `number.DEFAULT_VALUES` (were 10 / 1.2 / 2),
  `setup_api.setup_sizing`'s last fallback, and the dashboard's new-zone draft (was 5 L / 2 L/hr).
  A number restores its state first and seeds from the room's recorded setup answers second, so
  only a room with neither starts at these. `tests_ha/test_sizing_defaults.py` proves a new room
  gets them and a 2.18 room keeps its 6 L / 2 L/hr. The controller's `substrate_l` / `flow_lps`
  fallback options are unchanged.
- `docs/FEATURE_MATRIX.md` is removed with its links (README, INSTALL, USER_GUIDE, SYSTEM_OVERVIEW,
  GROW_PLANS), and so are the paragraphs in INSTALL.md and MCP.md that cited a two-room
  installation as live evidence.
- Links to `JakeTheRabbit/HA-Irrigation-Strategy`, `jaketherabbit.github.io` and the
  `ChillingSilence` releases and images point at `Chill-Division/HA-Irrigation-Strategy`:
  `manifest.json` `documentation` / `issue_tracker`, `const.REPAIRS_DOCS_URL`, both `url:` fields,
  `DOCS.md`, `whats-new.ts` `RELEASES_URL`, README, INSTALL, USER_GUIDE, SCREENSHOTS, the MCP
  README and the Pages workflow comment. INSTALL's move section covers a controller from either of JakeTheRabbit's
  repositories: this repository's app is `f50c47e4_f2_control`. `.github/FUNDING.yml` is removed.
- The `.env` import is removed: `env_parser.py`, the first step's `config_method` choice, the
  `load_env` step, Configure's `reload_env`, `_validate_env_entities` and their strings. So is the
  `load_yaml` step, which no step led to. An entry with `config_method: "env"` loads unchanged:
  nothing read the key or the file at runtime, and nothing rewrites the entry.
  `test_upgrade_in_place` proves it on the env-era fixture, with no `crop_steering.env` present.
- `frontend/scripts/package.mjs` writes `dashboard.html` to all three folders and `index.html` (keeps
  query and hash, opens `#/overview`) to the app, whose ingress opens it, and to the Pages site. It
  deletes any other page it finds there, so a page it stops writing cannot stay committed. The 13
  stubs in `www/` and in the app, and the integration's `www/index.html`, are removed. `?room=`
  resolves by room id only (`room:`, `room:f1_`), without the slug or `f2` aliases; `?view=` is
  no longer read. `F1_ALIASES`, for
  an old install's `sensor.crop_steering_system_*` ids, stays.
- `number.crop_steering_<prefix>pump_prime_time` (0-20 s, default 2) and `..._main_line_lead_time`
  (0-10 s, default 1), room-wide. The controller reads both before a shot opens anything
  (`_lead_time`; optional, so under an older integration it keeps 2 s and 1 s without holding the
  room), capped at those maximums, which keep a whole open sequence well inside
  `INFLIGHT_OPEN_WINDOW_S`. A shot's duration and litres still count from the zone valve opening.
  The dashboard groups them under Pump and valves, and setup's pump and main-line hints name them.
- The daily-minimum floor is removed from `decide()` (its last rule, kind `min_daily`), with
  `ZoneParams.min_daily_volume` and `drown_ceiling`, their bounds, `validate_params`' min <= max
  clamp, and `min_daily` in `CAP_EXEMPT` and `PLAN_HOLD_EXEMPT`. The controller no longer reads
  `input_number.crop_steering_<prefix>zone_N_min_daily_ml_per_plant` or `min_floor_drown_ceiling`,
  and the dashboard has no label for the latter. It fired only when no other rule did and only
  above a default of 0, so no other decision changes; the engine's tests still run all 96
  statements of `decide()` and 71 of its 72 branches.
- The dashboard's pages are grouped in `App.tsx`'s `sections`, each with its tabs: a menu entry
  opens its first tab, the toolbar (`<section> views`) switches between them, and the breadcrumb
  and title read `Section › Tab`. Reservoir is hidden until the room descriptor carries one of
  `RESERVOIR_KEYS`. A hash that is no page (`#/zones`, `#/sensors`) opens Overview.
- Removed with the pages: `pages/zones.tsx`, `pages/sensors.tsx`, setup's `Installation`, Help's
  daily routine and tool lists, Settings' room, watering and Advanced workflows sections, Insights'
  summary tiles, tabs, catch-test calculator and room map, `ZoneTable`'s full mode (`compact`),
  `DailyWaterSummary`, `recentReadings`, the `Hardware sizing` group help, and the CSS only they
  used. Added `pages/water.tsx` (the Water use panel and `WaterDelivery`) and `WateringPower`;
  `RoomOffBanner` takes `switchable`; Overview uses `useDrybackTrends`; the Water use panel's
  Today cell adds `mL per plant` from `dailyWater`.
- `SettingHelp` takes `limits` (`min–max unit · step`) and shows without the setting's words too.
  The grow-day lane's plot is 80 px tall (was 40), and its hint is a popover.
- Where to fix things, in the controller's notifications (the CS-208 text, the batch and sizing
  holds, the alert footer), `feed.py`'s problems, `strings.json` / `translations/en.json` and
  `docs/error-codes.json`: "Settings → Rooms & hardware", "Feed → Stock tanks", "Help → Error
  codes" and "Overview". No entity id, service or state changes.
- Browser checks follow the new pages. The Overview's two-screen limit at 1440×800 leaves out the
  demo banner, which a live Overview does not have: without it the Overview is 1,574 px of 1,600
  with the chart doubled (1,504 px before).

## [2.28.0] - 2026-09-29

Integration and controller **2.28.0**.

- **Moisture levels are used as set.** The peak VWC target, maintenance trigger, field capacity
  and rescue level each accepted more than the controller would use: a peak target of 87 was
  reported as outside the engine's range and used as 85. Each now has one range, the same
  wherever you set it: peak target 20–100%, maintenance trigger 10–100%, field capacity 40–100%
  and rescue level 10–65%. What keeps them sensible is their order, as before: the ramp stops at
  field capacity, and the trigger stays under the peak target and over the rescue level. A room
  set above the old limits now waters to what it was set to; a value below the new lower limits
  was already being used as the lowest one allowed.
- **Overnight, a zone's line shows tonight's dryback.** In P3 the grow-day line read, for example,
  "P3 · 60.1% now · … · P0 dryback 1.4% of 30%": that was the morning's dryback after lights-on,
  measured from the lights-on reading, and beside "P3" it looked as if tonight's dryback had
  barely started. Overnight the line now says how far the zone has dried from today's peak, which
  is what the P3 dryback target is about: "P3 dryback 30.5% of 30% from today's 86.5% peak".
- **Moisture levels that work against each other are pointed out.** On the Irrigation plan, a
  zone's moisture levels now say when, together, they will not do what each says alone: a
  maintenance trigger the controller moves (it keeps it under the peak target and above the
  rescue level) says which value it will use; a rescue level above where tonight's dryback ends
  says it would stop the dryback early, beside both settings; a trigger that lets the substrate
  dry further by day than the night's dryback says so; and a peak target above field capacity says
  the ramp stops at field capacity. These are advice only: any value can still be saved.
- **The first shot of the day waits for the plants to drink.** P0, the time after lights-on before
  the ramp, was meant to end once the substrate had dried a little more: Athena's additional
  dryback, 1–5%. It waited for the overnight P3 dryback target instead (30%, for example), which
  never came first, so the ramp always started at the latest-first-shot time. P0 now has its own
  setting, Additional dryback, 3% unless you change it: the ramp starts once moisture has dropped
  that far below its lights-on reading, or at the latest first shot, whichever comes first. It is
  in P0 on the Irrigation plan. The setting it takes over never did anything, so every room
  starts at 3%, and the built-in recipes use 2–5%.

### 🔧 Technical notes

- **One range per moisture level (engine, integration, controller).** `MOISTURE_RANGES`
  (`const.py`): `p1_target_vwc` 20–100, `p2_vwc_threshold` 10–100, `field_capacity` 40–100,
  `p3_emergency_vwc_threshold` 10–65. They are the number entities' ranges (room and zone) and the
  setup wizard's field capacity range, and grow plans' `ENGINE_BOUNDS`, Auto Setpoints' `BOUNDS`
  and the engine's `_PARAM_BOUNDS` (`p1_target`, `p2_threshold`, `field_capacity`,
  `p3_emergency_floor`) are the same, so `validate_params` never clips a value the setting
  accepted. CS-401 is left for a value outside them, which only an older install can hold. The
  engine's floors are unchanged; its tops were 85, 70, 90 and 60. The ordering clamps are unchanged
  (the ramp stops at field capacity; the trigger is kept at least 3 over the rescue level and 1
  under the lower of the peak target and field capacity). Proven in a real Home Assistant
  (`tests_ha/test_moisture_ranges.py`): entities, engine, grow plans and Auto Setpoints agree,
  neither end of a range is clipped, and a peak target of 87 is used as set with no CS-401.
- **Overnight dryback on the grow-day line (dashboard).** While a lane is in P3, `tracking` shows
  `dayDryback` (`lib/day-timeline.ts`): (peak − VWC) / peak × 100 with the peak the highest reading
  since lights-on, where the controller starts its peak, in place of the P0 figure
  (`morningDryback`, from the lights-on reading), which the other phases keep. A browser check pins
  the demo at 23:30 and finds every lane saying it.
- **Level-order advisories (dashboard).** `levelWarning` (`lib/level-order.ts`) reads a zone's
  peak target, field capacity, trigger, rescue level and its steering mode's P3 dryback target, as
  `buildSetpointPreview` resolves them with the page's drafts, and words, for the setting beside it,
  the controller's ordering (`max(rescue + 3, min(min(peak, field capacity) − 1, trigger))`, as
  `controller._params` applies it), a rescue level above `ceiling × (1 − dryback / 100)`, a daytime
  dryback `(ceiling − trigger) / ceiling` bigger than the P3 target, and a peak target above field
  capacity. Shown under a zone's settings only, a dryback target only for the mode in use, as an
  advisory like the probe-history ones. A browser check types a trigger and a rescue level out of
  order in the demo.
- **P0 additional dryback (engine, integration, controller, dashboard).**
  `ZoneParams.additional_dryback` (engine; None is the P3 `dryback_target`, as before; bounds
  1–40): P0 ends when `dryback_pct` reaches it, and `waiting_for`'s `p0_dryback` reads it. The
  controller reads it from `number.crop_steering_<prefix>[zone_N_]p0_dryback_drop_percent`
  (optional; 3 when missing), a setting that existed since 2025 and nothing read. That number is
  now "P0 Additional Dryback", 1–40%, default 3, and carries `read_by_controller`; a value restored
  without it (saved while nothing read it: the old 15% default, a recipe's 12–30%) starts at 3. The
  recipes' values are now 2–5%. The dashboard shows it in P0, its explainers and the grow-day P0
  line use it, and the projected P0 ends on it. Proven in a real Home Assistant
  (`tests_ha/test_p0_additional_dryback.py`): a new room at 3%, the controller reading the zone's
  own value, an old saved 15% and 24% starting at 3%, and a value set since kept.

## [2.27.2] - 2026-09-29

Integration and controller **2.27.2**.

- **Auto setpoints no longer gives up a day's watering for the overnight dryback.** To reach the P3
  dryback target, Auto setpoints stops maintenance shots early, so the day's drying adds to the
  night's. When a zone's nights dried too slowly for the target, it stopped them as soon as the
  morning ramp ended: a zone set to Vegetative got its ramp to 85% and then no water until the next
  morning, down to about 60% by lights-off, a generative day nobody asked for. Now a Vegetative zone
  keeps its maintenance shots until 3 hours before lights-off and a Generative zone until the middle
  of the day: Athena adjusts the dryback by adding or removing maintenance shots at the end of the
  day. When the target still can't be reached, the zone gets the deepest dryback left, and the
  Irrigation plan says so beside the P3 dryback target, for example "30% dryback unreachable at this
  zone's uptake: about 14% tonight, with maintenance shots until 17:00".

### 🔧 Technical notes

- **How early Auto setpoints may stop maintenance shots (controller, dashboard).**
  `curve_tracker.plan_day` stops P2 no earlier than `day_h − 3` hours after lights-on for a
  vegetative recipe and `day_h / 2` for a generative one (`Recipe.generative`, new, default False;
  Athena's stretch and finish stages set it), never inside P1. The dryback it cannot reach is capped
  (`achievable_dryback_pct`, `floor`), and its note names what the zone gets and until when. The
  controller passes the zone's steering mode (`_veg`) as `plan_ctx["generative"]` and publishes the
  note as `dryback_note` on `sensor.crop_steering_<prefix>zone_N_auto_setpoints`; the dashboard shows
  it beside the P3 dryback target of the mode in use and on the zone's Auto chip. A zone without
  Auto setpoints is unchanged. Proven with the real controller in a real Home Assistant
  (`tests_ha/test_auto_setpoints_steering_mode.py`): at 17:00 a Vegetative zone's trigger is still
  one maintenance shot under the peak and a Generative zone's is drying, from the zone's own select.

## [2.27.1] - 2026-09-28

Integration and controller **2.27.1**.

- **Maintenance shots wait for the last one to soak in.** A maintenance (P2) shot fired whenever
  moisture read below its trigger, checked every minute. With the trigger raised above the
  reading, it fired a shot a minute, before the first had reached the probes. There is now a
  **Time between P2 shots** setting, like P1's: a maintenance shot waits at least that long after
  the last shot. It is 5 minutes unless you change it, for every room and zone, including rooms
  already running; 0 turns it off. A zone's Next: line says when its next shot may fire.
- **Readings are rounded.** A probe that reports its reading unrounded, such as an estimated pore
  EC of 0.639473676681519, now shows as 0.639 when you pick entities in Rooms & setup, on the
  Sensors page, in a zone's details and in Insights. Only what is shown is rounded.

### 🔧 Technical notes

- **P2 time between shots (engine, integration, controller, dashboard).**
  `ZoneParams.p2_time_between_min` (engine default 0 = off; bounds 0–120): a P2 top-up, the plain
  one and the one beside a waiting rescue, fires only once `minutes_since_shot` (from the end of
  the last shot of any kind) reaches it, and `waiting_for`'s `p2_topup` then carries `in_min`.
  New `number.crop_steering_<prefix>p2_time_between_shots` and per-zone
  `number.crop_steering_<prefix>zone_N_p2_time_between_shots` (0–60 min, default 5; an upgraded
  install gets them at 5). The controller reads it as it reads P1's (plan override, zone, room)
  but as an optional setting: under an integration older than it, 5 applies without holding the
  room or raising CS-402. EC dilution and rescue flushes and the daily minimum keep their own
  10-minute `p2_min_interval_min`; the watchdog and the P3 rescue do not wait. The dashboard has
  it in P2 · Maintenance, and a zone under its trigger reads "shot at 15:21 (VWC 67% under 70%)";
  so does the vitals' Next line.
- **Rounded readings (dashboard).** `stateText` (`lib/units.ts`) shows a numeric entity state to at
  most three decimals, trailing zeros trimmed (`displayNumber`), and any other state as it is. Used
  by the Rooms & setup entity picker, the Sensors table, a zone's Reporting sensors and Insights'
  "Last reported". The demo has an unmapped estimated-pwEC probe with an unrounded reading, and the
  browser check finds it as 0.639 in the picker.

## [2.27.0] - 2026-09-28

Integration and controller **2.27.0**.

- **A refused change says why.** When Home Assistant would not make a change from the dashboard
  (renaming a room while it was watering, for example), the page said only "Response error: 500"
  and the reason went to Home Assistant's own log. The page now gives the reason, such as which
  switch has to be off first.
- **The substrate preset no longer guesses.** A zone keeps its pot volume, not what is in the pot,
  so Rooms & setup named a 3.2 L coco bag a Rockwool Hugo block, which holds 3.2 L too, and
  choosing Custom went straight back to it. The preset now reads Custom unless you have just
  picked one there, and Custom stays chosen. Nothing about the zone changes: its volume is what
  is saved, as before.
- **Room setup changes are recorded.** Each saved change to a room's setup (its name, zones,
  valves, probes, pot and dripper sizing, equipment) now shows in Home Assistant's Activity, and
  on the room's device page, with who saved it and what changed: for example "Growroom 2 setup
  saved (revision 2): renamed from “Crop Steering System”". A change Home Assistant refuses is not
  saved, so it is not recorded. The controller's log still says when it takes a saved change on.

### 🔧 Technical notes

- **Room services over the websocket (dashboard).** Inside Home Assistant, `HaClient.operator`
  calls the integration's response services (`setup_*`, `strategy_*`, `runs_*`, `stock_*`,
  `feed_*`, `whats_new_*`) with the websocket's `call_service` and `return_response`, as Home
  Assistant's own frontend calls a service, instead of `POST /api/services/…?return_response`.
  Home Assistant's REST API answers any `HomeAssistantError` a service raises with a bare 500 (it
  catches only `vol.Invalid` and `ServiceNotFound`), so every refusal lost its text; the websocket
  returns it as `error.message`, and Home Assistant logs it as "Error during service call to
  crop_steering.<service>: <reason>". A service the integration lacks (`not_found`) still reads
  "needs the updated Crop Steering integration". Outside Home Assistant (a token, no websocket)
  the REST call stays, and a 500 points at Home Assistant's log. Proven on Home Assistant's real
  web server and websocket (`tests_ha/test_refusal_reasons.py`, marked `web_server`); the oldest
  supported CI leg pins `pycares==4.4.0`, the one Home Assistant 2024.10 shipped with.
- **Substrate preset picker (dashboard).** `SubstratePresetPicker` shows a preset only while the
  volume is the one that preset filled in during this edit (`picked`, fresh for each room and
  zone); any other volume, typed or saved, reads Custom. It showed whichever preset matched the
  volume (`matchPreset`), so a volume that matched one could never read Custom.
- **Setup changes in the logbook (integration).** When `crop_steering.setup_save`, `setup_create`
  or `setup_remove` succeeds, the service fires the logbook's own event (`logbook_entry`,
  `homeassistant.const.EVENT_LOGBOOK_ENTRY`) with the service call's context, so the entry names
  the user. Its name is the room's name, its `entity_id` the room's
  `sensor.crop_steering_<prefix>engine_config`, and its message `setup_changes(before, after)`:
  the room as `setup_room` gave it to the page and as saved (renamed, archived or restored,
  plumbing, each mapping, and each zone's name, valve, probes and sizing), or "set up" or
  "archived", with the revision. The same line goes to the log at INFO
  (`custom_components.crop_steering.setup_api`). A refused change records nothing; a recording
  that fails is logged and never fails the save. Proven through the real recorder and logbook.

## [2.26.3] - 2026-09-28

Integration and controller **2.26.3**.

- **Choose how a zone's probes are read.** A zone with more than one probe read their average.
  Now each zone has two choices, one for moisture and one for EC: Average, Median, Lowest or
  Highest. Steer on the driest probe for safety while the EC stays an average, for example. In a
  zone's details, under Probes, each choice shows what the zone would read with it right now,
  including which probe the lowest and the highest are. A change takes effect at once, after a
  review, and the controller steers on the new reading from its next check. Every zone stays on
  Average until you choose, so nothing changes by itself.

### 🔧 Technical notes

- **Probe choices (integration, dashboard).** Per zone,
  `select.crop_steering_<prefix>zone_N_vwc_method` and `_ec_method` (Average, Median, Lowest,
  Highest; Average by default, and for an upgraded zone). `sensor.crop_steering_<prefix>vwc_zone_N`
  and `ec_zone_N` apply them (`calculations.combine_probes`; Average is the arithmetic mean it
  always was, and a choice they do not know reads as Average), update the moment a choice changes,
  and publish `probes` (each probe's reading, converted), `combined` (what every choice gives now)
  and `method`. The controller steers on those sensors unchanged, proven with the real controller.
  The dashboard's zone sheet has a Probes section with both choices, reviewed, and its Moisture and
  EC tiles say how they are read and what each probe reads.

## [2.26.2] - 2026-09-28

Integration and controller **2.26.2**.

- **Shorter vitals that say what comes next.** The controller's vitals notification no longer
  starts with a clock (the notification shows when it came) or a "LIVE" line. A room's name heads
  its lines only when there are several rooms, and watering switched off is still said. Under each
  zone it now says what the controller will do next, as the zone's Next: line on the dashboard does,
  for example "shot when VWC < 61% (now 58%) · P3 by 22:00". Settings → Notifications → Include
  room predictions in informational notifications leaves that out; it is on until you switch it off.

### 🔧 Technical notes

- **Vitals (controller, integration, dashboard).** `_maybe_notify` sends no `HH:MM` head (the
  missing-setpoint warning leads on a line of its own) and no `LIVE`/`HELD`: a room's name only when
  more than one room reports, with "(watering off)", or a "Watering off" line in a single room, when
  its engine switch is off. `next_text(conditions, at)` words the engine's `waiting_for` conditions
  as the dashboard's `waitingText` does; `_publish_waiting_for` keeps each zone's for it, and a
  zone's "Next:" line follows its own line. The new per-room
  `switch.crop_steering_<prefix>notify_predictions` ("Include Predictions in Notifications", on by
  default, also for an upgraded room) turns the "Next:" lines off; a controller that cannot read it
  includes them. `sensor.f2_control_vitals` keeps its state, the report's time. The dashboard's
  Settings has a Notifications section for the switch.

## [2.26.1] - 2026-09-28

Integration and controller **2.26.1**.

- **Each stock tank says which doser it is on.** In Stock tanks, put each bottle's tank on the
  Reservoir doser it feeds (Doser 1 to 6), and every batch the Reservoir mixes takes what that doser
  actually gave from it, by itself: no dose entity and no Record a batch. A batch stopped part-way
  takes only what went in. Each tank's per batch and batches left follow the feed stage in use. If you
  swap bottles between stages, put both tanks on that doser: each batch takes from the one named like
  the nutrient its recipe puts there. A tank on no doser works as before.
- **A dryback target says it is below the peak.** The dashboard shows every dryback target as
  "% below peak", where the Today settings showed a bare "%": 40 means drying back by 40% of the
  day's peak (an 87% peak dries back to 52%), not to 40% VWC.

### 🔧 Technical notes

- **Stock tanks on dosers (integration, dashboard).** A stock tank has `doser` (1 to 6, or none; a
  tank on one takes no `dose_entity`). `stock_api.StockStore` listens to the room's
  `sensor.crop_steering_<prefix>batch_status`; a `last` that ended after `reservoir_batch` (stored;
  set to the first run's time, so a batch before it is not counted) draws each tank on a doser by
  `last.dosed` (`stock.reservoir_draws`), logged with source `reservoir`. Several tanks on one doser
  are told apart by the nutrient that `last.stage`'s recipe puts on it (`stock.on_doser`); none is
  guessed at. `doses()` gives a tank on a doser what the stage in use doses from it; fills of the tank
  last-fill entity and `stock_record_batch` draw only the tanks on no doser. `stock_get` adds
  `dosers` (each mapped doser's switch and nutrient in the stage in use) and `reservoir_batch`;
  `sensor.crop_steering_<prefix>stock_low` adds each tank's `doser` and is rewritten when the feed
  settings change. Tanks stored before this load with no doser. The Stock tanks editor offers a Doser
  per tank in a room with dosers, and shows the dose entity only in a room without, or on a tank
  that has one.
- **Dryback unit (dashboard).** `DRYBACK_UNIT` ("% below peak", `setting-words.ts`) is the unit of
  every dryback target: the room model uses it for `number.crop_steering_*dryback_target` whatever
  unit Home Assistant gives the entity (`%`), and the plan views, the planning curve and the demo
  use it too. The entities are unchanged.

## [2.26.0] - 2026-09-27

Integration and controller **2.26.0**.

- **The controller waits for its settings before it waters.** While Home Assistant starts, or the
  Crop Steering integration reloads, a room's settings are missing for a moment. The controller used
  to fill them in with its own built-in values and could water on those; now the zone waits up to
  three passes (about three minutes) for them. A setting still missing after that is watered on its
  built-in value, as before, and the "settings missing" notice (CS-402) says which.
- **The dashboard says when the controller has stopped.** When the controller app stops for an
  update or a restart it says so first, and the dashboard shows "The controller app stopped 3 min
  ago", adding that it starts again by itself, which can take a few minutes. With no word from the
  controller at all, as just after Home Assistant restarts, it now says that this lasts a few
  minutes, instead of only that the controller is not running.
- **Feed EC and pH are gone.** The controller's source-water check (it held watering while a feed EC
  or pH probe read outside your limits), its two controller settings, the room's feed EC and pH
  limits, and the tank's EC and pH on the dashboard, with their History panel, are removed. Watering
  never waits on a feed probe now. A room that had one set carries on after the update, without
  having to be switched off and on.
- **Nutrient batches: the controller mixes your reservoir.** A new **Reservoir** page runs a room's
  batches with your own dosers. Map the reservoir's level sensor (an ultrasonic sensor on the lid,
  reading the distance down to the water), the fresh-water and recirculation solenoids and up to six
  dosers in Rooms & setup. When the reservoir reads almost empty with **Automatic batches** on (off
  until you turn it on), or when you press **Mix a batch now**, the controller refills it with fresh
  water for your fill time, starts the pump and the recirculation, waits 20 seconds, runs each doser
  in turn for its dose, then keeps mixing. The room waters nothing while a batch runs.
- **A feed recipe for each growth stage.** Give each doser its nutrient and its parts, the ratio off
  the nutrient chart (Athena Flower is 3 Core : 5 Bloom : 1 Balance : 0.5 Cleanse), and a strength in
  mL per litre per part; the page works out each doser's millilitres for your batch size and how long
  it runs at 600 mL/min, or the flow you set. Pick the stage each room is on; it is also a select in
  Home Assistant.
- **Dosers dose in the order you set**, dragged into place (or moved with the arrows) on the
  Reservoir page.
- **Batches are careful.** One starts only with the room's watering switch on and everything it uses
  reading off. With a level sensor and an almost-empty mark, one you ask for is refused unless the
  reservoir reads almost empty, so the fill cannot overflow it. If the reservoir did not fill,
  nothing is dosed. Anything that stops a batch part-way switches everything off and a notice says
  what went in.
- **The controller app starts with Home Assistant's host.** Start on boot is now on by default, so
  a box that restarts (a power cut, an update of the operating system) comes back watering instead
  of waiting, stopped, for someone to notice. If you set Start on boot yourself, either way, your
  setting stays.

### 🔧 Technical notes

- **Settings wait (controller).** `_zone_num` records each setting it fills in with a built-in value
  in `room._settings_missing` (reset at the start of `_loop_room`). `_blocked` holds a shot, after the
  engine switch, while any of them has been missing for fewer than `SETTINGS_WAIT_PASSES` (3) passes:
  "waiting for its settings to load (…)". CS-402 still fires after three passes, when the wait ends.
  Settings read later in a pass (the pot volume, in shot sizing) are not waited for. The controller
  tests see settings as loaded at once (`conftest._settings_load_at_once`) except
  `test_settings_wait.py`.
- **Stopped heartbeat (controller, dashboard).** On SIGTERM, after closing a shot in flight and
  saving state, `_say_stopped` sets each room's `sensor.crop_steering_<prefix>ai_heartbeat` to
  `stopped` with `stopped_at` (2 s timeout per room). It keeps `enable_flag` and `setup_revision` for
  the integration and leaves out `strategy_snapshot_version`, so `controller_supported` is false and
  no grow plan is armed on a stopped controller; the engine-offline repair still comes after 10
  minutes. The dashboard's `readHeartbeat` gains a `stopped` health: a "Controller stopped" warning
  and "The controller app stopped … ago" on the status line. A missing heartbeat's texts add that it
  lasts a few minutes after a restart or an update.

- **Feed EC/pH removed (controller, integration, dashboard, MCP).** The controller no longer reads
  `feed_ec_sensor`/`feed_ph_sensor` (app options or descriptor): `_read_feed_ec`, `_read_feed_ph`,
  `feed_grace_min` and the gate in `_blocked` are gone, the vitals never mention feed EC, and
  `ZoneSnapshot.feed_ec` takes the engine's default (3.0, as every install without a probe had).
  `Room()` loses its two feed arguments. The setup fingerprint no longer names the feed sensors, and
  `_without_feed` compares one saved before this without them, so an adopted room resumes. The
  integration drops `feed_ec_sensor`, `feed_ph_sensor`, `tank_ec_sensor` and `tank_ph_sensor` from
  the wizard, setup (`RETIRED_HARDWARE`: gone from a stored setup on its next save, refused if sent)
  and the `engine_config` descriptor, and `number.crop_steering_<prefix>irrigation_{ec,ph}_{min,max}`
  join `_RETIRED`, removed from the registry at setup. The dashboard's tank EC/pH readings, sparklines
  and Tank History sheet (`tank-history.ts/.tsx/.css`) are removed. CS-206's and CS-207's catalog
  text no longer name the gate; the MCP server's hardware schema follows.
- **Nutrient batches (integration).** Rooms & setup maps `reservoir_distance_sensor` (a sensor in
  mm, cm or m), `fresh_water_switch`, `recirc_switch` and `doser_1_switch` … `doser_6_switch`
  (`room.RESERVOIR_KEYS`): each a switch of its own, never the pump, main line, waste or a zone valve;
  the descriptor carries them only when mapped. `feed.py` (pure) checks a room's feed document (the
  batch settings `fill_s`, `batch_l`, `empty_mm`, `settle_s`, `pause_s`, `mix_s`; `dosers` with
  `flow_ml_min`; the dosing `order`; up to 12 `recipes` with `strength` and per-doser `label` and
  `parts`, at most 60 mL/L; the `stage`) and plans a batch: `ml = parts × strength × batch_l`,
  `seconds = ml / flow × 60`, in the room's order. `feed_api.py` stores it
  (`crop_steering.feed.<entry_id>`) with services `feed_get` (read), `feed_save` and `feed_mix`
  (administrator; `feed_mix` presses the room's button and is refused while the plan has a
  `problem`). New entities per room: `sensor.crop_steering_<prefix>feed_plan` (the plan the
  controller runs), `select.crop_steering_<prefix>feed_stage`,
  `switch.crop_steering_<prefix>auto_batches` (off) and `button.crop_steering_<prefix>mix_batch` (a
  new button platform).
- **Nutrient batches (controller).** `_batch_tick`, first in every pass for each room with a
  reservoir: `idle` → `filling` (fresh water on for `fill_s`) → `settling` (recirculation on, then the
  pump, for `settle_s`; then, with a level sensor and a mark, the level must read short of
  `empty_mm`, else CS-702 and no dose) → `dosing` / `pausing` (each dose's doser for its seconds,
  `pause_s` between; a plan with a dose over 1800 s is not run) → `mixing` (`mix_s`, then the pump
  off before the recirculation). It starts on a new Mix a Batch Now
  press (the first state seen is a baseline, a press seen more than 30 minutes late is ignored, and
  with a level sensor and a mark the reservoir must read almost empty) or, with `auto_batches` on,
  after `BATCH_LOW_PASSES` (3) almost-empty readings, once until the level reads fuller (`armed`).
  `_batch_refusal` names why one cannot start (CS-703): the plan's `problem`, a missing mapping, the
  watering switch or the room off, a latched fault, a pending setup, or anything it uses (its
  solenoids and dosers, the pump, the main line, every zone valve) not reading off. While a batch
  runs `_blocked` holds the room's shots, and every room's while one fills or doses
  (`BATCH_TIMED`); `run()` sleeps only until the step is due, and while one fills or doses
  `_wait_for_next_pass` checks it every `BATCH_WATCH_S` (5 s) and stops it at once when it must
  stop (`_batch_watch`), so switching watering off stops the fresh water within seconds. Switches are read back; a stop part-way
  (CS-701) switches off what was on and one that will not read off latches CS-301. The batch is kept
  in `state.json` as a room's `_batch` (`restore_batch`: any missing or malformed key takes its
  default), so a crash is switched off at the next start and SIGTERM (`_safe_off`) switches it off
  and says so once. `sensor.crop_steering_<prefix>batch_status` reports it, with times carrying their
  UTC offset. The setup fingerprint names `reservoir` only when one is mapped, so an existing room
  keeps its adoption.
- **Nutrient batches (dashboard, MCP).** The Reservoir page (`pages/reservoir.tsx`; `lib/feed.ts`
  mirrors `feed.py`'s plan and checks, `lib/feed-status.ts` reads the batch status, `lib/feed-demo.ts`
  serves the demo), with a pointer-events drag list for the order; a Reservoir & dosers card in Rooms
  & setup; `feed_*` calls are room-scoped; `autoBatches` joins the room view, and the reservoir's
  switches are never written directly. CS-701, CS-702 and CS-703 join the catalog. The MCP server's
  hardware schema takes the new keys.
- **Start on boot (controller app).** `addons/f2_control/config.yaml` `boot: manual` becomes
  `boot: auto`. Supervisor uses an app's saved Start on boot when its owner has ever set one and the
  app's default otherwise (`App.boot`: `persist.get(ATTR_BOOT, <default>)`; installing saves no
  choice), so an existing install nobody switched starts with the host after this update and one
  set by hand keeps its setting. `tests/test_controller_boot.py` holds the default. INSTALL.md's
  move from the retired mirror now turns the new app's Start on boot off until the move is done.

## [2.25.0] - 2026-09-27

Integration and controller **2.25.0**.

Eight changes from JakeTheRabbit/HA-Irrigation-Strategy (its pull requests 119 to 125 and 127), What's new
linking to this repository's releases, and Auto Setpoints without the Cloudflare judge. Checked by the lean, controller, engine, real-Home-Assistant (2026.9.3 and
2024.10.0) and browser suites; not run on hardware before release.

- **Each zone says what it is waiting for next**, in the controller's own numbers: for example "shot when
  VWC < 61% (now 58%) · dilution if pwEC > 3.6 (now 3) · P3 by 10:00 PM". It is on the zone cards, in a
  zone's details and at the end of its grow-day line, and only while the controller is watering the zone.
- **One watering switch per room.** System Enabled and Auto Irrigation Enabled did the same job as the
  room's watering switch, less well: a shot already running carried on. They are retired and hidden. If
  either one is off, the room's watering switch is switched off in its place, so nothing starts watering
  by surprise.
- **Switching a zone off stops a shot already running in it**, within a few seconds, as the watering
  switch does. The "shot stopped early" notice now says which switch stopped it.
- **One switch over every zone**, in the zones heading on the Overview and Zones, like the header toggle of
  a Home Assistant entities card: off pauses every zone, on switches every zone on, after a review.
- **Configure shows and saves the lights hours the controller actually uses.** It showed the hours
  recorded at setup, and saving there changed nothing the controller read. One room ran its morning ramp
  at 3 AM with its lights off because of it.
- **Water today can show per plant** (Settings → Appearance), each zone's water and daily limit divided by
  its plant count. It is the room's choice, so everyone sees the same, and the vitals notification follows
  it: "344 mL/plant day" instead of "12.4L day". The zone total stays the default.
- **The vitals notification no longer says "feed EC —"** in a room with no feed EC probe.
- **What's new.** After an update, the first person to open the dashboard sees the main changes, once;
  Help & tools shows them again. Its links go to this repository's release notes.
- **Auto Setpoints works from each zone's own readings only.** The optional Cloudflare AI judge is gone,
  with its three controller settings, so the same readings always give the same targets. If you had set it
  up: the P2 shot size it adjusted stays where it is and is yours to set again, and each zone goes back to
  the peak it learned itself.

### 🔧 Technical notes

- **Configure's lights hours.** `async_step_edit_zones_map` opens on the live
  `number.crop_steering_<prefix>lights_on_hour` and `_lights_off_hour` and writes them with
  `_set_live_numbers` before the save's reload; a save that leaves them alone writes back what is live.
- **Retired switches.** `switch.crop_steering_<prefix>system_enabled` and `_auto_irrigation_enabled` are
  named "(retired)" and hidden (`entity_registry_visible_default=False`; existing registry entries get
  `hidden_by=integration` at setup). The controller no longer gates on them: `_carry_retired_switches`
  switches the engine switch off while either reads off, raises CS-208, and `_blocked` says so. Deleting
  them waits until no older controller is left: one before this reads a missing switch as off.
- **A zone switched off stops its running shot.** `_wait_shot` reads
  `switch.crop_steering_<prefix>zone_N_enabled` with the engine switch, Room Active and manual override
  every round (at most 2 s apart); CS-305 names the switch that stopped the shot. Catalog updated.
- **What each zone waits for.** `crop_steering_engine.waiting_for(snapshot, params)` is pure and pinned to
  `decide()` by its tests. The controller publishes `sensor.crop_steering_<prefix>zone_N_waiting_for_app`
  every pass (state: the phase; attributes `conditions` and `at`). The dashboard shows it for the phase
  shown, while the controller waters the zone, from a list at most five minutes old.
- **Every zone at once.** `AllZonesSwitch` (`components/room-controls.tsx`) and `lib/all-zones.ts`; it
  writes the zones' own switches through the review.
- **Water today per plant.** `select.crop_steering_<prefix>water_today_view` ("Zone total" or "Per plant",
  `WATER_TODAY_VIEWS`), restored like the other selects. The dashboard reads and writes it
  (`lib/water-view.ts`; a plan does not own it), and `WaterUse`, `Metrics`, `zoneBreakdown` and
  `PlanCellContext` take each zone's plant count. The controller's vitals divide `daily_vol` by the plant
  count it sizes shots with when the room says `PER_PLANT`, pinned to the integration's words by a test.
- **Vitals and feed EC.** `_maybe_notify` adds `| feed EC …` only for a room with `feed_ec_sensor`, and
  says "unreadable" for one that reads nothing usable, since the source-water gate then holds it.
- **What's new.** `custom_components/crop_steering/WHATS_NEW.md` is served by `whats_new_get`;
  `whats_new_seen` moves one installation-wide record (`.storage/crop_steering.whats_new`) forward, for any
  signed-in user. A new installation starts at its own version. `tests/test_whats_new.py` requires the
  release's section. `RELEASES_URL` (`lib/whats-new.ts`) is
  `https://github.com/ChillingSilence/HA-Irrigation-Strategy/releases`.
- **No Cloudflare judge.** `jev_policy.py` and the `cf_account_id`, `cf_api_token` and `cf_gateway_id`
  options are removed. `auto_setpoints.working_peak` is the learned peak (no `peak_adj`), `p2_shot_size` is
  no longer managed or written, and `sensor.crop_steering_<prefix>zone_N_auto_setpoints` no longer has
  `jev`, `jev_last`, `jev_changed_today` or `working_peak_adjust`. `setpoint_supervisor.desired` takes the
  P2 shot size as a number; `Steer`, `evidence` and the `Supervisor` judge are gone.
- **Upgrade.** Supervisor drops the three Cloudflare options from an old configuration, and a saved zone's
  learned state loses the judge's keys (`peak_adj`, `jev`, `veto`) on load and keeps everything it learned
  (`tests/test_state_migration.py`). Each room gains its Water today select at "Zone total". The first
  start creates the What's new record as unknown, so the first dashboard visit shows the last 30 days of
  releases once.

## [2.24.0] - 2026-09-26

Pair: **controller 2.24.0**. Class **C3**. The controller changes in five ways (an offline switch
holds a shot, a dead probe gets 15 minutes' grace, a room switched back on within a day carries on, a zone
can be moved to a phase by hand, and the controller keeps reporting through a long shot). The integration
adds one select per zone and retires the entities and services nothing used (C2). The dashboard's wording
changes (C1). **Owner-approved rehearsal release** (the owner, 26 September 2026, asked for every open pull
request to be merged and released together, so this release carries several C2 and C3 changes at once), no
staging soak; see the release audit. Not run on hardware; the seven pull requests were merged together and
checked by the lean, controller, engine, real-Home-Assistant (2026.9.3 and 2024.10.0) and browser suites.

- **No shot starts while the pump, main line or a zone's valve is offline.** On 25 Sep F2's pump, main line
  and valves dropped out of Home Assistant for 45 minutes. The controller watered into them anyway, could
  not confirm anything had closed, and locked the room with a hardware hold for seven hours. Now the zone
  waits, its status names the offline switch, and it waters as soon as the switch reads again. Nothing
  opens, so nothing locks.
- **A moisture probe has to be out for 15 minutes before it counts as dead.** A Home Assistant restart or a
  sensor reconnecting no longer fires backup-timer shots or "moisture sensor not reporting" notifications.
  A probe that is really dead is handled as before, 15 minutes later.
- **A room switched back on within a day carries on where it was.** Switching F2 off and on to clear that
  hold sent every zone from P2 back to a fresh P1 ramp and reset today's counts. Now the phases, today's
  water and shot counts and the learned values are kept. A room that was off for longer than a day (an
  empty room between crops) still starts afresh.
- **Move a zone to a phase by hand.** Open the zone from Zones or Overview and pick P0, P1, P2 or P3 under
  **Phase**. After the review the controller moves it within a minute and carries on from there:
  lights-off still takes it to P3 and lights-on to P0. Today's counts stay. Home Assistant has a
  **Zone N Set Phase** select for the same thing, for automations.
- **The controller keeps reporting while it waters.** A long shot no longer makes the dashboard say
  "Controller not running", or every zone "Controller not reporting". Once a minute during a shot the
  controller repeats its last report. A controller that really stops is still flagged as before.
- **Each irrigation setting says what it does.** The Irrigation plan uses one name per setting everywhere,
  taken from the Athena Handbook where it has a term ("Peak VWC target", "Maintenance shot when below",
  "P3 dryback target"), with a line of help, a tag saying which way it acts and a **?** with the detail.
  Only the words change: no value, entity or decision.
- **A room that isn't watering says which switch stopped it.** The dashboard calls the room's engine switch
  **Watering** (Settings → Watering). The status line names the switch that stops a room (watering, System
  Enabled or Auto Irrigation Enabled) and links to Settings when the switch is there.
- **4 unused services and 43 unused entities are gone** (43 on a one-zone room, more on bigger rooms): a
  button that did nothing, switches for a layer that never shipped, settings nothing read and two sensors
  that were always "unknown". An existing room loses them the first time it starts; every setting in use
  keeps its entity id and value. The removed services only fired an event nothing listened for.

### 🔧 Technical notes

- **Offline feed path (#116).** `_blocked` checks last of all whether the zone's pump, main line or valve
  reads anything but `on`/`off` (`unavailable`, `unknown`, missing, or Home Assistant unreachable), and
  returns `<switches> offline (reads neither on nor off)`: nothing is opened and no hardware hold latches.
  Before, `ha_call` counted HTTP 200 as success and Home Assistant accepts `turn_on` for an unavailable
  switch, so the shot ran blind and failed its close read-back. A switch that goes offline during a shot
  still latches CS-301. The pH gate's in-grace `return None` became a fall-through so the check runs there.
- **Dead-probe grace (#116).** `Room._blind_since[z]` records when a zone's probe was first seen unreadable
  in this run; a readable probe clears it. Until `BLIND_GRACE_MIN` (15) has passed, a blind zone decides
  `(False, 0, Reason(..., "blind_wait"))`: no timer shot, no sibling copy, no CS-102. The time rules still
  apply. `docs/error-codes.json` (CS-102, CS-302 to CS-304) and `ERROR_CODES.md` are updated.
- **Room resume (#114).** `_loop_room` records `room._off_since` when Room Active goes from on to off and
  saves it as `_room_off_since` in the room's state block; `_room_switched_on` changes nothing when that is
  under `ROOM_RESUME_H` (24 h) ago. A room already off when the controller started has no known switch-off
  time and still starts a fresh run. An old state file has no such key and loads as before.
- **Phase by hand (#115).** `select.crop_steering_zone_N_set_phase` (`SET_PHASE_OPTIONS`: Keep, P0 to P3), a
  RestoreEntity. `_apply_phase_request` runs first in each zone's turn: it resets the select to Keep and
  only if that call succeeds moves the zone (P1 zeroes `shots`, P0 zeroes `peak`, daily counts are kept),
  logs `Z1 phase P1 -> P2, set by hand` and saves. It actuates nothing, so it does not need the kill
  switch. The dashboard's zone details get a Phase section with a review.
- **Keep-alive during a shot (#97).** `_wait_shot` calls `_keep_alive(remaining)` once per round: a room's
  heartbeat and its zones' status labels are repeated once they are 60 s old, at most two writes per
  round with short timeouts, so the kill switch is still read about every 2 s. `_report_before_acting`
  reports a room before its first shot after a restart or a switch-on. The new `Room` fields are runtime
  only. `ha_set` gains an optional `timeout`.
- **Setting words (#113).** `frontend/src/lib/setting-words.ts` holds each setting's label, short form,
  help, direction tag and explainer, read by the Irrigation plan, the Schedule, the charts, the Overview's
  timeline, water delivery and Help. The explainer is a Radix Popover (no new dependency).
- **Watering switch (#117).** `roomStatus()` checks the controller's `_blocked()` order: the engine switch,
  then `system_enabled`, then `auto_irrigation_enabled`, off or unreadable. `RoomStatus.action` renders as
  a link that selects the line's room first. Settings' "Room scheduling" is now "Watering".
- **Retired surface (#112).** Services `transition_phase`, `execute_irrigation_shot`,
  `check_transition_conditions` and `custom_shot`; the button platform; the `analytics_enabled`,
  `intelligence_*_enabled` and `zone_N_dripper_protection` switches; unused numbers, selects and two
  sensors (the full list is in #112). `_RETIRED` in `__init__.py` and `_remove_retired_entities`, run in
  `async_setup_entry` before the platforms load, remove this entry's registry entries for them, proven by
  an in-place upgrade test in `tests_ha`.
- **Combined tree.** `settings.tsx` and `USER_GUIDE.md` keep both #114's and #117's wording; #97's
  first-pass test uses `no_blind_grace`, since under #116 a blind zone no longer waters on the first pass.
## [2.23.0] - 2026-09-25

Pair: **controller 2.23.0**. Class **C1**: the dashboard, translations and documentation change; nothing
the controller or the integration decides changes. The controller's code changes in comments only (its
syntax tree is unchanged). **Owner-approved rehearsal release** (the owner, 25 September 2026), no staging
soak; see the release audit. Not run on hardware; checked by the lean, controller, real-Home-Assistant and
browser suites.

- **The Overview shows how today is tracking.** Each zone's lane on the grow-day chart now draws the
  target each phase is aiming for, yesterday's line and a dashed projection of the rest of the day. One
  line per zone sums it up: moisture now against yesterday at the same time, when the P1 target was
  reached, water so far against yesterday, and the morning dry-back. **Compare with** switches between
  yesterday, a typical day (the middle of the last seven) or nothing, and each layer can be hidden. On a
  laptop each zone's line stays on one row; point at it to read all of it.
- **Repairs cards link to the answer.** "Learn more" on a Crop Steering Repairs card opened the project's
  front page. It now opens the error-code guide, which explains the code every card carries.
- **Clearer wording.** Two Repairs cards call the controller by its app-store name, and three controller
  app settings that showed bare names now have a name and a description.
- **The online demo uses your own time zone** for its sample grows.
- **A new README.** The front page explains in plain words what the system does, with a current
  screenshot of every feature. Dated internal logs, unused files and retired history are gone.

### 🔧 Technical notes

- **Timeline tracking (#101).** `day-timeline.tsx`: a target step line per lane (the phase target, a
  setpoint changed mid-day, the plan's targets when one is armed), yesterday aligned by hours since its
  own lights-on with its shot ticks, and `projectFrom()` beside `projectDay` (whose output is unchanged)
  for the dashed projection and expected-shot ticks. Legend switches and "Compare with" (Yesterday,
  Typical as a p25 to p75 band, None) are remembered in the browser. From 1024 px wide the tracking line
  is one row with an ellipsis and a tooltip, so the Overview stays within two screens at any hour (1558
  px by day and 1574 px at night, at 1440 by 800).
- **Repairs link and unused code (#105).** `REPAIRS_DOCS_URL` (`docs/ERROR_CODES.md`) replaces a wiki
  page that did not exist, in `health.py` and `stock_api.py`. Unused constants, `_validate_entities`,
  three errors nothing raised and three translation strings nothing used are removed.
- **Wording (#102, #108).** The CS-601 and CS-602 descriptions; the `notify_service` example; add-on
  translations for `instance_name`, `hold_entities` and `rediscover_seconds`. Comments in the controller,
  the engine and the integration describe events without naming one site's rooms or devices.
- **Demo (#107).** `demoTimeZone()` dates the demo's runs in the browser's time zone.
- **Tests and CI (#99, #103).** The disabled CodeQL and duplicate install workflows and the Lovelace
  generator are removed. `axe()` in `verify-workspace.mjs` waits for colour transitions to finish, which
  fixes a contrast check that failed at random.
- **Docs (#104, #106, #110).** The README is rewritten with three new screenshots; `docs/audits` keeps
  only the first-run review; entries before 2.13.0 move to this file's git history; em and en dashes
  leave the docs' prose; references to the archive tags are removed.

## [2.22.0] - 2026-09-25

Pair: **controller 2.22.0**. Its code is unchanged: the app serves the new dashboard. Class **C2**:
stock tanks add integration entities, services and a Repairs card. Every other change is class
**C1** (dashboard only, nothing the controller or the integration reads) or **C0** (CI).
**Owner-approved rehearsal release** (the owner, 25 September 2026), no staging soak; see the
release audit. Not run on hardware; checked by the lean, controller, real-Home-Assistant and
browser suites.

- **Stock tanks.** A new Stock tanks page keeps track of the nutrient concentrates each batch tank
  is dosed from. Give each one its size, how much goes into one batch and a low mark. Every batch
  tank made takes its dose from every stock tank: it is counted when the tank's last-fill time
  moves on, or with **Record a batch** in a room without that sensor. The dose can follow a
  doser's own dose setting. At the low mark a Repairs card (CS-608) and an Overview notice say
  about how many batches are left, and `sensor.crop_steering_<room>stock_low` rises above 0 for a
  phone alert. **Refilled** or **Set level** clears it.
- **The Overview reads at a glance.** Each zone shows how fast it is drying, in VWC points per
  hour with a line of its last two hours; water today against its daily limit (amber from 80 %,
  red once spent); moisture against the current phase's target; and green or red valve pills.
  The four room numbers get one small bar per zone and an average per zone.
- **The same visuals on every page:** Zones, the zone sheet, Sensors (with a six-hour line for
  every numeric sensor), Activity, Insights, Compare runs, Rooms & setup and Settings. Colour only
  ever means a state.
- **Water use per zone** on the Zones page: today, this week, since the grow started and an
  estimate for the whole grow, with a bar of litres per grow week. It reads Home Assistant's
  long-term statistics, which it keeps for good.
- **Type the balance into the whole-grow table.** On the Schedule page, click a week or a day,
  type 0 to 100 (% generative) and press Enter. Under the table: the setpoints that balance gives,
  how far it moves from the week before and to the week after, the zone's readings today and the
  balance across the grow. Nothing is saved until Review & save.
- **The tank card graphs its EC and pH.** A 24-hour line beside each value, and a History panel
  over 24 hours, 7 days or 30 days. Where the controller checks feed water on a probe, its limits
  are drawn too.
- **No false "Controller not running" while it waters.** The dashboard now waits 10 minutes, the
  integration's own limit, before calling the controller silent. While a zone valve has been open
  no longer than the room's maximum shot, it says **Watering** instead.
- **The sidebar page updates itself.** Its address carries the version, so a browser fetches the
  new dashboard after an update instead of showing the old one for hours.
- **The online demo follows each release** (CI).

### 🔧 Technical notes

- **Stock tanks (#91, C2).** `stock.py` holds the pure rules (`clean_tanks`, `dose_ml`, `draw`,
  `refill`, `parse_fill`, `new_batch`, `batches_left`). `stock_api.py`'s `StockStore` keeps each
  room's tanks in `Store(hass, 1, "crop_steering.stock.<entry_id>")`, revisioned behind a lock;
  a change becomes the room's data only after the save succeeds, and corrupt stored data is
  reported, never overwritten. Batches are counted from `async_track_state_change_event` on the
  room's `tank_last_fill_sensor`: the first time seen is a baseline and only a strictly newer one
  counts. Services `stock_get` (read-only) and `stock_save`, `stock_refill`, `stock_record_batch`
  (admin, `expected_revision`). `sensor.crop_steering_<prefix>stock_low` (count of low tanks,
  tanks as attributes, not polled). Repairs `stock_low` is in `health.ISSUE_IDS` and survives a
  room switched off. Error code CS-608.
- **Panel cache (#89).** `setup_panel.py` registers `dashboard.html?v=<SOFTWARE_VERSION>`.
- **Mini visuals (#90, #95).** `lib/dryback.ts` (`drybackTrend`: a least-squares slope after a
  5-minute settle, at least a 10-minute span, a 2-hour window) and
  `components/mini-visuals.tsx` (`MiniBars`, `Meter`, `Sparkline`, `.pill`), used on every page.
  Sensors asks Home Assistant for all its lines in one history request.
- **Water use (#94).** `lib/water-use.ts` and `components/water-use.tsx`:
  `recorder/statistics_during_period` (hourly) inside Home Assistant, REST history when opened
  standalone. Grow-days start at lights-on; a grow-day's total is its counter's peak after the
  reset. The start comes from the plan when it is armed or saved, else the first day with water
  after at least five dry grow-days.
- **Whole-grow table (#93).** Each cell is an input: a whole number 0 to 100, applied on Enter or
  blur, Esc cancels, arrows and Tab move. `grow-plan.ts` gains `columnRange`, `rangeBlock`,
  `parseBalance` and `setpointRows`; `replaceRange` rejoins matching neighbours. Read-only while a
  plan is armed or active.
- **Tank history (#96).** `lib/tank-history.ts` and `components/tank-history.tsx`. The dashboard's
  history reads also allow the room descriptor's `tank_ec_sensor` and `tank_ph_sensor`, up to
  720 hours, one day per request with two in flight. Gate lines only while `feed_ec_sensor` /
  `feed_ph_sensor` are mapped, as `controller.py` applies them.
- **Watering, not silent (#98).** `HEARTBEAT_STALE_MS` goes from 5 to 10 minutes. `shotRunning()`
  (a mapped zone valve ON for no longer than the room's `max_shot_duration`, else 900 s) turns
  the stale `-controller` notice into an info "Watering" and the status line into Watering.
- **Demo (#92, C0).** `promote.yml` dispatches `pages.yml` on `main` after its apply step.
- The three dashboard bundles are rebuilt from the merged source.

## [2.21.0] - 2026-09-25

Pair: **controller 2.21.0**, one number for both halves from this release on. Class **C3**: the
controller and the integration change; the engine does not. **Owner-approved rehearsal release** (the
owner, 25 September 2026), no staging soak; see the release audit.

The Overview timeline is class **C1**: dashboard only, nothing the controller or the integration
reads. Not run on hardware; checked read-only against a live room's recorded history. A shot cut
short by something else is class **C3** (irrigation behaviour, controller only). Not run on
hardware; the 23 September event is replayed in the controller suite. A shot interrupted by a
Home Assistant restart is class **C3** (controller only). Not run on hardware; the restart is
replayed in the controller suite.

The dashboard changes below are class **C1**: dashboard only, nothing the controller or the
integration reads. Not run on hardware; checked by the browser contract scripts.

- **The Overview shows the day, first.** Its moisture and EC chart is replaced by the room's
  grow-day, at the top of the page under today's totals, from lights-on to the next lights-on, one row per zone on one time axis: lights-off shaded, the
  phase each zone was in, every shot (the valve opening, as wide as it was open), what held a zone
  back and for how long (a spent daily budget hatched red, *blocked 13:31–22:00*; a gate such as a
  dosing hold or the kill switch outlined amber), and every setpoint change, from what to what.
  Point at or tap any of it for the details; the same events are listed in words below.
- **What comes next is marked as an estimate.** The rest of the day is drawn dashed: P2 until
  lights-off and P3 from there. For a zone in P2 whose moisture has been falling steadily since
  its last shot settled, the dry-down is drawn to its re-water threshold: *next shot ≈ 14:20*.
  With too little recent data, a shot running or a hold open, it says why there is no estimate
  instead of guessing. A zone in P1 shows its next shot from the ramp's interval, one in P0 the
  latest time P1 can start; how long P0 and P1 last is not drawn, because nobody knows.
- **One line per zone:** its phase and for how long, P1 shots so far against the ramp's maximum,
  litres used against the daily budget, and the next expected shot. Moisture is scaled to the
  day's own readings, not 0–100 %; zones are named, never told apart by colour alone; red, amber
  and green only ever mean a state. The age of the newest reading is shown, and it fits a phone.
- **No new polling.** The day's history is read once when the Overview opens (inside Home
  Assistant over its own connection) and kept current from the updates the dashboard already
  receives.
- Insights keeps its moisture and EC chart.
- **Headings say what the page is, once.** The Overview is titled after its room (*Flower 1
  overview*). The sentences under page headings that only repeated them are gone; Today's targets
  and Scheduled targets keep theirs, because they say how a schedule and a draft behave.
- **The Overview is the room now.** Water per zone and per plant is on Zones, which already had
  it; the zones table keeps each zone's water today. The scheduling summary is gone: the status
  line at the top of every page already says whether the room is watering and why not. Recent
  activity opens beside any page from the top bar, and the daily workflow is now a linked daily
  routine at the top of Help & tools.
- **The Overview is shorter and balanced.** Under the grow day, the zones sit beside the tank
  instead of below it (on a phone they stack as before). The tank card has the same space above
  the tank and *Tank EC* as beside them, where before they sat flush under the heading, and shows
  the level, EC, pH and temperature with the pump, filling and last fill in one row, and one
  short line on what the pump and fill readings do not prove. The zones
  table carries each zone's target under its moisture and fits without scrolling sideways. The
  sentences under panel titles and the captions under today's totals moved into tooltips. At
  1440 px wide the Overview is under two screens tall; it was more than three.
- **A calmer look.** No text smaller than 12 px anywhere (118 places were 7–11 px, and the
  plan graph's labels 10.5–11 px), page and panel titles and today's totals in one semibold weight, no divider under every panel title, no shaded band behind
  table headers, neutral status chips with a coloured dot, and a quieter menu. Colours still
  follow your Home Assistant theme.
- **A shot that something else cuts short now ends there, and only the water it gave is counted.**
  On 23 September at 11:25 the batch tank ran empty 4 seconds into a zone 1 shot. The dosing
  automation took the tank and its pump, and the feed guard closed the valve and main line. The
  controller did not notice: it waited out the full 170 seconds and counted about 7.9 litres for
  about 0.2 litres delivered. It now checks during every shot, about every 2 seconds: when one
  of its holds (dosing, a tank fill, a flush) comes on, or the zone's valve is switched off by
  something else, the shot ends there and only the seconds the valve was open are counted. It
  closes its own valve and main line if they are still open, never touches a pump a hold is
  using, and sends one alert saying what ended the shot. A feed path closed by somebody else is
  not a hardware fault. Nothing is switched off on a timer, and the kill switch and manual
  override work as before.

- **A shot interrupted by a Home Assistant restart is closed, not left running.** If Home Assistant
  restarted (an update, a power blip to the host, a crash) or a valve's device reconnected while a
  shot was open, the valve kept running: after a restart Home Assistant says every switch changed
  just then, so the controller took its own open valve for someone hand-watering and left it on,
  with no alert. It now reads the valve's history: ON since the shot opened it, with only the
  restart in between, is the shot's and is closed (valve first, then the main line and pump, as
  always). A valve someone switched off and on again, or had on before the shot, is still left
  alone. If Home Assistant has no history for it, nothing is switched and the *may still be ON*
  notification (CS-309) says so, every loop until it can tell.

### 🔧 Technical notes

- New `frontend/src/lib/day-timeline.ts` (pure, tested): `growDay()` (lights-on to the next
  lights-on in the browser's time zone, as `foldRecorded` folds days), `phaseBands()`,
  `valveShots()`, `alignBands()`, `zoneBlocks()`, `setpointChanges()`, `levels()`, `readings()`,
  `dryDown()` (least squares over the last hour from 15 minutes after the last shot ended: at
  least five readings over at least 15 minutes, falling at least 0.1 %/h), `nextShot()` and
  `appendLive()`.
- Shots are the zone valve's on→off intervals (valves from the room's `engine_config`). The
  controller posts a loop's decision and phases after that loop's shots, so a shot is named by
  the first `current_decision` row after its valve closed (its `fired` entry,
  `Z<n> <phase> <reason>`), and a phase change posted by the same loop starts at the shot
  (`alignBands`). Holds are the zone's `current_decision` `blocked` entries, one interval per
  unbroken run of the same hold (numbers in the text may change): `daily-cap` is the budget,
  `BLOCK` a refusal, anything else a gate.
- Loading: `Controller.timeline(request)`. Inside Home Assistant, `history/history_during_period`
  on `hass.connection` (`live.ts` `liveHistory`): states without attributes and
  `minimal_response`, and the decision sensor with attributes and
  `significant_changes_only: false`. Standalone, `GET history/period` in chunks of 40 entities
  (`client.ts`). Limited to the selected room's entities and mapped valves, and to one grow-day.
  Loaded once per room and grow-day; `appendLive()` then adds each subscribed (standalone: each
  polled) change.
- Demo: `demoDay()` generates a grow-day on the demo probes' own day shape (P0, six P1 shots, P2
  top-ups, P3), shifted per probe, with a feed-EC hold on Flower 2 zone 2 ended by a feed-band
  change and Flower 1 zone 3 held since it was disabled.
- `pages/overview.tsx` renders `components/day-timeline.tsx` in place of `HistoryChart`, which
  stays on Insights, directly under the totals strip and above the tank and zones.
- `Heading.description` is optional. `pages/overview.tsx` titles itself `${room.name} overview`
  (plain *Overview* when no room is discovered). `.page-heading` margin 30/25 → 20/20 px (16/16 on
  a phone).
- New `components/activity-panel.tsx`: a top-bar button on every page opens a right-hand sheet
  with the room's last ten events (`EventList`) and a link to Activity. The Overview loses its
  Recent activity panel, the daily workflow card (now `ol.daily-routine` in Help's intro), the
  `DailyWaterSummary` table (still on Zones) and the `room-summary` block; their CSS goes with
  them.
- `.overview-grid` (zones `7fr`, tank `3fr`; one column under 1200 px). `ZoneTable({ compact })`:
  no *VWC reference* or arrow column and no zone icon, the target under moisture (its label
  wraps), `LastIrrigation({ compact })` without the date line. `components/tank-status.tsx` rewritten compact: a 100×120 drawing whose
  shape touches its box, `dl.tank-quality` and `dl.tank-equipment`, one 20 px inset; the hooks
  and value strings are unchanged. `Metrics` shows only the *waiting for controller data*
  caption. `DayTimeline` loses its heading paragraph. `verify-tank-status.mjs` holds the tank's
  top inset to its left inset.
- `styles.css` set its type and chrome twice: the original rules, then a later "Home
  Assistant-native density" block overriding them (`h1` 26/400 over 28/650, `h2` 20/400 over
  17/650, panel heading padding, table sizes, metric weight, nav weights). Each is now set once,
  in the original rules, and several changed: `h1` 24px/600, `h2` 16px/600, table text 13px with
  no header band, today's totals at weight 600; the later block keeps only the theme mappings. New `:root` tokens
  `--text-xs`…`--text-2xl` (12–24 px) and `--space-2`…`--space-6`. New `lib/type-scale.test.ts`
  fails any stylesheet under `frontend/src` that sets text below 12 px, a relative size without
  a 12 px floor (`.unit` is now `max(0.52em, 12px)`), or chart text below 12 px (the plan graph's
  `fontSize` 10.5/11 → 12). `.status-good` is a
  neutral pill (it leaves the `--primary-strong` contrast list); `nav button.active` has a
  neutral fill with a 2 px accent bar.
  The Overview's compact zones table keeps ages and units on one line at the larger table
  text; phone-only panel title sizes (18/20 px) are gone.
- **Controller** (`controller.py`), a shot cut short from outside: in every round `_wait_shot` also
  reads each `hold_entities` entity (ON as `_blocked` reads it, the shared `ON_STATES`) and the
  shot's own valve, with the same bounded reads and sleeps of at most 2 s between rounds, after the kill
  switch, `room_active` and manual override, which therefore still win. It returns
  `(elapsed, None | ("abort", entity) | ("external", entity))` instead of `(elapsed, bool)`. The
  valve reading OFF counts only once it has been seen ON in that shot: right after `turn_on`, Home
  Assistant can still show the old OFF (a Zigbee report can lag 1.6 s). `_execute_shot` hands an
  external stop to the new `_close_cut_short`, which switches off the shot's valve and main line
  unless they read OFF, and its pump unless it reads OFF or a hold is ON (the `_inflight_plan`
  rule). It reads back only what it switched off: a switch of its own that will not close still
  latches the hardware hold and keeps the record for the reconciler. Otherwise it clears
  `shot_inflight` as the normal close does. The error cleanup, which switches off all three, never
  runs for such a shot. Counted time: the valve's `last_changed` when it reads OFF and that falls
  between the valve opening and the detection, else the detection. Counters as for a kill-switch
  abort: the shot counts, with the volume delivered. One alert, `cutshort_<room>_z<n>` (*shot
  stopped early, something else closed the feed*, CS-307), debounced like the others, names the
  entity and the seconds delivered against planned. No change to add-on options, the state file,
  entities or the normal shot.
- **Controller** (`controller.py`), an interrupted shot after a Home Assistant restart: when a
  switch the in-flight record names reads ON with `last_changed` outside `INFLIGHT_OPEN_WINDOW_S`,
  `_inflight_plan` no longer hands it to a person on that alone. New `ha_history()` reads
  `GET history/period/<start>` (`minimal_response`, `no_attributes`, `end_time` now) from the
  window's start, and the pure `_on_since_shot()` decides: ON inside the window with only
  `unavailable`/`unknown` after it is the shot's (closed as before, with the line-in-use and hold
  rules unchanged); ON before the window, first ON after it, or an OFF after the shot opened it is a
  person's (left, record closed); no readable history, or a row it can't read, is `unsure` (CS-309,
  record kept, retried every loop). CS-309's catalog entry and alert text say so. The add-on test
  rig gains `FakeHA.ha_history` and an autouse fixture so no test reaches a real history endpoint.


## [2.19.5] - 2026-09-23

Pair: **controller 0.16.5**. Class **C3**: engine, controller and integration. **Owner-approved rehearsal
release** (the owner, 23 September 2026), no staging soak; see the release audit.

The irrigation changes (engine and controller) are class **C3**; the plan, setup and Repairs changes
are class **C2**. The zone status change is class **C3** (controller and integration).

- **A grow plan never stops a starving zone from being watered.** While a room's grow plan is held
  (in error, out of date, or missing after a restart) the controller held every shot on every zone
  the plan runs, for as long as the hold lasted. Now the overnight emergency shot, the lights-on
  watchdog and the minimum daily volume still water those zones; only the routine steering waits
  for the plan. A zone with a dead probe keeps its timed safety schedule too. The kill switch,
  a hardware fault, the zone switches, bad feed water and the daily budget still stop them, as
  before.
- **A missed minute at lights-on no longer holds a room all day.** A plan moved on to the new day
  only in the two minutes after lights-on. If Home Assistant was restarting then, or the
  controller or a probe was a few minutes late, the plan went into error and held every zone
  until the next lights-on. Now it applies the new day at the first minute it can, and keeps the
  previous day's targets until then. Changing the lights-on hour while a plan runs, or a lights-on
  hour that falls in the daylight-saving jump, no longer puts it in error either.
- **Zones cannot be changed under a running plan.** Setup now refuses to add or archive zones, or
  to archive the room, while its plan is armed or running, instead of saving the change and
  putting the plan in error. Disarm the plan first.
- **Repairs says when a plan is holding.** A card appears for every hold (the plan in error, the
  controller unable to use it, a zone the plan does not steer today), and a warning while a plan
  has not moved on to today, each with the reason.
- **The zone status sensor has one writer.** The zone status in Home Assistant had two authors
  taking turns about twice a minute: the integration, with a fixed 40 % moisture threshold
  (*Dry - Needs Water*), and the controller, with its phase-aware label (*Overnight dryback*). The
  controller now publishes its label on a separate entity, and the zone status shows exactly that,
  with its reason. When the controller has not reported for 10 minutes the zone status says
  *Controller not reporting* instead of guessing from a threshold. Cards and automations keep the
  same entity. Until the controller is updated too, the zone status shows the older controller's
  own label, as before, and is no longer fought over.

### 🔧 Technical notes

- **Engine** (`crop_steering_engine/core.py`, and the vendored copy): new
  `ZoneSnapshot.steering_held` (default `False`, so every caller is unchanged). When it is set,
  `decide()` skips the per-phase steering rules and the anti-lockout flush (it steers to
  `max_ec`, a plan setpoint) and fires only the P3 emergency, the watchdog and the minimum-daily
  floor; the high-EC blocks still apply and phases still move. Holding only the routine decision
  in the controller was not enough: a zone drying in P2 is a top-up first, so the watchdog behind
  it never came up.
- **Controller** (`controller.py`): `_snapshot` sets `steering_held` from `strategy_block`.
  `PLAN_HOLD_EXEMPT` = `p3_emergency`, `watchdog`, `min_daily`, `blind_fallback`,
  `blind_copy_rescue`; `_blocked(room, zone, reason)` lets those kinds through the plan hold (and
  logs it), and `_execute_shot(plan_exempt=True)` skips the plan preflight for them. The blind
  decisions are typed: FALLBACK is `blind_fallback`; COPY is `blind_copy_rescue` when the
  sibling's shot is one of the rescues, else `blind_copy`; none is exempt from the daily budget.
  A held zone that is not firing publishes the hold as its `block`, so the zone status and
  `current_decision` still show it.
- **Integration, plan** (`strategy.py`): `tick` applies the latest lights-on on the first tick
  that can (`_advance`), not only within 120 s of it. `activate` / `disarm` record
  `armed_at` / `disarm_at`, which take effect at the first lights-on after them by the current
  `lights_on_hour` (`_due`), so a changed hour re-anchors them; a day already applied is never
  applied again (`grow_day >= day`), and a later hour never takes the plan back a day. Lights-on
  is built per local date and compared in UTC (`_lights_on`, `_boundary`, `_next_boundary`): an
  hour inside a daylight-saving gap is the instant the clocks jump to, and `now - boundary` no
  longer compares wall clocks across a change. A recoverable fault (stale heartbeat, flag, zone
  switch or probe at lights-on, a failing hydraulic preview, an unreadable `lights_on_hour`,
  storage) keeps the last valid snapshot published and sets `degraded_reason` (a plan sensor
  attribute and a `strategy_get` response field), retried every tick. Only zones that no longer
  match the plan (or an archived room) are an error (`_Hold`), stored once instead of every
  minute. `async_init` no longer turns a missed lights-on into an error. The response's
  `armed_after` / `disarm_after` are computed from `armed_at` / `disarm_at` by the current hour.
- **Integration, setup** (`setup_api.py`): `safety_blockers` adds `_plan_blocker`: with a
  proposal, a change of the active zone set or archiving the room is refused while the plan is
  armed, active, disarming or in error. A change back to the plan's own zones is allowed.
  `remove_setup` passes its archive as the proposal. Covers `save_setup`, `remove_setup`, the
  options flow's zone map and `.env` reload.
- **Integration, Repairs** (`health.py`): `strategy_hold` (ERROR: plan status `error`, or a fresh
  heartbeat's `strategy_error`; WARNING: a zone the active plan does not steer today) and
  `strategy_degraded` (WARNING: `degraded_reason`), with `{reason}`; both cleared with the room's
  other cards when it is switched off. Translations in `strings.json` and `translations/en.json`.
- **Existing installs:** no state-file, option or entity-id change. A plan document stored by an
  older version (no `armed_at` / `disarm_at`) keeps working from its `armed_after` /
  `disarm_after`, and one stored in error with "Lights-on boundary was missed" applies its day on
  the first tick. An older controller with this integration sees fewer holds; this controller
  with an older integration still waters the rescues through its holds.
- **Tests:** `crop-steering-engine/tests/test_steering_held.py`,
  `addons/f2_control/tests/test_plan_hold_never_stops_rescues.py`,
  `tests/test_plan_never_holds_a_room_all_day.py` (stale heartbeat or probe at lights-on, Home
  Assistant down across it, the lights-on hour moved later and earlier, the Pacific/Auckland gap
  on 27 September 2026, a zone change while armed), new cards in `tests/test_health.py`, and
  `tests_ha/test_plan_holds.py` (the options flow refusing a zone change under an armed plan and
  saving it under a draft; every hold, and a plan that could not apply its day, in the real
  Repairs registry). `test_active_store_survives_reload_without_midday_reapplication` now asserts
  the stored snapshot stays active with a `degraded_reason` where it asserted the error, and
  `test_disarm_waits_for_next_boundary_and_survives_missed_boundary_restart` that the missed
  release is made on the first tick.
- **Zone status, one writer** (class C3: controller and integration). The controller publishes
  `sensor.crop_steering_<prefix>zone_N_status_app` (state: the `zone_status_label`; attributes
  `reason`, `friendly_name`, `engine`), `Room off` included, and no longer writes `zone_N_status`.
  The integration's `zone_N_status` (`CropSteeringZoneStatusSensor`, same unique id and entity id)
  mirrors it through `zone_status.mirrored_status`: the label and its reason, or
  `Controller not reporting` when the app entity is missing, `unknown`/`unavailable`, or its
  `last_reported` (else `last_updated`) is more than 10 minutes old, the engine-offline repair's
  limit. It is not polled: it updates on the app entity's `state_changed` and checks staleness
  every minute, and writes only when what it shows changes, so a 0.16.x controller still writing
  `zone_N_status` is left alone rather than overwritten every 30 s. With a controller from this
  release and an older integration, `zone_N_status` shows that integration's threshold label.
  `VWC_DRY_THRESHOLD` / `VWC_SATURATED_THRESHOLD` removed from `const.py`. The label and reason
  are now recorded on both entities; exclude `sensor.crop_steering_*_status_app` from the
  recorder to keep one copy. Tests: `tests/test_zone_status.py`,
  `addons/f2_control/tests/test_zone_status_one_owner.py`,
  `tests_ha/test_zone_status_one_owner.py` (an older controller's writes are not fought; with this
  controller there is exactly one writer). The two add-on tests that asserted the controller
  writing `zone_N_status` now assert `zone_N_status_app`.

## [2.19.4] - 2026-09-23

Pair: **controller 0.16.4** (no controller code change: it serves the 2.19.4 dashboard). Class **C1**:
dashboard only, nothing the controller or the integration reads. **Owner-approved rehearsal release** (the owner,
23 September 2026), no staging photoperiod; see the release audit.

- **The dashboard says when the controller is not running.** After a Home Assistant restart with
  the controller app stopped, its heartbeat simply disappears, and the dashboard looked normal:
  only a heartbeat that was present but old raised a yellow warning. A room that is switched on
  now raises a red *Controller not running* notice whenever the heartbeat is missing, unreadable
  or more than five minutes old, and its zone phases and statuses are marked *Stale*.
- **A status line on every page, for every room.** It says whether the room is watering, holding
  and why, or not watering and what to do about it (engine switched off, a setup change waiting to
  be adopted, stuck hardware, a grow plan hold, the controller stopped), and how old the
  controller's last report is: amber after two minutes, red after ten. Phones show it too.
- **Red notices are never pushed off the Overview.** Notices are ordered red, then yellow, then
  information. The Overview showed the first three in the order they were raised, so an
  information notice could hide a red one; every red notice is shown now. Zones with the same
  problem share one notice.
- **Zone status follows the controller.** Two writers share the zone status sensor. While the
  controller is running, the dashboard shows the controller's phase-aware status, and it never
  shows the integration's fixed-threshold *Dry - Needs Water* during P3, where drying back
  overnight is the plan.
- **The dashboard no longer downloads all of Home Assistant twice a minute.** Inside Home
  Assistant it fetched every entity (3.3 MB on a large install) every 30 seconds for each open
  tab, twice more for every change you applied, and kept going in a hidden tab. It now downloads
  once when it opens, then receives only changes to the few hundred entities it shows, as they
  happen, over Home Assistant's own connection. Opened on its own, outside Home Assistant, it
  still checks every 30 seconds, but not while the tab is hidden, and at once when you come back.
  Recorded sensor history loads its window once, then only the newest readings each minute.

### 🔧 Technical notes

- Dashboard (class C1, nothing the controller or integration reads): new
  `frontend/src/lib/controller-health.ts`. `readHeartbeat` dates a beat by the heartbeat's
  `last_updated` (UTC, the clock the integration's health check uses), falling back to the naive
  local `last_beat`; missing, unreadable (no usable time, or `unknown`/`unavailable`) and older
  than 5 min all count as not running. `controllerZoneLabel` mirrors `zone_status_label` in
  `crop_steering_engine/core.py`, rebuilt from the zone phase and its `reason` and
  `current_decision` `fired`/`blocked`; it is used while the heartbeat is fresh and the status
  sensor holds the integration's value (no `reason` attribute).
- `model.ts`: `buildRoom` raises `<room>-controller` (critical) in place of
  `<room>-stale-heartbeat` (warning), sets `Zone.stale`, merges identical per-zone notices into
  one (`zones-1-2-3-sensors`, no `zoneId`) and sorts alerts critical > warning > info. New
  `roomStatus()` (the status line, rendered by `components/status-line.tsx` above
  `RoomOffBanner`) and `leadingNotices()` (Overview: every critical, then up to three).
- Demo: heartbeats carry `last_beat` and are restamped on each demo refresh; each demo room
  publishes `app_status` and `current_decision`; demo zone statuses carry a `reason` like the
  controller's.
- Dashboard (class C1, nothing the controller or integration reads): new
  `frontend/src/lib/live.ts`. Inside the Home Assistant iframe (parent `hass.connection`),
  `/api/states` is fetched once for discovery (again only on Refresh, after a Setup or plan change,
  and on a websocket reconnect), then `subscribe_entities` covers `watchedEntities()`: every
  `*.crop_steering_*` entity, what room descriptors and heartbeats point at (kill switches, pumps,
  valves, tank and feed sensors), and the controller's per-zone sensors even before it has posted
  them. `applyEntityUpdate()` applies the compressed events; updates are published in 250 ms
  batches. A socket down for two 30 s ticks shows the offline banner; a refused subscription
  falls back to polling. Standalone: `whileVisible()` polls every 30 s only while the page is
  visible and refreshes on `visibilitychange`/`focus` (at most once per 10 s).
- Writes no longer fetch all states before and after: the preflight and the readback read only
  the written entities (`GET /api/states/<id>`) and merge them, never over a newer state.
- `sensor-context`: the 72–168 h window loads once; each minute `historySpan()` asks only for the
  time since the last load plus two minutes, and `mergeSeries()` folds it in.
- Known limit: a room or zone created from Home Assistant's own integration pages, not this
  dashboard's Setup, appears after Refresh, a reload or a Home Assistant reconnect.

## [2.19.3] - 2026-09-23

Pair: **controller 0.16.3**. **Owner-approved rehearsal release, no staging soak**: the owner
approved releasing on 23 September 2026 ("do all of it now") after the F2 dry tails of 21-22 September; the
release audit on the GitHub release names what was and was not exercised. Update with the engine off, read
the controller log, then watch the first shots.

The irrigation changes (controller and engine) are class **C3**, from the F2 history of 21-22 September
2026 and the review of it.
**Not run on hardware.** No add-on option changes. The state file gains three additive keys that the
previous controller ignores, so it can still read the file after a rollback.

- **A room deleted and set up again starts fresh.** Home Assistant keeps the last state of a removed
  entity for seven days, and a re-created room inherited the deleted one's settings, its room on/off
  switch and its kill switch: a room deleted while armed came back armed. Now a room only takes back
  values saved after it was created. An existing room restarts exactly as before.
- **The controller adopts a re-created room afresh.** It used to go on driving the room that no longer
  existed: with a different valve in the new room, arming it would have watered through the **old**
  valve. The integration now says which room it is, and a new room is adopted through the usual gate
  (kill switch and hardware OFF first).
- **Setup shows the version that is running, and waits for a restart.** After a HACS download Home
  Assistant keeps running the old code until it restarts; setup now says which version is running and
  will not create a room on stale code. *Configure* is never blocked.
- **Tested against the Home Assistant you run.** The real-Home-Assistant tests now run on HA 2026.9.3
  (Python 3.14) and on the oldest version supported, now **2024.10.0** (2024.3 never passed).
- **One repository.** The controller app is now installed only from this repository. The old
  `f2-control` mirror, which a release script pushed a copy to, is retired: it gets no more
  releases, and nothing in this repository writes to it. A controller installed from the mirror
  moves once; [docs/INSTALL.md](docs/INSTALL.md) has the steps, which carry its learned state and
  settings across. Never run the old and the new app at the same time.
- **Only an administrator can change plans, recipes and run records.** The Crop Steering sidebar
  is open to every Home Assistant login, and until now so was everything it can change: any
  login, a staff phone or the hallway kiosk, could arm a plan with a future start date (which
  holds every zone), disarm the plan that is running, or replace every room's recipe. Through
  the Crop Steering actions, which is what the sidebar uses, saving, arming and disarming plans,
  changing run records and recipes, holding a zone, forcing a phase and requesting a shot now
  need an administrator's login, as room setup already did. Everyone else can still open the
  sidebar and look. **Automations are not affected**: they run with no login of their own, even
  when a person set them off. A script that someone who is not an administrator starts from a
  dashboard is refused, like that person. Not changed: the room's own switches, selectors and
  numbers (a zone's hold switch, the phase selector, a setpoint) are Home Assistant entities and
  still follow Home Assistant's own permissions, so an ordinary login can still change those.
- **A zone that has used its day's water can still be rescued.** On 22 September Zone 1 had no water
  from 14:06 until lights-off with its moisture under the re-water line: the daily limit was reached
  by midday, and the limit also stopped the "no water for 3 hours" safety shot. That safety shot, the
  overnight emergency shot and the high-EC flushes now always pass the daily limit. Routine top-ups and
  EC-correction shots stop at it, and a shot that would cross it gets only what is left, not a ten
  minute shot with two litres of budget remaining.
- **The morning ramp always finishes, and never waits all day.** P1 runs in full whatever it is set
  to: it stops at its target or its maximum number of shots, not at the daily limit. Once the zone is
  full and only pore EC is keeping the ramp open, a spent budget ends the ramp instead of holding the
  zone in P1 with nothing it is allowed to fire.
- **Pore EC is read when it means something.** For the first 45 minutes after a shot the probe reads
  the fresh water passing it (6 to 8 mS/cm during the 22 September ramps, on zones that read about 4.5
  when left alone). Every EC decision now uses the last reading taken at least 45 minutes after a shot,
  so a passing spike no longer keeps the ramp flushing, doubles a shot or fires a flush, and an EC
  flush waits for the next such reading before it is repeated.
- **No safety shot at lights-on.** The whole night counted as "3 hours without water", so every zone
  got a safety shot the moment the lights came on, before its morning dry-back. The dry-back now comes
  first, as intended.
- **A restart after lights-on starts a proper day.** If the controller was not running when the lights
  went off (a reboot left it stopped), it came back in yesterday's P2 with yesterday's water already
  counted, and watered nothing all day. It now starts the day at P0 with its own budget.
- **A shot interrupted by a crash is closed at the next start, and nothing else is.** Before opening
  anything the controller writes down what a shot is about to open. If it dies mid-shot, or loses Home
  Assistant during the close, its next loop closes exactly that valve, main line and pump. **It never
  switches anything off on a timer or on suspicion.** The tank is circulated for well over 20 minutes to
  heat it, and zones are hand-watered with the valves and main line open: anything a person has
  switched since the shot started is theirs and is left alone, together with everything upstream of
  it; the pump is left alone while a hold (dosing, fill, flush, circulation) is on or another valve on
  the line is open; and nothing at all is touched while the room's kill switch is off.
- **Stopping or updating the app no longer switches everything off.** It used to switch off every pump
  and valve it knew, which ended tank circulation and hand-watering whenever the app was stopped,
  updated or restarted. Now it closes only the shot it has running, by the same rules as above, and
  counts the water that shot gave. With no shot running it switches nothing off. A pump that reports
  OFF a second late no longer latches a false hardware hold after a failed shot either (the
  15 September problem, on the one path the earlier fix missed).
- **A critical alert raised while Home Assistant is unreachable is not lost.** It is raised again until
  Home Assistant has it; the 30-minute quiet period starts only then.

### 🔧 Technical notes

- #49 `room.restored_state_is_ours(entry, last_state)` (`last_state.last_updated >= entry.created_at`,
  lenient when either is missing or naive) gates restore in the number, switch and select platforms.
- #50 the descriptor gains `entry_id` (not a fingerprint key); `Controller._is_another_room` re-opens
  adoption when it changes; first sight is remembered and changes nothing; `_setup` gains optional
  `entry_id`.
- #51 `config.step.user`/`room` and `options.step.init` show `SOFTWARE_VERSION`; `async_step_user` aborts
  `restart_required` while the on-disk `manifest.json` differs (read in the executor).
- #56 Validate: `Real Home Assistant` legs pinned (HA 2026.9.3 / plugin 0.13.366 / Python 3.14; HA
  2024.10.0 / Python 3.12) with a version assertion; `tests/run_ci.sh` ends `PARTIAL` (exit 1 unless
  `--allow-skip`) when that tier is skipped; minimum in `hacs.json`, README and INSTALL raised to 2024.10.0.
- `addons/f2_control/config.yaml` `url` points at this repository (metadata only; version unchanged).
- Removed `scripts/prepare_addon_release.py`, `scripts/publish_addon.sh` and
  `tests/test_addon_release.py`, the publisher for the mirror. The add-on's web root is already
  written by `frontend/scripts/package.mjs` and checked by `tests/test_dashboard_layout.py` and
  the Validate bundle check, so nothing it verified goes unchecked.
- New section in `docs/INSTALL.md`: moving an app from `4d457e60_f2_control` (mirror) to
  `6db5faba_f2_control` (this repository), copying `/data/state.json` and the options.
- New `custom_components/crop_steering/admin.py` `async_require_admin`: the one administrator
  check, extracted from `setup_api.py`. It now also runs before every state-changing service:
  `strategy_save`, `strategy_activate`, `strategy_disarm`, `runs_save`, `runs_archive`,
  `runs_import`, `save_recipe`, `apply_recipe`, `set_manual_override`, `transition_phase`,
  `execute_irrigation_shot` and `custom_shot`. Read-only services stay open: `strategy_get`,
  `strategy_preview`, `runs_get`, `check_transition_conditions`. New services are checked by
  default (the read-only ones are listed, not the others). Entity services on the integration's
  own entities (`switch.crop_steering_zone_N_manual_override`, `select.crop_steering_irrigation_phase`,
  `select.crop_steering_recipe_stage`, the numbers, the engine switch) are not covered; Home
  Assistant's entity permissions govern those, and its Users group may control every entity.
- Semantics are those of Home Assistant's own admin services: `context.user_id` empty passes, an
  unknown user id or a non-admin is refused. `setup_*` keep their stricter rule (no user is
  refused too) and their message. The panel stays `require_admin=False`.
- Refusals raise `HomeAssistantError("crop_steering.<service> requires an authenticated Home
  Assistant administrator")`, the type setup already used, not `Unauthorized`: over the REST API
  the console uses, `Unauthorized` is a bare 401 that the http ban middleware counts as a failed
  login (notification, then an IP ban at `login_attempts_threshold`).
- `services.yaml` says so on each checked service. Tests: `tests/test_admin_only.py` (every
  service; administrator, non-administrator, unknown user and no user) and
  `tests_ha/test_non_admin_user.py` (a real Users-group account, and a real automation it sets
  off). The `tests/` call stand-ins for `services.py` now carry a no-user context, as a real
  `ServiceCall` always has one.
- **Typed decisions (engine).** `decide()` still returns `(phase, p2_threshold, fire, size, reason)`;
  `reason` is a `Reason(str)` with `.kind` and `.cap_exempt` (`CAP_EXEMPT`). Exempt: `flush_high_ec`,
  `p1_ramp`, `p2_rescue`, `p3_emergency`, `watchdog`. Not exempt: `p0_ec_flush`, `p1_flush`, `p2_dilute`,
  `p2_topup`, `min_daily`. Non-firing: `idle`, `block_high_ec`, `hold_high_ec`, `block_daily_cap`. This
  replaces the substring test (`"flush" in ir`) that made every "P1 flush/runoff" shot an emergency.
- **Cap -> watchdog.** A non-exempt shot cancelled by the cap becomes the watchdog shot (`p2_shot_size`,
  kind `watchdog`) when the watchdog is due: lights on, not P0, more than `watchdog_hours` since the last
  shot, VWC under the P2 threshold. The watchdog no longer fires in P0.
- **P1 completion over budget.** P1 at `min(p1_target, field_capacity)` with `p1_minimum_shots` in and
  `daily_vol >= max_daily_volume` goes to P2: `P1 complete at ceiling; EC flush over daily budget`.
- **P0 EC flush** gated like the other flushes (feed below pore EC, VWC < FC - 2, `p2_min_interval_min`);
  not exempt.
- **New grow-day in any phase.** P1/P2 with `lights_on and new_grow_day` goes to P0 (`new grow-day -> P0
  (reset)`) and the existing P0 bookkeeping resets the counters. From P1/P2 this needs a dated
  `last_daily_reset` older than the grow-day start, so a fresh zone is never restarted mid-day. Blind
  zones follow the same rule in `_blind_time_transition`.
- **Settled EC.** New last field `ZoneSnapshot.ec_settled` (default `None`); every EC rule uses it when
  present. `EC_SETTLE_MIN = 45`. `_settled_ec` takes the fused reading as settled 45 min after the last
  shot ended (a switch-on anchor is not a shot), holds the last settled value in between, and passes
  `None` while the probe reads nothing valid. Only settled readings feed `ec_smooth`, so the EC step /
  PID. An EC correction acting on a settled value (anti-lockout, P0/P1 flush, P2 rescue/dilute) also
  waits 45 min after the last shot: a held value can never re-fire a cap-exempt flush every 10 minutes.
  The P1 EC-gate helper and the Jev evidence in `_auto_tick` use the same value. Published as
  `ec_settled` on `sensor.crop_steering_<room>zone_N_safety_status`.
- **EC offset at lights-on.** `_loop_room` clears `ec_offset`, the integral and the previous error
  before it builds the parameters for the tick that starts the zone's day.
- **Budget clipping (controller).** `_act_zone` cuts a non-exempt shot to the remaining budget at the
  zone's flow; under `MIN_SHOT_S` (5 s) it does not fire and publishes `BLOCK daily-cap (x L left)`.
  When less than a minimum shot is left, `_loop_room` decides again with the budget spent, so the
  watchdog rescue and P1 completion apply at the margin too. Copied and blind-schedule decisions are
  plain text and never exempt.
- **Write-ahead shot record.** `_execute_shot` saves `_shot_inflight` (zone, valve, mainline, pump,
  `started` in UTC) in the room's state block before opening anything and clears it once the close
  reads back OFF. `_reconcile_inflight` runs at the top of every loop, so at start-up: it closes a
  recorded switch only if Home Assistant's `last_changed` is within `INFLIGHT_OPEN_WINDOW_S` (-5 s to
  +60 s) of `started`, walking valve -> main line -> pump and stopping at the first switch that changed
  outside it; it leaves the main line and pump while another valve on the line is on, the pump while
  any `hold_entities` is on, and everything while the room's kill switch is not ON. A close that is not
  confirmed latches the hardware hold and alerts, and is retried each loop. A new shot in that room
  waits until the record is settled. `ha_get` returns `HAState`, a tuple that unpacks as before and
  carries `last_changed`.
- **Stopping the app.** `_safe_off` (SIGTERM / SIGINT: stop, update, restart) no longer switches off
  every mapped switch. It closes only a room's `_shot_inflight`, by the same `_inflight_plan` rules, and
  with no shot in flight it switches nothing off. The shot running in this process is closed whatever
  its kill switch reads; an older interrupted shot is left to the operator while its kill switch is not
  ON, as in the loop. What cannot be closed and read back OFF stays recorded for the next start. State
  is still saved on the way out.
- **Alerts.** `_alert` starts the 30-minute debounce, and sends the phone push, only once
  `persistent_notification.create` succeeds. A latched hardware hold this process has not announced is
  announced from `_recover_hardware_faults`.
- **Shot cleanup and stop.** The error-cleanup read-back uses `_confirm_switches` (1 s, then every
  0.5 s to 6 s). A `SystemExit` mid-shot counts `nominal_l * elapsed / duration` before re-raising
  (up to the end of the stop's close, like the normal close counts to its acknowledgement), and skips
  the error cleanup, which would otherwise switch the rest off.
- **State file.** Additive: `_shot_inflight` in a room block, `ec_settled` and `ec_settled_at` per zone.
  The previous controller (0.16.2) loads the new file: it ignores the new keys, keeps the room-block one
  when it saves and drops the two zone keys. An old file loads with the new keys at their defaults; a
  damaged record is ignored and logged.
- **Tests.** Engine: `crop-steering-engine/tests/test_day_structure.py` (32). Controller:
  `test_grow_day_and_budget.py` (15) and `test_interrupted_shot.py` (22). In `test_auto_setpoints.py`
  the plateau hand-over margin is now one 20-minute ramp interval instead of 0.5 h: the base run no
  longer includes the P0 lights-on watchdog shot that delayed it. `test_declared_plumbing.py`: a mapped
  pump is closed on exit when a shot of this controller left it on, and left alone otherwise (it
  asserted the old blanket switch-off). `fake_ha.FakeHA` reports
  `last_changed`. The `tests_ha/` tier was not run locally, and no `tests_ha/` test or seeded fixture was
  added for this change yet.

## [2.19.2] - 2026-09-21

Pair: **controller 0.16.2**. Class **C3**. Everything here comes from two reviews by use: the first
real install on a one-zone tent, set up from a phone, and an independent review of 2.19.1 upstream.
Nine small changes, each its own pull request with its own tests (#15 to #23). **This candidate
carries more than one behaviour change** (two C3, four C2), which
[docs/RELEASING.md](docs/RELEASING.md) says a candidate should not; they were bundled by decision
of the person running the only staging room, and a failed soak would have to be bisected across
them. The defects were seen on real hardware; **the fixes have not run on hardware** before
release. Update with the engine off, read the controller log, then watch the first shot.

- **Set things up in either order.** If the controller app was started before the integration was
  set up (the order the app store invites), a one-zone tent was shown Zones 2 and 3 that do not
  exist, each complaining "no hardware mapped", and a minute after setup Settings > Repairs told you
  to create a kill-switch helper by hand. Both are gone. The controller now waits for a room,
  invents nothing, and picks the room up by itself within a minute, with no restart. **If you saw
  that Repairs card: do not create the helper.** A room made by the wizard has its own kill
  switch, *Engine Enabled*; the helper would be a second one that does nothing.
- **A zone is called what you called it.** Name a zone "GT1" and its device in Home Assistant was
  still "Zone 1" or "Crop Steering Zone 1", depending on which part of the integration got there
  first. It is now the name you typed, and renaming the zone in Configure renames the device. A
  device you renamed yourself in Home Assistant keeps your name. No entity id changes.
- **Switching a room on no longer creates an irrigation event.** New switch-on timestamps are
  marked explicitly and displayed as unknown until an irrigation is recorded. Older unmarked
  timestamps are preserved: zero daily counters or missing history cannot establish whether an
  old timestamp represented irrigation or switch-on. Electrical operation does not prove water delivery.
- **The menu scrolls on a phone.** On a small screen the lower half of the side menu (including
  *Help & tools* and the version numbers) could not be reached.
- **Configure > Edit parameters no longer locks out a room that steers dry.** The number entities
  accept a P1 target and a P2 threshold as low as 5 %, the form insisted on 30 % and 25 %, and
  since 2.18.1 it opens on your current values. A room at P1 20 % could not submit the form even
  unchanged. The form now has exactly the limits of the entities it edits.
- **Assistants using the MCP tools can change how a room is plumbed.** A room that had declared
  its plumbing could never gain or lose its pump through them: the tools did not know the
  question existed. The plumbing and the pump or main-line mapping now travel together in one
  reviewed proposal, and a proposal that contradicts the declared plumbing is refused at preview.
- **Two holes in the release checks are closed.** A release pull request could also change a
  default, a dependency or an add-on permission inside the three files that hold the version
  numbers; and a controller-only release was accepted that could then never be promoted. Every
  release now raises the integration's number, a controller-only fix included.

### 🔧 Technical notes

- **Zones are never invented** (#17, **C3**). The shipped add-on options carry `num_zones: 3`,
  documented as "only used if Home Assistant isn't reachable at startup" but also used when Home
  Assistant answered and the integration simply was not set up yet. New
  `_default_zone_ids(options, descriptor) -> (ids, provisional)`: the descriptor's authoritative
  `active_zone_ids` / `num_zones` first, then fused sensors (provisional without a descriptor), else a
  hand-mapped `hardware` option keeps `num_zones`, else no zones when Home Assistant answers, else
  the documented fallback. While provisional the controller rediscovers every loop and re-resolves
  zones, enable flag and feed sensors. A state file that already holds phantom zones still loads.
  It also stops the controller's pre-setup `zone_N_status` states pushing the integration's own
  status sensor onto `sensor.crop_steering_zone_1_status_2` on a first install.
- **Last irrigation is an event** (#18, **C3**). New per-zone state field `last_shot_is_anchor`
  (additive: `_fresh_zone` default `False`; an old file without it retains its existing timestamp,
  because daily counters reset and history expires). `_room_switched_on` still stamps `last_shot`
  so the blind-probe schedule counts from switch-on; `zone_N_last_irrigation_app` publishes
  `unknown` while the flag is set, including for a room that is off. No option or entity change.
  Final review added regression coverage for partial sensor startup, legacy numeric strings and
  malformed excluded-volume values, and genuine irrigation timestamps after daily rollover.
- **The kill-switch repair judges the right switch** (#19, **C2**). `health._kill_switch()` trusted
  the heartbeat's `enable_flag` over the room's own descriptor. While the heartbeat reports an older
  `setup_revision` than the descriptor (both plain ints), the engine holds every zone anyway and
  adoption moves it to the descriptor's flag, so that flag is the one judged. An up-to-date engine
  is believed as before (custom add-on `enable_flag`), a deleted legacy helper is still reported,
  and a controller too old to report a revision is believed as before.
- **Zone device name** (#16, **C2**). `room.zone_device_name(entry, zone_num)`, used by the button,
  number and select platforms, which used to register the same device under two different names.
  The room device is left alone.
- **Edit parameters limits** (#20, **C2**). The four fields read `native_min_value` /
  `native_max_value` from `NUMBER_DESCRIPTIONS`. Only the lower limits of `p1_target_vwc` (30 -> 5)
  and `p2_vwc_threshold` (25 -> 5) actually move.
- **MCP plumbing** (#21, **C2**, `mcp-server/` only). `plumbing` in the strict input schema; the
  room carries `plumbing` ("" = never declared) and `plumbing_inferred`; `config()` includes the
  layout only when declared, which puts it in the payload, the comparison snapshot and the readback
  digest, and never declares one on the operator's behalf. New
  `tests_ha/test_mcp_setup_contract.py` sends that payload to the real `setup_save`.
- **Sidebar scroll** (#15, **C1**). `.desktop-sidebar` / `.mobile-sidebar` get `overflow-y: auto` and
  `overscroll-behavior: contain`, their children `flex-shrink: 0`; checked in `verify-live.mjs` at
  390x640 and 1280x480. The committed bundle is rebuilt from that source.
- **Release guards** (#22, #23, **C0**). `without_version()` compares each version file with only its
  version field blanked, and `check_pull_request` takes the files' text as a required argument; a
  release that does not change the integration version is refused, and a release branch is named
  for the integration version. Both take effect once promoted, because GitHub reads the workflow
  from `main`.
- **Upgrade in place.** No add-on option and no entity id changes. One additive state-file field
  (`last_shot_is_anchor`). A room that never declared its plumbing still publishes byte-for-byte
  the descriptor it did, and the controller's saved setup fingerprint still matches, so an update
  resumes without a disarm cycle. Every change above is tested both on a fresh install and from the
  seeded snapshots of old installs in `tests_ha/fixtures/`.
- **Documented, not changed.** A probe whose reading has not changed for 20 minutes is treated as
  dead and the zone goes onto the blind schedule. That is deliberate (a probe pulled out of its
  cube leaves a plant that will need saving), and it also fires on a bench test with no plant in
  the cube. [docs/troubleshooting.md](docs/troubleshooting.md) now says so, along with the three
  first-install symptoms fixed above.

## [2.19.1] - 2026-09-21

Pair: **controller 0.16.1**. Class **C3** by the table, because the controller is touched, though
what changes there is one new attribute on a sensor it already publishes: no change to irrigation
behaviour, options, the state file or any entity id. **Not run on hardware** before release: update
with the engine off, then check the sidebar reads 2.19.1 and 0.16.1.

- **Crop Steering has its icon.** Adding the integration, the integrations page and HACS all showed
  a grey "icon not available" box. The integration now carries its own icon and logo, with
  versions that stay readable on a dark theme. Needs Home Assistant 2026.3 or newer; older
  versions carry on showing the placeholder, and nothing else changes for them.
- **You can see what you are running without leaving the dashboard.** The sidebar, under *Help &
  tools*, now shows the integration version and the controller version. Both come from the parts
  that are actually running, not from the page, so it cannot show a version you have not got, and
  a half that is too old to say (or a controller that is not running) reads "not reported".
  After an update it is the quickest check that both halves really moved.

### 🔧 Technical notes

- New `custom_components/crop_steering/brand/` (`icon`, `logo`, `@2x`, and `dark_` variants), which
  Home Assistant 2026.3+ serves for a custom integration with no manifest change. Built from
  `img/crop-steering-logo.png` by `scripts/make_brand_images.py`: the icon is the emblem alone (it is
  shown at about 40 px), the logo keeps the wordmark, dark variants sit on a white rounded tile,
  all reduced to 256 colours with alpha (10-53 KB each). `tests/test_brand_images.py` pins names
  and sizes from the PNG headers. Class **C1**: nothing the controller reads.
- Versions in the sidebar. The integration publishes `integration_version` in each room's
  `engine_config` descriptor (from `SOFTWARE_VERSION`, already tied to `manifest.json` by the version
  tests). The controller publishes `controller_version` in each room's `ai_heartbeat` and logs it on
  start; it reads the number from the `config.yaml` it was built from, which the Dockerfile now
  copies into the image as `/app/addon.yaml`. **No number is duplicated anywhere**, so a release
  has nothing extra to bump; the tests fail if the report and `config.yaml` disagree or the
  Dockerfile stops shipping the file. The descriptor attribute is proven not to enter the
  controller's setup fingerprint, so an integration update still resumes without a disarm cycle.
  Class **C3** by the table (the controller and its Dockerfile are touched), though the change is
  one new attribute on a sensor the controller already publishes: no state-file, option or
  entity-id change.

## [2.19.0] - 2026-09-21

Pair: **controller 0.16.0**. It also carries 2.18.1 / controller 0.15.2, which was never published by
itself. Class **C3**. Released without a staging soak by decision of the two people who run it; see
[the record](https://github.com/JakeTheRabbit/HA-Irrigation-Strategy/blob/v2.22.0/docs/audits/2026-09-21-release-2.18.1.md). **Not run on hardware** before release: treat
the first update of each box as the first run. Engine off, update, check the log, watch the first shot.

- **Setup now asks how your room is plumbed, and holds you to the answer.** 2.18.0 worked it out
  from what you left empty: no pump chosen meant "this room has no pump". That is right for a tent
  on one smart plug. It is silently wrong for a room that *does* have a pump and whose pump was
  never chosen, or was cleared by mistake: the controller opened the valve, ran no pump, and
  counted the water as delivered while the plants got none. The wizard and **Rooms & setup** now
  ask the question outright (zone valves only; a pump, then zone valves; a main-line valve, then
  zone valves; or all three), and the switches you choose have to match your answer.
- **If they ever stop matching, the room is held, with a reason.** A room that says it has a pump
  and has none mapped is not watered, nothing is counted as delivered, and you get a notification
  saying what to fix. It used to look healthy until the plants wilted.
- **Nothing changes for a room that is already set up.** It carries on exactly as it does today,
  and an update does not need the kill switch cycled. Open **Rooms & setup** (or *Configure*) when
  it suits you: it shows what your current switches imply and asks you to confirm. From then on
  the protection above applies to that room too.

### 🔧 Technical notes

- New optional `plumbing` in a room's setup and, **only when declared**, in the engine descriptor:
  `valves_only`, `pump_valves`, `mainline_valves`, `pump_mainline_valves`
  (`custom_components/crop_steering/plumbing.py`; the controller carries the same table and a test
  reads both). `prepare_setup` refuses a save whose mapped switches contradict a declared layout,
  both ways, for an active room. Once declared it can be changed, not withdrawn; a client that does
  not send it keeps the stored value.
- Controller: `plumbing_hold()` gates `_blocked` and, as a last line of defence, `_execute_shot`.
  A contradiction or a layout the controller does not know holds the room, alerts
  (`f2_plumbing_<room>`, at most every 30 minutes), opens nothing and counts nothing. A mapped
  switch the declaration disowns is still safed on exit and still has to read OFF for adoption.
- **Upgrade in place:** an undeclared room publishes byte-for-byte the descriptor it did (key set
  pinned in `tests/test_plumbing.py`), and `plumbing` joins the setup fingerprint only when present,
  so the fingerprint saved by controller 0.15.x still matches and the room resumes without a disarm
  cycle. Proven in `tests_ha/` from seeded snapshots: a one-switch tent recorded by running upstream
  2.18.0's own wizard (`fixtures/entry_2_18_one_switch_tent.json`, fingerprint computed by
  controller 0.15.1's code) and the 2.17 pumped room. Declaring later is an ordinary setup change
  (new revision, adopted with the kill switch and hardware OFF).
- Wizard and Configure: a required list question at the top of the hardware step; no prefill for a
  new room; Configure prefills the declared layout or what the saved switches imply. Clearing the
  pump of a room declared with one is refused in the form. Rooms & setup asks only when
  `setup_read` reports the `plumbing` capability, so a newer dashboard served by the add-on beside
  an older integration neither asks nor sends it.
- Not changed: the env-file path (rooms configured that way stay undeclared until saved through a
  form), add-on options, the state file format, every entity id.
- **Not run on hardware.** Everything above is proven against a real Home Assistant and the real
  controller code with a fake switch layer. No physical pump or valve has been driven by this build.

## [2.18.1] - 2026-09-21

Pair with controller **0.15.2** (0.15.1 plus a test-only seam; irrigation behaviour is unchanged). Bug fixes only. Nothing an operator has set moves: every fix below was checked against seeded snapshots of older installs. Each was reproduced on 2.18.0 inside a real Home Assistant before it was fixed; the write-up is [docs/audits/2026-09-21-first-run-review.md](docs/audits/2026-09-21-first-run-review.md).

- **The integration starts on older Home Assistant.** On anything before Home Assistant 2026.5 the setup wizard finished and the integration then showed "Failed to set up": no entities, no dashboard. It lists 2024.3 as supported, and now it is.
- **Your lights times are used.** The wizard asks when your lights turn on and off, stored the answer, and then always ran on 12 and 0. The grow-day, the morning dry-back and the overnight phase now follow the hours you typed. If you already set them on a dashboard, those are kept.
- **"Edit parameters" does something.** Changing a value under Configure said "saved" and quietly put the old value back. It now changes what the controller reads, and the form opens on the current value rather than the one from the day you installed.
- **A sensor or pump can be removed, not just swapped.** Under Configure you could replace a mapping but never clear it: it came straight back. That matters more now that a pump is optional.
- **Boxes that did nothing say so.** The waste-valve box promised the valve is "forced closed during a shot". The controller has never operated it, so if your plumbing relies on that, arrange it yourself. The grow-light, notification, humidity and VPD boxes are likewise marked as recorded only.
- **The pump box says what leaving it empty means.** Since 2.18.0 an empty pump is accepted and the controller then never runs one: it opens the zone switch and counts the shot as delivered. That is right for a one-switch tent and wrong for a room that has a pump, so the box now says so where you choose it.
- **Every box is explained.** The feed EC and feed pH pickers showed their raw names (`feed_ec_sensor`) with no label at all, and each zone's name and "in use" box had no help text. Two Configure messages showed as raw keys.
- **Small pots can be adjusted.** A 0.65 L rockwool cube was accepted by setup and then could not be edited, because the setting's minimum was 1 L.

**🔧 Technical notes**

- `setup_panel`: `frontend.async_panel_exists` was added in Home Assistant **2026.5.0** (absent from core tags 2024.3.0, 2025.1.0, 2026.2.3, 2026.3.0, 2026.4.0) and was called unconditionally inside `async_setup_entry`: `AttributeError`, entry state `SETUP_ERROR`. `_panel_exists()` uses the helper when it exists and otherwise `PANEL in hass.data[frontend.DATA_PANELS]`, which is what the helper does. Neither test tier could see it: `tests/test_setup_panel.py` assigns the function onto its own stub, and `tests_ha/conftest.py` replaced the whole panel registration with a no-op. `tests_ha` now stands in for the web server only and runs the registration against the real frontend module; with the fix reverted, that tier fails.
- `number.PARAM_TO_ENTITY_KEY` gains `lights_on_hour` / `lights_off_hour`. A seed only applies to an entity being created for the first time (`RestoreEntity` wins afterwards); pinned by a seeded upgrade where setup recorded 10-22, the operator set 8-20, and 8-20 survives.
- `OptionsFlowHandler.async_step_edit_parameters` calls `number.set_value` on the live entities before `_update`, so the reload restores the value just written; defaults come from the live entities. The OFF check and its abort are unchanged, and nothing is written when it refuses.
- `_hardware_schema._ent` prefills with `description={"suggested_value": ...}` instead of `default=`. The frontend omits an emptied field and voluptuous re-applied the default. `test_native_hardware_schema_retains_explicit_tank_telemetry` now asserts the same intent (the form opens showing the mapping) and additionally that the field can be cleared.
- Translations: `options.abort.not_env_config` / `reload_failed`; labels and tooltips for `feed_ec_sensor` / `feed_ph_sensor` on both mapping forms; tooltips for all 24 `zone_N_name` / `zone_N_active`; truthful text for `waste_switch`, `light_entity`, `notification_service`, `humidity_sensor`, `vpd_sensor` (no runtime consumer in the integration, the add-on or the engine) and for `pump_switch`.
- Global `substrate_volume` minimum 1.0 -> 0.1 and `drippers_per_plant` maximum 6 -> 20, matching `setup_api.SIZING` and the per-zone entities.
- Tests, lean: `tests/test_translations.py` (every abort reason, error key and menu entry has a message in the flow that raises it; every mapping-form field has a label and a tooltip; hassfest's own key, quoted-placeholder and orphan-tooltip patterns; a field with no runtime consumer may not promise behaviour, and fails the day one gains a consumer). An honest pre-2026.5 case in `tests/test_setup_panel.py`.
- Tests, real Home Assistant (`tests_ha/`, 4 -> 30): `test_setup_entry.py`, `test_configure.py`, `test_upgrade_in_place.py` driven by seeded snapshots in `tests_ha/fixtures/` (a 2.17 wizard room and an env-file era room: tuned values, an operator-renamed entity, a unit-less probe, and controller 0.14's saved setup fingerprint resuming with the kill switch ON), and `test_install_to_controller.py`, which hands a freshly installed room to the **real add-on controller** and requires it to find, adopt and water it.
- Controller test seam: `F2_STATE_PATH` (see the add-on changelog). Docs: `docs/TESTING.md` describes the real-Home-Assistant tier, the fixtures and running hassfest without Docker.
- Not changed, raised for a decision: an unmapped pump is read as "this room has no pump" (2.18.0). See the audit for a demonstration and three options.

## [2.18.0] - 2026-09-21

Pair with controller **0.15.1** (0.15.0 plus one fix: a room switched off stays off while Home Assistant restarts).

- **The setup wizard no longer throws your work away.** If something was wrong at the end (a valve that was on, a probe in the wrong unit, a mistyped entity), the wizard closed and every zone, sensor and size you had entered was gone. It now shows the same step again with everything still filled in and says what to fix. Problems are reported on the step where you entered them, not three screens later, and the message says whether the entity is on, unreachable or does not exist instead of always "must read OFF".
- **A brand-new install is found by the controller.** On a fresh install Home Assistant named most of this integration's entities from their labels (`number.p1_target_vwc`, `sensor.engine_config`) instead of the `crop_steering_` ids the controller and dashboard read, so a new room was never discovered and never watered. New installs and new rooms now register under the documented ids. Existing rooms are untouched: Home Assistant keeps the ids it already holds. If you first installed on 2.17 or earlier and your room was never found, update, then remove the room and add it again.
- **A tent with one switch works.** A room whose only hardware is one smart plug or solenoid per zone saved fine and then never watered, because the controller insisted on a separate pump and main-line valve. A zone now needs only its valve; pump and main-line are used when you have them. Every safety check still applies to whatever hardware the room has.
- **Probes in other units are converted, not rejected.** Pore EC in µS/cm and moisture reported as a 0-1 volume fraction are accepted and converted to mS/cm and percent, including mixed probes in one zone and the source-water EC probe. `ppm` is still refused, with the reason: the 500 or 700 scale is not something a sensor reports.
- **The Cloudflare judge now looks after P2.** With Auto Setpoints on and a Cloudflare token in the controller's options, the `typesafe/jev` model is asked once an hour during P2 whether pore EC should be flushed or stacked and whether the peak still fits. It may nudge that zone's P2 shot size (1-4 % of substrate) and hold the working peak up to 2 points above or below the learned one: one small step per lever per grow-day, never while a dated plan owns the room. It cannot fire, size or delay a shot. If a guard trips (probe not believable, water not landing) or Cloudflare does not answer within 5 seconds, nothing changes. The zone's Auto Setpoints status shows what it said and what it changed today.
- **Less typing, fewer wrong numbers in Rooms & setup.** Choose litres or US gallons and L/h or GPH (always saved as metric); pick a common block or pot with its litres shown; work out real dripper flow from a catch test; and see the zone's learned peak as a suggestion beside field capacity. Suggestions are never applied for you.

**🔧 Technical notes**

- `config_flow`: `_retry_form` re-shows a step through `add_suggested_values_to_schema` with `errors.base = setup_invalid`; the zones step validates with `prepare_setup` and `safety_blockers` before moving on; the reconfigure zone map does the same. `safety_blockers` messages keep "must read OFF" and append the cause.
- Controller: pump and mainline are optional in discovery, late mapping, setup adoption, the per-zone gate and `_execute_shot`; lead times are skipped with the hardware they belong to, the close read-back and the hardware-fault latch cover the actuators that exist. The three-switch sequence and its timing are unchanged (tested).
- Controller `_auto_tick`: hourly P2 consult (`auto_setpoints.jev_due` / `jev_verdict`), `p2_shot_size` joins `managed` while the judge is configured, `working_peak = learned peak + peak_adj` drives the P1 target and the P2 threshold. New status attributes `jev_last`, `jev_changed_today`, `working_peak_adjust`. Learned state restores across restarts.
- New `units.py`: exact conversions only (`µS/cm`, Greek-mu `μS/cm`, `uS/cm` -> mS/cm; `m³/m³` -> %). Unknown or missing units pass through unchanged so older installs keep their readings. The controller converts the source-water EC probe the same way before its 0-20 sanity range.
- `number`, `select`, `sensor` and `button` set `self.entity_id` from the object id they already computed. Home Assistant ignores `_attr_object_id` (the 2.17.1 switch fix, now everywhere): in a real Home Assistant 75 of a one-zone room's 134 entities registered under label-derived ids. Found by the new real-HA test job; a permanent test asserts every entity lands on the id its code asks for.
- CI: a `real-home-assistant` job runs `tests_ha/` in a real Home Assistant (`pytest-homeassistant-custom-component`, Python 3.13): the wizard end to end for a one-switch room, and the registered id of every entity. The sidebar panel is stubbed there (it needs the frontend wheel and a web server). The stub suite could not see the 2.17.0 entity-id bug; this can.

## [2.17.2] - 2026-09-20

Documentation only; no code change. Pair with controller **0.14.0** (unchanged).

- Feature matrix: rows for the 2.17 features with what is tested and what was exercised live on 20 September (room off, restart-safe setup, patient read-back), what was not (the full P1 ramp through a live lights-on, Auto Setpoints writing live), and an updated live deployment row.
- Planning guide: "Read the combined graph" now describes the projected P0-P3 day, the overnight lines and the P2 threshold note, replacing text from before 2.16.1.
- Entity reference: `room_active`, `auto_setpoints` and the per-zone `auto_setpoints` sensor.
- User guide, sidebar guide and the controller's documentation tab no longer describe the Today / Schedule navigation as awaiting verification or use the old page names.

## [2.17.1] - 2026-09-20

Pair with controller **0.14.0** (unchanged).

- Fix: the new Room Active and Auto Setpoints switches registered under ids made from their labels (`switch.crop_steering_room_active_off_empty_room_no_irrigation_no_alerts`), which the controller and dashboard never look for, so the room on/off control did nothing on a fresh 2.17.0 install. Switches now suggest `switch.crop_steering_<prefix><key>` when first registered. Found on the first live install, where the four entities were renamed in the entity registry.
- If you installed 2.17.0: rename the two switches per room to `switch.crop_steering_<prefix>room_active` and `switch.crop_steering_<prefix>auto_setpoints` in Settings > Entities (an entity already registered keeps its id), or remove them and restart on 2.17.1.

## [2.17.0] - 2026-09-20

Pair with controller **0.14.0**.

- **Room on/off.** Each room has a Room Active switch. Turn it off when nothing is growing: no irrigation (scheduled, emergency or blind-probe fallback), no alerts, no repair issues, and the room's open notifications are dismissed. Turn it back on and the room starts a clean cycle from the overnight phase; water history is kept.
- **P1 always runs in full.** The ramp no longer ends on a clock. However late the first shot lands, P1 fires its shots in order until the target is recovered (after at least the new minimum shot count) or the maximum shot count is reached. Only then does P2 start.
- **See the sensor where you set the target.** The Today graph you drag targets on now draws that zone's recorded VWC and pore EC underneath them (this grow-day and the previous one), with now, peak and trough above it, on an axis scaled to the readings instead of 0-100 %. A deeper 24 h / 72 h / 7 d history panel sits below, and setpoint fields warn when a target sits outside what the probe reads.
- **The whole day is drawn the way it runs.** P0 keeps drying after lights-on, P1 climbs one step per shot (all of them), P2 fires a shot each time VWC falls to its threshold, and P3 dries down overnight to the next lights-on. Timing uses the zone's own measured dry-down rate, so it is a projection, not a schedule. Hover any riser for its time and size.
- **A restart no longer strands irrigation.** The controller used to forget which setup it had accepted whenever it restarted, then refuse to water until the kill switch was turned off and on again, without saying so. On 2026-09-20 a host reboot cost F2 two hours of its morning ramp that way. It now remembers the setup it accepted and carries on after a restart if nothing changed (pump, mainline and valves must still read off). A genuinely changed setup still needs the off-and-on, and now says so with a notification naming exactly what has to read off. The first start after this upgrade still needs one off-and-on, because the old build saved nothing to remember.
- **A slow pump report no longer stops the room.** After a shot the controller checks that pump, mainline and valve all read off. It used to look once, a second later, and a Zigbee plug that answered in 1.6 seconds latched a false hardware hold that stopped F2 for 16 hours. It now looks at 1 second as before and then keeps re-reading for up to 6, so a late report passes and a genuinely stuck valve still latches within the same minute.
- **When P2 shows no sawtooth, the graph says why.** The engine fires a P2 shot only once VWC has dried down to the P2 threshold. A threshold far under the P1 target spends the whole window drying, so the graph now draws the threshold across P2, says how many points and hours away it is, and names the threshold that gives shots from the start of P2.
- **Auto Setpoints (off by default).** The controller learns each zone's real ceiling, what a shot lifts it, and how fast it dries. When a P1 ramp stops rising for two shots it hands over to P2 and carries the achieved peak forward as the P1 target, then probes 1 point higher after 3 days. It only ever rewrites per-zone target numbers; the engine still decides every shot.

**🔧 Technical notes**

- `switch.crop_steering_<prefix>room_active` (default on) and `switch.crop_steering_<prefix>auto_setpoints` (default off). `health.py` clears the room's repair issues while the room is off; the controller publishes `app_status: room_off` and a `room_active` heartbeat attribute.
- Engine core: P1 time exit removed; `ZoneParams.p1_min_shots` (from `number.…p1_minimum_shots`, clamped to `p1_max_shots`). Both vendored copies stay byte-identical.
- New pure modules in the controller: `auto_setpoints` (learner), `setpoint_supervisor` (bounded, stepped, ladder-safe writes), `curve_tracker` (day planner), `engine_twin` (test twin around the real `decide()`), `jev_policy` (optional Cloudflare `typesafe/jev` judge, consulted only on a plateau; any failure returns no verdict and never blocks irrigation).
- Gain is learned only from ramp shots fired at least 2 points under the ceiling; dryback rates fold in once per grow-day as that day's mean. Near-ceiling top-ups no longer shrink the P2 band.
- Publishes `sensor.crop_steering_<prefix>zone_<N>_auto_setpoints` (off / learning / tracking / frozen) with learned_peak, gain, day_rate, night_rate, p1_outcome, hold_days, frozen_reason, last_change, jev, managed.
- Add-on options `cf_account_id`, `cf_api_token`, `cf_gateway_id` (all optional). Auto Setpoints never writes while a dated plan owns the room.
- Dashboard: `foldRecorded`, `smoothRecorded`, `dryRates`, `projectDay` and `planningAxis` in `frontend/src/lib/planning-curve.ts`; the dryback target is measured from the projected peak (as the engine measures it from the recorded one) rather than from field capacity. Lines carry a scale-free `data-planning-values` signature because the axis now follows the data.
- Fix: the live history request had no `end_time`, so Home Assistant returned only the first 24 h of a 72 h or 7 d window.
- Controller: the adopted `setup_revision` is saved per room with a fingerprint of what was adopted (`_setup` in `/data/state.json`: pump, mainline, valves, enable flag, active zones, feed sensors). Same revision and fingerprint after a restart is resumed without the engine flag reading off; hardware must still read off. Malformed or missing records keep the full fail-safe. A pending setup raises `f2_setup_<room>` (debounced, dismissed on adoption, silent for archived rooms), and the per-zone hold line carries `[blocked: ...]` in every phase.
- Controller `_confirm_switches`: first read at 1 s, then every 0.5 s to a 6 s deadline (`CONFIRM_FIRST_READ_S`, `CONFIRM_POLL_S`, `CONFIRM_TIMEOUT_S`). Regression tests cover a 1.6 s report (no latch) and a pump that never reports off (latches, bounded).
- Dashboard: `p2Advice` explains a missing or late P2 sawtooth; nominal dry-down is now 2 / 1 points per hour (lights on / off) until a zone has history, replacing 0.7 / 0.35 taken from one low-light week.

## [2.16.1] - 2026-09-08

- Replace competing Manual setpoints and Grow plan navigation with Irrigation plan: Today and Schedule.
- Show effective active schedule targets in Today; hide misleading fallback controls while a schedule owns the room.
- Connect VWC and dashed EC planning references across lights-off and overnight to the next lights-on. Missing EC anchors remain gaps; overnight EC is an interpolation, not a prediction.
- Keep emergency-floor edits and saved-reference overlays independent. Preserve legacy routes and unsaved-draft navigation guards.
- Bundle the same dashboard in controller 0.13.3; no controller decision changes.

## [2.16.0] - 2026-09-08

- Add a local MCP connector for LLM-assisted configuration with reviewed, room-scoped proposals and opt-in writes.
- Seed the isolated demo with synthetic named recipes and current/previous runs; live libraries remain unseeded.
- Temporarily collapse the Home Assistant sidebar while embedded, with persistent desktop/mobile menu access and restore on leaving.

- Add graphical room tank level, pump and fill status, tank EC/pH/temperature, and recorded fill completion time to Overview.
- Show controller state, mapped valve status and last irrigation time in zone tables, mobile cards and details.
- Add optional room-specific tank telemetry mappings, separate from feed-water safety gates. Unknown data stays unknown; level changes are never presented as fill events.
- Pair with controller 0.13.2 for the bundled dashboard and timezone-aware irrigation event publication.

## [2.15.0] - 2026-09-08

- Add an empty, room-scoped library for saving and reusing user-authored plans as local drafts. Browser storage is separate for live and demo; loading preserves the current zone start dates and uses existing plan validation/review.
- Support the legacy same-room `maximum_shot_duration` entity alongside the canonical name in the controller and runtime calculator. Canonical entities take precedence; invalid configured values do not silently acquire another room's cap.
- Pair with controller 0.13.1. No crop-guide numerical presets or publisher endorsement are included.

## [2.14.0] - 2026-09-08

See the whole day while editing setpoints: the draft VWC/EC curves and P3 emergency floor move immediately beside the saved reference. Compare retained readings over a day, week, month or run-to-date with another run at the same grow age. Water cards distinguish total zone delivery, average per plant and pot capacity, with a local runtime calculator.

**🔧 Technical notes — integration 2.14.0, controller 0.13.0.**

- Add phase-focused manual editing, bounds-aware graph handles, saved/draft overlays and read-only active-plan previews.
- Add room-scoped, revisioned run metadata with captured target references and Recorder comparisons. Recorded history remains subject to retention; a reference captured today is not a historical target audit.
- Add explicit all-plant daily zone litres, per-plant averages, nominal phase-shot volumes and capped runtime estimates. P1 series budgets are conditional; daily adaptive shot counts are not predicted.
- Count new delivered litres from configured flow and elapsed runtime, including duration caps, fractional-second truncation, minimum runtimes and partial aborts. Freeze sizing per shot to prevent in-flight configuration edits changing its recorded volume. Existing totals are preserved.
- Keep all edits local until reviewed; comparison registration and runtime calculators do not activate irrigation.

## [2.13.2] - 2026-09-08

- Show each room's configured name in the workspace instead of a generic sensor label.
- Package the corrected workspace in controller 0.12.1; irrigation logic is unchanged from 0.12.0.
- Document the verified in-place upgrade, preserved settings and consolidated branches.

## [2.13.1] - 2026-09-08

Fix a startup failure when multiple rooms load at once. Every room can now share the native sidebar reliably. Controller 0.12.0 remains the matching version.

**🔧 Technical notes.** Serialize sidebar/static-path registration across concurrent config-entry setup. Live installation exposed the duplicate-panel exception; deterministic concurrent-startup and retry tests cover the correction.

## [2.13.0] - 2026-09-08

One Home Assistant native workspace brings room setup, current readings and whole-grow planning together. The combined VWC/EC planning graph follows each zone's selected day, week and steering profile. Existing installations keep their room identities, setpoints and hydraulic settings.

**🔧 Technical notes — integration 2.13.0, controller 0.12.0.**

- Replace the dashboard family with one React/shadcn operator workspace using inherited Home Assistant themes, bundled fonts and responsive layouts.
- Add reactive combined VWC/EC planning curves, recorded dual-axis history and per-zone day/week recipes with continuous steering between explicit endpoint profiles.
- Add durable plan storage, revisioned preview/save/arm/disarm services and atomic expiring controller snapshots applied at local lights-on boundaries.
- Add reviewed room/zone lifecycle and searchable sensor mapping with stable IDs, archived restoration, per-zone sizing and controller adoption status.
- Add local catch-test calculations, sensor diagnostics and equipment maps; remove unsupported yield/potency claims from the active UI.
- Correct duration accounting, volume-cap bypasses, shared-hardware fault recovery, relative-dryback timing conversion, low-flow sizing and stale sequential-plan decisions.
- Bundle the dashboard in the integration with automatic sidebar registration, publish app-repository metadata, consolidate install/operation instructions, and archive superseded assets with provenance.
- Resolve setup hydraulics from the current room/zone number entities so a rename or mapping edit preserves live plant counts, pot size and dripper settings.
- Archive unused facility examples, environment templates and disabled workflows; add current README screenshots and a public interactive demo link.
- Preserve base VWC shot sizes while EC is unknown, suspend EC adaptation, and expose degraded EC status (#37).
- Reject nonfinite or invalid/stale/future-dated feed readings; describe arithmetic sensor averaging and relative dryback accurately (#38, #39).
- Persist timed manual override deadlines across restart/reload and cancel obsolete callbacks on retrigger/manual changes (#40).
- Track rolling seven grow-day delivery estimates with explicit partial-history coverage; missing weekly sources remain unknown (#41).
- Audit all branch tips and retain recoverable archives; use tracked-only controller release packaging.
- See docs/FEATURE_MATRIX.md for validation evidence and live commissioning limits.

## Older releases

Releases before 2.13.0 (up to July 2026) are in the git history of this file.
