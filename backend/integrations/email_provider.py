"""
Email Notification Provider (backend/integrations/email_provider.py)
Dispatches passenger Email alerts using SendGrid, SMTP, or Simulation logging.
"""

import os
import logging
import datetime
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger("email_provider")


class EmailProvider:
    """
    Sends passenger journey alert emails upon disruption.
    Tracks SENT, FAILED, and SIMULATED status.
    """

    def __init__(self):
        self.provider = (os.getenv("EMAIL_PROVIDER") or "simulation").lower()
        self.api_key = os.getenv("EMAIL_API_KEY", "").strip()
        self.from_email = os.getenv("EMAIL_FROM", "alerts@railmind.in").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5 and self.provider != "simulation")

    def format_email_body(
        self,
        passenger_name: str,
        train_number: str,
        delay_minutes: int,
        expected_arrival: str,
        journey_status: str,
        alternatives: List[Dict[str, Any]],
        ai_explanation: Optional[str] = None
    ) -> str:
        """Constructs the standard email content per Section 21."""
        alts_text = ""
        for idx, alt in enumerate(alternatives[:2], 1):
            train = alt.get("train", alt.get("train_number", "XXXXX"))
            station = alt.get("station", alt.get("station_name", "Current Station"))
            dep = alt.get("departure", alt.get("departure_time", "--:--"))
            arr = alt.get("expected_destination_arrival", alt.get("arrival_time", "--:--"))
            transfer = alt.get("transfer_time", alt.get("transfer_minutes", 0))
            transfer_str = f"{transfer} min" if transfer else "None (Direct/Same station)"
            avail = alt.get("availability", alt.get("availability_status", "Not provided"))
            fare = alt.get("formatted_fare", f"₹{alt.get('fare')}" if alt.get("fare") else "Not provided")

            alts_text += f"""
Alternative {idx}:
Train: {train}
Station: {station}
Departure: {dep}
Expected destination arrival: {arr}
Transfer: {transfer_str}
Availability: {avail}
Fare: {fare}
"""

        ai_block = ai_explanation or "RailMind deterministic engine calculated alternative paths based on live running status and transfer safety buffers."

        return f"""Hello {passenger_name},

Your train has been delayed.

Current Train:
Train {train_number}

Delay:
+{delay_minutes} minutes

Expected Arrival:
{expected_arrival}

Journey Status:
{journey_status}

RailMind has automatically analyzed alternative ways to reach your destination.
{alts_text}
RailMind AI Explanation:

{ai_block}

Please review the options in RailMind and choose the journey that works best for you.

RailMind does not automatically modify your railway booking.
"""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Dispatches email alert.
        Returns delivery result with status SENT, FAILED, or SIMULATED.
        """
        now = datetime.datetime.utcnow()

        # SendGrid delivery if configured
        if self.is_configured and self.provider == "sendgrid":
            try:
                url = "https://api.sendgrid.com/v3/mail/send"
                payload = {
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.from_email, "name": "RailMind Journey Intelligence"},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": content}]
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in [200, 202]:
                        logger.info(f"Email successfully sent to {to_email} via SendGrid.")
                        return {
                            "status": "SENT",
                            "provider": "sendgrid",
                            "recipient": to_email,
                            "sent_at": now.isoformat(),
                            "response": "Delivered via SendGrid API"
                        }
                    else:
                        logger.error(f"SendGrid error: {resp.text}")
                        return {
                            "status": "FAILED",
                            "provider": "sendgrid",
                            "recipient": to_email,
                            "sent_at": None,
                            "response": resp.text[:200]
                        }
            except Exception as e:
                logger.error(f"Failed to dispatch email via SendGrid: {e}")
                return {
                    "status": "FAILED",
                    "provider": "sendgrid",
                    "recipient": to_email,
                    "sent_at": None,
                    "response": str(e)
                }

        # Simulation / Local fallback: Log audit trail
        logger.info(f"[EMAIL SIMULATION] Dispatch to {to_email}: Subject: '{subject}'")
        return {
            "status": "SIMULATED",
            "provider": self.provider,
            "recipient": to_email,
            "sent_at": now.isoformat(),
            "response": "Dispatched via RailMind simulated Email gateway (Live provider key not configured)"
        }


# Global singleton
email_provider = EmailProvider()
