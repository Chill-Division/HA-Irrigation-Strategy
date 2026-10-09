"""The MIT licence travels with every part a box installs, and the README credits where PHASE
Control began.

HACS installs only custom_components/crop_steering, the app's image is built from addons/f2_control
alone, and the engine is its own package: each carries its own copy of LICENSE, which the licence asks
for in every copy. The dashboard is built from open-source packages whose licences ask the same, so
the build ships THIRD_PARTY_LICENSES.txt beside it (frontend/vite.config.ts).
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LICENSE = (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_the_licence_names_jaketherabbit_first():
    assert LICENSE.startswith("MIT License\n")
    holders = re.findall(r"^Copyright \(c\) \d{4} (.+)$", LICENSE, re.M)
    assert holders == ["JakeTheRabbit", "Chill Division"]


@pytest.mark.parametrize(
    "part",
    ["custom_components/crop_steering", "addons/f2_control", "crop-steering-engine"],
)
def test_every_part_installed_on_its_own_carries_the_licence(part):
    assert (ROOT / part / "LICENSE").read_text(encoding="utf-8") == LICENSE


def test_the_apps_image_holds_the_licence():
    dockerfile = (ROOT / "addons" / "f2_control" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^COPY LICENSE /app/LICENSE$", dockerfile, re.M)


def test_the_readme_credits_the_original():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/JakeTheRabbit/HA-Irrigation-Strategy" in readme


def test_the_dashboard_ships_its_libraries_licences():
    folders = ["addons/f2_control/www/public", "custom_components/crop_steering/www"]
    texts = {
        folder: (ROOT / folder / "THIRD_PARTY_LICENSES.txt").read_text(encoding="utf-8")
        for folder in folders
    }
    assert (
        len(set(texts.values())) == 1
    ), "both copies of the dashboard ship the same list"
    text = texts[folders[0]]
    titles = re.findall(r"^=+\n(\S+) \S+ \((.+)\)\n=+\n", text, re.M)
    names = {name for name, _ in titles}
    for name in (
        "react",
        "react-dom",
        "recharts",
        "lucide-react",
        "class-variance-authority",
        "tailwindcss",
        "@fontsource-variable/roboto",
    ):
        assert name in names, f"{name} is bundled but not listed"
    # Every entry carries its licence's text, or says where it is.
    for entry in re.split(r"^=+\n\S+ \S+ \(.+\)\n=+\n", text, flags=re.M)[1:]:
        assert len(entry.strip()) > 20
