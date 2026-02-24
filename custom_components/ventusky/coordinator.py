"""DataUpdateCoordinator for Ventusky."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_LAT, CONF_LON, CONF_REFRESH_INTERVAL, DOMAIN, USER_AGENT, VENTUSKY_URL_TEMPLATE
from .weather_parser import parse_weather_html

_LOGGER = logging.getLogger(__name__)


class VentuskyCoordinator(DataUpdateCoordinator[dict]):
    """Fetch and cache Ventusky weather data."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialise coordinator."""
        self._lat = entry.data[CONF_LAT]
        self._lon = entry.data[CONF_LON]
        interval_minutes = entry.data.get(CONF_REFRESH_INTERVAL, 60)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict:
        """Fetch HTML and parse it (BeautifulSoup runs in executor)."""
        url = VENTUSKY_URL_TEMPLATE.format(lat=self._lat, lon=self._lon)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status} from {url}")
                    html = await resp.text()
        except aiohttp.ClientError as exc:
            raise UpdateFailed(f"Network error fetching {url}: {exc}") from exc

        try:
            data = await self.hass.async_add_executor_job(parse_weather_html, html)
        except Exception as exc:
            raise UpdateFailed(f"Failed to parse Ventusky HTML: {exc}") from exc

        return data
