"""Nutrient batches per room, stored and served; see feed.py for the rules.

Response-only services addressed by canonical room id, like the stock tank services. Reading is
open to any signed-in user; changing the settings or a feed recipe, or asking for a batch, needs an
administrator. What the controller app runs is published as sensor.crop_steering_<prefix>feed_plan,
rewritten whenever the settings change and at each midnight (Home Assistant's), when the feed
schedule's week, or a stage held by hand, may move the stage in use; that stage is also a select, so it
can be picked from Home Assistant. A batch is asked for by pressing the room's Mix a Batch Now button (button.py),
which the controller reads; feed_mix presses it for the dashboard. With `force`, the dashboard's test
refill says the person checked that the fill fits: for FORCE_S the plan sensor carries
`mix_force_until`, and the controller does not refuse that press for a fill that might not fit.
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
FORCE_S = 120  # how long a forced refill's word stands: the controller sees its press well within


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
        self.force_until = None  # until when (UTC) a forced refill's word stands

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

    @staticmethod
    def today():
        """Today in Home Assistant's time zone: the feed schedule's weeks start at its midnight."""
        from homeassistant.util import dt as dt_util

        return dt_util.now().date()

    def plan(self) -> dict:
        return feed.plan(self.data, self.mapped, self.today())

    def in_use(self):
        """The recipe in use today, by id (feed.in_use)."""
        return feed.in_use(self.data, self.today())

    def start(self):
        """At each midnight, tell the entities: the schedule's week, or the end of a stage held by
        hand, may have moved the stage in use. Returns the unsubscribe."""
        from homeassistant.core import callback
        from homeassistant.helpers.dispatcher import async_dispatcher_send
        from homeassistant.helpers.event import async_track_time_change

        @callback
        def new_day(_now):
            async_dispatcher_send(self.hass, f"{SIGNAL}_{self.entry.entry_id}")

        return async_track_time_change(self.hass, new_day, hour=0, minute=0, second=1)

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

    def forced(self):
        """While a forced refill's word stands, until when (ISO, UTC); else None."""
        from homeassistant.util import dt as dt_util

        if self.force_until is None or self.force_until <= dt_util.utcnow():
            return None
        return self.force_until.isoformat()

    async def mix(self, context=None, force=False):
        """Ask the controller app for a batch now: press the room's Mix a Batch Now button, which it
        reads by entity id. Refused, with the reason, while the plan could not run. With `force` the
        person checked that the fill fits: the plan sensor says so before the button is pressed, so
        the controller never sees the press without it."""
        entity_id = f"button.{DOMAIN}_{self.prefix}mix_batch"
        state = self.hass.states.get(entity_id)
        if state is None or state.state == "unavailable":
            raise ValueError(
                f"The room's Mix a Batch Now button ({entity_id}) is not available"
            )
        problem = self.plan()["problem"]
        if problem:
            raise ValueError(problem)
        if force:
            from datetime import timedelta

            from homeassistant.helpers.dispatcher import async_dispatcher_send
            from homeassistant.util import dt as dt_util

            self.force_until = dt_util.utcnow() + timedelta(seconds=FORCE_S)
            async_dispatcher_send(self.hass, f"{SIGNAL}_{self.entry.entry_id}")
        await self.hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True, context=context
        )
        pressed = self.hass.states.get(entity_id)
        return {**self.response(), "requested": pressed.state if pressed else None}

    async def set_stage(self, name: str):
        """The feed stage picked by its recipe's name (the select in Home Assistant). With the feed
        schedule running, it holds until the schedule's next week starts (feed.pick)."""
        async with self._lock:
            if self.error:
                raise ValueError(self.error)
            match = next(
                (item for item in self.data["recipes"] if item["name"] == name), None
            )
            if match is None:
                raise ValueError(f"No feed recipe is called {name}")
            draft = feed.pick(deepcopy(self.data), match["id"], self.today())
            if (draft["stage"], draft["held_until"]) != (
                self.data["stage"],
                self.data.get("held_until"),
            ):
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
    unsubscribe = manager.start()
    if unsubscribe:
        entry.async_on_unload(unsubscribe)

    async def handle(call):
        if call.service != "feed_get":
            await async_require_admin(hass, call, f"{DOMAIN}.{call.service}")
        try:
            target = resolve_feed(hass, call.data["room_id"])
            if call.service == "feed_get":
                return target.response()
            if call.service == "feed_mix":
                return await target.mix(call.context, call.data.get("force", False))
            return await target.save(call.data)
        except (ValueError, KeyError, OSError) as error:
            raise HomeAssistantError(str(error)) from error

    for service in SERVICES:
        schema = {vol.Required("room_id"): str}
        if service == "feed_save":
            schema[vol.Required("expected_revision")] = vol.All(int, vol.Range(min=0))
            schema[vol.Required("document")] = dict
        if service == "feed_mix":
            schema[vol.Optional("force", default=False)] = bool
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
