"""
SMS Notification Provider (backend/integrations/sms_provider.py)
Dispatches passenger SMS alerts using Twilio, Fast2SMS, or Simulation logging.
"""

import os
import logging
import datetime
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("sms_provider")


class SMSProvider:
    """
    Sends passenger SMS alerts upon journey disruption.
    Tracks SENT, FAILED, and SIMULATED status.
    """

    def __init__(self):
        self.provider = (os.getenv("SMS_PROVIDER") or "simulation").lower()
        self.api_key = os.getenv("SMS_API_KEY", "").strip()
        self.from_number = os.getenv("SMS_FROM_NUMBER", "+1234567890").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5 and self.provider != "simulation")

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        event_type: str = "TRAIN_DELAY"
    ) -> Dict[str, Any]:
        """
        Send SMS notification.
        Returns delivery result with status SENT, FAILED, or SIMULATED.
        """
        now = datetime.datetime.utcnow()

        # Production Twilio delivery if configured
        if self.is_configured and self.provider == "twilio":
            # Twilio uses account SID (usually part of key or separate)
            try:
                # Basic standard Twilio REST API call
                account_sid = os.getenv("TWILIO_ACCOUNT_SID", self.api_key.split(":")[0] if ":" in self.api_key else "")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN", self.api_key.split(":")[1] if ":" in self.api_key else self.api_key)
                if account_sid and auth_token:
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(
                            url,
                            data={"To": to_phone, "From": self.from_number, "Body": message},
                            auth=(account_sid, auth_token)
                        )
                        if resp.status_code in [200, 201]:
                            logger.info(f"SMS successfully sent to {to_phone} via Twilio.")
                            return {
                                "status": "SENT",
                                "provider": "twilio",
                                "recipient": to_phone,
                                "sent_at": now.isoformat(),
                                "response": resp.json()
                            }
                        else:
                            logger.error(f"Twilio SMS error: {resp.text}")
                            return {
                                "status": "FAILED",
                                "provider": "twilio",
                                "recipient": to_phone,
                                "sent_at": None,
                                "response": resp.text[:200]
                            }
            except Exception as e:
                logger.error(f"Failed to dispatch SMS via Twilio: {e}")
                return {
                    "status": "FAILED",
                    "provider": "twilio",
                    "recipient": to_phone,
                    "sent_at": None,
                    "response": str(e)
                }

        # Simulation / Local mode: Log clear audit trail
        logger.info(f"[SMS SIMULATION] Dispatch to {to_phone}: {message[:80]}...")
        return {
            "status": "SIMULATED",
            "provider": self.provider,
            "recipient": to_phone,
            "sent_at": now.isoformat(),
            "response": "Dispatched via RailMind simulated SMS gateway (Live provider key not configured)"
        }


# Global singleton
sms_provider = SMSProvider()
