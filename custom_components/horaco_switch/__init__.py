"""HORACO / OEM Managed Switch — Home Assistant Integration.

Talks directly to the switch CGI interface, no intermediate service needed.
Based on the scraping logic from https://github.com/byte4geek/switch-dashboard
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .scraper import HoracoScraper, SwitchData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HORACO Switch from a config entry."""
    scraper = HoracoScraper(
        session=async_get_clientsession(hass),
        ip=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        http_port=entry.data.get(CONF_PORT, 80),
    )

    coordinator = HoracoCoordinator(hass, scraper, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok


class HoracoCoordinator(DataUpdateCoordinator[SwitchData]):
    """Central coordinator — polls the switch at a fixed interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        scraper: HoracoScraper,
        entry: ConfigEntry,
    ) -> None:
        self.scraper = scraper
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{scraper.ip}",
            update_interval=timedelta(
                seconds=entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            ),
        )

    async def _async_update_data(self) -> SwitchData:
        data = await self.scraper.scrape()
        if not data.available:
            raise UpdateFailed(f"Switch {self.scraper.ip} is unreachable")
        return data
