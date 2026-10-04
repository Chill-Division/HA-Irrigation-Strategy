<!--
One change per pull request, into `main`. See CONTRIBUTING.md.
If describing it needs the word "and", it is two pull requests.
-->

## 🌱 In plain English

<!-- What changes for the person running a room, and why. No jargon. -->

## 🔧 Technical notes

<!-- What changed in the code and why this way. Anything a reviewer would otherwise have to work out. -->

## How it was tested

<!-- Which suites, and the new tests that fail without this change. -->

- **On real hardware:** <!-- exactly what was run on real plumbing, or "not run on hardware" -->
- **Existing installs:** <!-- what happens to a box that updates in place; name the seeded fixture if state, options or entities are touched -->

## Checklist

- [ ] One change. No unrelated fixes, no drive-by reformatting.
- [ ] Targets `main`.
- [ ] Does **not** change a version number (only `scripts/release.py` does).
- [ ] Its notes are under **Unreleased** in `CHANGELOG.md` (🌱 and 🔧), in `addons/f2_control/CHANGELOG.md` if the controller or the dashboard it serves changed, and in `WHATS_NEW.md` if a grower would notice.
- [ ] Generated files (dashboard bundle, vendored engine copy) changed only together with their source.
- [ ] Nothing under `.github/`, no dependency or Dockerfile change, unless that is the whole pull request.
- [ ] Config flow, entity ids or what the integration tells the controller: proven in `tests_ha/`, not only against the stubs.
