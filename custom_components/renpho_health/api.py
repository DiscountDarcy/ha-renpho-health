"""API wrapper for the Renpho Health cloud API.

Wraps the synchronous renpho-api library for use with Home Assistant's
async executor, translating exceptions into HA-compatible errors.
"""

from __future__ import annotations

import logging
from typing import Any

from renpho import RenphoClient, RenphoAPIError
from renpho.constants import ENDPOINTS
from renpho.crypto import encrypt_request

_LOGGER = logging.getLogger(__name__)


class RenphoHealthAPIError(Exception):
    """Base exception for Renpho Health API errors."""


class AuthError(RenphoHealthAPIError):
    """Authentication failed (bad credentials, account locked, etc.)."""


class RateLimitError(RenphoHealthAPIError):
    """API rate limit exceeded."""


class ConnectionError_(RenphoHealthAPIError):
    """Network or connection error."""


def validate_credentials(email: str, password: str) -> dict[str, Any]:
    """Test credentials by logging in and returning user info.

    This is a synchronous function — call via hass.async_add_executor_job.

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


def _fetch_family_members(client: RenphoClient) -> dict[str, str]:
    """Fetch family members from the Renpho Health API.

    Returns a dict mapping user_id -> display_name.
    Falls back gracefully if the endpoint is unavailable.
    """
    try:
        body = encrypt_request({})
        result = client._post(ENDPOINTS["family"], body)
        from renpho.crypto import decrypt_response
        data = result.get("data", "")
        if not data:
            return {}
        members = decrypt_response(data) if isinstance(data, str) else data
        family: dict[str, str] = {}
        for member in members if isinstance(members, list) else members.get("list", []):
            uid = str(member.get("userId", member.get("id", "")))
            name = member.get("nickName", member.get("name", ""))
            if uid and name:
                family[uid] = name
        return family
    except Exception:
        _LOGGER.debug("Could not fetch family members, using single-user mode", exc_info=True)
        return {}


def _get_user_name(client: RenphoClient, user_id: str, family: dict[str, str]) -> str:
    """Get the display name for a user ID."""
    if user_id in family:
        return family[user_id]
    user_info = client.user_info or {}
    if str(user_info.get("id", "")) == str(user_id):
        return user_info.get("accountName", user_info.get("name", ""))
    return ""


def fetch_all_data(email: str, password: str) -> dict[str, Any]:
    """Fetch all measurements from all scales on the account.

    This is a synchronous function — call via hass.async_add_executor_job.

    Returns:
        {
            "user_id": str,
            "user_info": dict,
            "users": {user_id: display_name, ...},  # All users on account
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
                            ...
                            "time_stamp": int,
                            "measured_at": str (ISO 8601),
                            "scale_name": str,
                            "user_id": str,
                            "user_name": str,
                        },
                    ],
                },
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
        return {
            "user_id": client.user_id,
            "user_info": client.user_info or {},
            "users": {},
            "scales": [],
        }

    # Fetch family members for multi-user support
    family = _fetch_family_members(client)

    # If no family data, at least map the authenticated user
    users: dict[str, str] = dict(family)
    auth_name = client.user_info.get("accountName", "") if client.user_info else ""
    if client.user_id and client.user_id not in users and auth_name:
        users[str(client.user_id)] = auth_name

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
        # Tag with user identity
        uid = str(m.get("userId", m.get("user_id", client.user_id or "")))
        m["_user_id"] = uid
        m["_user_name"] = _get_user_name(client, uid, family)
        seen_tables[table].append(m)

    for table_name, measurements in seen_tables.items():
        meta = scales_meta.get(table_name, {})
        measurements.sort(key=lambda x: x.get("time_stamp", 0), reverse=True)

        scale_entry = {
            "name": meta.get("scaleName") or "Scale",
            "table_name": table_name,
            "model": meta.get("internalModel", ""),
            "mac": meta.get("mac", ""),
            "measurements": _normalize_measurements(measurements, meta.get("scaleName") or "Renpho Scale"),
        }
        scales.append(scale_entry)

    return {
        "user_id": client.user_id,
        "user_info": client.user_info or {},
        "users": users,
        "scales": scales,
    }


def _normalize_measurements(measurements: list[dict], scale_name: str) -> list[dict]:
    """Normalize measurement dicts: add computed fields, convert types."""
    result = []
    for m in measurements:
        ts = m.get("time_stamp")
        normalized = dict(m)
        normalized["scale_name"] = scale_name
        # Pull user identity from our internal tags
        normalized["user_id"] = m.get("_user_id", "")
        normalized["user_name"] = m.get("_user_name", "")
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
