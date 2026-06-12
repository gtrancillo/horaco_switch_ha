"""Sensor platform for HORACO Managed Switch.

Architecture:
  • One "parent" Device  → the physical switch  (model, firmware, uptime, MAC, ports summary)
  • One "child" Device per port  → Port N (link, speed, duplex, TX bytes, RX bytes,
                                            TX packets, RX packets, TX errors, RX errors)

This way the UI groups everything per port instead of exposing a flat list of
disconnected entities.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HoracoCoordinator
from .const import DOMAIN
from .scraper import PortData, SwitchData

_LOGGER = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Device helpers
# ────────────────────────────────────────────────────────────────────────────

def switch_device_info(coordinator: HoracoCoordinator) -> DeviceInfo:
    """DeviceInfo for the physical switch (parent device)."""
    d = coordinator.data
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.scraper.ip)},
        name=f"Switch {coordinator.scraper.ip}",
        manufacturer="HORACO",
        model=d.model if d else "Unknown",
        sw_version=d.firmware if d else None,
        hw_version=None,
        connections={("mac", d.mac)} if d and d.mac else set(),
        configuration_url=f"http://{coordinator.scraper.ip}",
    )


def port_device_info(coordinator: HoracoCoordinator, port_num: str) -> DeviceInfo:
    """DeviceInfo for a single port (child device, via_device → switch)."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{coordinator.scraper.ip}_port{port_num}")},
        name=f"Port {port_num}",
        manufacturer="HORACO",
        model=f"Port {port_num}",
        via_device=(DOMAIN, coordinator.scraper.ip),
    )


# ────────────────────────────────────────────────────────────────────────────
# Switch-level sensor descriptors
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class SwitchSensorDesc(SensorEntityDescription):
    value_fn: Callable[[SwitchData], Any] | None = None


SWITCH_SENSORS: tuple[SwitchSensorDesc, ...] = (
    SwitchSensorDesc(
        key="uptime",
        name="Uptime",
        icon="mdi:timer-outline",
        value_fn=lambda d: d.uptime or None,
    ),
    SwitchSensorDesc(
        key="firmware",
        name="Firmware",
        icon="mdi:chip",
        value_fn=lambda d: d.firmware or None,
    ),
    SwitchSensorDesc(
        key="mac_address",
        name="MAC Address",
        icon="mdi:identifier",
        value_fn=lambda d: d.mac or None,
    ),
    SwitchSensorDesc(
        key="ports_up",
        name="Ports Up",
        icon="mdi:ethernet",
        native_unit_of_measurement="ports",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: sum(1 for p in d.ports if p.status == "up"),
    ),
    SwitchSensorDesc(
        key="ports_total",
        name="Ports Total",
        icon="mdi:ethernet",
        native_unit_of_measurement="ports",
        value_fn=lambda d: len(d.ports),
    ),
)


# ────────────────────────────────────────────────────────────────────────────
# Per-port sensor descriptors
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class PortSensorDesc(SensorEntityDescription):
    value_fn: Callable[[PortData], Any] | None = None


PORT_SENSORS: tuple[PortSensorDesc, ...] = (
    PortSensorDesc(
        key="speed",
        name="Speed",
        icon="mdi:speedometer",
        value_fn=lambda p: p.speed or None,
    ),
    PortSensorDesc(
        key="duplex",
        name="Duplex",
        icon="mdi:transfer",
        value_fn=lambda p: p.duplex or None,
    ),
    PortSensorDesc(
        key="tx_bytes",
        name="TX",
        icon="mdi:upload-network-outline",
        native_unit_of_measurement="B",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda p: p.tx_bytes,
    ),
    PortSensorDesc(
        key="rx_bytes",
        name="RX",
        icon="mdi:download-network-outline",
        native_unit_of_measurement="B",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda p: p.rx_bytes,
    ),
    PortSensorDesc(
        key="tx_packets",
        name="TX Packets",
        icon="mdi:arrow-up-circle-outline",
        native_unit_of_measurement="packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda p: p.tx_packets,
    ),
    PortSensorDesc(
        key="rx_packets",
        name="RX Packets",
        icon="mdi:arrow-down-circle-outline",
        native_unit_of_measurement="packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda p: p.rx_packets,
    ),
    PortSensorDesc(
        key="flow_control",
        name="Flow Control",
        icon="mdi:swap-horizontal",
        value_fn=lambda p: p.flow_control or None,
    ),
)


# ────────────────────────────────────────────────────────────────────────────
# Platform setup
# ────────────────────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HoracoCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    # Switch-level sensors
    for desc in SWITCH_SENSORS:
        entities.append(SwitchLevelSensor(coordinator, desc))

    # Port-level sensors (one child device per port)
    if coordinator.data:
        for port in coordinator.data.ports:
            for desc in PORT_SENSORS:
                entities.append(PortLevelSensor(coordinator, port.port, desc))

    async_add_entities(entities)


# ────────────────────────────────────────────────────────────────────────────
# Entity classes
# ────────────────────────────────────────────────────────────────────────────

class SwitchLevelSensor(CoordinatorEntity[HoracoCoordinator], SensorEntity):
    """Sensor attached to the parent switch device."""

    entity_description: SwitchSensorDesc

    def __init__(self, coordinator: HoracoCoordinator, desc: SwitchSensorDesc) -> None:
        super().__init__(coordinator)
        self.entity_description = desc
        self._attr_unique_id = f"{DOMAIN}_{coordinator.scraper.ip}_{desc.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = switch_device_info(coordinator)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data) if self.coordinator.data else None


class PortLevelSensor(CoordinatorEntity[HoracoCoordinator], SensorEntity):
    """Sensor attached to a per-port child device."""

    entity_description: PortSensorDesc

    def __init__(
        self,
        coordinator: HoracoCoordinator,
        port_num: str,
        desc: PortSensorDesc,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = desc
        self._port_num = port_num
        self._attr_unique_id = f"{DOMAIN}_{coordinator.scraper.ip}_port{port_num}_{desc.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = port_device_info(coordinator, port_num)

    def _port(self) -> PortData | None:
        if not self.coordinator.data:
            return None
        return next((p for p in self.coordinator.data.ports if p.port == self._port_num), None)

    @property
    def native_value(self) -> Any:
        p = self._port()
        return self.entity_description.value_fn(p) if p else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        p = self._port()
        if not p:
            return {}
        return {
            "status": p.status,
            "link": p.link,
        }
