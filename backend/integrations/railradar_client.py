"""
RailRadar API Client (backend/integrations/railradar_client.py)
Direct client communicating with the RailRadar Live Railway API.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class RailRadarAPIError(Exception):
    """Base exception for RailRadar API errors."""
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class RailRadarAuthError(RailRadarAPIError):
    """401 Authentication Failure."""
    def __init__(self, message: str = "RailRadar authentication failed. Check the configured API key."):
        super().__init__(401, message)


class RailRadarNotFoundError(RailRadarAPIError):
    """404 Not Found."""
    def __init__(self, message: str = "Train or railway resource not found on RailRadar."):
        super().__init__(404, message)


class RailRadarRateLimitError(RailRadarAPIError):
    """429 Rate Limit Exceeded."""
    def __init__(self, message: str = "RailRadar API rate limit reached. Please wait for the next refresh."):
        super().__init__(429, message)


class RailRadarServiceError(RailRadarAPIError):
    """503 Service Unavailable."""
    def __init__(self, message: str = "RailRadar service temporarily unavailable."):
        super().__init__(503, message)


class RailRadarClient:
    """
    HTTP Client for RailRadar API.
    Sends Authorization: Bearer <API_KEY>
    Provides endpoints for live train status, schedules, and train search.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or os.getenv("RAILRADAR_API_BASE_URL", "https://api.railradar.in")).rstrip("/")
        self.api_key = api_key or os.getenv("RAILRADAR_API_KEY", "").strip()
        try:
            self.timeout = float(timeout or os.getenv("RAILRADAR_API_TIMEOUT", "10"))
        except ValueError:
            self.timeout = 10.0

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid-looking API key is configured."""
        return bool(self.api_key and not self.api_key.startswith("<") and len(self.api_key) > 5)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "RailMind-Intelligence-Engine/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        status = response.status_code
        if status == 401:
            logger.error("RailRadar 401: Authentication failed. Verify RAILRADAR_API_KEY.")
            raise RailRadarAuthError()
        elif status == 404:
            logger.warning(f"RailRadar 404: Resource not found for URL {response.url}")
            raise RailRadarNotFoundError()
        elif status == 429:
            logger.warning("RailRadar 429: Rate limit hit.")
            raise RailRadarRateLimitError()
        elif status == 503 or status == 502 or status == 504:
            logger.error(f"RailRadar {status}: Service unavailable.")
            raise RailRadarServiceError()
        elif status >= 400:
            logger.error(f"RailRadar HTTP error {status}: {response.text}")
            raise RailRadarAPIError(status, f"RailRadar API error ({status}): {response.text[:200]}")

        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse RailRadar JSON response: {e}")
            raise RailRadarAPIError(status, "Invalid JSON received from RailRadar")

    async def get_live_train_status(self, train_number: str) -> Dict[str, Any]:
        """
        GET /v1/trains/{number}/live
        Returns live train status, delay, current location, and expected arrival/departure.
        """
        if not self.is_configured:
            raise RailRadarAuthError("RailRadar API key is not configured. Set RAILRADAR_API_KEY in .env.")

        url = f"{self.base_url}/v1/trains/{train_number}/live"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                return self._handle_response(response)
            except httpx.RequestError as e:
                logger.error(f"RailRadar network request error for train {train_number}: {e}")
                raise RailRadarServiceError(f"RailRadar network error: {str(e)}")

    async def get_train_schedule(self, train_number: str) -> Dict[str, Any]:
        """
        GET /v1/trains/{number}/schedule
        Returns full scheduled route with stations, days, and times.
        """
        if not self.is_configured:
            raise RailRadarAuthError("RailRadar API key is not configured. Set RAILRADAR_API_KEY in .env.")

        url = f"{self.base_url}/v1/trains/{train_number}/schedule"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                return self._handle_response(response)
            except httpx.RequestError as e:
                logger.error(f"RailRadar network request error for train {train_number} schedule: {e}")
                raise RailRadarServiceError(f"RailRadar network error: {str(e)}")

    async def search_trains_between(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        GET /v1/trains/between?from={from}&to={to}&date={date}
        Returns trains operating between the specified pair of stations.
        """
        if not self.is_configured:
            raise RailRadarAuthError("RailRadar API key is not configured. Set RAILRADAR_API_KEY in .env.")

        url = f"{self.base_url}/v1/trains/between"
        params = {"from": from_station.upper(), "to": to_station.upper()}
        if date:
            params["date"] = date

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers(), params=params)
                data = self._handle_response(response)
                if isinstance(data, list):
                    return data
                return data.get("trains", data.get("data", []))
            except httpx.RequestError as e:
                logger.error(f"RailRadar network request error for search {from_station}->{to_station}: {e}")
                raise RailRadarServiceError(f"RailRadar network error: {str(e)}")


# Singleton instance
railradar_client = RailRadarClient()
