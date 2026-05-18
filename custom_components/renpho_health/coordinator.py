"""DataUpdateCoordinator for the Renpho Health integration.

Polls the Renpho Health cloud API on a configurable interval and
makes data available to sensor entities.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    fetch_all_data,
    AuthError,
    RenphoHealthAPIError,
    RateLimitError,
)
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL_MINUTES, MIN_SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class RenphoHealthCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch Renpho Health data."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        password: str,
        scan_interval_minutes: int = DEFAULT_SCAN_INTERVAL_MINUTES,
    ) -> None:
        """Initialize the coordinator."""
        self._email = email
        self._password = password
        self._scan_interval_minutes = max(scan_interval_minutes, MIN_SCAN_INTERVAL_MINUTES)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=self._scan_interval_minutes),
            always_update=True,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the Renpho Health API.

        Runs in the executor since renpho-api makes synchronous HTTP calls.
        """
        try:
            data = await self.hass.async_add_executor_job(
                fetch_all_data, self._email, self._password
            )
        except AuthError as exc:
            _LOGGER.error("Renpho Health authentication failed: %s", exc)
            raise UpdateFailed(f"Authentication failed: {exc}") from exc
        except RateLimitError as exc:
            _LOGGER.warning("Renpho Health rate limited: %s. Will retry.", exc)
            raise UpdateFailed(f"Rate limited: {exc}") from exc
        except RenphoHealthAPIError as exc:
            _LOGGER.error("Renpho Health API error: %s", exc)
            raise UpdateFailed(f"API error: {exc}") from exc
        except Exception as exc:
            _LOGGER.exception("Unexpected error fetching Renpho Health data")
            raise UpdateFailed(f"Unexpected error: {exc}") from exc

        if not data or not data.get("scales"):
            _LOGGER.debug("No scale data in Renpho Health response")

        return data

    @property
    def latest_measurement(self) -> dict[str, Any] | None:
        """Return the most recent measurement across all scales.

        Used for quick access to latest weight, BMI, etc.
        """
        if not self.data:
            return None
        scales = self.data.get("scales", [])
        if not scales:
            return None
        # Measurements are already sorted newest-first per scale
        primary = scales[0].get("measurements", [])
        return primary[0] if primary else None

    def measurement_for_entity(self, scale_name: str, metric_key: str) -> Any:
        """Get the value for a specific metric from the latest measurement.

        Returns None if no data available.
        """
        if not self.data:
            return None
        for scale in self.data.get("scales", []):
            if scale.get("name") == scale_name:
                measurements = scale.get("measurements", [])
                if measurements:
                    return measurements[0].get(metric_key)
        return None

    def all_metrics_for_scale(self, scale_name: str) -> dict[str, Any]:
        """Return all metrics from the latest measurement for a scale."""
        if not self.data:
            return {}
        for scale in self.data.get("scales", []):
            if scale.get("name") == scale_name:
                measurements = scale.get("measurements", [])
                return measurements[0] if measurements else {}
        return {}
