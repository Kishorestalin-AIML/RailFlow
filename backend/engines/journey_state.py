import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.models.schema import Journey, JourneyLeg, Train, Station, Booking, Passenger


def time_to_minutes(t_str: str) -> int:
    """Parse 'HH:MM' string to minutes from midnight."""
    clean = t_str.split(" ")[0].strip()
    parts = clean.split(":")
    hours = int(parts[0])
    mins = int(parts[1])
    return hours * 60 + mins


def minutes_to_time(m: int) -> str:
    """Format minutes from midnight back to 'HH:MM'."""
    normalized = m % (24 * 60)
    hours = normalized // 60
    mins = normalized % 60
    return f"{hours:02d}:{mins:02d}"


def calculate_eta(scheduled_time: str, delay_minutes: int) -> str:
    """Calculate expected time given scheduled time and delay."""
    sched_m = time_to_minutes(scheduled_time)
    eta_m = sched_m + delay_minutes
    return minutes_to_time(eta_m)


def calculate_connection_buffer_minutes(arrival_time_str: str, departure_time_str: str) -> int:
    """
    Calculate buffer in minutes between an arrival and subsequent departure.
    Assumes same day or connection departing within 24h of arrival.
    """
    arr_m = time_to_minutes(arrival_time_str)
    dep_m = time_to_minutes(departure_time_str)
    
    # If connection departure is earlier in clock time than arrival, it likely rolls past midnight
    diff = dep_m - arr_m
    if diff < -720:  # e.g., arrival 23:30, departure 01:00 (+90 mins)
        diff += 1440
    return diff


