# Changelog

All notable changes to PHASE Steering (Crop Steering until 1.0.2) will be documented in this file.

**Two views per release.** Each version leads with what changed and why it matters, written so
anyone can follow it without knowing the internals, followed by **🔧 Technical notes**, the entity-
and code-level detail for developers and AI agents working on the repo.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-10-09

Integration and controller **1.0.3**.

- **The project's address is now github.com/Chill-Division/PHASE-Steering.** The old address
  keeps working, so a Home Assistant that already has it needs no change: leave it as it is.

### 🔧 Technical notes

- Both repositories were renamed on 2026-10-09: `Chill-Division/HA-Irrigation-Strategy` to
  `Chill-Division/PHASE-Steering`, and `ChillingSilence/HA-Irrigation-Strategy` to
  `ChillingSilence/PHASE-Steering`. GitHub redirects the old addresses for the web, its API and
  git. HACS records a rename itself (`renamed_repositories` in its source), and the Supervisor's
  `git ls-remote` and `git fetch` follow the redirect (checked on the old public address).
- The Supervisor names the app after the address it was added from. A box on the old address keeps
  `f50c47e4_f2_control` and its `/data`; one added at the new address gets `f99c52b1_f2_control`.
  Swapping one address for the other is a move ([INSTALL.md](docs/INSTALL.md)), not an update, and
  the app's documentation and the install guide say to leave the old one.
- Links: `manifest.json` (documentation, issue tracker), the Repairs cards' Learn more
  (`const.REPAIRS_DOCS_URL`), What's new's release notes, the app's `config.yaml`, `repository.yaml`
  and DOCS.md, the README's links, badges and pictures, the docs, and `release.py`'s `PUBLIC`.
  `tests/test_repository_links.py` keeps every link on the new name.
- No repository may ever take an old name: it would take the address from every box still on it.

## [1.0.2] - 2026-10-09

Integration and controller **1.0.2**.

- **Crop Steering is now PHASE Steering**, short for Precision Hydration And Steering Engine, with
  a new icon: the day's four phases around a drop of water. Nothing else changes: your rooms,
  settings, strategies, history and automations carry on as they were.

### 🔧 Technical notes

- Names only. The integration (`manifest.json`, `hacs.json`), its sidebar entry (now
  `mdi:water-circle`), the room's device, the zones' entity names (`PHASE Steering Zone N …`), the
  setup wizard's default name, the setup and Repairs texts, the error codes, the dashboard, the
  controller app (`PHASE Steering Controller`, its panel and `repository.yaml`) and the brand images.
  The integration keeps the name in one place, `const.PRODUCT_NAME`.
- Unchanged: the `crop_steering` domain, every entity id, the `f2_control` slug and the app's
  options and `/data`, the sidebar's address, the strategy and feed recipe file formats and the
  repository's address.
- The room's device had two names, "Crop Steering System" from the sensors and "Crop Steering" from
  the other platforms, whichever registered last; it has one, PHASE Steering. Home Assistant renames
  the device and the entities' default names in place, and keeps any name the operator gave either.
  From 2026.9 Home Assistant shows the device's name in front of each entity's, so a room's entities
  read "PHASE Steering …" there.
- Controller: the vitals notifications are titled "PHASE Steering vitals" where the app's
  "Name in notifications" option was never changed. A room left at the wizard's default name
  (PHASE Steering, or Crop Steering System before) is still left out of alerts
  (`DEFAULT_ROOM_NAMES`).
