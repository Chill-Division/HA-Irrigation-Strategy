"""Nutrient batches per room, stored and served; see feed.py for the rules.

Response-only services addressed by canonical room id, like the stock tank services. Reading is
open to any signed-in user; changing the settings or a feed recipe, or asking for a batch, needs an
administrator. What the controller app runs is published as sensor.crop_steering_<prefix>feed_plan,
rewritten whenever the settings change; the feed stage in use is also a select, so it can be changed
from Home Assistant. A batch is asked for by pressing the room's Mix a Batch Now button (button.py),
which the controller reads; feed_mix presses it for the dashboard.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
import logging

from . import feed
from .admin import async_require_admin
from .const import DOMAIN
from .room import room_prefix

_LOGGER = logging.getLogger(__name__)

SERVICES = ("feed_get", "feed_save", "feed_mix")
SIGNAL = f"{DOMAIN}_feed_changed"


def mapped_dosers(hardware: dict) -> dict[int, str]:
    """The room's doser switches from Rooms & hardware, by doser number."""
    return {
        number: hardware[key]
        for number, key in enumerate(feed.DOSER_KEYS, start=1)
        if isinstance(hardware.get(key), str) and hardware.get(key)
    }


class FeedStore:
    def __init__(self, hass, entry, store=None):
        self.hass, self.entry = hass, entry
        self.prefix = room_prefix(entry)
        self.room_id = "room:" + self.prefix
        self._store = store
        self._lock = asyncio.Lock()
        self.data = feed.empty()
        self.error = None

    @property
    def mapped(self) -> dict[int, str]:
        config = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        hardware = config.get("hardware", {}) if isinstance(config, dict) else {}
        return mapped_dosers(hardware if isinstance(hardware, dict) else {})

    async def async_init(self):
        try:
            if self._store is None:
                from homeassistant.helpers.storage import Store

                self._store = Store(
                    self.hass, 1, f"{DOMAIN}.feed.{self.entry.entry_id}"
                )
            value = await self._store.async_load()
            if value is not None:
                if (
                    not isinstance(value, dict)
                    or type(value.get("revision")) is not int
                ):
                    raise ValueError("Invalid stored revision")
                self.data = feed.clean(value, {"revision": value["revision"]})
        except Exception as error:
            self.error = (
                "Stored feed settings could not be loaded; they have not been overwritten: "
                f"{error}"
            )

    def plan(self) -> dict:
        return feed.plan(self.data, self.mapped)

    def response(self):
        return {
            "schema_version": 1,
            "room_id": self.room_id,
            **deepcopy(self.data),
            "mapped": {str(number): entity for number, entity in self.mapped.items()},
            "plan": self.plan(),
            "max_dosers": feed.MAX_DOSERS,
            "max_recipes": feed.MAX_RECIPES,
            "error": self.error,
        }

    async def save(self, data):
        async with self._lock:
            if self.error:
                raise ValueError(self.error)
            if data.get("expected_revision") != self.data["revision"]:
                raise ValueError(
                    "Feed settings changed elsewhere. Reload before saving."
                )
            await self._commit(feed.clean(data.get("document"), self.data))
            return self.response()

    async def mix(self, context=None):
        """Ask the controller app for a batch now: press the room's Mix a Batch Now button, which it
        reads by entity id. Refused, with the reason, while the plan could not run."""
        entity_id = f"button.{DOMAIN}_{self.prefix}mix_batch"
        state = self.hass.states.get(entity_id)
        if state is None or state.state == "unavailable":
            raise ValueError(
                f"The room's Mix a Batch Now button ({entity_id}) is not available"
            )
        problem = self.plan()["problem"]
        if problem:
            raise ValueError(problem)
        await self.hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True, context=context
        )
        pressed = self.hass.states.get(entity_id)
        return {**self.response(), "requested": pressed.state if pressed else None}

    async def set_stage(self, name: str):
        """The feed stage chosen by its recipe's name (the select in Home Assistant)."""
        async with self._lock:
            if self.error:
                raise ValueError(self.error)
            match = next(
                (item for item in self.data["recipes"] if item["name"] == name), None
            )
            if match is None:
                raise ValueError(f"No feed recipe is called {name}")
            if match["id"] != self.data["stage"]:
                draft = deepcopy(self.data)
                draft["stage"] = match["id"]
                await self._commit(draft)

    async def _commit(self, draft):
        """Store the next revision; only a saved change becomes the room's settings."""
        draft["revision"] = self.data["revision"] + 1
        await self._store.async_save(draft)
        self.data = draft
        from homeassistant.helpers.dispatcher import async_dispatcher_send

        async_dispatcher_send(self.hass, f"{SIGNAL}_{self.entry.entry_id}")


def resolve_feed(hass, room_id):
    if not isinstance(room_id, str) or not room_id.startswith("room:"):
        raise ValueError("A canonical room_id is required")
    matches = [
        manager
        for manager in hass.data.get(DOMAIN, {}).get("_feed", {}).values()
        if manager.room_id == room_id
    ]
    if len(matches) != 1:
        raise ValueError("Feed room is unknown or ambiguous")
    return matches[0]


def get_feed(hass, entry):
    return hass.data.get(DOMAIN, {}).get("_feed", {}).get(entry.entry_id)


async def async_setup_feed(hass, entry):
    import voluptuous as vol
    from homeassistant.core import SupportsResponse
    from homeassistant.exceptions import HomeAssistantError

    manager = FeedStore(hass, entry)
    await manager.async_init()
    hass.data.setdefault(DOMAIN, {}).setdefault("_feed", {})[entry.entry_id] = manager

    async def handle(call):
        if call.service != "feed_get":
            await async_require_admin(hass, call, f"{DOMAIN}.{call.service}")
        try:
            target = resolve_feed(hass, call.data["room_id"])
            if call.service == "feed_get":
                return target.response()
            if call.service == "feed_mix":
                return await target.mix(call.context)
            return await target.save(call.data)
        except (ValueError, KeyError, OSError) as error:
            raise HomeAssistantError(str(error)) from error

    for service in SERVICES:
        schema = {vol.Required("room_id"): str}
        if service == "feed_save":
            schema[vol.Required("expected_revision")] = vol.All(int, vol.Range(min=0))
            schema[vol.Required("document")] = dict
        hass.services.async_register(
            DOMAIN,
            service,
            handle,
            schema=vol.Schema(schema),
            supports_response=SupportsResponse.ONLY,
        )


async def async_unload_feed(hass, entry):
    managers = hass.data.get(DOMAIN, {}).get("_feed", {})
    managers.pop(entry.entry_id, None)
    if not managers:
        for service in SERVICES:
            hass.services.async_remove(DOMAIN, service)
