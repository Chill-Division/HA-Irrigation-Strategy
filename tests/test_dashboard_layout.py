"""Contracts for all shipped dashboard entry points and install metadata."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "addons/f2_control/www/public/dashboard.html"


def test_dashboard_is_accessible_self_contained_and_bundles_font_license():
    source = DASHBOARD.read_text(encoding="utf-8")
    assert '<html lang="en"' in source
    assert 'id="root"' in source
    assert "Operator dashboard" in source
    assert not re.search(r"<script[^>]+src=", source)
    assert not re.search(r'<link[^>]+rel="stylesheet"', source)
    assert not re.search(r"url\([\"\x27]?https?://", source)
    assert "<noscript>" in source
    assert "SIL OPEN FONT LICENSE" in source


def test_all_install_paths_ship_identical_dashboard():
    integration = ROOT / "custom_components/crop_steering/www/dashboard.html"
    assert DASHBOARD.read_bytes() == integration.read_bytes()


def test_each_folder_holds_the_dashboard_and_the_page_that_opens_it_only():
    """The app's sidebar entry opens index.html (ingress serves it for "/"); the integration's panel
    opens dashboard.html itself. The pages that redirected the original author's old bookmarks are
    gone, and so is the demo site's copy; the build removes any page it no longer writes, so none
    can linger committed."""
    assert not (ROOT / "www").exists(), "the demo site's copy is gone"
    expected = {
        "addons/f2_control/www/public": {"dashboard.html", "index.html"},
        "custom_components/crop_steering/www": {"dashboard.html"},
    }
    for relative, names in expected.items():
        found = {page.name for page in (ROOT / relative).glob("*.html")}
        assert found == names, relative
    for relative in ("addons/f2_control/www/public/index.html",):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "./dashboard.html" in source
        assert "location.search" in source and "location.hash" in source


def test_repository_metadata_does_not_expose_legacy_facility_config_as_an_app():
    assert (ROOT / "repository.yaml").exists()
    assert not (ROOT / "config.yaml").exists()
    assert not list((ROOT / "archive").rglob("config.yaml"))
    assert (ROOT / "addons/f2_control/config.yaml").exists()