- Tests: `tests_ha/test_product_name.py` (a fresh install, and a seeded old install updated in
  place: the device and names follow, no id moves, the operator's device name stays) and a real
  wizard left at its default name in `tests_ha/test_alerts_name_the_zone.py`.

## [1.0.1] - 2026-10-08

Integration and controller **1.0.1**.

- **Unified naming of Irrigation Strategy and Feed Recipes.**
- **Feed EC now set per-recipe** to allow for steering at lower EC rootzones, defaults to 3.0EC
  where not set.
- Bug fixes and improvements.

### 🔧 Technical notes

- Docs: `docs/HOW_IT_WORKS.md`, linked first in the README's Documentation and from the user guide.
  Every rule in it is the one the engine, the controller or Auto setpoints applies, and its pictures
  are the README's own screenshots.
- Release: `scripts/release.py --sync` fast-forwards the public `main` to `main` here once Validate
  has passed on it, with no version, tag or release. `sync_refusal` refuses when the commits since
  touch `custom_components/` or `addons/f2_control/`: the Supervisor builds the app from the public
  `main`, so they would reach every box that installs or rebuilds it under the last released
  number. `docs/RELEASING.md` (Commits that ship nothing) and CLAUDE.md say when to use it.
  The app's changelog, documentation and pictures and the controller's tests go too
  (`SHOWN_ONLY`): the Supervisor only shows them, and none is built into the image.
- Docs: stale references removed across `docs/`, `CONTRIBUTING.md`, the engine's README and the
  app's `DOCS.md`, each checked against the code. `docs/ENTITIES.md` gains the room prefix, an
  Engine ranges table (the `validate_params` bounds narrower than the entities') and corrected
  rows for `maximum_ec`, `field_capacity`, EC stacking, the steering selects, the display-only EC
  sensors, `app_status`, `ai_heartbeat`, the safety sensors and the manual override.
  `docs/RELEASING.md` says the 2.x numbers can be used again.
- Text only, no change to watering: `docs/error-codes.json` (CS-206, CS-401, CS-601, CS-606,
  CS-608) and `docs/ERROR_CODES.md` from it; the CS-206 and CS-401 notifications in
  `controller.py`; the CS-606 Repairs card (`strings.json`, `translations/en.json`); the Maximum EC
  help and the Reservoir's not-reported note on the dashboard; comments and docstrings in the
  engine (both copies), the controller, `health.py`, `strategy.py` and `room.py`; the app's
  `num_zones` and `enable_flag` option texts (`addons/f2_control/translations/en.yaml`); and the
  `whats_new_seen` example version in `services.yaml`.
- Integration: `sensor.crop_steering_<prefix>p1/p2/p3_shot_duration_seconds` time the configured
  shot in each active zone from the zone's own `substrate_volume`, `drippers_per_plant` and
  `dripper_flow_rate` (the room's where the zone has none), then whole seconds, at least
  `MIN_SHOT_S` and at most `max_shot_duration`, as `_act_zone` does. The state is the longest
  zone's, attribute `zones` each zone's, and unknown when no zone's sizing gives a flow (it used to
  read 0). `ShotCalculator.calculate_shot_duration` takes `drippers_per_plant`;
  `capped_shot_seconds` is new. `tests_ha/test_shot_duration_sensors.py` holds the real sensors
  against the real controller's arithmetic.
- Feed EC: `feed.clean` keeps a recipe's optional `ec` (mS/cm, 0.1 to 10; none, empty or 0 is
  none; a stored recipe without it loads with none) and `feed.plan` publishes the stage in use's
  as `feed_ec` on `sensor.crop_steering_<prefix>feed_plan`. The controller's `feed_plan()` reads it
  (anything not a number from 0.1 to 10 is none) and `_snapshot` passes it as
  `ZoneSnapshot.feed_ec`, which every flush and dilution test in `decide()` compares pore EC with;
  without it the engine's default stays 3.0. The dashboard's recipe card has the field, recipe
  files carry `ec` (a file without it imports with none), and CS-206 says where the feed's EC comes
  from. `tests_ha/test_feed_batches.py` takes a recipe's EC from the real `feed_save` to the real
  controller's snapshot.
- Wording: "irrigation strategy" (or "strategy") replaces "grow plan", "plan" and the irrigation
  "recipe" in the dashboard, the integration's Repairs cards (CS-606, CS-607), `services.yaml`,
  `setup_api`'s zone-change refusal, `strategy_model`'s zone check, the strategy sensor's friendly
  name (Irrigation strategy), `select.crop_steering_<prefix>recipe_stage`'s name (Strategy Stage),
  `docs/error-codes.json` and the docs. Nothing a box or an automation reads moves: entity ids,
  service ids and fields, the `#/strategy` and `#/grow-plan` addresses, the library's storage key
  and the export format (`crop-steering-plan`) stay; exported files are now named
  `crop-steering-strategy-….json`. The controller's Auto setpoints frozen reason names an armed
  irrigation strategy. The browser checks and unit tests follow the new labels.
- Dashboard: a feed recipe card's "In use" pill, export and remove buttons are one group
  (`.res-recipe-actions`), the header grid's last column; on a phone they take a row of their own.

## [1.0.0] - 2026-10-05

Integration and controller **1.0.0**.

- **Version 1.0, for everyone.** The first release published at
  github.com/Chill-Division/HA-Irrigation-Strategy, where HACS and Settings → Apps install it from.
  The numbers start again: 1.0.0 follows 2.37.1. On a box already running 2.37, the Supervisor
  offers the controller app as usual, but HACS offers no lower number: redownload Crop Steering in
  HACS and pick 1.0.0. What's new then shows what's new in 1.0.
- **Credits and licences.** The README credits JakeTheRabbit's HA-Irrigation-Strategy, where Crop
  Steering began, and the licence names him and Chill Division. Every part a box installs carries
  the licence, and the dashboard ships its open-source libraries' licences beside it.
- **The README shows the public repository's pictures.** Its screenshots and its link to the rest
  come from github.com/Chill-Division/HA-Irrigation-Strategy, like its other links.
- **Fresh screenshots.** The README and the screenshots page show this release, the new icon
  included.
- **No What's new with the first-run tour.** Someone shown round the dashboard for the first time
  is not also shown what changed in it. The two met only where a room was set up again on a box
  that had run an older release.
- **A new icon.** A tank of water with a seedling in front of it, white on the same blue tile: in
  the dashboard's menu, on Home Assistant's integrations page, in HACS, and for the controller app
  in Settings → Apps. The logo beside it says Crop Steering in the tile's blue, which reads on a
  light theme and a dark one.
- **Steadier accessibility checks.** The checks that read the dashboard's contrast in the dark
  theme no longer fail now and then on text that was still turning light. They wait until nothing
  on the page is changing colour, so what they measure is what a grower sees.

### 🔧 Technical notes

- Licence: `LICENSE` names JakeTheRabbit and, under him, Chill Division. Copies ship in
  `custom_components/crop_steering/` (HACS installs only that folder, and the release zip holds
  only it), `addons/f2_control/` (the Dockerfile copies it into the app's image) and
  `crop-steering-engine/`. The dashboard build writes `THIRD_PARTY_LICENSES.txt`: every npm package
  in the build's module graph, and Tailwind, sorted and undated (`frontend/vite.config.ts`).
  `package.mjs` ships it beside both copies of the dashboard, and `tests/test_licence.py` holds
  all of it.
- Docs: the README's six image addresses (raw.githubusercontent.com) and its screenshots link move
  from `ChillingSilence` to `Chill-Division`, where its other links already went. They stay
  absolute, so HACS, which shows the README, shows the pictures too (`docs/SCREENSHOTS.md`).
- Docs: the twelve `img/` screenshots that show the menu or the time of day are retaken by the
  browser checks that write them, at 2:35 PM in the demo (`TZ=Asia/Dubai`), as the last set was
  taken in the afternoon. `docs/SCREENSHOTS.md` says to take them while the day is under way.
- Dashboard: `WhatsNewOnUpdate` marks the installed release seen and opens no window when it starts
  the first-run tour (`whats_new_get`'s `tour`), as its comment already said it did. The
  verify-dashboard tour check opens the demo as a new installation whose record is behind
  (`?tour=new&whats-new=2.22.0`): the tour, and no What's new, which the bundle before this opened
  too.
- Release: `scripts/release.py --start-again` releases a number below the last one, never one the
  changelog already has (`check_number`). It leaves `WHATS_NEW.md` with only the sections numbered
  up to the new release (`drop_numbered_above`), since the dashboard orders releases by number; the
  changelogs keep everything. `test_version_consistency` now holds every release to one number for
  the pair: it skipped anything below 2.21.0, which 1.x would have been. Integration:
  `WhatsNew.async_init` reads a record numbered above the installed release as unknown, so a box
  that last showed 2.37.1 shows the last 30 days of releases up to 1.0.0 and marks it. The
  real-HA What's new tests number their earlier releases 0.x, under every real one.
- Dashboard, integration and app: `BrandGlyph` (`frontend/src/components/brand-glyph.tsx`)
  replaces the menu's droplets. Its seedling is drawn twice, first wide in the tile's colour
  (`.brand-glyph-halo`), so the tank's lines stop short of it. A new script,
  `frontend/scripts/make-brand-images.mjs` (run after `npm run build`), draws the integration's
  `brand/` images and the app's `icon.png` and `logo.png` from the built dashboard's own mark, in
  its light theme's colours and font. It replaces `scripts/make_brand_images.py` and that
  script's 2.2 MB source picture, `img/crop-steering-logo.png`. The `dark_` images are gone: Home
  Assistant serves the light ones in their place, which `tests_ha/test_brand_images.py` proves
  through its web server.
- Tests: `settled` (`frontend/scripts/settled.mjs`) waits until no finite animation or transition
  is running (at most 5 s), then two frames, and every axe audit in the browser checks calls it
  first. At reduced motion every element eases every property for 0.01 ms, and an element added
  while its parent's colour is still changing starts its own change only when the parent's ends,
  so after the theme flips a colour reaches nested text one level a frame: the strategy page's
  headings took about twelve frames on a CPU slowed sixfold. The two-frame wait read them still
  dark on dark (#212121 on #1c1c1c, 1.05:1) in "setting explainer, dark", which failed pull
  requests #58 and #139. With the race forced, the old wait failed 6 runs of 6 and `settled`
  none. It replaces `verify-workspace`'s own one-pass `settle` and `light-shot.mjs`'s `settled`.
