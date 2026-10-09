"""Serve the bundled operator dashboard without copying files or sidebar YAML."""

import asyncio
from pathlib import Path

from .const import DOMAIN, PRODUCT_NAME, SOFTWARE_VERSION

PANEL = "crop-steering"
URL = "/crop_steering"
# The panel's element (www/panel.js): it holds the dashboard in a frame the size of the panel.
ELEMENT = "crop-steering-panel"


async def async_setup_panel(hass):
    from homeassistant.components import frontend

    state = hass.data.setdefault(DOMAIN, {}).setdefault("_setup", {})
    # Config entries set up concurrently. Hold the shared lock across static-path
    # registration so another room cannot pass the panel guard during that await.
    lock = state.setdefault("panel_lock", asyncio.Lock())
    async with lock:
        if state.get("panel_registered") or frontend.async_panel_exists(hass, PANEL):
            return
        if not state.get("static_registered"):
            from homeassistant.components.http import StaticPathConfig

            directory = str(Path(__file__).parent / "www")
            await hass.http.async_register_static_paths(
                [StaticPathConfig(URL, directory, False)]
            )
            state["static_registered"] = True
        # Another integration can claim this route while HTTP registration yields.
        # Leave its panel unowned so our unload never removes it.
        if frontend.async_panel_exists(hass, PANEL):
            return
        # A custom panel, not the built-in iframe one: Home Assistant draws its own title bar
        # above an iframe panel, and none above a custom panel. `_panel_custom` is what
        # panel_custom.async_register_panel registers (a module, not embedded in a frame of its
        # own), without depending on panel_custom.
        frontend.async_register_built_in_panel(
            hass,
            "custom",
            sidebar_title=PRODUCT_NAME,
            sidebar_icon="mdi:water-circle",
            frontend_url_path=PANEL,
            # The page is served without cache headers, so a browser can keep showing the
            # previous release's copy for hours after an update. A new version is a new URL.
            config={
                "url": f"{URL}/dashboard.html?v={SOFTWARE_VERSION}",
                "_panel_custom": {
                    "name": ELEMENT,
                    "module_url": f"{URL}/panel.js?v={SOFTWARE_VERSION}",
                    "embed_iframe": False,
                    "trust_external": False,
                },
            },
            require_admin=False,
        )
        state["panel_registered"] = True


def async_unload_panel(hass):
    """Remove only the panel we registered, after the final entry unloads."""
    from homeassistant.components import frontend

    if hass.data.get(DOMAIN, {}).get("_setup", {}).pop("panel_registered", False):
        frontend.async_remove_panel(hass, PANEL)
