"""Tests for the API wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.renpho_health.api import (
    validate_credentials,
    fetch_all_data,
    AuthError,
    RenphoHealthAPIError,
    RateLimitError,
    _fetch_family_members,
    _get_user_name,
    _normalize_measurements,
)
from tests.conftest import (
    SAMPLE_MEASUREMENTS,
    SAMPLE_DEVICE_INFO,
    SAMPLE_FAMILY,
    _create_mock_client,
    _mock_renpho,
)


class TestValidateCredentials:
    """Test credential validation."""

    def test_valid_credentials(self, mock_client):
        """Should return user data on successful login."""
        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            result = validate_credentials("test@example.com", "testpass")
            assert result["user_id"] == "12345"
            assert result["token"] == "mock-token-abc123"
            assert result["user_info"]["accountName"] == "Test User"

    def test_invalid_credentials(self):
        """Should raise AuthError when login fails with auth-related message."""
        mock_client = MagicMock()
        mock_client.login = MagicMock(side_effect=_mock_renpho.RenphoAPIError("invalid password"))

        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            with pytest.raises(AuthError, match="Invalid credentials"):
                validate_credentials("bad@example.com", "wrongpass")

    def test_missing_token(self):
        """Should raise AuthError if login succeeds but no token."""
        mock_client = MagicMock()
        mock_client.login = MagicMock(return_value={})
        mock_client.token = None
        mock_client.user_id = None

        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            with pytest.raises(AuthError, match="no token/user_id"):
                validate_credentials("test@example.com", "testpass")


class TestFetchAllData:
    """Test fetching all measurement data."""

    def test_fetch_single_user(self, mock_client):
        """Should return organized scale data for single user."""
        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            result = fetch_all_data("test@example.com", "testpass")
            assert result["user_id"] == "12345"
            assert len(result["scales"]) == 1
            assert result["scales"][0]["name"] == "Bathroom Scale"
            assert result["scales"][0]["model"] == "ES-26M"
            assert len(result["scales"][0]["measurements"]) == 2  # newest first

    def test_measurements_sorted_newest_first(self, mock_client):
        """Should sort measurements with newest first."""
        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            result = fetch_all_data("test@example.com", "testpass")
            measurements = result["scales"][0]["measurements"]
            ts0 = measurements[0]["time_stamp"]
            ts1 = measurements[1]["time_stamp"]
            assert ts0 > ts1, "Measurements should be sorted newest-first"

    def test_rate_limit_error(self):
        """Should raise RateLimitError on 429."""
        mock_client = MagicMock()
        mock_client.get_all_measurements = MagicMock(
            side_effect=_mock_renpho.RenphoAPIError("429 Too Many Requests")
        )

        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            with pytest.raises(RateLimitError):
                fetch_all_data("test@example.com", "testpass")

    def test_empty_measurements(self, mock_client):
        """Should return empty scales list when no measurements."""
        mock_client.get_all_measurements = MagicMock(return_value=[])

        with patch("custom_components.renpho_health.api.RenphoClient", return_value=mock_client):
            result = fetch_all_data("test@example.com", "testpass")
            assert result["scales"] == []
            assert result["user_id"] == "12345"


class TestNormalizeMeasurements:
    """Test measurement normalization."""

    def test_numeric_conversion(self):
        """Should convert string values to floats."""
        raw = [
            {"weight": "82.5", "bmi": "24.8", "time_stamp": 1715550000}
        ]
        normalized = _normalize_measurements(raw, "Test Scale")
        assert isinstance(normalized[0]["weight"], float)
        assert normalized[0]["weight"] == 82.5

    def test_iso_timestamp(self):
        """Should convert unix timestamp to ISO 8601."""
        raw = [{"time_stamp": 1715550000}]
        normalized = _normalize_measurements(raw, "Test Scale")
        assert "measured_at" in normalized[0]
        assert "T" in normalized[0]["measured_at"]  # ISO format

    def test_scale_name_injected(self):
        """Should inject scale_name into each measurement."""
        raw = [{"time_stamp": 1715550000}]
        normalized = _normalize_measurements(raw, "Bathroom Scale")
        assert normalized[0]["scale_name"] == "Bathroom Scale"

    def test_none_values_preserved(self):
        """Should handle None values gracefully."""
        raw = [{"weight": None, "time_stamp": 1715550000}]
        normalized = _normalize_measurements(raw, "Test Scale")
        assert normalized[0]["weight"] is None


class TestFamilyMembers:
    """Test family member fetching."""

    def test_get_user_name_self(self):
        """Should return authenticated user's name."""
        client = _create_mock_client()
        name = _get_user_name(client, "12345", {})
        assert name == "Test User"

    def test_get_user_name_family(self):
        """Should return family member's name when in family dict."""
        client = _create_mock_client()
        family = {"67890": "Jack"}
        name = _get_user_name(client, "67890", family)
        assert name == "Jack"

    def test_get_user_name_unknown(self):
        """Should return empty string for unknown user."""
        client = _create_mock_client()
        name = _get_user_name(client, "99999", {})
        assert name == ""
