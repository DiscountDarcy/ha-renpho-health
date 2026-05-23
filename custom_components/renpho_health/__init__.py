"""Renpho Health integration for Home Assistant.

Fetches body composition data from the Renpho Health cloud API
and exposes it as sensor entities.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import AuthError
from .const import (
    CONF_UNIT_SYSTEM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_UNIT_SYSTEM,
    MIN_SCAN_INTERVAL_MINUTES,
)
from .coordinator import RenphoHealthCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate a config entry to a newer version.

    Called by HA when the config entry's stored version differs from the
    config flow class VERSION. Standalone function required in HA 2026.x+.
    """
    _LOGGER.debug(
        "Migrating Renpho Health config entry from version %s",
        config_entry.version,
    )

    if config_entry.version == 1:
        # v1 → v2: Added unit_system option
        new_data = {**config_entry.data}
        if CONF_UNIT_SYSTEM not in new_data:
            new_data[CONF_UNIT_SYSTEM] = DEFAULT_UNIT_SYSTEM
        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            version=2,
        )
        _LOGGER.info(
            "Migrated Renpho Health config entry to version 2 (added unit_system=%s)",
            DEFAULT_UNIT_SYSTEM,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renpho Health from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    unit_system = entry.options.get(
        CONF_UNIT_SYSTEM,
        entry.data.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM),
    )

    coordinator = RenphoHealthCoordinator(
        hass,
        email=email,
        password=password,
        scan_interval_minutes=scan_interval,
        unit_system=unit_system,
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except AuthError as exc:
        raise ConfigEntryAuthFailed(f"Authentication failed: {exc}") from exc
    except Exception as exc:
        raise ConfigEntryNotReady(f"Failed to connect: {exc}") from exc

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register for options updates (e.g., scan interval change)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — update coordinator unit and trigger refresh."""
    coordinator: RenphoHealthCoordinator | None = entry.runtime_data
    if coordinator is not None:
        new_unit = entry.options.get(
            CONF_UNIT_SYSTEM,
            entry.data.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM),
        )
        new_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        if coordinator.unit_system != new_unit:
            coordinator.unit_system = new_unit
            # Force sensor values to recalculate immediately
            coordinator.async_update_listeners()
        # Update interval — reload to recreate coordinator with new timing
        coordinator.update_interval = timedelta(minutes=max(new_interval, MIN_SCAN_INTERVAL_MINUTES))
    else:
        await hass.config_entries.async_reload(entry.entry_id)
