# Changelog

All notable changes to the Advanced Automated Crop Steering System will be documented in this file.

**Two views per release.** Each version leads with what changed and why it matters, written so
anyone can follow it without knowing the internals, followed by **🔧 Technical notes**, the entity-
and code-level detail for developers and AI agents working on the repo.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- **The public repository's README and docs between releases.** A change to the README, the docs,
  the pictures, the scripts or the tests can now go to the public repository without a new version.
  A change to the integration or the controller app still waits for a release.

### 🔧 Technical notes

- Release: `scripts/release.py --sync` fast-forwards the public `main` to `main` here once Validate
  has passed on it, with no version, tag or release. `sync_refusal` refuses when the commits since
  touch `custom_components/` or `addons/f2_control/`: the Supervisor builds the app from the public
  `main`, so they would reach every box that installs or rebuilds it under the last released
  number. `docs/RELEASING.md` (Commits that ship nothing) and CLAUDE.md say when to use it.

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
