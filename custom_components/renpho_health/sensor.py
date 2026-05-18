"""Sensor platform for the Renpho Health integration.

Creates one sensor entity per metric per scale device.
When multiple users share a scale, creates per-user sensor entities.
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

from .const import DOMAIN, METRICS, UNIT_IMPERIAL, KG_TO_LB, WEIGHT_KEYS
from .coordinator import RenphoHealthCoordinator

_LOGGER = logging.getLogger(__name__)

# Map metric unit strings to HA unit constants
UNIT_MAP: dict[str, str] = {
    "kg": UnitOfMass.KILOGRAMS,
    "lb": UnitOfMass.POUNDS,
    "%": PERCENTAGE,
    "kg/m²": "kg/m²",
    "kcal/day": "kcal/day",
    "bpm": "bpm",
    "level": "level",
    "years": "years",
}


def _safe_slug(value: str) -> str:
    """Create a safe slug from a string for entity IDs."""
    return value.replace(" ", "_").lower().replace("(", "").replace(")", "")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Renpho Health sensors from a config entry."""
    coordinator: RenphoHealthCoordinator = entry.runtime_data

    # Wait for first data fetch so we know what scales and users exist
    await coordinator.async_config_entry_first_refresh()

    entities: list[RenphoHealthSensor] = []

    data = coordinator.data
    if not data or not data.get("scales"):
        _LOGGER.warning("No Renpho Health sensor entities created — no scale data found")
        async_add_entities([])
        return

    # Detect multi-user: collect all distinct user IDs from measurements
    all_users: dict[str, str] = {}  # user_id -> user_name
    for scale in data["scales"]:
        for m in scale.get("measurements", []):
            uid = m.get("user_id", "")
            uname = m.get("user_name", "")
            if uid and uid not in all_users:
                all_users[uid] = uname

    multi_user = len(all_users) > 1

    # Also check the users dict from the API response
    users_from_api: dict[str, str] = data.get("users", {})
    if not all_users and users_from_api:
        # Fallback: use API-level user data
        all_users = users_from_api
        multi_user = len(users_from_api) > 1

    # Build lookups for measurements by (scale_name, user_id)
    measurements_by_scale_user: dict[tuple[str, str], dict] = {}
    for scale in data["scales"]:
        scale_name = scale.get("name", "Scale")
        for m in scale.get("measurements", []):
            uid = m.get("user_id", "")
            key = (scale_name, uid)
            if key not in measurements_by_scale_user:
                measurements_by_scale_user[key] = m

    # Determine which user+scale combinations to create entities for
    entity_configs: list[dict] = []

    for scale in data["scales"]:
        scale_name = scale.get("name", "Scale")
        scale_model = scale.get("model", "")
        scale_mac = scale.get("mac", "")
        table_name = scale.get("table_name", "")

        if multi_user and all_users:
            for user_id, user_name in all_users.items():
                entity_configs.append({
                    "scale_name": scale_name,
                    "scale_model": scale_model,
                    "scale_mac": scale_mac,
                    "table_name": table_name,
                    "user_id": user_id,
                    "user_name": user_name,
                })
        else:
            entity_configs.append({
                "scale_name": scale_name,
                "scale_model": scale_model,
                "scale_mac": scale_mac,
                "table_name": table_name,
                "user_id": "",
                "user_name": "",
            })

    for config in entity_configs:
        for key, name, unit, device_class_str, state_class_str, icon in METRICS:
            entities.append(
                RenphoHealthSensor(
                    coordinator=coordinator,
                    scale_name=config["scale_name"],
                    scale_model=config["scale_model"],
                    scale_mac=config["scale_mac"],
                    table_name=config["table_name"],
                    metric_key=key,
                    metric_name=name,
                    metric_unit=unit,
                    device_class_str=device_class_str,
                    state_class_str=state_class_str,
                    icon=icon,
                    user_id=config["user_id"],
                    user_name=config["user_name"],
                    multi_user=multi_user,
                )
            )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d Renpho Health sensor entities (%d users, %d scales)",
                      len(entities), len(all_users) or 1, len(data["scales"]))
    else:
        _LOGGER.warning("No Renpho Health sensor entities created")


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
        user_id: str = "",
        user_name: str = "",
        multi_user: bool = False,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._scale_name = scale_name
        self._metric_key = metric_key
        self._metric_name = metric_name
        self._metric_unit = metric_unit
        self._user_id = user_id
        self._user_name = user_name
        self._multi_user = multi_user

        # Entity identity
        safe_key = _safe_slug(metric_key)
        safe_scale = _safe_slug(scale_name)
        safe_user = _safe_slug(user_name) if user_name else ""

        # Unique ID includes user to prevent collisions
        # v2 suffix forces fresh entities (old ones had cached "kg" unit)
        if user_id:
            self._attr_unique_id = f"v2_{table_name}_{user_id}_{metric_key}"
            self.entity_id = f"sensor.renpho_{safe_scale}_{safe_user}_{safe_key}"
        else:
            self._attr_unique_id = f"v2_{table_name}_{metric_key}"
            self.entity_id = f"sensor.renpho_{safe_scale}_{safe_key}"

        self._attr_has_entity_name = True
        self._attr_icon = icon

        # Store the base metric unit — dynamic property below handles Imperial conversion
        self._base_metric_unit = metric_unit

        # Entity name — HA prepends device name ("Bathroom Scale") for friendly display
        # Multi-user: "Sam Weight" → "Bathroom Scale Sam Weight"
        # Single-user: "Weight" → "Bathroom Scale Weight"
        if user_name:
            self._attr_name = f"{user_name} {metric_name}"
        else:
            self._attr_name = metric_name

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

        # Device info — group by scale+user so each person has their own device
        if multi_user and user_id:
            device_ident = f"{table_name}_{scale_mac}_{user_id}"
            device_title = f"{scale_name} ({user_name})"
        else:
            device_ident = f"{table_name}_{scale_mac}"
            device_title = scale_name

        model_display = f"Renpho {scale_model}" if scale_model else "Renpho Smart Scale"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_ident)},
            name=device_title,
            manufacturer="Renpho",
            model=model_display,
            entry_type=DeviceEntryType.SERVICE,
            sw_version=scale_model if scale_model else None,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def _find_measurement(self) -> dict | None:
        """Find the latest measurement for this entity's scale and user."""
        if not self.coordinator.data:
            return None
        for scale in self.coordinator.data.get("scales", []):
            if scale.get("name") == self._scale_name:
                for m in scale.get("measurements", []):
                    # Match by user_id if set, otherwise take first
                    if self._user_id:
                        if m.get("user_id") == self._user_id:
                            return m
                    else:
                        return m
        return None

    @property
    def native_value(self) -> Any:
        """Return the current value of the sensor."""
        measurement = self._find_measurement()
        if measurement:
            val = measurement.get(self._metric_key)
            if val is not None and self.coordinator.unit_system == UNIT_IMPERIAL and self._metric_key in WEIGHT_KEYS:
                try:
                    val = round(float(val) * KG_TO_LB, 1)
                except (ValueError, TypeError):
                    pass
            return val
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit — dynamically checks Imperial/Metric setting."""
        unit = self._base_metric_unit
        if self.coordinator.unit_system == UNIT_IMPERIAL and self._metric_key in WEIGHT_KEYS:
            unit = "lb"
        return UNIT_MAP.get(unit, unit) if unit else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}
        measurement = self._find_measurement()
        if measurement:
            attrs["measured_at"] = measurement.get("measured_at")
            attrs["scale_name"] = self._scale_name
            if self._user_name:
                attrs["user_name"] = self._user_name
        if self.coordinator.data:
            for scale in self.coordinator.data.get("scales", []):
                if scale.get("name") == self._scale_name:
                    attrs["scale_model"] = scale.get("model", "")
                    break
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.native_value is not None
