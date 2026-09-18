import os
import time
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger("railway_client")


class RailwayApiClient:
    """
    Direct HTTP client for communicating with external Indian Railway Data APIs.
    Configurable via environment variables.
    """

    def __init__(self):
        self.base_url = os.getenv("RAILWAY_API_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("RAILWAY_API_KEY", "").strip()
        self.provider = os.getenv("RAILWAY_API_PROVIDER", "generic_railway_api").strip()
        self.timeout = float(os.getenv("RAILWAY_API_TIMEOUT", "10.0"))

    @property
    def is_configured(self) -> bool:
        """Determines if valid credentials and endpoints are supplied."""
        return bool(self.base_url and self.api_key and not self.api_key.startswith("your_"))

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Api-Key": self.api_key,
            "Accept": "application/json"
        }

    async def search_trains(self, from_station: str, to_station: str, date: str) -> Dict[str, Any]:
        """Search trains between two stations."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/between"
        params = {"from": from_station.upper(), "to": to_station.upper(), "date": date}
        return await self._get(url, params)

    async def get_train_details(self, train_number: str) -> Dict[str, Any]:
        """Fetch general train information."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/{train_number}"
        return await self._get(url)

    async def get_train_schedule(self, train_number: str) -> Dict[str, Any]:
        """Fetch scheduled intermediate station halts."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/{train_number}/schedule"
        return await self._get(url)

    async def get_live_status(self, train_number: str, date: str) -> Dict[str, Any]:
        """Fetch live running status & delays."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/{train_number}/live"
        params = {"date": date}
        return await self._get(url, params)

    async def get_availability(self, train_number: str, date: str, class_type: str, quota: str = "GN") -> Dict[str, Any]:
        """Fetch seat quota availability."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/{train_number}/availability"
        params = {"date": date, "class": class_type, "quota": quota}
        return await self._get(url, params)

    async def get_fare(self, train_number: str, date: str, class_type: str, quota: str = "GN") -> Dict[str, Any]:
        """Fetch fare breakdown."""
        if not self.is_configured:
            return {"success": False, "reason": "not_configured"}

        url = f"{self.base_url}/trains/{train_number}/fare"
        params = {"date": date, "class": class_type, "quota": quota}
        return await self._get(url, params)

    async def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._headers(), params=params)
                duration_ms = (time.time() - start) * 1000
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "data": data, "duration_ms": duration_ms}
                else:
                    logger.warning(f"Railway API returned HTTP {resp.status_code} for {url}")
                    return {"success": False, "status_code": resp.status_code, "duration_ms": duration_ms}
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.warning(f"Railway API network error ({url}): {e}")
            return {"success": False, "error": str(e), "duration_ms": duration_ms}


# Singleton client instance
railway_client = RailwayApiClient()
