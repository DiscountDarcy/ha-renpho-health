"""Renpho Health integration for Home Assistant.

Fetches body composition data from the Renpho Health cloud API
and exposes it as sensor entities.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import AuthError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import RenphoHealthCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renpho Health from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)

    coordinator = RenphoHealthCoordinator(
        hass,
        email=email,
        password=password,
        scan_interval_minutes=scan_interval,
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except AuthError as exc:
        raise ConfigEntryAuthFailed(f"Authentication failed: {exc}") from exc
    except Exception as exc:
        raise ConfigEntryNotReady(f"Failed to connect: {exc}") from exc

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register for options updates (e.g., scan interval change)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (e.g., scan interval changed)."""
    await hass.config_entries.async_reload(entry.entry_id)
