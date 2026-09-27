"""Buttons for Crop Steering: "Mix a Batch Now" for the room's reservoir.

Pressing it does nothing here. Home Assistant records when it was pressed as the button's state, and
the controller app, which reads that, mixes one nutrient batch the next time it looks: fill, mix and
dose (feed.py). It is a request, not a command: the controller only starts one while the room's
watering switch is on and nothing else is in the way, and says so if it cannot.
"""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SOFTWARE_VERSION
from .room import room_prefix

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([CropSteeringMixBatchButton(entry)])


class CropSteeringMixBatchButton(ButtonEntity):
    _attr_icon = "mdi:beaker-plus-outline"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_mix_batch"
        self._attr_name = "Mix a Batch Now"
        self._attr_object_id = f"{DOMAIN}_{room_prefix(entry)}mix_batch"
        # An explicit entity_id is the suggestion Home Assistant uses at first registration.
        self.entity_id = f"button.{self._attr_object_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Crop Steering",
            manufacturer="Home Assistant Community",
            model="Professional Irrigation Controller",
            sw_version=SOFTWARE_VERSION,
        )

    async def async_press(self) -> None:
        _LOGGER.info(
            "Nutrient batch requested for %s", room_prefix(self._entry) or "the room"
        )
