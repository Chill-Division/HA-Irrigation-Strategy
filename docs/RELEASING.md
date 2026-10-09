# Releasing

This software opens valves and runs pumps on unattended crops, so a release goes to one set of rooms
before it goes to everyone. It takes one command for each:

```bash
python scripts/release.py 2.26.0            # released here: the rooms that track this repository update
python scripts/release.py 2.26.0 --public   # later, the same commit for everyone else
```

## Two repositories

| Repository | Who installs from it | What moves its `main` |
| --- | --- | --- |
| `ChillingSilence/PHASE-Control` (this one) | The maintainer's own rooms. They are the test. | Merged pull requests, and `release.py <version>`'s commit |
| `Chill-Division/PHASE-Control` | Everyone else | `release.py <version> --public`, which fast-forwards it to a version already released here, and `release.py --sync`, for commits that ship nothing |

Every pull request is merged into `main` ([CONTRIBUTING.md](../CONTRIBUTING.md)), and releases are
made from it. The public repository takes no pull requests and no commits of its own: everything on
it was released here first, byte for byte.

## How an update reaches a box

| Half | Delivered by | What offers an update |
| --- | --- | --- |
| Integration (`custom_components/`) | HACS | A **GitHub release** on the repository the box added. |
| Controller (`addons/f2_control/`) | Supervisor's app store | A new `version:` in `addons/f2_control/config.yaml` on the branch the box tracks. `config.yaml` has no `image:`, so Supervisor builds the controller on the box from that branch. |

What follows from that (checked against the Supervisor source):

- **A box follows the branch it was installed from, for life.** A plain repository address means
  `main`. Never rename or delete `main`.
- **The repository address is the controller's identity.** The same controller installed from the
  other repository is a different app with an empty `/data`: phase, counters, water history and
  learned peaks start again. Moving a box is a migration ([INSTALL.md](INSTALL.md)), not an edit.
- **Both repositories were called `HA-Irrigation-Strategy` until October 2026**, then for a day
  `PHASE-Steering`, and are now `PHASE-Control`, with the app. GitHub sends the old addresses on to
  the new ones, for git, HACS and the web, so a box added under an old one keeps it and keeps
  updating. From the public repository its controller is `f50c47e4_f2_control` under
  `HA-Irrigation-Strategy`, `f99c52b1_f2_control` under `PHASE-Steering` and `4cddaccb_f2_control`
  under `PHASE-Control`. Never create a repository under an old name: it would take the address
  from every such box.
- **Between releases, `main` also carries what was merged since the last one.** Only a release
  changes the number, so no box is offered anything new before then. But a controller built in
  the meantime (a fresh install, a Rebuild, or an update to the last release taken late) builds
  `main` as it is then, under the last released number. So merge close to releasing. The public
  repository's `main` only ever moves to a released commit.

## Writing the notes

Every pull request writes its own notes, so a release has nothing left to write. Under the
**Unreleased** heading at the top of each file (add the heading if it is not there):

- `CHANGELOG.md`, `## [Unreleased]`: first its lines on what changes for the person running a room,
  and why, under no heading of their own; then its lines under **🔧 Technical notes** (entities,
  code, upgrade). A short paragraph above them may say what the release was checked by.
- `addons/f2_control/CHANGELOG.md`, `# Unreleased`: what changed in the controller or in the
  dashboard it serves. Leave it out when neither did.
- `custom_components/crop_steering/WHATS_NEW.md`, `## Unreleased`: one line a grower would notice,
  in their words, or nothing. The dashboard's What's new window shows these once after an update;
  the rules are at the top of that file. At most five lines per release; small things are one last
  line, `- Bug fixes and improvements.`

No pull request changes a version number. The release command is the only thing that does.

## Releasing here

When the changes for a release are merged into `main` and Validate has passed on the last merge:

```bash
git checkout main && git pull --ff-only
python scripts/release.py 2.26.0 --dry-run   # the files it changes, and the release notes
python scripts/release.py 2.26.0
```

The release command refuses unless `main` is checked out, clean, the same as `origin/main` and
green in Validate, the number is new and higher, and `CHANGELOG.md` has its Unreleased notes. Then
it:

