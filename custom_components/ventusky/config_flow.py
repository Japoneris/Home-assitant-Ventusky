"""Config flow for Ventusky integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LAT,
    CONF_LON,
    CONF_LOCATION_NAME,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    VENTUSKY_URL_TEMPLATE,
    USER_AGENT,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LAT): cv.latitude,
        vol.Required(CONF_LON): cv.longitude,
        vol.Required(CONF_LOCATION_NAME): str,
        vol.Optional(CONF_REFRESH_INTERVAL, default=DEFAULT_REFRESH_INTERVAL): vol.All(
            int, vol.Range(min=5)
        ),
    }
)


async def _test_fetch(hass: HomeAssistant, lat: float, lon: float) -> bool:
    """Try fetching the Ventusky page; return True on success."""
    url = VENTUSKY_URL_TEMPLATE.format(lat=lat, lon=lon)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


class VentuskyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ventusky."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            lat = user_input[CONF_LAT]
            lon = user_input[CONF_LON]

            unique_id = f"{lat}_{lon}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            ok = await _test_fetch(self.hass, lat, lon)
            if not ok:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_LOCATION_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
