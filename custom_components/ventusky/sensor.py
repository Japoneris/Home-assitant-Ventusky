"""Sensor entities for Ventusky."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPrecipitationDepth,
    DEGREE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION_NAME, DOMAIN
from .coordinator import VentuskyCoordinator


@dataclass(frozen=True)
class VentuskySensorEntityDescription(SensorEntityDescription):
    """Describes a Ventusky sensor."""


SENSOR_TYPES: tuple[VentuskySensorEntityDescription, ...] = (
    VentuskySensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    VentuskySensorEntityDescription(
        key="rain_today",
        name="Rain Today",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
    ),
    VentuskySensorEntityDescription(
        key="wind_speed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
    ),
    VentuskySensorEntityDescription(
        key="wind_bearing",
        name="Wind Bearing",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ventusky sensor entities."""
    coordinator: VentuskyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VentuskySensor(coordinator, entry, description)
        for description in SENSOR_TYPES
    )


class VentuskySensor(CoordinatorEntity[VentuskyCoordinator], SensorEntity):
    """A single Ventusky sensor."""

    entity_description: VentuskySensorEntityDescription

    def __init__(
        self,
        coordinator: VentuskyCoordinator,
        entry: ConfigEntry,
        description: VentuskySensorEntityDescription,
    ) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        location = entry.data[CONF_LOCATION_NAME]
        self._attr_name = f"Ventusky {location} {description.name}"
        self._attr_unique_id = f"ventusky_{entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        """Return the sensor value."""
        data = self.coordinator.data
        hourly = data.get("hourly_24h", [])
        if not hourly:
            return None
        current = hourly[0]

        if self.entity_description.key == "temperature":
            return current.get("temperature_c")

        if self.entity_description.key == "wind_speed":
            return current.get("wind_speed_kmh")

        if self.entity_description.key == "wind_bearing":
            return current.get("wind_direction_deg")

        if self.entity_description.key == "rain_today":
            today_str = datetime.now(tz=timezone.utc).strftime("%Y/%m/%d")
            total = sum(
                slot.get("precipitation_mm") or 0
                for slot in hourly
                if slot.get("date") == today_str
            )
            return round(total, 2)

        return None
