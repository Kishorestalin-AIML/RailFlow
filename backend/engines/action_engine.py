import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.schema import Recommendation, Journey
from backend.engines.decision_engine import DecisionEngine
from backend.engines.alternative_engine import AlternativeTrainEngine


class ActionEngine:
    """
    Translates deterministic decisions into passenger-centric actionable recommendations.
    Provides structured 4-point clarity:
    1. WHAT HAPPENED?
    2. WHY DOES IT MATTER?
    3. WHAT OPTIONS EXIST?
    4. WHAT CAN I DO NOW?
    """

    def __init__(self, db: Session, minimum_safe_buffer_minutes: int = 30):
        self.db = db
        self.decision_engine = DecisionEngine(db, minimum_safe_buffer_minutes=minimum_safe_buffer_minutes)
        self.alternative_engine = AlternativeTrainEngine(db)

    def generate_recommendation(self, journey_id: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates the decision (or retrieves latest) and generates structured recommendation.
        Persists into recommendations table.
        """
        decision_data = self.decision_engine.evaluate_decision(journey_id, event_id=event_id)
        decision_id = decision_data["decision_id"]
        status = decision_data["situation_status"]
        impact = decision_data.get("impact_summary", {})

        delay_min = impact.get("delay_minutes", 0)
        affected_train = impact.get("affected_train", "your train")
        conn_train = impact.get("connection_train", "connecting service")
        remaining_buffer = impact.get("remaining_buffer_minutes")
        required_buffer = impact.get("required_buffer_minutes", 30)
        expected_arrival = impact.get("expected_arrival", "09:45")
        conn_departure = impact.get("connection_departure", "09:20")

        # Discover alternative connections from the interchange station
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        transfer_station = "MAS"
        dest_station = "NDLS"
        journey_date = datetime.date.today().strftime("%Y-%m-%d")

        if journey and len(journey.legs) > 1:
            transfer_station = journey.legs[0].to_station_code
            dest_station = journey.destination_station_code
            journey_date = journey.journey_date

        alternative_trains = []
        if status in ["AT_RISK", "MISSED"]:
            alternative_trains = self.alternative_engine.find_alternative_connections(
                from_station_code=transfer_station,
                to_station_code=dest_station,
                expected_arrival_time=expected_arrival,
                journey_date=journey_date,
                min_safe_transfer_buffer_minutes=required_buffer
            )

        if status == "MISSED":
            rec_status = "CRITICAL_ALERT"
            title = f"Connection Missed: Train {affected_train} Transfer Disrupted"
            what_happened = (
                f"Train {affected_train} is currently delayed by {delay_min} minutes. "
                f"Its estimated arrival ({expected_arrival}) is later than Train {conn_train}'s "
                f"scheduled departure ({conn_departure})."
            )
            why_it_matters = (
                f"The physical transfer window at the interchange station has lapsed. "
                f"You will not be able to board your scheduled connecting train {conn_train}."
            )
            options = [
                {
                    "option_id": "OPT_LATER_TRAIN",
                    "title": "Board Later Scheduled Train",
                    "description": f"Evaluate subsequent services from {transfer_station} to {dest_station}. {len(alternative_trains)} feasible trains identified.",
                    "tag": "Recommended",
                    "alternatives": alternative_trains[:3]
                },
                {
                    "option_id": "OPT_STATION_HELP",
                    "title": "Visit Chief Commercial Inspector (CCI) / Station Superintendent",
                    "description": "Request IRCTC / Railway transfer endorsement on the next available train.",
                    "tag": "Official Procedure"
                },
                {
                    "option_id": "OPT_TDR",
                    "title": "File TDR for Full Refund",
                    "description": "Missed connection rules entitle passenger to full refund without cancellation fees.",
                    "tag": "Refund Option"
                }
            ]
            actions = [
                {"type": "REVIEW_ALTERNATIVE", "label": "Review Alternative Trains", "variant": "primary"},
                {"type": "CLAIM_REFUND_INFO", "label": "View Missed Connection Rules", "variant": "secondary"}
            ]

        elif status == "AT_RISK":
            rec_status = "ACTION_REQUIRED"
            title = f"Connection at Risk: Transfer Buffer Narrowed to {remaining_buffer} Min"
            what_happened = (
                f"Train {affected_train} has incurred a {delay_min}-minute delay en route. "
                f"Expected arrival at transfer station is now {expected_arrival}."
            )
            why_it_matters = (
                f"Your connection transfer buffer is reduced to {remaining_buffer} minutes, "
                f"falling {required_buffer - (remaining_buffer or 0)} minutes below the configured "
                f"{required_buffer}-minute safe transfer buffer required for platform navigation."
            )
            options = [
                {
                    "option_id": "OPT_PREP_TRANSIT",
                    "title": "Rapid Interchange Transit",
                    "description": f"Move towards exit doors before arrival to cover the {remaining_buffer}-minute transfer.",
                    "tag": "Time Sensitive"
                },
                {
                    "option_id": "OPT_SCREEN_LATER",
                    "title": "Pre-Screen Later Connection Alternatives",
                    "description": f"Inspect backup services departing after {expected_arrival}. {len(alternative_trains)} feasible options found.",
                    "tag": "Proactive Backup",
                    "alternatives": alternative_trains[:3]
                }
            ]
            actions = [
                {"type": "REVIEW_ALTERNATIVE", "label": "Review Alternative Connections", "variant": "primary"},
                {"type": "MONITOR", "label": "Continue Monitoring Running Updates", "variant": "secondary"},
                {"type": "SET_ALERT", "label": "Set 10-Min Proximity Alert", "variant": "secondary"}
            ]

        elif status == "CANCELLED":
            rec_status = "CRITICAL_ALERT"
            title = f"Train {affected_train} Cancelled by Railways"
            what_happened = f"Train {affected_train} has been officially cancelled on this service corridor."
            why_it_matters = "Your scheduled journey cannot proceed as ticketed."
            options = [
                {
                    "option_id": "OPT_ALT_SERVICE",
                    "title": "Find Alternative Daily Service",
                    "description": "Search available capacity on parallel express and special trains.",
                    "tag": "Travel Action"
                },
                {
                    "option_id": "OPT_AUTO_REFUND",
                    "title": "Automatic Full Cancellation Refund",
                    "description": "Full fare is credited automatically without filing TDR.",
                    "tag": "Financial Protection"
                }
            ]
            actions = [
                {"type": "SEARCH_TRAINS", "label": "Search Alternative Trains", "variant": "primary"},
                {"type": "REFUND_STATUS", "label": "Check Refund Status", "variant": "secondary"}
            ]

        else:
            rec_status = "SAFE"
            title = "Journey On Schedule: Safe Connection Buffer"
            what_happened = f"Train {affected_train} is running with nominal delay ({delay_min} min)."
            why_it_matters = (
                f"Transfer buffer of {remaining_buffer} minutes provides sufficient buffer "
                f"above the {required_buffer}-minute safety requirement."
            )
            options = [
                {
                    "option_id": "OPT_NO_ACTION",
                    "title": "Proceed According to Schedule",
                    "description": "Normal boarding and transfer times apply.",
                    "tag": "Standard"
                }
            ]
            actions = [
                {"type": "MONITOR", "label": "Continue Monitoring", "variant": "secondary"}
            ]

        rec_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.utcnow()

        db_rec = Recommendation(
            id=rec_id,
            journey_id=journey_id,
            decision_id=decision_id,
            title=title,
            status=rec_status,
            what_happened=what_happened,
            why_it_matters=why_it_matters,
            options_json=json.dumps(options),
            actions_json=json.dumps(actions),
            created_at=now
        )
        self.db.add(db_rec)
        self.db.commit()
        self.db.refresh(db_rec)

        return {
            "id": rec_id,
            "journey_id": journey_id,
            "decision_id": decision_id,
            "title": title,
            "status": rec_status,
            "what_happened": what_happened,
            "why_it_matters": why_it_matters,
            "options": options,
            "actions": actions,
            "ai_explanation": None,
            "created_at": now.isoformat()
        }

    def get_latest_recommendation(self, journey_id: str) -> Optional[Dict[str, Any]]:
        rec = (
            self.db.query(Recommendation)
            .filter(Recommendation.journey_id == journey_id)
            .order_by(Recommendation.created_at.desc())
            .first()
        )
        if not rec:
            return None

        return {
            "id": rec.id,
            "journey_id": rec.journey_id,
            "decision_id": rec.decision_id,
            "title": rec.title,
            "status": rec.status,
            "what_happened": rec.what_happened,
            "why_it_matters": rec.why_it_matters,
            "options": rec.options,
            "actions": rec.actions,
            "ai_explanation": rec.ai_explanation,
            "created_at": rec.created_at.isoformat()
        }
