"""Tests for config flow."""

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.renpho_health import config_flow
from custom_components.renpho_health.config_flow import (
    RenphoHealthConfigFlow,
    RenphoHealthOptionsFlow,
    STEP_USER_DATA_SCHEMA,
)
from custom_components.renpho_health.const import (
    DOMAIN,
    UNIT_IMPERIAL,
    UNIT_METRIC,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_UNIT_SYSTEM,
)


class TestConfigFlowSchema:
    """Test the config flow schema validation."""

    def test_valid_input_minimal(self):
        """Schema should accept minimal valid input."""
        result = STEP_USER_DATA_SCHEMA({
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "mypassword",
        })
        assert result[CONF_EMAIL] == "test@example.com"
        assert result[CONF_PASSWORD] == "mypassword"
        # Defaults
        assert result["unit_system"] == DEFAULT_UNIT_SYSTEM
        assert result["scan_interval"] == DEFAULT_SCAN_INTERVAL_MINUTES

    def test_valid_input_full(self):
        """Schema should accept full input with all options."""
        result = STEP_USER_DATA_SCHEMA({
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "mypassword",
            "unit_system": UNIT_METRIC,
            "scan_interval": 30,
        })
        assert result["unit_system"] == UNIT_METRIC
        assert result["scan_interval"] == 30

    def test_missing_required_email(self):
        """Schema should reject missing email."""
        with pytest.raises(vol.Invalid):
            STEP_USER_DATA_SCHEMA({
                CONF_PASSWORD: "mypassword",
            })

    def test_missing_required_password(self):
        """Schema should reject missing password."""
        with pytest.raises(vol.Invalid):
            STEP_USER_DATA_SCHEMA({
                CONF_EMAIL: "test@example.com",
            })

    def test_scan_interval_too_low(self):
        """Schema should reject scan interval below minimum."""
        with pytest.raises(vol.Invalid):
            STEP_USER_DATA_SCHEMA({
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "mypassword",
                "scan_interval": 1,  # min is 5
            })

    def test_scan_interval_too_high(self):
        """Schema should reject scan interval above maximum."""
        with pytest.raises(vol.Invalid):
            STEP_USER_DATA_SCHEMA({
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "mypassword",
                "scan_interval": 10000,  # max is 1440
            })

    def test_invalid_unit_system(self):
        """Schema should reject invalid unit system."""
        with pytest.raises(vol.Invalid):
            STEP_USER_DATA_SCHEMA({
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "mypassword",
                "unit_system": "stone",
            })


class TestOptionsFlow:
    """Test the options flow."""

    def test_options_schema_defaults(self):
        """Options flow should show current values as defaults."""
        options_schema = vol.Schema(
            {
                vol.Optional("unit_system", default=UNIT_IMPERIAL): vol.In(
                    {UNIT_IMPERIAL: "Imperial (lbs)", UNIT_METRIC: "Metric (kg)"}
                ),
                vol.Optional("scan_interval", default=60): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=1440)
                ),
            }
        )
        result = options_schema({})
        assert result["unit_system"] == UNIT_IMPERIAL
        assert result["scan_interval"] == 60
