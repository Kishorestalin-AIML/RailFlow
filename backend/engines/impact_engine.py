from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.schema import Journey
from backend.engines.journey_state import calculate_connection_buffer_minutes, calculate_eta


class ImpactEngine:
    """
    Deterministic Impact Calculation Layer.
    Evaluates what railway events and delays mean for a specific passenger journey.
    Calculates safety margins, connection viability, and severity levels.
    """

    def __init__(self, db: Session, minimum_safe_buffer_minutes: int = 30):
        self.db = db
        self.minimum_safe_buffer_minutes = minimum_safe_buffer_minutes

    def calculate_journey_impact(self, journey_id: str) -> Dict[str, Any]:
        """
        Evaluate impact for the given journey based on current leg timings and delays.
        Returns a structured impact dictionary.
        """
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        legs = sorted(journey.legs, key=lambda l: l.leg_order)
        if not legs:
            return {
                "impact_type": "NO_IMPACT",
                "severity": "LOW",
                "affected_train": "N/A",
                "delay_minutes": 0,
                "remaining_buffer_minutes": None,
                "required_buffer_minutes": self.minimum_safe_buffer_minutes,
                "status_summary": "No active journey legs found."
            }

        # Single-leg journey evaluation
        if len(legs) == 1:
            leg = legs[0]
            if leg.status == "CANCELLED":
                return {
                    "impact_type": "TRAIN_CANCELLED",
                    "severity": "CRITICAL",
                    "affected_train": leg.train_number,
                    "delay_minutes": leg.delay_arrival_min,
                    "remaining_buffer_minutes": None,
                    "required_buffer_minutes": self.minimum_safe_buffer_minutes,
                    "status_summary": f"Train {leg.train_number} has been cancelled."
                }
            elif leg.delay_arrival_min > 45:
                return {
                    "impact_type": "SIGNIFICANT_DELAY",
                    "severity": "MEDIUM",
                    "affected_train": leg.train_number,
                    "delay_minutes": leg.delay_arrival_min,
                    "remaining_buffer_minutes": None,
                    "required_buffer_minutes": self.minimum_safe_buffer_minutes,
                    "status_summary": f"Train {leg.train_number} delayed by {leg.delay_arrival_min} min."
                }
            else:
                return {
                    "impact_type": "ON_SCHEDULE",
                    "severity": "LOW",
                    "affected_train": leg.train_number,
                    "delay_minutes": leg.delay_arrival_min,
                    "remaining_buffer_minutes": None,
                    "required_buffer_minutes": self.minimum_safe_buffer_minutes,
                    "status_summary": "Journey operating within normal parameters."
                }

        # Multi-leg connection journey evaluation
        first_leg = legs[0]
        second_leg = legs[1]

        arr_expected = first_leg.actual_arrival or calculate_eta(first_leg.scheduled_arrival, first_leg.delay_arrival_min)
        dep_connection = second_leg.actual_departure or second_leg.scheduled_departure

        buffer_minutes = calculate_connection_buffer_minutes(arr_expected, dep_connection)

        # Connection logic
        if first_leg.status == "CANCELLED":
            impact_type = "TRAIN_CANCELLED"
            severity = "CRITICAL"
            summary = f"Originating train {first_leg.train_number} cancelled. Connection to Train {second_leg.train_number} disrupted."
        elif buffer_minutes <= 0:
            impact_type = "MISSED_CONNECTION"
            severity = "CRITICAL"
            summary = (
                f"Connection missed: Train {first_leg.train_number} ETA {arr_expected} is after "
                f"Train {second_leg.train_number} departure {dep_connection} (buffer: {buffer_minutes} min)."
            )
        elif buffer_minutes < self.minimum_safe_buffer_minutes:
            impact_type = "CONNECTION_RISK"
            severity = "HIGH"
            summary = (
                f"Connection at risk: Buffer of {buffer_minutes} min is below required "
                f"{self.minimum_safe_buffer_minutes} min threshold at {first_leg.to_station_code}."
            )
        else:
            impact_type = "SAFE_CONNECTION"
            severity = "LOW"
            summary = (
                f"Connection buffer is healthy ({buffer_minutes} min remaining vs "
                f"{self.minimum_safe_buffer_minutes} min required threshold)."
            )

        return {
            "impact_type": impact_type,
            "severity": severity,
            "affected_train": first_leg.train_number,
            "delay_minutes": first_leg.delay_arrival_min,
            "remaining_buffer_minutes": buffer_minutes,
            "required_buffer_minutes": self.minimum_safe_buffer_minutes,
            "connection_train": second_leg.train_number,
            "connection_departure": dep_connection,
            "expected_arrival": arr_expected,
            "status_summary": summary
        }
