import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.schema import Decision, Journey
from backend.engines.impact_engine import ImpactEngine


class DecisionEngine:
    """
    Deterministic Decision Engine.
    Evaluates passenger journey constraints, risk boundaries, and rule sets.
    Generates structured decisions without probabilistic hallucinations.
    """

    def __init__(self, db: Session, minimum_safe_buffer_minutes: int = 30):
        self.db = db
        self.impact_engine = ImpactEngine(db, minimum_safe_buffer_minutes=minimum_safe_buffer_minutes)

    def evaluate_decision(self, journey_id: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates a deterministic decision for the journey.
        Stores the decision in SQLite and returns the structured result.
        """
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        impact = self.impact_engine.calculate_journey_impact(journey_id)
        impact_type = impact["impact_type"]
        remaining_buffer = impact.get("remaining_buffer_minutes")
        required_buffer = impact.get("required_buffer_minutes", 30)

        feasible_actions: List[Dict[str, Any]] = []

        if impact_type == "MISSED_CONNECTION":
            situation_status = "MISSED"
            system_assessment = "Connecting train cannot be boarded due to delay exceeding the transfer window."
            reason = (
                f"Train {impact.get('affected_train')} estimated arrival {impact.get('expected_arrival')} "
                f"is past connection departure {impact.get('connection_departure')}."
            )
            feasible_actions = [
                {
                    "action_type": "REVIEW_ALTERNATIVE_CONNECTION",
                    "feasibility": "FEASIBLE",
                    "title": "Review Alternative Connection Trains",
                    "description": "Inspect later scheduled services departing from transfer station."
                },
                {
                    "action_type": "FILE_TDR_REFUND",
                    "feasibility": "REQUIRES_USER_ACTION",
                    "title": "File TDR / Railway Inconvenience Claim",
                    "description": "Initiate official IRCTC TDR filing for missed connection refund."
                },
                {
                    "action_type": "CONTINUE_CURRENT_JOURNEY",
                    "feasibility": "NOT_FEASIBLE",
                    "title": "Continue to Original Connecting Train",
                    "description": "Impossible to catch original scheduled connection."
                }
            ]

        elif impact_type == "CONNECTION_RISK":
            situation_status = "AT_RISK"
            system_assessment = "Alternative connection should be reviewed while actively monitoring running speed."
            reason = (
                f"Current delay of {impact.get('delay_minutes')} min reduces transfer buffer to "
                f"{remaining_buffer} min, falling {required_buffer - (remaining_buffer or 0)} min "
                f"below the configured {required_buffer}-minute safe transfer margin."
            )
            feasible_actions = [
                {
                    "action_type": "REVIEW_ALTERNATIVE_CONNECTION",
                    "feasibility": "FEASIBLE",
                    "title": "Review Alternative Connection Trains",
                    "description": "Pre-screen subsequent trains from transfer station in case delay compounds."
                },
                {
                    "action_type": "MONITOR_CONNECTION",
                    "feasibility": "FEASIBLE",
                    "title": "Continue Monitoring Running Updates",
                    "description": "Track section running speeds and station dwell times."
                },
                {
                    "action_type": "CONTINUE_CURRENT_JOURNEY",
                    "feasibility": "REQUIRES_USER_ACTION",
                    "title": "Maintain Existing Travel Itinerary",
                    "description": "Prepare for rapid station platform transit upon arrival."
                }
            ]

        elif impact_type == "TRAIN_CANCELLED":
            situation_status = "CANCELLED"
            system_assessment = "Originating train cancelled by railway operations."
            reason = f"Train {impact.get('affected_train')} has been cancelled on this route."
            feasible_actions = [
                {
                    "action_type": "SEARCH_ALTERNATIVE_TRAIN",
                    "feasibility": "FEASIBLE",
                    "title": "Find Alternative Trains",
                    "description": "Search other trains serving the same corridor today."
                },
                {
                    "action_type": "FULL_REFUND_CLAIM",
                    "feasibility": "REQUIRES_USER_ACTION",
                    "title": "Claim Full Cancellation Refund",
                    "description": "Full refund without cancellation charges per Indian Railways rules."
                }
            ]

        else:
            situation_status = "SAFE"
            system_assessment = "Journey is operating safely within acceptable buffers."
            reason = (
                f"Connection transfer buffer ({remaining_buffer} min) meets or exceeds "
                f"the {required_buffer}-minute safety requirement."
            )
            feasible_actions = [
                {
                    "action_type": "CONTINUE_CURRENT_JOURNEY",
                    "feasibility": "FEASIBLE",
                    "title": "Continue Current Journey",
                    "description": "No immediate intervention required."
                },
                {
                    "action_type": "MONITOR_CONNECTION",
                    "feasibility": "FEASIBLE",
                    "title": "Routine Status Monitoring",
                    "description": "Receive automated updates if delay changes by > 15 minutes."
                }
            ]

        decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow()

        db_decision = Decision(
            id=decision_id,
            journey_id=journey_id,
            event_id=event_id,
            situation_status=situation_status,
            system_assessment=system_assessment,
            reason=reason,
            feasible_actions_json=json.dumps(feasible_actions),
            created_at=now
        )
        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)

        return {
            "decision_id": decision_id,
            "journey_id": journey_id,
            "situation_status": situation_status,
            "system_assessment": system_assessment,
            "reason": reason,
            "feasible_actions": feasible_actions,
            "impact_summary": impact,
            "timestamp": now.isoformat()
        }

    def get_latest_decision(self, journey_id: str) -> Optional[Dict[str, Any]]:
        decision = (
            self.db.query(Decision)
            .filter(Decision.journey_id == journey_id)
            .order_by(Decision.created_at.desc())
            .first()
        )
        if not decision:
            return None

        return {
            "decision_id": decision.id,
            "journey_id": decision.journey_id,
            "situation_status": decision.situation_status,
            "system_assessment": decision.system_assessment,
            "reason": decision.reason,
            "feasible_actions": decision.feasible_actions,
            "timestamp": decision.created_at.isoformat()
        }
