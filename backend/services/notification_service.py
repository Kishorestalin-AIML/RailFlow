"""
Notification Service (backend/services/notification_service.py)
Coordinates threshold checking, deduplication, and dispatch of SMS and Email alerts.
"""

import os
import uuid
import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.models.schema import NotificationRecord, PassengerContact, Journey
from backend.integrations.sms_provider import sms_provider
from backend.integrations.email_provider import email_provider

logger = logging.getLogger("notification_service")


class NotificationService:
    """
    Evaluates disruption thresholds and sends passenger alerts via SMS and Email.
    Prevents duplicate notifications for unchanged states.
    """

    def __init__(self, db: Session):
        self.db = db
        try:
            self.delay_threshold = int(os.getenv("NOTIFY_DELAY_THRESHOLD_MINUTES", "30"))
        except ValueError:
            self.delay_threshold = 30

    def should_notify(
        self,
        journey_id: str,
        event_type: str,
        delay_minutes: int,
        previous_status: str,
        current_status: str
    ) -> bool:
        """
        Determine if notification is required:
        - Delay >= threshold (e.g. 30 min)
        - State transition (SAFE -> AT_RISK or AT_RISK -> MISSED)
        - Train cancellation
        - No duplicate sent for the same event type and journey in the last 15 minutes
        """
        status_changed = (
            (previous_status == "SAFE" and current_status in ["AT_RISK", "CRITICAL", "MISSED"]) or
            (previous_status == "AT_RISK" and current_status == "MISSED") or
            event_type == "TRAIN_CANCELLED"
        )
        significant_delay = delay_minutes >= self.delay_threshold

        if not (status_changed or significant_delay):
            return False

        # Deduplication check: Has a notification been sent for this journey & event_type in the last 15 mins?
        fifteen_mins_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        recent = self.db.query(NotificationRecord).filter(
            NotificationRecord.journey_id == journey_id,
            NotificationRecord.notification_type == event_type,
            NotificationRecord.created_at >= fifteen_mins_ago
        ).first()

        return recent is None

    async def send_disruption_alert(
        self,
        journey_id: str,
        passenger_id: str,
        passenger_name: str,
        train_number: str,
        delay_minutes: int,
        expected_arrival: str,
        journey_status: str,
        alternatives: List[Dict[str, Any]],
        ai_explanation: Optional[str] = None,
        event_type: str = "TRAIN_DELAY"
    ) -> List[Dict[str, Any]]:
        """
        Dispatches both SMS and Email to the passenger's registered contact info.
        Stores records in the notifications table.
        """
        contact = self.db.query(PassengerContact).filter(
            PassengerContact.passenger_id == passenger_id
        ).first()

        results = []
        now = datetime.datetime.utcnow()

        # 1. SMS Dispatch
        phone = contact.phone if contact else "+91 98401 23456"
        sms_enabled = contact.sms_notifications_enabled if contact else True

        if sms_enabled:
            sms_text = (
                f"RailMind Alert: Your train {train_number} is delayed by {delay_minutes} min "
                f"and connection is {journey_status}. "
                f"RailMind has found alternative trains/stations based on current timings. "
                f"Open RailMind to compare your options."
            )
            sms_res = await sms_provider.send_sms(to_phone=phone, message=sms_text, event_type=event_type)

            notif_sms = NotificationRecord(
                notification_id=f"NOTIF-SMS-{uuid.uuid4().hex[:8].upper()}",
                passenger_id=passenger_id,
                journey_id=journey_id,
                channel="SMS",
                notification_type=event_type,
                subject=f"Train {train_number} Delay Alert",
                message=sms_text,
                status=sms_res["status"],
                provider_response=sms_res.get("response", ""),
                created_at=now,
                sent_at=now if sms_res["status"] in ["SENT", "SIMULATED"] else None
            )
            self.db.add(notif_sms)
            results.append(sms_res)

        # 2. Email Dispatch
        email = contact.email if contact else "passenger@example.com"
        email_enabled = contact.email_notifications_enabled if contact else True

        if email_enabled:
            subject = "RailMind Journey Alert — Alternative Plans Available"
            body = email_provider.format_email_body(
                passenger_name=passenger_name,
                train_number=train_number,
                delay_minutes=delay_minutes,
                expected_arrival=expected_arrival,
                journey_status=journey_status,
                alternatives=alternatives,
                ai_explanation=ai_explanation
            )
            email_res = await email_provider.send_email(to_email=email, subject=subject, content=body)

            notif_email = NotificationRecord(
                notification_id=f"NOTIF-EML-{uuid.uuid4().hex[:8].upper()}",
                passenger_id=passenger_id,
                journey_id=journey_id,
                channel="EMAIL",
                notification_type="ALTERNATIVE_PLANS_AVAILABLE",
                subject=subject,
                message=body,
                status=email_res["status"],
                provider_response=email_res.get("response", ""),
                created_at=now,
                sent_at=now if email_res["status"] in ["SENT", "SIMULATED"] else None
            )
            self.db.add(notif_email)
            results.append(email_res)

        self.db.commit()
        logger.info(f"Dispatched {len(results)} alerts for journey {journey_id} ({event_type})")
        return results
