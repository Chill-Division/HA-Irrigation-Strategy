"""One command releases the repository (scripts/release.py): it dates the Unreleased notes, sets
every version and checks the result before anything is committed, pushed or published.

Only the pure part is tested here: what the release commit will contain, and when to refuse. The
version files are the repository's own, so a change to their format that the release would miss
fails here first.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import release  # noqa: E402
import release_notes  # noqa: E402
from custom_components.crop_steering.whats_new import parse  # noqa: E402

REPO = "https://github.com/owner/repo"
DAY = "2026-10-01"
CHANGELOG = """# Changelog

Intro.

## [Unreleased]

Two changes.

- **A thing.** It is better.

### 🔧 Technical notes

- `thing.py`.

## [2.24.0] - 2026-09-26

Pair: **controller 2.24.0**.

- Older.
"""
ADDON = """# Unreleased

No change to the state file.

- **A thing.** `thing.py`.

# 2.24.0

Pair with integration 2.24.0.
"""
WHATS_NEW = """# What's new

The rules.

## Unreleased

- Bug fixes and improvements.
- Each zone does a new thing, which a grower would
  notice at once.

## 2.24.0 - 2026-09-26

- Older.
"""


def _files(**notes):
    files = release.read_files()
    files.update(
        {
            release.CHANGELOG: CHANGELOG,
            release.ADDON_CHANGELOG: ADDON,
            release.WHATS_NEW: WHATS_NEW,
        }
    )
    files.update(notes)
    return files


def test_every_version_is_set_and_nothing_else_moves():
    before = _files()
    old = release.current_version(before)
    after = release.prepare(before, "9.9.9", DAY)
    assert json.loads(after[release.MANIFEST])["version"] == "9.9.9"
    assert 'SOFTWARE_VERSION = "9.9.9"' in after[release.CONST]
    assert re.search(r'^version: "9\.9\.9"$', after[release.ADDON_CONFIG], re.M)
    assert "badge/Release-9.9.9-" in after[release.README]
    for path in (release.MANIFEST, release.CONST, release.ADDON_CONFIG, release.README):
        assert after[path].replace("9.9.9", old) == before[path], path


def test_a_release_changes_no_line_endings():
    """A rewrite that switched a file's line endings would change every line of it."""
    before = _files()
    after = release.prepare(before, "9.9.9", DAY)
    for path in before:
        assert after[path].count("\r\n") == before[path].count("\r\n"), path


def test_the_unreleased_notes_become_the_release():
    after = release.prepare(_files(), "9.9.9", DAY)
    changelog = after[release.CHANGELOG]
    assert "## [Unreleased]" not in changelog
    assert (
        f"## [9.9.9] - {DAY}\n\nIntegration and controller **9.9.9**.\n\nTwo changes."
        in changelog
    )
    assert changelog.index("## [9.9.9]") < changelog.index("## [2.24.0]")
    notes = release_notes.notes(changelog, "9.9.9", REPO)
    assert (
        notes.startswith("Integration and controller **9.9.9**.")
        and "**A thing.**" in notes
    )
    addon = after[release.ADDON_CHANGELOG]
    assert addon.startswith(
        "# 9.9.9\n\nPair with integration 9.9.9.\n\nNo change to the state file."
    )
    assert "# 2.24.0" in addon


def test_whats_new_is_dated_with_the_small_things_last():
    text = release.prepare(_files(), "9.9.9", DAY)[release.WHATS_NEW]
    newest = parse(text)[0]
    assert (newest["version"], newest["date"]) == ("9.9.9", DAY)
    assert newest["items"] == [
        "Each zone does a new thing, which a grower would notice at once.",
        "Bug fixes and improvements.",
    ]
    assert "## Unreleased" not in text and "The rules." in text


