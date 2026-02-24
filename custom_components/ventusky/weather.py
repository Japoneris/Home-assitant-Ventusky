"""WeatherEntity for Ventusky."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfSpeed, UnitOfTemperature, UnitOfPrecipitationDepth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION_NAME, DOMAIN
from .coordinator import VentuskyCoordinator

# Maps Ventusky description strings -> HA condition constants
CONDITION_MAP: dict[str, str] = {
    "clear sky": "sunny",
    "clear sky with few clouds": "partlycloudy",
    "partly cloudy": "partlycloudy",
    "mostly cloudy": "cloudy",
    "high clouds": "partlycloudy",
    "overcast": "cloudy",
    "fog": "fog",
    "freezing fog": "fog",
    "light rain": "rainy",
    "rain": "rainy",
    "heavy rain": "pouring",
    "overcast with light rain": "rainy",
    "overcast with rain": "rainy",
    "overcast with heavy rain": "pouring",
    "light drizzle": "rainy",
    "drizzle": "rainy",
    "freezing drizzle": "rainy",
    "light snow": "snowy",
    "snow": "snowy",
    "heavy snow": "snowy",
    "sleet": "snowy-rainy",
    "light sleet": "snowy-rainy",
    "thunderstorm": "lightning",
    "thunderstorm with light rain": "lightning-rainy",
    "thunderstorm with rain": "lightning-rainy",
    "thunderstorm with heavy rain": "lightning-rainy",
    "thunderstorm with snow": "lightning-rainy",
    "hail": "hail",
}


def _map_condition(description: str, is_night: bool, current_hour: int) -> str:
    """Map a Ventusky description to a HA condition string."""
    desc_lower = description.lower()
    ha_cond = CONDITION_MAP.get(desc_lower, "exceptional")
    if ha_cond == "sunny" and (is_night or current_hour < 7 or current_hour >= 20):
        return "clear-night"
    return ha_cond


def _parse_date(date_str: str) -> datetime:
    """Parse 'YYYY/MM/DD' to UTC-aware datetime."""
    return datetime.strptime(date_str, "%Y/%m/%d").replace(tzinfo=timezone.utc)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ventusky weather entity."""
    coordinator: VentuskyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VentuskyWeatherEntity(coordinator, entry)])


class VentuskyWeatherEntity(CoordinatorEntity[VentuskyCoordinator], WeatherEntity):
    """Representation of Ventusky weather."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(self, coordinator: VentuskyCoordinator, entry: ConfigEntry) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"Ventusky {entry.data[CONF_LOCATION_NAME]}"
        self._attr_unique_id = f"ventusky_{entry.entry_id}"

    @property
    def _current(self) -> dict | None:
        """Return current hour slot (first in hourly_24h)."""
        hourly = self.coordinator.data.get("hourly_24h", [])
        return hourly[0] if hourly else None

    @property
    def native_temperature(self) -> float | None:
        c = self._current
        return c["temperature_c"] if c else None

    @property
    def condition(self) -> str | None:
        c = self._current
        if not c:
            return None
        hour = datetime.now().hour
        return _map_condition(c["weather_description"], False, hour)

    @property
    def native_wind_speed(self) -> float | None:
        c = self._current
        return c["wind_speed_kmh"] if c else None

    @property
    def wind_bearing(self) -> float | None:
        c = self._current
        return c["wind_direction_deg"] if c else None

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return hourly forecast (next ~25 slots)."""
        hourly = self.coordinator.data.get("hourly_24h", [])
        forecasts: list[Forecast] = []
        for slot in hourly[:25]:
            date_str = slot.get("date", "")
            time_str = slot.get("time", "00:00")
            try:
                dt = datetime.strptime(
                    f"{date_str} {time_str}", "%Y/%m/%d %H:%M"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            hour = dt.hour
            prob = slot.get("precipitation_probability_pct")
            if prob == -1:
                prob = None

            forecasts.append(
                Forecast(
                    datetime=dt.isoformat(),
                    condition=_map_condition(
                        slot.get("weather_description", ""), False, hour
                    ),
                    native_temperature=slot.get("temperature_c"),
                    native_precipitation=slot.get("precipitation_mm"),
                    precipitation_probability=prob,
                    native_wind_speed=slot.get("wind_speed_kmh"),
                    wind_bearing=slot.get("wind_direction_deg"),
                )
            )
        return forecasts

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return 8-day daily forecast."""
        forecast_days = self.coordinator.data.get("forecast", [])
        forecasts: list[Forecast] = []

        for day in forecast_days[:8]:
            date_str = day.get("date", "")
            try:
                dt = _parse_date(date_str)
            except ValueError:
                continue

            slots = day.get("hourly", [])
            if not slots:
                continue

            temps = [s["temperature_c"] for s in slots if s.get("temperature_c") is not None]
            max_temp = max(temps) if temps else None
            min_temp = min(temps) if temps else None

            precip_total = sum(
                s.get("precipitation_mm") or 0 for s in slots
            )

            probs = [
                s["precipitation_probability_pct"]
                for s in slots
                if s.get("precipitation_probability_pct") not in (None, -1)
            ]
            max_prob = max(probs) if probs else None

            # Daytime condition from 13:00 slot
            day_slot = next(
                (s for s in slots if s.get("time") == "13:00"), slots[0]
            )
            condition = _map_condition(
                day_slot.get("weather_description", ""), False, 13
            )

            forecasts.append(
                Forecast(
                    datetime=dt.isoformat(),
                    condition=condition,
                    native_temperature=max_temp,
                    native_templow=min_temp,
                    native_precipitation=precip_total if precip_total > 0 else None,
                    precipitation_probability=max_prob,
                )
            )
        return forecasts
