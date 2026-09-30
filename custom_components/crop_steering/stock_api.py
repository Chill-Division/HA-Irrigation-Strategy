"""Stock tanks per room, stored and served; see stock.py for the rules.

Response-only services addressed by canonical room id, like the run and strategy services. Reading
is open to any signed-in user; changing a tank, recording a refill or a batch needs an
administrator. A tank on one of the room's dosers is drawn when the controller reports a batch it
mixed ended (sensor.crop_steering_<prefix>batch_status, its `last`): by what that doser gave. Any
other tank is drawn when the room's mapped tank last-fill entity moves to a newer time, or when the
operator records a batch. A room whose tanks run low gets a Repairs card.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import logging

from . import stock
from .admin import async_require_admin
from .const import DOMAIN, REPAIRS_DOCS_URL
from .room import room_prefix

_LOGGER = logging.getLogger(__name__)

SERVICES = ("stock_get", "stock_save", "stock_refill", "stock_record_batch")
SIGNAL = f"{DOMAIN}_stock_changed"
ISSUE = "stock_low"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid(value) -> dict:
    """A stored document, checked as strictly as an edit; anything else is refused."""
    if not isinstance(value, dict) or type(value.get("revision")) is not int:
        raise ValueError("Invalid stored revision")
    data = stock.empty()
    data["revision"] = value["revision"]
    data["tanks"] = stock.clean_tanks(value.get("tanks", []), [], _now())
    # clean_tanks gives new ids and times; the stored ones are the truth.
    for tank, raw in zip(data["tanks"], value.get("tanks", [])):
        for key in ("id", "refilled_at", "updated_at"):
            tank[key] = raw.get(key, tank[key])
    last = value.get("last_batch")
    data["last_batch"] = datetime.fromisoformat(last).isoformat() if last else None
    mixed = value.get("reservoir_batch")
    data["reservoir_batch"] = (
        datetime.fromisoformat(mixed).isoformat() if mixed else None
    )
    history = value.get("history", [])
    data["history"] = history[: stock.HISTORY] if isinstance(history, list) else []
    return data


class StockStore:
    def __init__(self, hass, entry, store=None):
        self.hass, self.entry = hass, entry
        self.prefix = room_prefix(entry)
        self.room_id = "room:" + self.prefix
        self.slug = (getattr(entry, "data", None) or {}).get("room_slug", "default")
        self.issue_id = (
            ISSUE if self.slug in ("", "default") else f"{ISSUE}_{self.slug}"
        )
        self._store = store
        self._lock = asyncio.Lock()
        self.data = stock.empty()
        self.error = None

    @property
    def fill_entity(self) -> str | None:
        """The room's tank last-fill entity from Rooms & setup; None when unmapped."""
        config = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        hardware = config.get("hardware", {}) if isinstance(config, dict) else {}
        return hardware.get("tank_last_fill_sensor") or None

    async def async_init(self):
        try:
            if self._store is None:
                from homeassistant.helpers.storage import Store

                self._store = Store(
                    self.hass, 1, f"{DOMAIN}.stock.{self.entry.entry_id}"
                )
            value = await self._store.async_load()
            if value is not None:
                self.data = _valid(value)
        except Exception as error:
            self.error = (
                "Stored stock tanks could not be loaded; they have not been overwritten: "
                f"{error}"
            )

    @property
    def batch_entity(self) -> str:
        """Where the controller reports the room's nutrient batches (controller.py _batch_publish)."""
        return f"sensor.{DOMAIN}_{self.prefix}batch_status"

    def start(self):
        """Count batches from the Reservoir and the fill entity, and raise the low-stock card.
        Returns the unsubscribe for the listeners, or None when there is nothing to listen to.
        """
        self._alert()
        if self.error:
            return None
        from homeassistant.core import callback
        from homeassistant.helpers.event import async_track_state_change_event

        entity = self.fill_entity
        # The fill time at start-up is a starting point, not a batch (stock.new_batch); so is the
        # Reservoir's last batch the first time this runs (_reservoir).
        if entity:
            current = self.hass.states.get(entity)
            self.hass.async_create_task(self._fill(current.state if current else None))
        self.hass.async_create_task(
            self._reservoir(self.hass.states.get(self.batch_entity))
        )

        @callback
        def changed(event):
            state = event.data.get("new_state")
            if event.data.get("entity_id") == self.batch_entity:
                self.hass.async_create_task(self._reservoir(state))
            else:
                self.hass.async_create_task(self._fill(state.state if state else None))

        return async_track_state_change_event(
            self.hass, [e for e in (entity, self.batch_entity) if e], changed
        )

    def _feed(self):
        """The room's feed settings (feed_api.py), or None when they cannot be read."""
        from .feed_api import get_feed

        manager = get_feed(self.hass, self.entry)
        return None if manager is None or manager.error else manager

    def _nutrients(self, stage=None) -> dict[int, str]:
        """What a recipe puts on each doser: the one called `stage`, or the stage in use."""
        manager = self._feed()
        if manager is None:
            return {}
        recipes = manager.data.get("recipes", [])
        if stage is None:
            recipe = next(
                (r for r in recipes if r["id"] == manager.data.get("stage")), None
            )
        else:
            recipe = next((r for r in recipes if r["name"] == stage), None)
        return {
            int(n): dose["label"]
            for n, dose in (recipe or {}).get("doses", {}).items()
            if dose.get("label")
        }

    def dosers(self) -> dict[str, dict]:
        """The room's dosers from Rooms & setup, each with its switch and the nutrient the stage
        in use puts on it (None when it doses nothing in that stage)."""
        from .feed_api import mapped_dosers

        config = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        hardware = config.get("hardware", {}) if isinstance(config, dict) else {}
        nutrients = self._nutrients()
        return {
            str(n): {"switch": entity, "nutrient": nutrients.get(n)}
            for n, entity in mapped_dosers(
                hardware if isinstance(hardware, dict) else {}
            ).items()
        }

    def doses(self) -> dict[str, float]:
        """What one batch takes from each tank right now, in mL. A tank on a doser: what the stage
        in use doses from it (0 when that stage does not use it). Any other: its dose entity's
        reading, or its fixed dose."""
        doses = {}
        for tank in self.data["tanks"]:
            if tank.get("doser"):
                doses[tank["id"]] = 0.0
                continue
            state = (
                self.hass.states.get(tank["dose_entity"])
                if tank["dose_entity"]
                else None
            )
            doses[tank["id"]] = stock.dose_ml(tank, state.state if state else None)
        manager = self._feed()
        for dose in manager.plan()["doses"] if manager is not None else []:
            owner = stock.on_doser(self.data["tanks"], dose["doser"], dose["label"])
            if owner is not None:
                doses[owner["id"]] = float(dose["ml"])
        return doses

    def _hand_doses(self) -> dict[str, float]:
        """A batch the Reservoir did not mix (a fill, or one recorded by hand) draws only from the
        tanks on no doser: the others lose what their dosers give, in the Reservoir's batches.
        """
        on = {tank["id"] for tank in self.data["tanks"] if tank.get("doser")}
        return {
            tank_id: ml for tank_id, ml in self.doses().items() if tank_id not in on
        }

    async def _reservoir(self, state):
        """A batch the Reservoir mixed ended (the batch status's `last`): each tank on a doser
        loses what its doser gave. Counted once, by when it ended; the first time this runs, the
        batch already reported is a starting point, not counted (it ended before any tank here was
        on a doser)."""
        last = state.attributes.get("last") if state is not None else None
        # The controller gives the time with its UTC offset; one without is read as UTC.
        ended = (
            stock.parse_fill(str(last.get("at")), timezone.utc)
            if isinstance(last, dict) and last.get("at")
            else None
        )
        async with self._lock:
            if self.error:
                return
            draft = deepcopy(self.data)
            counted = draft.get("reservoir_batch")
            if counted is None:
                draft["reservoir_batch"] = _now()
                await self._commit(draft)
                return
            if ended is None or ended <= datetime.fromisoformat(counted):
                return
            draft["reservoir_batch"] = ended.isoformat()
            draws = stock.reservoir_draws(
                draft["tanks"], last.get("dosed"), self._nutrients(last.get("stage"))
            )
            if draws:
                stock.draw(draft, draws, ended.isoformat(), "reservoir")
                _LOGGER.info(
                    "Stock tanks for %s: Reservoir batch at %s counted",
                    self.room_id,
                    ended,
                )
            await self._commit(draft)

    async def _fill(self, state):
        from homeassistant.util import dt as dt_util

        zone = dt_util.get_default_time_zone()
        async with self._lock:
            if self.error:
                return
            fill = stock.parse_fill(state, zone)
            draft = deepcopy(self.data)
            counted = stock.new_batch(draft, fill)
            if counted and draft["tanks"]:
                stock.draw(draft, self._hand_doses(), fill.isoformat(), "fill")
                _LOGGER.info(
                    "Stock tanks for %s: batch at %s counted", self.room_id, fill
                )
            if counted or draft["last_batch"] != self.data["last_batch"]:
                await self._commit(draft)

    def response(self):
        doses = self.doses()
        return {
            "schema_version": 1,
            "room_id": self.room_id,
            **deepcopy(self.data),
            "fill_entity": self.fill_entity,
            "dosers": self.dosers(),
            "doses": doses,
            "low": [tank["id"] for tank in stock.low_tanks(self.data)],
            "max_tanks": stock.MAX_TANKS,
            "error": self.error,
        }

    async def mutate(self, action, data):
        async with self._lock:
            if self.error:
                raise ValueError(self.error)
            if data.get("expected_revision") != self.data["revision"]:
                raise ValueError("Stock tanks changed elsewhere. Reload before saving.")
            now = _now()
            draft = deepcopy(self.data)
            if action == "stock_save":
                draft["tanks"] = stock.clean_tanks(
                    data.get("tanks"), draft["tanks"], now
                )
            elif action == "stock_refill":
                stock.refill(draft, data.get("id"), data.get("level_l"), now)
            elif action == "stock_record_batch":
                stock.draw(draft, self._hand_doses(), now, "manual")
            else:
                raise ValueError("Unsupported stock operation")
            await self._commit(draft)
            return self.response()

    async def _commit(self, draft):
        """Store the next revision; only a saved change becomes the room's tanks."""
        draft["revision"] = self.data["revision"] + 1
        await self._store.async_save(draft)
        self.data = draft
        self._alert()
        from homeassistant.helpers.dispatcher import async_dispatcher_send

        async_dispatcher_send(self.hass, f"{SIGNAL}_{self.entry.entry_id}")

    def _alert(self):
        """One Repairs card per room while any tank is at or below its low mark."""
        from homeassistant.helpers import issue_registry as ir

        low = stock.low_tanks(self.data)
        if not low:
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            return
        doses = self.doses()
        lines = []
        for tank in low:
            left = stock.batches_left(tank, doses.get(tank["id"], 0))
            lines.append(
                f"- {tank['name']}: {tank['level_l']:g} L of {tank['capacity_l']:g} L"
                + (
                    ""
                    if left is None
                    else f", about {left} batch{'es' if left != 1 else ''} left"
                )
            )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE,
            translation_placeholders={
                "count": str(len(low)),
                "tanks": "\n".join(lines),
            },
            learn_more_url=REPAIRS_DOCS_URL,
        )


