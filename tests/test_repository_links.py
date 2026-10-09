"""Every link to this project names its repository as it is now called: PHASE-Control.

Both repositories were HA-Irrigation-Strategy until October 2026, then for a day PHASE-Steering.
GitHub sends the old addresses on to the new ones, so an old link still works, but only for as
long as no repository takes an old name. So what ships, the README and the docs link to the public repository by the name
`scripts/release.py` publishes to. JakeTheRabbit's repository, where it began, keeps its own name,
and the changelogs keep the links they had at the time.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = "Chill-Division/PHASE-Control"
# A link to one of our repositories under an old name: on GitHub, in a raw picture, or in a My
# Home Assistant link's parameters.
OLD = r"(?:HA-Irrigation-Strategy|PHASE-Steering)"
OLD_LINK = re.compile(
    rf"(?:github\.com|githubusercontent\.com)/(?:Chill-Division|ChillingSilence)/{OLD}"
    rf"|repository={OLD}"
    rf"|(?:Chill-Division|ChillingSilence)%2F{OLD}",
    re.IGNORECASE,
)
HISTORY = {"CHANGELOG.md", "addons/f2_control/CHANGELOG.md"}


def _constant(path, name):
    """A module's constant, as written in it (no import: the integration needs Home Assistant)."""
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    (value,) = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(getattr(target, "id", None) == name for target in node.targets)
    ]
    return ast.literal_eval(value)


def test_releases_go_to_the_public_repository_by_its_name():
    assert _constant("scripts/release.py", "PUBLIC") == PUBLIC


def test_what_ships_links_to_the_public_repository():
    home = f"https://github.com/{PUBLIC}"
    integration = ROOT / "custom_components" / "crop_steering"
    manifest = json.loads((integration / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["documentation"] == home
    assert manifest["issue_tracker"] == f"{home}/issues"
    repairs = _constant("custom_components/crop_steering/const.py", "REPAIRS_DOCS_URL")
    assert repairs == f"{home}/blob/main/docs/ERROR_CODES.md"
    whats_new = (ROOT / "frontend" / "src" / "lib" / "whats-new.ts").read_text(
        encoding="utf-8"
    )
    assert f'RELEASES_URL = "{home}/releases";' in whats_new
    for app_file in ("addons/f2_control/config.yaml", "repository.yaml"):
        assert f"url: {home}\n" in (ROOT / app_file).read_text(
            encoding="utf-8"
        ), app_file


def test_nothing_links_to_a_repository_by_its_old_name():
    files = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    me = Path(__file__).resolve().relative_to(ROOT).as_posix()
    stale = []
    for name in files:
        if name in HISTORY or name == me:
            continue
        try:
            text = (ROOT / name).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue  # a picture, a font, or a file deleted but not yet committed
        stale += [
            f"{name}:{text.count(chr(10), 0, match.start()) + 1}"
            for match in OLD_LINK.finditer(text)
        ]
    assert stale == []