1. dates the three Unreleased sections as `2.26.0` and today (with nothing written for the
   controller, its entry only names the pair; with nothing for growers, What's new says
   "Bug fixes and improvements.");
2. sets `2.26.0` in `manifest.json`, `const.py`, the controller's `config.yaml` and the README badge;
3. runs the version and notes tests on the result (it needs pytest);
4. commits `release: 2.26.0`, tags `v2.26.0`, pushes both;
5. publishes the GitHub release, its notes the changelog entry up to its technical notes, linking to
   those at the tag.

The rooms that track this repository are then offered the pair: HACS offers the integration and
Supervisor the controller. Update them, confirm the versions and a current controller heartbeat,
and watch a grow-day. If the push went through but publishing the release did not (a network error,
an expired login), run the same command again: it publishes the release for the tag and stops.

## Releasing it for everyone

When it has run well here:

```bash
python scripts/release.py 2.26.0 --public --dry-run
python scripts/release.py 2.26.0 --public
```

It checks that `v2.26.0` is released here and green in Validate, pushes that exact commit and its tag
to the public `main` (a fast-forward, or nothing: git refuses anything else), and publishes the same
release there. Nothing is rebuilt or re-tagged.

## Commits that ship nothing

```bash
python scripts/release.py --sync --dry-run
python scripts/release.py --sync
```

The README, the docs, the pictures, the scripts and the tests can go to the public `main` between
releases. `--sync` takes `main` as it is here, once Validate has passed on it, to the public `main`:
a fast-forward, with no version and no release. It refuses when anything since the public `main`
changes the integration or the controller app (`custom_components/`, `addons/f2_control/`). The
Supervisor builds the app from the public `main`, so a change there would reach every box that
installs or rebuilds it, under the last released number: release those instead. The app's
changelog, documentation and pictures (`CHANGELOG.md`, `DOCS.md`, `icon.png`, `logo.png`) and the
controller's tests go: the Supervisor only shows those, and none of them is built into the image.

A version that goes wrong here is never made public. Fix it, merge the fix, and release the next
number here. **A version number is never reused for different code**, apart from the 2.x
numbers 1.0.0 started again from (Versions, below).

## Versions

- The integration and the controller carry **one number** and are released together, even when one
  of them did not change. `tests/test_version_consistency.py` keeps `manifest.json`, `const.py`, the
  controller's `config.yaml`, the README badge and both changelogs on it.
- Numbers only go up. A patch number for fixes, the minor number for anything new.
- Once, they started again: 1.0.0, the first release for everyone, followed 2.37.1
  (`release.py 1.0.0 --start-again`). The releases and tags numbered before it were deleted and
  both changelogs start at 1.0.0, so 2.x numbers can be used again. `--start-again` refuses a
  number that is not lower, or that the changelog already has. It leaves What's new with only the
  releases numbered up to the new one, since the dashboard orders them by number. HACS offers a
  box no number lower than the one it has, so a box on 2.37 gets 1.0.0 by Redownload in HACS; the
  Supervisor offers the controller app at any new number.
- Once, a number was released twice: 1.0.3 went out with only the repository's new links, was
  withdrawn the same day (its tags and GitHub releases deleted, `release: 1.0.3` reverted on
  `main`), and was released again with the PHASE Control name. A box that took the first 1.0.3 is
  offered nothing for the second, as both say 1.0.3: Redownload in HACS and Rebuild the app get it.

## Rolling back a room

- **Integration:** HACS, the repository, *Redownload*, choose the previous version, restart Home
  Assistant.
- **Controller:** restore the app's backup taken before the update. A backup of a locally built
  app holds its image beside `/data`, so the code and the state go back together; confirm yours
  does before you rely on it. Take one before every update.
- No branch of either repository is ever moved backwards. The fix is the next release.

## Setting up the public repository (once)

Create `Chill-Division/PHASE-Control` empty (no README, licence or `.gitignore`), or as a fork
of this one, and allow GitHub Actions on it, so its releases get their packaged archives. The first
`--public` creates its `main`. Pointing the links in the code at it (What's new, `manifest.json`, the
app store's `repository.yaml` and `config.yaml`, the README) is a pull request of its own.
