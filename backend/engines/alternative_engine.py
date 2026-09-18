from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.schema import Train, TrainAvailability, TrainFare
from backend.engines.journey_state import time_to_minutes


class AlternativeTrainEngine:
    """
    Evaluates backup & alternative connection options when transfer buffer is at risk or missed.
    Queries normalized database and adapter, filters by departure time feasibility,
    and returns verified availability and fares (or explicitly 'Not provided').
    """

    def __init__(self, db: Session):
        self.db = db

    def find_alternative_connections(
        self,
        from_station_code: str,
        to_station_code: str,
        expected_arrival_time: str,
        journey_date: str,
        min_safe_transfer_buffer_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Searches viable connections departing from the interchange station
        at or after (expected_arrival_time + min_safe_transfer_buffer_minutes).
        """
        arr_m = time_to_minutes(expected_arrival_time)
        min_dep_m = arr_m + min_safe_transfer_buffer_minutes

        # Query all trains serving this corridor
        trains = (
            self.db.query(Train)
            .filter(
                Train.source_station_code == from_station_code,
                Train.destination_station_code == to_station_code
            )
            .all()
        )

        alternatives = []
        for t in trains:
            t_dep_m = time_to_minutes(t.departure_time)

            # Check if departure time allows safe transfer
            # (handling same day departure after arrival, or next day if past midnight)
            diff = t_dep_m - arr_m
            if diff < -720:  # rolled past midnight
                diff += 1440

            is_feasible = diff >= min_safe_transfer_buffer_minutes

            # Retrieve availabilities
            av_records = (
                self.db.query(TrainAvailability)
                .filter(
                    TrainAvailability.train_number == t.train_number,
                    TrainAvailability.journey_date == journey_date
                )
                .all()
            )

            # Retrieve fares
            fare_records = (
                self.db.query(TrainFare)
                .filter(
                    TrainFare.train_number == t.train_number,
                    TrainFare.journey_date == journey_date
                )
                .all()
            )
            fare_dict = {f.class_code: f.total_fare for f in fare_records}

            classes_data = []
            if av_records:
                for av in av_records:
                    classes_data.append({
                        "class_type": av.class_type,
                        "status": av.status,
                        "seats_available": av.seats_available,
                        "fare_formatted": f"₹{fare_dict.get(av.class_type, av.fare)}" if av.fare or av.class_type in fare_dict else "Not provided"
                    })
            else:
                classes_data.append({
                    "class_type": "3A",
                    "status": "Not provided",
                    "seats_available": 0,
                    "fare_formatted": "Not provided"
                })

            alternatives.append({
                "train_number": t.train_number,
                "train_name": t.train_name,
                "from_station": from_station_code,
                "to_station": to_station_code,
                "departure_time": t.departure_time,
                "arrival_time": t.arrival_time,
                "duration_minutes": t.duration_minutes,
                "transfer_window_minutes": diff,
                "is_feasible": is_feasible,
                "feasibility_tag": "FEASIBLE" if is_feasible else "TIGHT_OR_BEFORE_ARRIVAL",
                "availabilities": classes_data
            })

        # Sort: feasible trains first, ordered by departure time
        alternatives.sort(key=lambda x: (not x["is_feasible"], x["transfer_window_minutes"]))
        return alternatives
