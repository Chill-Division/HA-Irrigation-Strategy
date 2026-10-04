"""A release's GitHub notes come from its changelog entry (scripts/release_notes.py).

HACS shows a release's notes in its update dialog. They were one line ("Candidate. Pair:
controller 0.16.5 ..."); what each entry says first, for exactly those readers, stayed in
CHANGELOG.md.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import release_notes  # noqa: E402

REPO = "https://github.com/owner/repo"
CHANGELOG = """# Changelog

## [Unreleased]

- Not released yet.

## [2.21.0] - 2026-10-01

Pair: one number. Not run on
hardware.

- **Error codes.** See [Error codes](docs/ERROR_CODES.md) and [HACS](https://hacs.xyz),
  wrapped onto a second line.
- A second bullet.

### 🔧 Technical notes

- `controller.py` internals.

## [2.20.0] - 2026-09-01

No plain section here.
"""


def test_the_notes_are_the_entry_up_to_its_technical_notes():
    text = release_notes.notes(CHANGELOG, "2.21.0", REPO)
    assert text.startswith("Pair: one number. Not run on hardware.")
    assert "**Error codes.**" in text and "In plain English" not in text
    assert "Technical notes" in text and "controller.py internals" not in text
    assert "Not released yet" not in text
    assert text.rstrip().endswith(f"({REPO}/blob/v2.21.0/CHANGELOG.md)")


def test_relative_links_point_at_the_files_at_that_tag():
    text = release_notes.notes(CHANGELOG, "2.21.0", REPO)
    assert f"[Error codes]({REPO}/blob/v2.21.0/docs/ERROR_CODES.md)" in text
    assert "[HACS](https://hacs.xyz)" in text  # absolute links are left alone


def test_a_missing_entry_or_section_is_refused():
    with pytest.raises(SystemExit, match="no entry for 9.9.9"):
        release_notes.notes(CHANGELOG, "9.9.9", REPO)
    with pytest.raises(SystemExit, match="says nothing before its technical notes"):
        release_notes.notes(CHANGELOG, "2.20.0", REPO)


def test_the_newest_release_in_this_repository_has_notes():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    newest = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M).group(1)
    text = release_notes.notes(changelog, newest, REPO)
    assert "\n- " in text and len(text) > 200


def test_wrapped_lines_are_joined_into_their_paragraph_or_bullet():
    text = release_notes.notes(CHANGELOG, "2.21.0", REPO)
    assert "Pair: one number. Not run on hardware." in text
    assert "(https://hacs.xyz), wrapped onto a second line.\n- A second bullet." in text


def test_the_script_writes_utf8_where_the_console_cannot():
    """`--notes-file <(python scripts/release_notes.py ...)` on Windows: that pipe is cp1252,
    which had no 🌱 for the heading the notes once carried, so the script died before writing a
    line and the release got empty notes. An arrow in a release's own words does the same.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    def cp1252(text):
        try:
            return text.encode("cp1252") is not None
        except UnicodeEncodeError:
            return False

    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    version = next(
        v for v in released if not cp1252(release_notes.notes(changelog, v, REPO))
    )
    run = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_notes.py"), version],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp1252"},
    )
    assert run.returncode == 0, run.stderr.decode(errors="replace")
    assert not cp1252(run.stdout.decode("utf-8"))