class JourneyStateEngine:
    """
    Maintains the dynamic state of passenger journeys.
    Aggregates railway events and train running information to calculate:
    - Expected arrival times
    - Dynamic delay deltas
    - Inter-leg connection buffers
    - Overall journey status
    """

    def __init__(self, db: Session):
        self.db = db

    def get_journey_by_id_or_pnr(self, identifier: str) -> Optional[Journey]:
        journey = self.db.query(Journey).filter(Journey.id == identifier).first()
        if not journey:
            journey = self.db.query(Journey).filter(Journey.pnr == identifier.upper()).first()
        return journey

    def recalculate_journey_state(self, journey_id: str) -> Dict[str, Any]:
        """
        Recalculates state for all legs and connection buffers of the journey.
        Updates the database records accordingly.
        """
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        legs = sorted(journey.legs, key=lambda l: l.leg_order)
        if not legs:
            return {"status": journey.status, "legs": []}

        # Compute leg actual/estimated arrival times based on delays
        for leg in legs:
            if leg.delay_arrival_min > 0:
                leg.actual_arrival = calculate_eta(leg.scheduled_arrival, leg.delay_arrival_min)
                leg.status = "DELAYED"
            else:
                leg.actual_arrival = leg.scheduled_arrival
                leg.status = "ON_TIME"

        connection_buffer: Optional[int] = None
        journey_status = "SAFE"

        # If multi-leg connection journey:
        if len(legs) > 1:
            first_leg = legs[0]
            second_leg = legs[1]

            effective_arr = first_leg.actual_arrival or first_leg.scheduled_arrival
            effective_dep = second_leg.actual_departure or second_leg.scheduled_departure

            connection_buffer = calculate_connection_buffer_minutes(effective_arr, effective_dep)

            # Determine baseline journey status based on buffer
            if connection_buffer <= 0:
                journey_status = "MISSED"
            elif connection_buffer < 30:  # default minimum safe buffer 30 mins
                journey_status = "CONNECTION_AT_RISK"
            else:
                journey_status = "SAFE"

        journey.status = journey_status
        journey.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        self.db.refresh(journey)

        return {
            "journey_id": journey.id,
            "pnr": journey.pnr,
            "status": journey.status,
            "connection_buffer_minutes": connection_buffer,
            "legs_count": len(legs),
            "updated_at": journey.updated_at.isoformat()
        }

    def serialize_journey_detail(self, journey: Journey) -> Dict[str, Any]:
        """Convert a Journey entity into a comprehensive state dictionary."""
        legs_data = []
        legs = sorted(journey.legs, key=lambda l: l.leg_order)
        connection_buffer: Optional[int] = None

        for leg in legs:
            train = leg.train
            from_st = leg.from_station
            to_st = leg.to_station

            actual_arr = leg.actual_arrival or calculate_eta(leg.scheduled_arrival, leg.delay_arrival_min)
            actual_dep = leg.actual_departure or leg.scheduled_departure

            legs_data.append({
                "leg_order": leg.leg_order,
                "train_number": leg.train_number,
                "train_name": train.train_name if train else f"Express {leg.train_number}",
                "from_station": {
                    "code": from_st.code if from_st else leg.from_station_code,
                    "name": from_st.name if from_st else leg.from_station_code,
                    "city": from_st.city if from_st else "",
                    "state": from_st.state if from_st else "",
                    "platforms": from_st.platforms if from_st else 4
                },
                "to_station": {
                    "code": to_st.code if to_st else leg.to_station_code,
                    "name": to_st.name if to_st else leg.to_station_code,
                    "city": to_st.city if to_st else "",
                    "state": to_st.state if to_st else "",
                    "platforms": to_st.platforms if to_st else 4
                },
                "scheduled_departure": leg.scheduled_departure,
                "scheduled_arrival": leg.scheduled_arrival,
                "actual_departure": actual_dep,
                "actual_arrival": actual_arr,
                "delay_arrival_min": leg.delay_arrival_min,
                "status": leg.status
            })

        if len(legs) > 1:
            first_arr = legs_data[0]["actual_arrival"]
            second_dep = legs_data[1]["actual_departure"]
            connection_buffer = calculate_connection_buffer_minutes(first_arr, second_dep)

        passenger_name = "Demo Passenger"
        passenger_email = "demo.passenger@railintel.in"
        booking_status = "CNF"
        booking_class = "3A"
        coach = "B2"
        berth_number = 34

        if journey.booking:
            booking_status = journey.booking.booking_status
            booking_class = journey.booking.booking_class
            coach = journey.booking.coach
            berth_number = journey.booking.berth_number
            if journey.booking.passenger:
                passenger_name = journey.booking.passenger.name
                passenger_email = journey.booking.passenger.email

        source_station = self.db.query(Station).filter(Station.code == journey.source_station_code).first()
        dest_station = self.db.query(Station).filter(Station.code == journey.destination_station_code).first()

        return {
            "journey_id": journey.id,
            "pnr": journey.pnr,
            "passenger_name": passenger_name,
            "passenger_email": passenger_email,
            "source_station": {
                "code": source_station.code if source_station else journey.source_station_code,
                "name": source_station.name if source_station else journey.source_station_code,
                "city": source_station.city if source_station else "",
                "state": source_station.state if source_station else "",
                "platforms": source_station.platforms if source_station else 4
            },
            "destination_station": {
                "code": dest_station.code if dest_station else journey.destination_station_code,
                "name": dest_station.name if dest_station else journey.destination_station_code,
                "city": dest_station.city if dest_station else "",
                "state": dest_station.state if dest_station else "",
                "platforms": dest_station.platforms if dest_station else 4
            },
            "journey_date": journey.journey_date,
            "journey_status": journey.status,
            "legs": legs_data,
            "connection_buffer_minutes": connection_buffer,
            "minimum_safe_buffer_minutes": 30,
            "booking_status": booking_status,
            "booking_class": booking_class,
            "coach": coach,
            "berth_number": berth_number,
            "updated_at": journey.updated_at.strftime("%I:%M %p") if journey.updated_at else "Now",
            "data_source": "SIMULATED DATA"
        }
