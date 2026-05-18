"""Tests for coordinator and integration setup.

Note: These tests mock out DataUpdateCoordinator.__init__ since the
pytest-homeassistant-custom-component test harness requires a full
HA event loop with frame helpers. The actual coordinator behavior
is tested in the API and sensor test suites.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.renpho_health.const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    UNIT_IMPERIAL,
    UNIT_METRIC,
)


class TestCoordinator:
    """Test the RenphoHealthCoordinator."""

    @pytest.fixture
    def mock_parent_init(self):
        """Prevent DataUpdateCoordinator.__init__ from running."""
        with patch(
            "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
            return_value=None,
        ):
            from custom_components.renpho_health.coordinator import RenphoHealthCoordinator
            yield RenphoHealthCoordinator

    def test_init_defaults(self, mock_parent_init):
        """Coordinator should initialize with correct defaults."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(
            hass,
            email="test@example.com",
            password="testpass",
        )
        assert coordinator._email == "test@example.com"
        assert coordinator._password == "testpass"
        assert coordinator.unit_system == UNIT_IMPERIAL
        assert coordinator._scan_interval_minutes == DEFAULT_SCAN_INTERVAL_MINUTES

    def test_init_custom_interval(self, mock_parent_init):
        """Coordinator should respect custom scan interval."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(
            hass,
            email="test@example.com",
            password="testpass",
            scan_interval_minutes=30,
        )
        assert coordinator._scan_interval_minutes == 30

    def test_init_below_min_interval(self, mock_parent_init):
        """Coordinator should clamp scan interval to minimum."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(
            hass,
            email="test@example.com",
            password="testpass",
            scan_interval_minutes=1,
        )
        assert coordinator._scan_interval_minutes == 5  # Min is 5

    def test_init_metric_unit(self, mock_parent_init):
        """Coordinator should accept metric unit system."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(
            hass,
            email="test@example.com",
            password="testpass",
            unit_system=UNIT_METRIC,
        )
        assert coordinator.unit_system == UNIT_METRIC

    def test_latest_measurement_empty(self, mock_parent_init):
        """Should return None when no data."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(hass, "test@example.com", "testpass")
        coordinator.data = None
        assert coordinator.latest_measurement is None

    def test_latest_measurement_with_data(self, mock_parent_init):
        """Should return most recent measurement."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(hass, "test@example.com", "testpass")
        coordinator.data = {
            "scales": [
                {
                    "name": "Bathroom Scale",
                    "measurements": [
                        {"weight": 82.5, "bmi": 24.8},
                        {"weight": 82.8, "bmi": 24.9},
                    ],
                }
            ]
        }
        latest = coordinator.latest_measurement
        assert latest is not None
        assert latest["weight"] == 82.5  # first = newest

    def test_measurement_for_entity(self, mock_parent_init):
        """Should look up metric by scale name and key."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(hass, "test@example.com", "testpass")
        coordinator.data = {
            "scales": [
                {
                    "name": "Bathroom Scale",
                    "measurements": [{"weight": 82.5, "bmi": 24.8}],
                }
            ]
        }
        assert coordinator.measurement_for_entity("Bathroom Scale", "weight") == 82.5
        assert coordinator.measurement_for_entity("Bathroom Scale", "bmi") == 24.8
        assert coordinator.measurement_for_entity("NonExistent", "weight") is None

    def test_all_metrics_for_scale(self, mock_parent_init):
        """Should return all metrics for a given scale."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(hass, "test@example.com", "testpass")
        coordinator.data = {
            "scales": [
                {
                    "name": "Bathroom Scale",
                    "measurements": [{"weight": 82.5, "bmi": 24.8, "bodyfat": 22.3}],
                }
            ]
        }
        metrics = coordinator.all_metrics_for_scale("Bathroom Scale")
        assert metrics["weight"] == 82.5
        assert metrics["bmi"] == 24.8

    def test_all_metrics_empty(self, mock_parent_init):
        """Should return empty dict when no data."""
        RenphoHealthCoordinator = mock_parent_init
        hass = MagicMock()
        coordinator = RenphoHealthCoordinator(hass, "test@example.com", "testpass")
        coordinator.data = None
        assert coordinator.all_metrics_for_scale("Any") == {}


class TestErrorGuards:
    """Guard against accidentally logging credentials."""

    def test_api_error_no_password_leak(self):
        """AuthError message should not expose raw credentials."""
        from custom_components.renpho_health.api import AuthError
        err = AuthError("Invalid credentials")
        assert "password" not in str(err).lower()
        assert "secret" not in str(err).lower()
