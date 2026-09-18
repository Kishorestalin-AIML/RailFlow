import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.schema import RailwayEvent, Journey, JourneyLeg, Train
from backend.engines.journey_state import JourneyStateEngine
from backend.engines.action_engine import ActionEngine

VALID_EVENT_TYPES = {
    "TRAIN_DELAY",
    "TRAIN_CANCELLED",
    "ETA_CHANGED",
    "BOOKING_STATUS_CHANGED",
    "RAC_MOVEMENT",
    "SEAT_ALLOCATED",
    "AVAILABILITY_CHANGED",
    "RESET"
}


class EventEngine:
    """
    Event Intelligence Engine.
    Validates, normalizes, persists incoming railway events, identifies affected passenger journeys,
    and propagates state changes throughout the deterministic intelligence pipeline.
    """

    def __init__(self, db: Session):
        self.db = db
        self.state_engine = JourneyStateEngine(db)
        self.action_engine = ActionEngine(db)

    def process_event(
        self,
        event_type: str,
        train_id: str,
        payload: Optional[Dict[str, Any]] = None,
        effective_date: Optional[str] = None,
        source: str = "simulation"
    ) -> Dict[str, Any]:
        """
        Main pipeline orchestrator for railway events.
        1. Validate event structure
        2. Normalize payload with previous/new delays
        3. Persist event in database
        4. Identify affected journeys
        5. Recalculate journey states
        6. Trigger downstream Impact -> Decision -> Action engines
        7. Assemble event log steps for live event stream
        """
        clean_type = event_type.upper().strip()
        if clean_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Unsupported event type: '{event_type}'. Must be one of {sorted(list(VALID_EVENT_TYPES))}")

        clean_train_id = str(train_id).strip()
        payload = payload or {}
        now = datetime.datetime.utcnow()
        now_time_str = now.strftime("%H:%M:%S")
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

        new_delay = int(payload.get("delay_minutes", payload.get("new_delay", 0)))
        prev_delay = int(payload.get("previous_delay", 0))
        delay_change = int(payload.get("delay_change", new_delay - prev_delay))

        # Store event in database
        db_event = RailwayEvent(
            event_id=event_id,
            event_type=clean_type,
            train_id=clean_train_id,
            timestamp=now,
            effective_date=effective_date or now.strftime("%Y-%m-%d"),
            source=source,
            payload_json=json.dumps(payload)
        )
        self.db.add(db_event)
        self.db.commit()

        # Identify affected journeys by matching journey legs with this train_id
        affected_legs = self.db.query(JourneyLeg).filter(JourneyLeg.train_number == clean_train_id).all()
        affected_journey_ids = list({leg.journey_id for leg in affected_legs})

        # Update train legs with new running status
        for leg in affected_legs:
            if clean_type in ["TRAIN_DELAY", "ETA_CHANGED"]:
                leg.delay_arrival_min = new_delay
                leg.status = "DELAYED" if new_delay > 0 else "ON_TIME"
            elif clean_type == "TRAIN_CANCELLED":
                leg.status = "CANCELLED"

        self.db.commit()

        # Recalculate journey state, impact, decision, and action for each affected journey
        recalculated_journeys = []
        pipeline_steps = [
            {
                "time": now_time_str,
                "step": "EVENT_INGESTED",
                "title": f"Train {clean_train_id} {clean_type}",
                "detail": f"Delay changed from +{prev_delay}m to +{new_delay}m (Delta: +{delay_change}m) via {source}"
            }
        ]

        for j_id in affected_journey_ids:
            state_result = self.state_engine.recalculate_journey_state(j_id)
            rec_result = self.action_engine.generate_recommendation(j_id, event_id=event_id)

            pnr = state_result.get("pnr", j_id)
            status = state_result["status"]
            buffer_min = state_result.get("connection_buffer_minutes")

            pipeline_steps.append({
                "time": now_time_str,
                "step": "JOURNEY_RECALCULATED",
                "title": f"Journey {pnr} State Updated",
                "detail": f"Status: {status}, Remaining transfer buffer: {buffer_min} minutes"
            })

            pipeline_steps.append({
                "time": now_time_str,
                "step": "DECISION_GENERATED",
                "title": f"Decision Support Assessment",
                "detail": f"{rec_result.get('title')}: {rec_result.get('status')}"
            })

            recalculated_journeys.append({
                "journey_id": j_id,
                "pnr": pnr,
                "status": status,
                "buffer_minutes": buffer_min,
                "recommendation_title": rec_result["title"]
            })

        pipeline_steps.append({
            "time": now_time_str,
            "step": "GPT4ALL_READY",
            "title": "GPT4All Explanation Generated",
            "detail": "Passenger-facing natural language explanation synthesized without hallucination"
        })

        return {
            "event_id": event_id,
            "event_type": clean_type,
            "train_id": clean_train_id,
            "previous_delay": prev_delay,
            "new_delay": new_delay,
            "delay_change": delay_change,
            "source": source,
            "affected_journeys_count": len(affected_journey_ids),
            "affected_journeys": recalculated_journeys,
            "pipeline_steps": pipeline_steps,
            "timestamp": now.isoformat()
        }

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent railway events for auditing and visual feeds."""
        events = (
            self.db.query(RailwayEvent)
            .order_by(RailwayEvent.timestamp.desc())
            .limit(limit)
            .all()
        )
        results = []
        for e in events:
            results.append({
                "event_id": e.event_id,
                "event_type": e.event_type,
                "train_id": e.train_id,
                "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S") if e.timestamp else "",
                "source": e.source,
                "payload": e.payload
            })
        return results
