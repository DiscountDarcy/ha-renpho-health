"""Config flow for the Renpho Health integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import validate_credentials, AuthError, RenphoHealthAPIError
from .const import (
    DOMAIN,
    CONF_UNIT_SYSTEM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_UNIT_SYSTEM,
    MIN_SCAN_INTERVAL_MINUTES,
    UNIT_IMPERIAL,
    UNIT_METRIC,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(
            CONF_UNIT_SYSTEM, default=DEFAULT_UNIT_SYSTEM
        ): vol.In({UNIT_IMPERIAL: "Imperial (lbs)", UNIT_METRIC: "Metric (kg)"}),
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_MINUTES
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=1440)),
    }
)


class RenphoHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renpho Health."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
            unit_system = user_input.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM)

            # Validate credentials
            try:
                user_data = await self.hass.async_add_executor_job(
                    validate_credentials, email, password
                )
            except AuthError:
                errors["base"] = "invalid_auth"
            except RenphoHealthAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(f"renpho_{email}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Renpho Health ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_UNIT_SYSTEM: unit_system,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return RenphoHealthOptionsFlow(config_entry)


class RenphoHealthOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Renpho Health."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # Parent OptionsFlow already stores config_entry — don't reassign
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        current_unit = self.config_entry.options.get(
            CONF_UNIT_SYSTEM,
            self.config_entry.data.get(CONF_UNIT_SYSTEM, DEFAULT_UNIT_SYSTEM),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UNIT_SYSTEM,
                    default=current_unit,
                ): vol.In({UNIT_IMPERIAL: "Imperial (lbs)", UNIT_METRIC: "Metric (kg)"}),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_interval,
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=1440)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
