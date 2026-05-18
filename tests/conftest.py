"""Test fixtures and mocks for Renpho Health integration tests."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock the renpho module before any imports happen
_mock_renpho = MagicMock()
_mock_renpho.RenphoClient = MagicMock()
_mock_renpho.RenphoAPIError = type("RenphoAPIError", (Exception,), {})
_mock_renpho.constants = MagicMock()
_mock_renpho.constants.ENDPOINTS = {"family": "/v3/family/list"}
_mock_renpho.crypto = MagicMock()
_mock_renpho.crypto.encrypt_request = MagicMock(return_value={"data": "encrypted"})
_mock_renpho.crypto.decrypt_response = MagicMock(return_value=[])

sys.modules["renpho"] = _mock_renpho
sys.modules["renpho.constants"] = _mock_renpho.constants
sys.modules["renpho.crypto"] = _mock_renpho.crypto


def _create_mock_client(email="test@example.com", password="testpass"):
    """Create a mock RenphoClient with realistic attributes."""
    client = MagicMock()
    client.email = email
    client.password = password
    client.token = "mock-token-abc123"
    client.user_id = "12345"
    client.user_info = {
        "id": 12345,
        "accountName": "Test User",
        "email": email,
    }
    client.login = MagicMock(return_value=client.user_info)
    client.get_all_measurements = MagicMock(return_value=SAMPLE_MEASUREMENTS)
    client.get_device_info = MagicMock(return_value=SAMPLE_DEVICE_INFO)
    return client


# Sample data matching real Renpho Health API responses
SAMPLE_MEASUREMENTS = [
    {
        "tableName": "A1B2C3D4E5F6",
        "userId": 12345,
        "time_stamp": 1715550000,
        "weight": 82.5,
        "bmi": 24.8,
        "bodyfat": 22.3,
        "water": 55.2,
        "muscle": 42.1,
        "bone": 4.2,
        "bmr": 1780,
        "visfat": 8,
        "subfat": 18.5,
        "protein": 16.8,
        "bodyage": 35,
        "sinew": 64.1,
        "fatFreeWeight": 64.1,
        "heartRate": 72,
        "cardiacIndex": 3.2,
        "bodyShape": 3,
    },
    {
        "tableName": "A1B2C3D4E5F6",
        "userId": 12345,
        "time_stamp": 1715463600,
        "weight": 82.8,
        "bmi": 24.9,
        "bodyfat": 22.5,
        "water": 55.0,
        "muscle": 42.0,
        "bone": 4.2,
        "bmr": 1775,
        "visfat": 8,
        "subfat": 18.7,
        "protein": 16.7,
        "bodyage": 35,
        "sinew": 64.0,
        "fatFreeWeight": 64.0,
        "heartRate": 70,
        "cardiacIndex": 3.1,
        "bodyShape": 3,
    },
]

SAMPLE_DEVICE_INFO = {
    "scale": [
        {
            "tableName": "A1B2C3D4E5F6",
            "scaleName": "Bathroom Scale",
            "internalModel": "ES-26M",
            "mac": "AA:BB:CC:DD:EE:FF",
        }
    ]
}

# Multi-user sample data
SAMPLE_MEASUREMENTS_MULTI_USER = [
    {
        "tableName": "A1B2C3D4E5F6",
        "userId": 12345,
        "time_stamp": 1715550000,
        "weight": 82.5,
        "bmi": 24.8,
        "bodyfat": 22.3,
        "water": 55.2,
        "muscle": 42.1,
        "bone": 4.2,
        "bmr": 1780,
        "visfat": 8,
        "subfat": 18.5,
        "protein": 16.8,
        "bodyage": 35,
        "sinew": 64.1,
        "fatFreeWeight": 64.1,
        "heartRate": 72,
        "cardiacIndex": 3.2,
        "bodyShape": 3,
    },
    {
        "tableName": "A1B2C3D4E5F6",
        "userId": 67890,
        "time_stamp": 1715550100,
        "weight": 65.0,
        "bmi": 22.1,
        "bodyfat": 28.5,
        "water": 52.0,
        "muscle": 38.5,
        "bone": 3.8,
        "bmr": 1450,
        "visfat": 5,
        "subfat": 24.0,
        "protein": 15.5,
        "bodyage": 30,
        "sinew": 46.5,
        "fatFreeWeight": 46.5,
        "heartRate": 68,
        "cardiacIndex": 2.8,
        "bodyShape": 2,
    },
]

SAMPLE_FAMILY = [
    {"userId": 12345, "nickName": "Sam"},
    {"userId": 67890, "nickName": "Jack"},
]


@pytest.fixture
def mock_client():
    """Fixture providing a mock RenphoClient."""
    return _create_mock_client()


@pytest.fixture
def mock_client_multi_user():
    """Fixture providing a mock RenphoClient with multi-user data."""
    client = _create_mock_client()
    client.get_all_measurements = MagicMock(return_value=SAMPLE_MEASUREMENTS_MULTI_USER)
    return client
