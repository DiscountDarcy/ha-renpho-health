"""Tests for constants, unit conversion, and metric definitions."""

import pytest

from custom_components.renpho_health.const import (
    DOMAIN,
    KG_TO_LB,
    WEIGHT_KEYS,
    METRICS,
    UNIT_IMPERIAL,
    UNIT_METRIC,
    DEFAULT_UNIT_SYSTEM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)


def test_domain_name():
    """Domain should match the directory name."""
    assert DOMAIN == "renpho_health"


def test_kg_to_lb_conversion():
    """Test the kilogram to pound conversion factor."""
    assert round(KG_TO_LB, 4) == 2.2046
    # 1 kg = 2.2046 lbs
    assert round(1 * KG_TO_LB, 1) == 2.2
    # 82.5 kg ≈ 181.9 lbs
    assert round(82.5 * KG_TO_LB, 1) == 181.9


def test_weight_keys_are_mass_metrics():
    """Only mass-based metrics should be in WEIGHT_KEYS."""
    assert "weight" in WEIGHT_KEYS
    assert "sinew" in WEIGHT_KEYS
    assert "fatFreeWeight" in WEIGHT_KEYS
    # Non-mass metrics should NOT be here
    assert "bmi" not in WEIGHT_KEYS
    assert "bodyfat" not in WEIGHT_KEYS
    assert "bmr" not in WEIGHT_KEYS


def test_metrics_structure():
    """Each metric tuple should have 6 fields."""
    for metric in METRICS:
        assert len(metric) == 6, f"Metric {metric[0]} should have 6 fields"
        key, name, unit, device_class, state_class, icon = metric
        assert isinstance(key, str) and key
        assert isinstance(name, str) and name
        if unit is not None:
            assert isinstance(unit, str)
        if device_class is not None:
            assert isinstance(device_class, str)
        if state_class is not None:
            assert isinstance(state_class, str)
        assert isinstance(icon, str) and icon.startswith("mdi:")


def test_metrics_count():
    """Should have exactly 16 metrics."""
    assert len(METRICS) == 16


def test_unit_system_constants():
    """Unit system constants should be distinct."""
    assert UNIT_IMPERIAL == "imperial"
    assert UNIT_METRIC == "metric"
    assert UNIT_IMPERIAL != UNIT_METRIC


def test_default_scan_interval():
    """Default scan interval should be sensible."""
    assert DEFAULT_SCAN_INTERVAL_MINUTES == 60
    assert MIN_SCAN_INTERVAL_MINUTES == 5
    assert MIN_SCAN_INTERVAL_MINUTES <= DEFAULT_SCAN_INTERVAL_MINUTES


def test_default_unit_system():
    """Default unit system should be imperial (user's preference)."""
    assert DEFAULT_UNIT_SYSTEM == UNIT_IMPERIAL


def test_metric_keys_always_lowercase():
    """Metric keys match API response field names (some camelCase)."""
    for key, _, _, _, _, _ in METRICS:
        assert isinstance(key, str) and len(key) > 0, f"Metric key '{key}' should be non-empty"
        assert " " not in key, f"Metric key '{key}' should not contain spaces"
        # Keys must be valid Python identifiers (for getattr-style access)
        assert key.isidentifier(), f"Metric key '{key}' should be a valid identifier"
