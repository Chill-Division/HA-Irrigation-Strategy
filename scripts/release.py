#!/usr/bin/env python3
"""Release this repository in one command.

    python scripts/release.py 2.25.0             # release it here; the boxes that track it update
    python scripts/release.py 2.25.0 --public    # then the same commit, for everyone else
    python scripts/release.py 2.25.0 --dry-run   # either one: show what it would do, change nothing

The first form releases `main` as it is, once the Validate workflow has passed on it. It dates the
Unreleased sections of CHANGELOG.md, the controller's CHANGELOG.md and WHATS_NEW.md as this version,
sets the version in manifest.json, const.py, the controller's config.yaml and the README badge,
checks the result with the version and notes tests, commits it as "release: <version>", tags it
v<version>, pushes both and publishes the GitHub release, its notes taken from the changelog.

`--public` takes that tagged commit, unchanged, once Validate has passed on it too, to the main
branch of PUBLIC (only ever a fast-forward) and publishes the same release there. Nothing is
rebuilt: the commit everyone else gets is the one the boxes tracking this repository ran.

It needs git, an authenticated GitHub CLI (`gh auth login`) and pytest. docs/RELEASING.md says
when to run it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import release_notes  # noqa: E402

PUBLIC = "Chill-Division/HA-Irrigation-Strategy"
BRANCH = "main"
WORKFLOW = "ci-validate.yml"
FIXES = "Bug fixes and improvements."

MANIFEST = "custom_components/crop_steering/manifest.json"
CONST = "custom_components/crop_steering/const.py"
ADDON_CONFIG = "addons/f2_control/config.yaml"
README = "README.md"
CHANGELOG = "CHANGELOG.md"
ADDON_CHANGELOG = "addons/f2_control/CHANGELOG.md"
WHATS_NEW = "custom_components/crop_steering/WHATS_NEW.md"
FILES = (MANIFEST, CONST, ADDON_CONFIG, README, CHANGELOG, ADDON_CHANGELOG, WHATS_NEW)
CHECKS = (
    "tests/test_version_consistency.py",
    "tests/test_whats_new.py",
    "tests/test_release_notes.py",
)


class Refused(SystemExit):
    """A reason not to release. Nothing has been pushed or published when it is raised."""


def version_tuple(version: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise Refused(f"'{version}' is not a version: use three numbers, like 2.25.0")
    major, minor, patch = (int(part) for part in version.split("."))
    return major, minor, patch


# --------------------------------------------------------------------------- the edits
def _replace_one(text: str, pattern: str, new: str, where: str) -> str:
    """Replace the one match of `pattern`'s group 1 with `new`, leaving the rest of the file
    byte for byte, its line endings included."""
    matches = list(re.finditer(pattern, text, re.M))
    if len(matches) != 1:
        raise Refused(f"{where}: expected one version to set, found {len(matches)}")
    start, end = matches[0].span(1)
    return text[:start] + new + text[end:]


def set_versions(files: dict[str, str], version: str) -> dict[str, str]:
    out = dict(files)
    out[MANIFEST] = _replace_one(
        files[MANIFEST], r'^\s*"version":\s*"([^"]+)"', version, MANIFEST
    )
    out[CONST] = _replace_one(
        files[CONST], r'^SOFTWARE_VERSION = "([^"]+)"', version, CONST
    )
    out[ADDON_CONFIG] = _replace_one(
        files[ADDON_CONFIG], r'^version:\s*"?([0-9.]+)"?\s*$', version, ADDON_CONFIG
    )
    out[README] = _replace_one(
        files[README], r"badge/Release-(\d+\.\d+\.\d+)-", version, README
    )
    return out


def _section(text: str, heading: str, level: str) -> tuple[int, int] | None:
    """(start, end) of the section under an exact heading line, up to the next heading of the
    same level; None when there is no such heading."""
    match = re.search(rf"^{re.escape(heading)}[ \t]*\r?\n", text, re.M)
    if not match:
        return None
    following = re.search(rf"^{re.escape(level)} ", text[match.end() :], re.M)
    end = match.end() + following.start() if following else len(text)
    return match.start(), end


def date_changelog(text: str, version: str, day: str) -> str:
    span = _section(text, "## [Unreleased]", "##")
    # What changed, for anyone, comes first, under no heading of its own; the technical notes follow.
    summary = (
        re.split(r"^### ", text[span[0] : span[1]], maxsplit=1, flags=re.M)[0] if span else ""
    )
    if span is None or not re.search(r"^- ", summary, re.M):
        raise Refused(
            f"{CHANGELOG} has no '## [Unreleased]' section that says what this release changes "
            "before its technical notes: write it there first"
        )
    start, end = span
    body = text[start:end].split("\n", 1)[1].lstrip("\n")
    opening = f"Integration and controller **{version}**.\n\n"
    return f"{text[:start]}## [{version}] - {day}\n\n{opening}{body}{text[end:]}"


def date_addon_changelog(text: str, version: str) -> str:
    pair = f"Pair with integration {version}."
    span = _section(text, "# Unreleased", "#")
    if span is None:  # nothing was written for the controller
        return f"# {version}\n\n{pair}\n\n{text}"
    start, end = span
    body = text[start:end].split("\n", 1)[1].lstrip("\n")
    return f"{text[:start]}# {version}\n\n{pair}\n\n{body}{text[end:]}"


def date_whats_new(text: str, version: str, day: str) -> str:
    heading = f"## {version} - {day}"
    span = _section(text, "## Unreleased", "##")
    if span is None:  # nothing a grower would notice
        first = re.search(r"^## \d+\.\d+\.\d+ - ", text, re.M)
        at = first.start() if first else len(text)
        return f"{text[:at]}{heading}\n\n- {FIXES}\n\n{text[at:]}"
    start, end = span
    items: list[str] = []
    for line in text[start:end].split("\n")[1:]:
        if line.startswith("- "):
            items.append(line)
        elif (
            line.startswith("  ") and line.strip() and items
        ):  # continues the line above
            items[-1] += "\n" + line
        elif line.strip():
            raise Refused(
                f"{WHATS_NEW}: the Unreleased section holds only '- ' lines, one per change; "
                f"found {line!r}"
            )
    fixes = f"- {FIXES}"
    items = [item for item in items if item != fixes] + (
        [fixes] if fixes in items else []
    )  # the small things together, last
    if not items:
        items = [fixes]
    return f"{text[:start]}{heading}\n\n" + "\n".join(items) + f"\n\n{text[end:]}"


def prepare(files: dict[str, str], version: str, day: str) -> dict[str, str]:
    """Every file the release commit changes, as it will be. Pure: `files` maps each path in
    FILES to its current text."""
    out = set_versions(files, version)
    out[CHANGELOG] = date_changelog(files[CHANGELOG], version, day)
    out[ADDON_CHANGELOG] = date_addon_changelog(files[ADDON_CHANGELOG], version)
    out[WHATS_NEW] = date_whats_new(files[WHATS_NEW], version, day)
    return out


def current_version(files: dict[str, str]) -> str:
    return json.loads(files[MANIFEST])["version"]


# --------------------------------------------------------------------------- git and GitHub
def run(*cmd: str, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode:
        raise Refused(
            f"`{' '.join(cmd)}` failed:\n{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def slug_of(url: str) -> str:
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    if not match:
        raise Refused(f"origin is not a GitHub repository: {url}")
    return match.group(1)


def public_url(origin_url: str) -> str:
    """PUBLIC, reached the way origin is (SSH or HTTPS), so the same credentials push to it."""
    if origin_url.startswith("git@"):
        return f"git@github.com:{PUBLIC}.git"
    return f"https://github.com/{PUBLIC}.git"


def ci_verdict(runs: list[dict], sha: str) -> str | None:
    """None when the newest Validate run on `sha` passed; otherwise why not."""
    mine = [r for r in runs if r.get("head_sha") == sha]
    if not mine:
        return f"Validate has not run on {sha[:12]}"
    newest = max(mine, key=lambda r: (r.get("run_number", 0), r.get("run_attempt", 0)))
    if newest.get("status") != "completed":
        return f"Validate is still running on {sha[:12]}: {newest.get('html_url')}"
    if newest.get("conclusion") != "success":
        return f"Validate {newest.get('conclusion')} on {sha[:12]}: {newest.get('html_url')}"
    return None


def require_ci(slug: str, sha: str) -> None:
    runs = json.loads(
        run(
            "gh",
            "api",
            f"repos/{slug}/actions/workflows/{WORKFLOW}/runs?head_sha={sha}&per_page=50",
        )
    )["workflow_runs"]
    verdict = ci_verdict(runs, sha)
    if verdict:
        raise Refused(f"{verdict}. Release once it has passed.")


def publish_release(slug: str, version: str, changelog: str) -> str:
    body = release_notes.notes(changelog, version, f"https://github.com/{slug}")
    payload = {
        "tag_name": f"v{version}",
        "name": version,
        "body": body,
        "make_latest": "true",
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
    try:
        created = run(
            "gh", "api", "-X", "POST", f"repos/{slug}/releases", "--input", handle.name
        )
    finally:
        os.unlink(handle.name)
    return json.loads(created)["html_url"]


def release_exists(slug: str, tag: str) -> bool:
    found = subprocess.run(
        ["gh", "api", f"repos/{slug}/releases/tags/{tag}"],
        cwd=ROOT,
        capture_output=True,
    )
    return found.returncode == 0


def read_files() -> dict[str, str]:
    # newline="" keeps every file's line endings as they are (LF; tests/test_line_endings.py)
    return {
        path: (ROOT / path).open(encoding="utf-8", newline="").read() for path in FILES
    }


def write_files(files: dict[str, str]) -> None:
    for path, text in files.items():
        with (ROOT / path).open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)


def checks_pass() -> bool:
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *CHECKS],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(result.stdout[-3000:] or result.stderr[-3000:])
    return result.returncode == 0


# --------------------------------------------------------------------------- the two steps
def release_here(version: str, dry_run: bool) -> None:
    version_tuple(version)
    tag = f"v{version}"
    run("git", "fetch", "--quiet", "--tags", "origin", BRANCH)
    slug = slug_of(run("git", "remote", "get-url", "origin"))
    if run("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        if release_exists(slug, tag):
            raise Refused(
                f"{tag} is already released on {slug}: a number is never reused"
            )
        # The last run pushed the tag and stopped before publishing its release: finish that.
        changelog = run("git", "show", f"{tag}:{CHANGELOG}")
        if dry_run:
            print(f"Would publish the release for the already pushed {tag} on {slug}")
            return
        print(
            f"Released {version} on {slug}: {publish_release(slug, version, changelog)}"
        )
        return
    if run("git", "rev-parse", "--abbrev-ref", "HEAD") != BRANCH:
        raise Refused(f"check out {BRANCH} first")
    if run("git", "status", "--porcelain"):
        raise Refused("the working tree has changes: commit or stash them first")
    sha = run("git", "rev-parse", "HEAD")
    if sha != run("git", "rev-parse", f"origin/{BRANCH}"):
        raise Refused(f"{BRANCH} is not origin/{BRANCH}: pull (or push) first")
    files = read_files()
    now = current_version(files)
    if version_tuple(version) <= version_tuple(now):
        raise Refused(f"{version} is not newer than {now}")
    if run("git", "tag", "--list", tag):
        raise Refused(
            f"{tag} exists here but not on origin: delete it (git tag -d {tag})"
        )
    try:
        require_ci(slug, sha)
    except Refused as why:
        if not dry_run:
            raise
        print(f"(a real run would stop here: {why})")

    day = date.today().isoformat()
    after = prepare(files, version, day)
    write_files(after)
    try:
        if not checks_pass():
            raise Refused("the version and notes checks failed on the release commit")
        if dry_run:
            print(run("git", "diff", "--stat"))
            print(f"\nRelease notes for v{version} on {slug}:\n")
            print(
                release_notes.notes(
                    after[CHANGELOG], version, f"https://github.com/{slug}"
                )
            )
            return
        run("git", "add", *FILES)
        run("git", "commit", "--quiet", "-m", f"release: {version}")
    finally:
        if dry_run or run("git", "rev-parse", "HEAD") == sha:  # nothing committed
            write_files(files)
            run("git", "reset", "--quiet", "--", *FILES)
    run("git", "tag", "-a", tag, "-m", version)
    try:
        run(
            "git",
            "push",
            "--atomic",
            "origin",
            f"HEAD:refs/heads/{BRANCH}",
            f"refs/tags/{tag}",
        )
    except Refused:  # nothing reached origin: take back the local commit and tag too
        run("git", "tag", "-d", tag)
        run("git", "reset", "--quiet", "--hard", sha)
        raise
    url = publish_release(slug, version, after[CHANGELOG])
    print(f"Released {version} on {slug}: {url}")
    print(
        "Boxes that track this repository are offered it now. When it has run well there:\n"
        f"  python scripts/release.py {version} --public"
    )


def release_public(version: str, dry_run: bool) -> None:
    version_tuple(version)
    run("git", "fetch", "--quiet", "--tags", "origin")
    origin = run("git", "remote", "get-url", "origin")
    slug = slug_of(origin)
    tag = f"v{version}"
    if not run("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        raise Refused(
            f"{tag} is not released on {slug} yet: run without --public first"
        )
    sha = run("git", "rev-parse", f"{tag}^{{commit}}")
    require_ci(slug, sha)
    if subprocess.run(["gh", "api", f"repos/{PUBLIC}"], capture_output=True).returncode:
        raise Refused(f"{PUBLIC} does not exist (or this login cannot see it)")
    if release_exists(PUBLIC, tag):
        raise Refused(f"{tag} is already released on {PUBLIC}")
    changelog = run("git", "show", f"{tag}:{CHANGELOG}")
    if dry_run:
        print(f"Would push {sha[:12]} ({tag}) to {PUBLIC} {BRANCH}, and publish:\n")
        print(release_notes.notes(changelog, version, f"https://github.com/{PUBLIC}"))
        return
    # No "+": git refuses anything but a fast-forward of the public main. Pushing again after a
    # run that stopped before publishing changes nothing, and the release is then published.
    run(
        "git",
        "push",
        "--atomic",
        public_url(origin),
        f"{sha}:refs/heads/{BRANCH}",
        f"refs/tags/{tag}",
    )
    url = publish_release(PUBLIC, version, changelog)
    print(f"Released {version} on {PUBLIC}: {url}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("version", help="the new version, e.g. 2.25.0")
    parser.add_argument(
        "--public", action="store_true", help=f"release a tagged version on {PUBLIC}"
    )
    parser.add_argument("--dry-run", action="store_true", help="change nothing")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # the notes may carry emoji
    step = release_public if args.public else release_here
    step(args.version.removeprefix("v"), args.dry_run)


if __name__ == "__main__":
    main()
