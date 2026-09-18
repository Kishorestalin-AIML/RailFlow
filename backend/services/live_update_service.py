import os
import asyncio
import logging
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal
from backend.models.schema import TrainLiveStatus, JourneyLeg, DataRefreshLog, Journey
from backend.integrations.railway_api import railway_adapter
from backend.engines.event_engine import EventEngine
from backend.engines.alternative_engine import AlternativeEngine
from backend.ai.gpt4all_agent import gpt4all_agent
from backend.services.notification_service import NotificationService

logger = logging.getLogger("live_update_service")


class LiveUpdateService:
    """
    Periodic Live Railway Information Poller.
    Monitors active journeys, checks running status, detects deltas,
    and dispatches change events through the Event Engine.
    """

    def __init__(self, interval_seconds: Optional[int] = None):
        self.interval_seconds = interval_seconds or int(os.getenv("LIVE_UPDATE_INTERVAL_SECONDS", "30"))
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, broadcast_callback=None):
        """Starts background polling task."""
        if self._is_running:
            return
        self._is_running = True
        self._broadcast_callback = broadcast_callback
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"LiveUpdateService started with interval={self.interval_seconds}s")

    async def stop(self):
        """Stops background polling task."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("LiveUpdateService stopped.")

    async def _poll_loop(self):
        while self._is_running:
            try:
                await self.poll_and_detect_changes()
            except Exception as e:
                logger.error(f"Error in LiveUpdateService loop: {e}")

            # Sleep until next check interval
            await asyncio.sleep(self.interval_seconds)

    async def poll_and_detect_changes(self):
        """
        Polls trains currently on active journeys, checks live running status,
        and generates events when differences are detected.
        """
        with SessionLocal() as db:
            # 1. Identify distinct trains associated with active journeys
            active_legs = db.query(JourneyLeg).filter(JourneyLeg.status != "ARRIVED").all()
            train_numbers = list({leg.train_number for leg in active_legs})

            if not train_numbers:
                return

            today_str = datetime.date.today().strftime("%Y-%m-%d")

            for train_no in train_numbers:
                start_time = datetime.datetime.utcnow()
                try:
                    status_data = await railway_adapter.get_train_running_status(train_no, today_str)
                    new_delay = int(status_data.get("delay_minutes", 0))

                    # 2. Check previous status in database
                    prev_record = (
                        db.query(TrainLiveStatus)
                        .filter(TrainLiveStatus.train_number == train_no)
                        .order_by(TrainLiveStatus.last_updated.desc())
                        .first()
                    )

                    prev_delay = prev_record.delay_minutes if prev_record else 0

                    # 3. Detect change
                    if prev_record is None or prev_delay != new_delay:
                        delta = new_delay - prev_delay
                        logger.info(f"Change detected on Train {train_no}: {prev_delay}m -> {new_delay}m (Delta: {delta}m)")

                        # Save new status
                        live_status = TrainLiveStatus(
                            train_number=train_no,
                            station_code=status_data.get("current_station", "Katpadi"),
                            expected_arrival=status_data.get("actual_arrival", "08:30"),
                            expected_departure=status_data.get("actual_departure", "22:30"),
                            delay_minutes=new_delay,
                            status=status_data.get("running_status", "ON_TIME"),
                            last_updated=datetime.datetime.utcnow(),
                            source=status_data.get("source", "railway_api"),
                            is_live=status_data.get("is_live", False)
                        )
                        db.add(live_status)
                        db.commit()

                        # Dispatch event into Event Engine
                        event_engine = EventEngine(db)
                        event_result = event_engine.process_event(
                            event_type="TRAIN_DELAY",
                            train_id=train_no,
                            payload={
                                "previous_delay": prev_delay,
                                "new_delay": new_delay,
                                "delay_change": delta,
                                "delay_minutes": new_delay,
                                "source": status_data.get("source", "railway_api")
                            },
                            source=status_data.get("source", "railway_api")
                        )

                        # Automatic Alternative Search & Notification Dispatch
                        notif_service = NotificationService(db)
                        alt_engine = AlternativeEngine(db)

                        for j_info in event_result.get("affected_journeys", []):
                            j_id = j_info.get("journey_id")
                            j_status = j_info.get("status", "SAFE")
                            journey_obj = db.query(Journey).filter(Journey.id == j_id).first()
                            passenger = journey_obj.booking.passenger if (journey_obj and journey_obj.booking) else None
                            p_id = passenger.id if passenger else "PASS-DEMO-01"
                            p_name = passenger.name if passenger else "Kishore Stalin"

                            if notif_service.should_notify(
                                journey_id=j_id,
                                event_type="TRAIN_DELAY",
                                delay_minutes=new_delay,
                                previous_status="SAFE" if prev_delay < 30 else "AT_RISK",
                                current_status=j_status
                            ):
                                alt_matrix = alt_engine.get_complete_alternative_comparison(j_id)
                                ai_explanation = gpt4all_agent.explain_journey({
                                    "journey_status": j_status,
                                    "current_train": {
                                        "number": train_no,
                                        "delay_minutes": new_delay,
                                        "expected_arrival": status_data.get("actual_arrival", "08:30")
                                    },
                                    "alternatives": alt_matrix.get("alternatives", [])
                                })
                                try:
                                    await notif_service.send_disruption_alert(
                                        journey_id=j_id,
                                        passenger_id=p_id,
                                        passenger_name=p_name,
                                        train_number=train_no,
                                        delay_minutes=new_delay,
                                        expected_arrival=status_data.get("actual_arrival", "08:30"),
                                        journey_status=j_status,
                                        alternatives=alt_matrix.get("alternatives", []),
                                        ai_explanation=ai_explanation,
                                        event_type="TRAIN_DELAY"
                                    )
                                except Exception as n_err:
                                    logger.warning(f"Failed to dispatch alert: {n_err}")

                        # Broadcast via SSE callback if available
                        if self._broadcast_callback:
                            await self._broadcast_callback(event_result)

                    # Log refresh activity
                    duration_ms = (datetime.datetime.utcnow() - start_time).total_seconds() * 1000
                    refresh_log = DataRefreshLog(
                        source=status_data.get("source", "railway_api"),
                        train_number=train_no,
                        status_code=200,
                        fetched_at=datetime.datetime.utcnow(),
                        duration_ms=duration_ms,
                        message=f"Polling check completed: delay={new_delay}m"
                    )
                    db.add(refresh_log)
                    db.commit()

                except Exception as ex:
                    logger.warning(f"Error polling Train {train_no}: {ex}")


# Singleton instance
live_update_service = LiveUpdateService()
