"""The integration's brand images as Home Assistant serves them (2026.3+, from its own `brand/`
folder), which the integrations page, the "add integration" dialog and HACS show.

There is no dark_ image: on a dark theme Home Assistant falls back to the light one, a blue tile and
wordmark that read on a dark card too. That fallback is Home Assistant's, so it is proven through
its real web server on each Home Assistant this tier runs; were it missing, a dark theme would show
"icon not available"."""

from pathlib import Path

import pytest
from homeassistant.setup import async_setup_component

pytestmark = pytest.mark.web_server
BRAND = Path(__file__).resolve().parents[1] / "custom_components" / "crop_steering" / "brand"


@pytest.mark.parametrize(
    ("asked", "served"),
    [
        ("icon.png", "icon.png"),
        ("icon@2x.png", "icon@2x.png"),
        ("logo.png", "logo.png"),
        ("logo@2x.png", "logo@2x.png"),
        ("dark_icon.png", "icon.png"),
        ("dark_icon@2x.png", "icon@2x.png"),
        ("dark_logo.png", "logo.png"),
        ("dark_logo@2x.png", "logo@2x.png"),
    ],
)
async def test_every_image_a_theme_asks_for_is_ours(hass, hass_client, asked, served):
    assert await async_setup_component(hass, "brands", {})
    client = await hass_client()
    response = await client.get(f"/api/brands/integration/crop_steering/{asked}")
    assert response.status == 200
    assert await response.read() == (BRAND / served).read_bytes()
