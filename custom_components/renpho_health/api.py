"""API wrapper for the Renpho Health cloud API.

Wraps the synchronous renpho-api library for use with Home Assistant's
async executor, translating exceptions into HA-compatible errors.
"""

from __future__ import annotations

import logging
from typing import Any

from renpho import RenphoClient, RenphoAPIError

_LOGGER = logging.getLogger(__name__)


class RenphoHealthAPIError(Exception):
    """Base exception for Renpho Health API errors."""


class AuthError(RenphoHealthAPIError):
    """Authentication failed (bad credentials, account locked, etc.)."""


class RateLimitError(RenphoHealthAPIError):
    """API rate limit exceeded."""


class ConnectionError_(RenphoHealthAPIError):
    """Network or connection error."""


async def validate_credentials(email: str, password: str) -> dict[str, Any]:
    """Test credentials by logging in and returning user info.

    Raises:
        AuthError: If credentials are invalid.
        RenphoHealthAPIError: On other failures.
    """
    try:
        client = RenphoClient(email, password)
        user_data = client.login()
        if not client.token or not client.user_id:
            raise AuthError("Login succeeded but no token/user_id returned")
        return {
            "user_id": client.user_id,
            "user_info": client.user_info or {},
            "token": client.token,
        }
    except RenphoAPIError as exc:
        msg = str(exc).lower()
        if any(kw in msg for kw in ("password", "credential", "auth", "login", "unauthorized", "not found")):
            raise AuthError(f"Invalid credentials: {exc}") from exc
        raise RenphoHealthAPIError(f"API error during login: {exc}") from exc


async def fetch_all_data(email: str, password: str) -> dict[str, Any]:
    """Fetch all measurements from all scales on the account.

    Returns:
        {
            "user_id": str,
            "scales": [
                {
                    "name": str,
                    "table_name": str,
                    "model": str,
                    "mac": str,
                    "measurements": [
                        {
                            "weight": float,
                            "bmi": float,
                            "bodyfat": float,
                            ...
                            "time_stamp": int (Unix timestamp),
                            "measured_at": str (ISO 8601),
                            "scale_name": str,
                        },
                        ...
                    ],
                },
                ...
            ],
        }

    Raises:
        AuthError: If credentials are invalid.
        RenphoHealthAPIError: On other failures.
    """
    try:
        client = RenphoClient(email, password)
        all_measurements = client.get_all_measurements()
    except RenphoAPIError as exc:
        msg = str(exc).lower()
        if any(kw in msg for kw in ("password", "credential", "auth", "login", "unauthorized")):
            raise AuthError(f"Invalid credentials: {exc}") from exc
        if "rate" in msg or "too many" in msg or "429" in msg:
            raise RateLimitError(f"Rate limited: {exc}") from exc
        raise RenphoHealthAPIError(f"API error fetching data: {exc}") from exc

    if not all_measurements:
        _LOGGER.warning("No measurements returned from Renpho Health API")
        return {"user_id": client.user_id, "scales": []}

    # Get device info for scale metadata
    try:
        device_info = client.get_device_info()
    except Exception:
        _LOGGER.warning("Could not fetch device info, continuing without it")
        device_info = {}

    scales_meta = {s.get("tableName"): s for s in device_info.get("scale", [])}

    # Organize measurements by scale
    scales = []
    seen_tables: dict[str, list[dict]] = {}

    for m in all_measurements:
        table = m.get("tableName", "unknown")
        if table not in seen_tables:
            seen_tables[table] = []
        seen_tables[table].append(m)

    for table_name, measurements in seen_tables.items():
        meta = scales_meta.get(table_name, {})
        # Sort by timestamp descending (newest first)
        measurements.sort(key=lambda x: x.get("time_stamp", 0), reverse=True)

        scale_entry = {
            "name": meta.get("scaleName", f"Scale ({table_name})"),
            "table_name": table_name,
            "model": meta.get("internalModel", ""),
            "mac": meta.get("mac", ""),
            "measurements": _normalize_measurements(measurements, meta.get("scaleName", "Renpho Scale")),
        }
        scales.append(scale_entry)

    return {
        "user_id": client.user_id,
        "user_info": client.user_info or {},
        "scales": scales,
    }


def _normalize_measurements(measurements: list[dict], scale_name: str) -> list[dict]:
    """Normalize measurement dicts: add computed fields, convert types."""
    result = []
    for m in measurements:
        ts = m.get("time_stamp")
        normalized = dict(m)
        normalized["scale_name"] = scale_name
        # Convert timestamp to ISO 8601 if present
        if ts:
            from datetime import datetime, timezone

            try:
                dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                normalized["measured_at"] = dt.isoformat()
            except (ValueError, OSError):
                normalized["measured_at"] = str(ts)

        # Ensure numeric fields are floats
        for field in (
            "weight", "bmi", "bodyfat", "water", "muscle", "bone",
            "bmr", "visfat", "subfat", "protein", "bodyage", "sinew",
            "fatFreeWeight", "heartRate", "cardiacIndex",
        ):
            if field in normalized and normalized[field] is not None:
                try:
                    normalized[field] = float(normalized[field])
                except (ValueError, TypeError):
                    pass

        result.append(normalized)
    return result
