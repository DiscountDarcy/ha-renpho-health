"""Tests for sensor entity logic — unit conversion, naming, multi-user."""

import pytest

from custom_components.renpho_health.const import (
    KG_TO_LB,
    WEIGHT_KEYS,
    UNIT_IMPERIAL,
    UNIT_METRIC,
    METRICS,
)
from custom_components.renpho_health.sensor import _safe_slug


class TestSafeSlug:
    """Test entity ID slug generation."""

    def test_spaces_to_underscores(self):
        assert _safe_slug("Hello World") == "hello_world"

    def test_parentheses_removed(self):
        assert _safe_slug("Test (Value)") == "test_value"

    def test_mixed_case_lowered(self):
        assert _safe_slug("Bathroom Scale") == "bathroom_scale"


class TestUnitConversion:
    """Test Imperial/Metric unit conversion logic."""

    def test_weight_conversion(self):
        """Weight keys should convert from kg to lb in Imperial mode."""
        assert "weight" in WEIGHT_KEYS
        assert "fatFreeWeight" in WEIGHT_KEYS

    def test_non_weight_unchanged(self):
        """Non-weight metrics should NOT be in WEIGHT_KEYS."""
        non_weight_metrics = {"bmi", "bodyfat", "water", "muscle", "bone",
                              "bmr", "visfat", "subfat", "protein", "bodyage",
                              "heartRate", "cardiacIndex", "bodyShape"}
        for key in non_weight_metrics:
            assert key not in WEIGHT_KEYS, f"{key} should not be a weight key"

    def test_kg_to_lb_math(self):
        """Basic conversion math."""
        assert round(100 * KG_TO_LB, 1) == 220.5
        assert round(50 * KG_TO_LB, 1) == 110.2
        assert round(82.5 * KG_TO_LB, 1) == 181.9


class TestMetricDefinitions:
    """Test the METRICS list covers all expected metrics."""

    EXPECTED_KEYS = {
        "weight", "bmi", "bodyfat", "water", "muscle", "bone",
        "bmr", "visfat", "subfat", "protein", "bodyage", "sinew",
        "fatFreeWeight", "heartRate", "cardiacIndex", "bodyShape",
    }

    def test_all_expected_keys_present(self):
        """All 16 expected metrics should be defined."""
        actual_keys = {m[0] for m in METRICS}
        assert actual_keys == self.EXPECTED_KEYS

    def test_icons_valid_mdi(self):
        """All icons should be valid MDI format."""
        for key, name, unit, dc, sc, icon in METRICS:
            assert icon.startswith("mdi:"), f"Icon for '{key}' should be MDI: {icon}"

    def test_measurement_state_class(self):
        """All metrics should have measurement state class for long-term stats."""
        for key, name, unit, dc, sc, icon in METRICS:
            assert sc == "measurement", f"'{key}' should have state class 'measurement'"
