"""Binary sensor platform — port link state (UP/DOWN).

Each port gets a connectivity binary_sensor under its own child device.
Attributes carry all port details: speed, duplex, flow control, counters.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HoracoCoordinator
from .const import DOMAIN, PORT_STATUS_UP
from .scraper import PortData
from .sensor import port_device_info   # reuse the helper

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HoracoCoordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        return
    async_add_entities(
        PortLinkBinarySensor(coordinator, p.port)
        for p in coordinator.data.ports
    )


class PortLinkBinarySensor(CoordinatorEntity[HoracoCoordinator], BinarySensorEntity):
    """Binary sensor: ON = link up, OFF = down or disabled."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Link"

    def __init__(self, coordinator: HoracoCoordinator, port_num: str) -> None:
        super().__init__(coordinator)
        self._port_num = port_num
        self._attr_unique_id = f"{DOMAIN}_{coordinator.scraper.ip}_port{port_num}_link"
        self._attr_device_info = port_device_info(coordinator, port_num)

    def _port(self) -> PortData | None:
        if not self.coordinator.data:
            return None
        return next((p for p in self.coordinator.data.ports if p.port == self._port_num), None)

    @property
    def is_on(self) -> bool | None:
        p = self._port()
        return p.status == PORT_STATUS_UP if p else None

    @property
    def icon(self) -> str:
        p = self._port()
        return "mdi:ethernet" if (p and p.status == PORT_STATUS_UP) else "mdi:ethernet-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        p = self._port()
        if not p:
            return {}
        return {
            "status":       p.status,
            "link":         p.link,
            "speed":        p.speed,
            "duplex":       p.duplex,
            "flow_control": p.flow_control,
            "tx_bytes":     p.tx_bytes,
            "rx_bytes":     p.rx_bytes,
            "tx_packets":   p.tx_packets,
            "rx_packets":   p.rx_packets,
        }
