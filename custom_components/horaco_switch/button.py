"""Button platform — Reboot switch.

Single button entity under the parent switch device.
Sends POST /reboot.cgi {"cmd":"reboot"} directly to the hardware.
"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HoracoCoordinator
from .const import DOMAIN
from .sensor import switch_device_info   # reuse the helper

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HoracoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RebootButton(coordinator)])


class RebootButton(CoordinatorEntity[HoracoCoordinator], ButtonEntity):
    """Button that reboots the managed switch."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_has_entity_name = True
    _attr_name = "Reboot"
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: HoracoCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.scraper.ip}_reboot"
        self._attr_device_info = switch_device_info(coordinator)

    async def async_press(self) -> None:
        _LOGGER.warning("Rebooting switch %s via Home Assistant", self.coordinator.scraper.ip)
        ok = await self.coordinator.scraper.reboot()
        if not ok:
            _LOGGER.error("Reboot failed for %s", self.coordinator.scraper.ip)