def resolve_stock(hass, room_id):
    if not isinstance(room_id, str) or not room_id.startswith("room:"):
        raise ValueError("A canonical room_id is required")
    matches = [
        manager
        for manager in hass.data.get(DOMAIN, {}).get("_stock", {}).values()
        if manager.room_id == room_id
    ]
    if len(matches) != 1:
        raise ValueError("Stock tank room is unknown or ambiguous")
    return matches[0]


async def async_setup_stock(hass, entry):
    import voluptuous as vol
    from homeassistant.core import SupportsResponse
    from homeassistant.exceptions import HomeAssistantError

    manager = StockStore(hass, entry)
    await manager.async_init()
    hass.data.setdefault(DOMAIN, {}).setdefault("_stock", {})[entry.entry_id] = manager
    unsubscribe = manager.start()
    if unsubscribe:
        entry.async_on_unload(unsubscribe)

    async def handle(call):
        if call.service != "stock_get":
            await async_require_admin(hass, call, f"{DOMAIN}.{call.service}")
        try:
            target = resolve_stock(hass, call.data["room_id"])
            if call.service == "stock_get":
                return target.response()
            return await target.mutate(call.service, call.data)
        except (ValueError, KeyError, OSError) as error:
            raise HomeAssistantError(str(error)) from error

    for service in SERVICES:
        schema = {vol.Required("room_id"): str}
        if service != "stock_get":
            schema[vol.Required("expected_revision")] = vol.All(int, vol.Range(min=0))
        if service == "stock_save":
            schema[vol.Required("tanks")] = vol.All(
                list, vol.Length(max=stock.MAX_TANKS)
            )
        elif service == "stock_refill":
            schema[vol.Required("id")] = str
            # Left out: refilled to capacity. Given: the level read off the tank.
            schema[vol.Optional("level_l")] = vol.All(
                vol.Coerce(float), vol.Range(min=0, max=10000)
            )
        hass.services.async_register(
            DOMAIN,
            service,
            handle,
            schema=vol.Schema(schema),
            supports_response=SupportsResponse.ONLY,
        )


async def async_unload_stock(hass, entry):
    from homeassistant.helpers import issue_registry as ir

    managers = hass.data.get(DOMAIN, {}).get("_stock", {})
    manager = managers.pop(entry.entry_id, None)
    if manager is not None:
        ir.async_delete_issue(hass, DOMAIN, manager.issue_id)
    if not managers:
        for service in SERVICES:
            hass.services.async_remove(DOMAIN, service)
