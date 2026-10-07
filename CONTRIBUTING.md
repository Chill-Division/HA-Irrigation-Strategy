# Contributing

This software opens valves and runs pumps on unattended crops, and it updates itself onto boxes nobody is watching. How a change gets in matters as much as what it does. How it gets *out* to rooms is in [docs/RELEASING.md](docs/RELEASING.md).

## The rule

> **One change, one branch, one pull request.**

A change is one thing a reviewer can hold in their head: one feature, one fix, one refactor, one upgrade of a dependency. If the honest description of a pull request needs the word "and", it is two pull requests.

This is not tidiness. Large mixed changes are how problems get in:

- **They cannot be reviewed.** Nobody reads four thousand changed lines. They skim, and approve what they did not read. One release arrived as five commits in forty-five minutes touching the setup wizard, the controller's shot sequence, twenty dashboard source files and a new cloud feature; four defects went through with it ([docs/audits/2026-09-21-first-run-review.md](docs/audits/2026-09-21-first-run-review.md)).
- **They cannot be tested alone.** When a room misbehaves after an update carrying six changes, the first day goes on finding out which one did it.
- **They cannot be taken back alone.** Reverting one bad feature out of a mixed commit means rewriting it by hand, in a hurry, on the code that drives the pump.
- **Things hide in them.** A mistake, a debugging leftover, or something deliberately malicious is far easier to slip past a reviewer inside a big change than in a small one. This matters more here than in most projects: boxes build the controller straight from this repository.

## Branches

| Branch | What it is |
| --- | --- |
| `main` | **Every pull request targets `main`**, and releases are made from it. The rooms that track this repository build the controller from it, and every public release was released here first ([docs/RELEASING.md](docs/RELEASING.md)). Nothing reaches it but merged pull requests and the release command's commits. |
| `feat/…` `fix/…` `docs/…` `ci/…` | Your change. Branch from `main`, delete after merging. |

## What a pull request must be

1. **One change.** No drive-by reformatting, no unrelated fixes "while I was there", no refactor bundled with a behaviour change. Found something else? Open a second pull request.
2. **Small enough to read.** As a guide, under about 400 changed lines of hand-written code, not counting tests. A feature that genuinely needs more (it crosses the integration, the controller and the dashboard) is built as **one commit per layer**, each passing the tests, so it can be reviewed commit by commit.
3. **Complete.** It passes every check by itself, and it leaves `main` working if nothing else is ever merged. Half a feature behind a later pull request is not a smaller change, it is a broken one.
4. **Tested where the risk is.** Anything touching the config flow, entity ids, or what the integration tells the controller is proven in `tests_ha/` (a real Home Assistant), not only against the stubs in `tests/`. Anything touching persisted state, add-on options or entities comes with a seeded snapshot of an old install showing it still loads ([docs/TESTING.md](docs/TESTING.md)).
5. **Honest about hardware.** Say what was run on real plumbing and, just as plainly, what was not. "Not run on hardware" is a perfectly good answer for a pull request; the rooms that take the release here are where it runs first. Leaving it unsaid is not.
6. **Version-free, with its notes.** A pull request never changes `manifest.json`, `const.py` or the add-on's `config.yaml` version: only the release command does. It writes its own notes under **Unreleased** in `CHANGELOG.md`, the controller's `CHANGELOG.md` and `WHATS_NEW.md`, so the release has nothing left to write ([docs/RELEASING.md](docs/RELEASING.md), *Writing the notes*).

The pull request template asks for all of this.

## Generated files

Two kinds of file in this repository are produced from other files. They change **only** in the same pull request as their source, and the checks prove they match:

| Generated | From | Check |
| --- | --- | --- |
| `custom_components/crop_steering/www/` and `addons/f2_control/www/` (the dashboard, one ~1 MB minified file) | `frontend/src` via `npm run build --prefix frontend` | CI rebuilds it and fails if the committed file differs by one byte |
| `addons/f2_control/f2_control/crop_steering_engine/` | `crop-steering-engine/src/crop_steering_engine/` | CI diffs the two copies |

Nobody can review a minified bundle by eye, so nobody is asked to: review `frontend/src`, and let the check prove the bundle is that source and nothing else. **A pull request that changes a generated file without its source, or fails that check, is not merged**, whatever the explanation.

## Changes that get a slower read

Open these as their own pull request, never mixed into a feature, and read every line:

- anything under `.github/` (a workflow runs with the repository's token);
- `Dockerfile`, `build.yaml`, `requirements*.txt`, `package.json`, `package-lock.json` (what gets installed onto every box and every CI run);
- `addons/f2_control/config.yaml` (what the controller is allowed to touch on the host);
- anything that adds a network call, a new outbound address, or a new credential.

## Commits

Conventional commits (`feat:` `fix:` `docs:` `test:` `ci:` `chore:`; `release:` is the release command's), imperative, with the *why* in the body. Each commit is one logical step and leaves the tests passing. Merge pull requests with **Create a merge commit**, not squash: the reviewed commits stay intact, `git log --first-parent main` reads as one line per pull request, and `git revert -m 1 <merge>` takes a whole feature back out in one step.

## Review and merging

- **The author does not merge their own pull request.** Someone else reads **Files changed**, top to bottom, and merges.
- That applies without exception to changes written by an AI assistant. An assistant may write the code and open the pull request; a person reads it and decides. An assistant merges a pull request, or runs the release command, only when the owner asks for that, each time, and never pushes to `main` itself.
- Every `Validate` job is green on the exact commit being merged, with the branch up to date with `main`.
- A reviewer who does not understand a change asks, and the answer goes into the code or the pull request, not into a chat that disappears.

Releasing is a separate decision, the owner's: `scripts/release.py` releases what is on `main` to the rooms that track this repository, and `--public` then takes that same commit to everyone else ([docs/RELEASING.md](docs/RELEASING.md)). A green CI is what it needs, not a reason to run it.

## Changes from JakeTheRabbit/HA-Irrigation-Strategy

This repository started as a fork of it and now goes its own way. A change from there is taken like any other: a branch, a pull request into `main`, read commit by commit, with its notes.
