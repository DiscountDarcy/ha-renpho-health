"""Sensor platform for the Renpho Health integration.

Creates one sensor entity per metric per scale device.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, METRICS
from .coordinator import RenphoHealthCoordinator

_LOGGER = logging.getLogger(__name__)

# Map metric unit strings to HA unit constants
UNIT_MAP: dict[str, str] = {
    "kg": UnitOfMass.KILOGRAMS,
    "%": PERCENTAGE,
    "kg/m²": "kg/m²",
    "kcal/day": "kcal/day",
    "bpm": "bpm",
    "level": "level",
    "years": "years",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Renpho Health sensors from a config entry."""
    coordinator: RenphoHealthCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first data fetch so we know what scales exist
    await coordinator.async_config_entry_first_refresh()

    entities: list[RenphoHealthSensor] = []

    data = coordinator.data
    if data and data.get("scales"):
        for scale in data["scales"]:
            scale_name = scale.get("name", "Unknown Scale")
            scale_model = scale.get("model", "")
            scale_mac = scale.get("mac", "")
            table_name = scale.get("table_name", "")

            # Create one entity per metric
            for key, name, unit, device_class_str, state_class_str, icon in METRICS:
                entities.append(
                    RenphoHealthSensor(
                        coordinator=coordinator,
                        scale_name=scale_name,
                        scale_model=scale_model,
                        scale_mac=scale_mac,
                        table_name=table_name,
                        metric_key=key,
                        metric_name=name,
                        metric_unit=unit,
                        device_class_str=device_class_str,
                        state_class_str=state_class_str,
                        icon=icon,
                    )
                )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d Renpho Health sensor entities", len(entities))
    else:
        _LOGGER.warning("No Renpho Health sensor entities created — no scale data found")


class RenphoHealthSensor(CoordinatorEntity[RenphoHealthCoordinator], SensorEntity):
    """Sensor entity for a single Renpho Health metric."""

    def __init__(
        self,
        coordinator: RenphoHealthCoordinator,
        scale_name: str,
        scale_model: str,
        scale_mac: str,
        table_name: str,
        metric_key: str,
        metric_name: str,
        metric_unit: str | None,
        device_class_str: str | None,
        state_class_str: str | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._scale_name = scale_name
        self._metric_key = metric_key
        self._metric_name = metric_name
        self._metric_unit = metric_unit

        # Entity identity
        safe_key = metric_key.replace(" ", "_").lower()
        safe_scale = scale_name.replace(" ", "_").lower().replace("(", "").replace(")", "")
        self.entity_id = f"sensor.renpho_{safe_scale}_{safe_key}"
        self._attr_unique_id = f"{table_name}_{metric_key}"
        self._attr_name = f"Renpho {scale_name} {metric_name}"
        self._attr_icon = icon

        # Unit of measurement
        if metric_unit and metric_unit in UNIT_MAP:
            self._attr_native_unit_of_measurement = UNIT_MAP[metric_unit]
        else:
            self._attr_native_unit_of_measurement = metric_unit

        # Device class
        if device_class_str:
            try:
                self._attr_device_class = SensorDeviceClass(device_class_str)
            except ValueError:
                pass

        # State class
        if state_class_str:
            try:
                self._attr_state_class = SensorStateClass(state_class_str)
            except ValueError:
                pass

        # Device info for grouping sensors under a scale device
        model_display = f"Renpho {scale_model}" if scale_model else "Renpho Smart Scale"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{table_name}_{scale_mac}")},
            name=scale_name,
            manufacturer="Renpho",
            model=model_display,
            entry_type=DeviceEntryType.SERVICE,
            sw_version=scale_model if scale_model else None,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the current value of the sensor."""
        if not self.coordinator.data:
            return None
        for scale in self.coordinator.data.get("scales", []):
            if scale.get("name") == self._scale_name:
                measurements = scale.get("measurements", [])
                if measurements:
                    return measurements[0].get(self._metric_key)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}

        if not self.coordinator.data:
            return attrs

        for scale in self.coordinator.data.get("scales", []):
            if scale.get("name") == self._scale_name:
                measurements = scale.get("measurements", [])
                if measurements:
                    latest = measurements[0]
                    attrs["measured_at"] = latest.get("measured_at")
                    attrs["scale_name"] = self._scale_name
                    attrs["scale_model"] = scale.get("model", "")
                break

        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.native_value is not None