def test_a_release_with_nothing_written_for_growers_or_the_controller():
    files = _files()
    files[release.WHATS_NEW] = WHATS_NEW.replace(
        WHATS_NEW[WHATS_NEW.index("## Unreleased") : WHATS_NEW.index("## 2.24.0")], ""
    )
    files[release.ADDON_CHANGELOG] = ADDON[ADDON.index("# 2.24.0") :]
    after = release.prepare(files, "9.9.9", DAY)
    assert parse(after[release.WHATS_NEW])[0]["items"] == [
        "Bug fixes and improvements."
    ]
    assert after[release.ADDON_CHANGELOG].startswith(
        "# 9.9.9\n\nPair with integration 9.9.9.\n\n# 2.24.0"
    )


def test_it_refuses_a_release_nobody_has_written_up():
    with pytest.raises(release.Refused, match="no '## \\[Unreleased\\]' section"):
        release.prepare(
            _files(**{release.CHANGELOG: CHANGELOG.replace("## [Unreleased]", "")}),
            "9.9.9",
            DAY,
        )
    # Nothing before the technical notes says what changed, for anyone.
    unsaid = CHANGELOG.replace("- **A thing.** It is better.\n\n", "")
    with pytest.raises(release.Refused, match="what this release changes"):
        release.prepare(_files(**{release.CHANGELOG: unsaid}), "9.9.9", DAY)
    # Written under the heading the changelog no longer has: the same.
    headed = CHANGELOG.replace(
        "- **A thing.** It is better.",
        "### 🌱 In plain English\n\n- **A thing.** It is better.",
    )
    with pytest.raises(release.Refused, match="what this release changes"):
        release.prepare(_files(**{release.CHANGELOG: headed}), "9.9.9", DAY)
    stray = WHATS_NEW.replace("## Unreleased\n", "## Unreleased\n\nA paragraph.\n")
    with pytest.raises(release.Refused, match="only '- ' lines"):
        release.prepare(_files(**{release.WHATS_NEW: stray}), "9.9.9", DAY)


@pytest.mark.parametrize("version", ["2.25", "v2.25.0", "2.25.0-rc1", ""])
def test_a_version_is_three_numbers(version):
    with pytest.raises(release.Refused, match="not a version"):
        release.version_tuple(version)


def _run(number, status="completed", conclusion="success", sha="abc", attempt=1):
    return {
        "head_sha": sha,
        "run_number": number,
        "run_attempt": attempt,
        "status": status,
        "conclusion": conclusion,
        "html_url": f"https://github.com/owner/repo/actions/runs/{number}",
    }


def test_it_releases_only_a_commit_validate_has_passed():
    assert release.ci_verdict([_run(7)], "abc") is None
    assert "has not run" in release.ci_verdict([], "abc")
    assert "has not run" in release.ci_verdict([_run(7, sha="other")], "abc")
    assert "still running" in release.ci_verdict([_run(7, status="in_progress")], "abc")
    assert "failure" in release.ci_verdict([_run(7, conclusion="failure")], "abc")
    # the newest run decides: a rerun that passed, or a later push's run that failed
    assert (
        release.ci_verdict([_run(7, conclusion="failure"), _run(7, attempt=2)], "abc")
        is None
    )
    assert "failure" in release.ci_verdict(
        [_run(7), _run(8, conclusion="failure")], "abc"
    )


def test_the_public_repository_is_reached_the_way_origin_is():
    assert (
        release.slug_of("git@github.com:Me/HA-Irrigation-Strategy.git")
        == "Me/HA-Irrigation-Strategy"
    )
    assert (
        release.slug_of("https://github.com/Me/HA-Irrigation-Strategy")
        == "Me/HA-Irrigation-Strategy"
    )
    assert (
        release.public_url("git@github.com:Me/x.git")
        == f"git@github.com:{release.PUBLIC}.git"
    )
    assert (
        release.public_url("https://github.com/Me/x.git")
        == f"https://github.com/{release.PUBLIC}.git"
    )
    with pytest.raises(release.Refused):
        release.slug_of("https://gitlab.com/Me/x.git")
