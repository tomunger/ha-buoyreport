"""Sensor entities for an NDBC buoy.

One config entry == one station == one device. A sensor is created for every
observation the station actually reports in its first fetch, so land stations
(pressure + water temp only) do not get empty wind/wave entities.
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    EntityCategory,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, DOMAIN, MANUFACTURER, STATION_PAGE_URL
from .coordinator import NdbcBuoyCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="observation_time",
        name="Observation time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="wind_speed",
        name="Wind speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_gust",
        name="Wind gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KNOTS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_bearing",
        name="Wind direction",
        native_unit_of_measurement=DEGREE,
        icon="mdi:compass",
    ),
    SensorEntityDescription(
        key="wave_height",
        name="Wave height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves",
    ),
    SensorEntityDescription(
        key="wave_period",
        name="Wave period",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="swell_height",
        name="Swell height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves",
    ),
    SensorEntityDescription(
        key="swell_period",
        name="Swell period",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="swell_direction",
        name="Swell direction",
        icon="mdi:compass",
    ),
    SensorEntityDescription(
        key="wind_wave_height",
        name="Wind wave height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.FEET,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves",
    ),
    SensorEntityDescription(
        key="wind_wave_period",
        name="Wind wave period",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wind_wave_direction",
        name="Wind wave direction",
        icon="mdi:compass",
    ),
    SensorEntityDescription(
        key="pressure",
        name="Pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pressure_tendency",
        name="Pressure tendency",
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:gauge",
    ),
    SensorEntityDescription(
        key="air_temp",
        name="Air temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="dew_point",
        name="Dew point",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="water_temp",
        name="Water temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    station_id = entry.data[CONF_STATION_ID]
    # Short device name keeps entity IDs tidy (e.g. sensor.buoy_46087_wind_speed);
    # the full NDBC description is kept on the device's model field.
    return DeviceInfo(
        identifiers={(DOMAIN, station_id)},
        name=f"Buoy {station_id.upper()}",
        manufacturer=MANUFACTURER,
        model=entry.data.get("name") or "Ocean buoy",
        configuration_url=STATION_PAGE_URL.format(station_id=station_id),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create entities for the observations this station reports."""
    coordinator: NdbcBuoyCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    entities: list[SensorEntity] = [NdbcLocationSensor(coordinator, entry)]
    entities.extend(
        NdbcBuoySensor(coordinator, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
        if data.get(desc.key) is not None
    )
    async_add_entities(entities)


class NdbcBuoySensor(CoordinatorEntity[NdbcBuoyCoordinator], SensorEntity):
    """A single observation value from a buoy."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NdbcBuoyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        station_id = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{station_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        if self.entity_description.key == "wind_bearing":
            cardinal = self.coordinator.data.get("wind_cardinal")
            if cardinal:
                return {"cardinal": cardinal}
        return None


class NdbcLocationSensor(CoordinatorEntity[NdbcBuoyCoordinator], SensorEntity):
    """Exposes the buoy position for the Map card and a Google Maps link."""

    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_icon = "mdi:map-marker"

    def __init__(
        self, coordinator: NdbcBuoyCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        station_id = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{station_id}_location"
        self._attr_device_info = _device_info(entry)

    def _coords(self) -> tuple[float, float] | None:
        lat = self.coordinator.data.get("latitude")
        lon = self.coordinator.data.get("longitude")
        if lat is None or lon is None:
            return None
        return lat, lon

    @property
    def native_value(self) -> str | None:
        coords = self._coords()
        return f"{coords[0]}, {coords[1]}" if coords else None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        coords = self._coords()
        if not coords:
            return None
        lat, lon = coords
        attrs: dict[str, object] = {
            # latitude/longitude make this entity plottable on the Map card.
            "latitude": lat,
            "longitude": lon,
            "map_url": f"https://www.google.com/maps?q={lat},{lon}",
        }
        if name := self.coordinator.data.get("name"):
            attrs["station_name"] = name
        return attrs
