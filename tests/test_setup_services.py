"""Setup response services require authenticated administrator context."""

import asyncio
import sys
from types import SimpleNamespace

import pytest

from .test_setup import rig, payload, api


def test_response_services_require_admin_and_return_actual_saved_revision(
    monkeypatch, caplog
):
    from . import ha_stubs

    ha_stubs.install()
    core = sys.modules["homeassistant.core"]
    monkeypatch.setattr(
        core,
        "SupportsResponse",
        SimpleNamespace(ONLY="only", OPTIONAL="optional"),
        raising=False,
    )
    monkeypatch.setattr(
        sys.modules["voluptuous"], "ALLOW_EXTRA", object(), raising=False
    )
    hass, _, _ = rig()
    handlers = {}
    hass.services = SimpleNamespace(
        async_register=lambda domain, name, fn, **kwargs: handlers.setdefault(name, fn)
    )
    admin = {"is_admin": False}

    async def user(_id):
        return SimpleNamespace(**admin)

    hass.auth = SimpleNamespace(async_get_user=user)
    asyncio.run(api.async_setup_setup_services(hass))
    asyncio.run(api.async_setup_setup_services(hass))
    assert set(handlers) == {"setup_read", "setup_save", "setup_create", "setup_remove"}
    call = SimpleNamespace(
        context=SimpleNamespace(user_id="person"), return_response=True, data=payload()
    )
    with pytest.raises(Exception, match="administrator"):
        asyncio.run(handlers["setup_save"](call))
    assert not hass.config_entries.updates
    admin["is_admin"] = True
    fired = []
    hass.bus = SimpleNamespace(
        async_fire=lambda event, data, context=None: fired.append(
            (event, data, context)
        )
    )
    result = asyncio.run(handlers["setup_save"](call))
    assert result["revision"] == 1 and result["active_zone_ids"] == [2]
    # Recorded in the logbook, as the person who saved it.
    ((event, data, context),) = fired
    assert (event, data["name"], context) == (
        "logbook_entry",
        "Veg renamed",
        call.context,
    )
    assert data["message"].startswith("setup saved (revision 1): renamed from “Veg”; ")
    result = asyncio.run(handlers["setup_read"](call))
    assert result["api_version"] == 1 and result["rooms"][0]["revision"] == 1

    # A save stands even when recording it fails; the log says it was not recorded.
    def refuse(*_args, **_kwargs):
        raise RuntimeError("no logbook")

    hass.bus = SimpleNamespace(async_fire=refuse)
    call.data = {**payload(), "expected_revision": 1, "room_name": "Veg again"}
    result = asyncio.run(handlers["setup_save"](call))
    assert result["revision"] == 2 and result["room_name"] == "Veg again"
    assert "could not be recorded" in caplog.text
