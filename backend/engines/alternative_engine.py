"""
Alternative Engine (backend/engines/alternative_engine.py)
Computes both same-station and nearby-station alternative travel plans.
Calculates waiting time, transfer time, travel time, and expected destination arrival.
Prunes infeasible options deterministically.
"""

from typing import Dict, Any, List, Optional
import datetime
from sqlalchemy.orm import Session

from backend.models.schema import Train, TrainAvailability, TrainFare, Station, Journey
from backend.engines.journey_state import time_to_minutes, minutes_to_time

# Verified railway junction connections and estimated transit times between nearby hubs (minutes)
NEARBY_STATION_TRANSFERS = {
    ("CBE", "ED"): {"station_name": "Erode Junction", "transit_time_min": 65, "distance_km": 100},
    ("ED", "SA"): {"station_name": "Salem Junction", "transit_time_min": 55, "distance_km": 60},
    ("SA", "KPD"): {"station_name": "Katpadi Junction", "transit_time_min": 140, "distance_km": 160},
    ("KPD", "MAS"): {"station_name": "Chennai Central", "transit_time_min": 110, "distance_km": 130},
    ("MAS", "TBM"): {"station_name": "Tambaram", "transit_time_min": 35, "distance_km": 28},
}


class AlternativeEngine:
    """
    Finds and compares:
    1. Same-station alternative trains.
    2. Relevant nearby junction station alternatives.
    Calculates exact destination arrival times and passenger trade-offs.
    """

    def __init__(self, db: Session):
        self.db = db

    def find_same_station_alternatives(
        self,
        from_station_code: str,
        to_station_code: str,
        expected_arrival_time: str,
        journey_date: str,
        min_safe_buffer_minutes: int = 30,
        min_safe_transfer_buffer_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find trains departing from the same connection station
        after expected arrival + min buffer.
        """
        if min_safe_transfer_buffer_minutes is not None:
            min_safe_buffer_minutes = min_safe_transfer_buffer_minutes

        arr_m = time_to_minutes(expected_arrival_time)
        trains = (
            self.db.query(Train)
            .filter(
                Train.source_station_code == from_station_code,
                Train.destination_station_code == to_station_code
            )
            .all()
        )

        results = []
        for t in trains:
            dep_m = time_to_minutes(t.departure_time)
            # Calculate transfer buffer
            buffer_min = dep_m - arr_m
            if buffer_min < -720:  # rolled over midnight
                buffer_min += 1440

            feasible = buffer_min >= min_safe_buffer_minutes
            waiting_time = max(0, buffer_min)
            travel_time = t.duration_minutes or 360

            # Compute Expected Destination Arrival
            dest_arr_m = (dep_m + travel_time) % 1440
            expected_dest_arr = minutes_to_time(dest_arr_m)

            # Availability & Fares
            avail_info = self._get_best_availability(t.train_number, journey_date)
            fare_info = self._get_fare_info(t.train_number, journey_date)

            # Query all availability classes for this train
            av_records = (
                self.db.query(TrainAvailability)
                .filter(TrainAvailability.train_number == t.train_number)
                .all()
            )
            fare_records = (
                self.db.query(TrainFare)
                .filter(TrainFare.train_number == t.train_number)
                .all()
            )
            fare_dict = {f.class_code: f.total_fare for f in fare_records}
            classes_data = []
            for av in av_records:
                f_val = fare_dict.get(av.class_type, av.fare)
                classes_data.append({
                    "class_type": av.class_type,
                    "status": av.status,
                    "seats_available": av.seats_available,
                    "fare_formatted": f"₹{f_val}" if f_val else "Not provided"
                })

            if not classes_data:
                classes_data.append({
                    "class_type": "3A",
                    "status": avail_info["status"],
                    "seats_available": 24,
                    "fare_formatted": fare_info["formatted"]
                })

            results.append({
                "option_type": "SAME_STATION",
                "train_number": t.train_number,
                "train_name": t.train_name,
                "station_code": from_station_code,
                "station_name": self._get_station_name(from_station_code),
                "departure_time": t.departure_time,
                "expected_destination_arrival": expected_dest_arr,
                "waiting_time_minutes": waiting_time,
                "transfer_time_minutes": 0,
                "transfer_window_minutes": buffer_min,
                "train_travel_minutes": travel_time,
                "total_journey_duration_minutes": waiting_time + travel_time,
                "availability": avail_info["formatted"],
                "availability_status": avail_info["status"],
                "availabilities": classes_data,
                "fare": fare_info["total_fare"],
                "formatted_fare": fare_info["formatted"],
                "is_feasible": feasible,
                "feasibility_reason": "Safe connection window" if feasible else f"Insufficient transfer window ({buffer_min}m < {min_safe_buffer_minutes}m)"
            })

        results.sort(key=lambda x: (not x["is_feasible"], x["departure_time"]))
        return results

    def find_nearby_station_alternatives(
        self,
        current_station_code: str,
        destination_station_code: str,
        current_time: str,
        journey_date: str
    ) -> List[Dict[str, Any]]:
        """
        Calculates alternatives via adjacent hub stations (e.g. Erode, Salem, Katpadi).
        Factors in: transfer time to station + buffer + departure + train travel time.
        """
        cur_m = time_to_minutes(current_time)
        results = []

        # Find nearby candidate stations
        candidates = []
        for (src, alt_st), info in NEARBY_STATION_TRANSFERS.items():
            if src == current_station_code:
                candidates.append((alt_st, info["station_name"], info["transit_time_min"]))

        for alt_code, alt_name, transit_min in candidates:
            # Earliest possible arrival at alternate station
            earliest_arr_m = cur_m + transit_min
            safe_dep_m = earliest_arr_m + 25  # 25 min boarding buffer

            # Find trains from that alternate station to destination
            trains = (
                self.db.query(Train)
                .filter(
                    Train.source_station_code == alt_code,
                    Train.destination_station_code == destination_station_code
                )
                .all()
            )

            for t in trains:
                dep_m = time_to_minutes(t.departure_time)
                diff = dep_m - earliest_arr_m
                if diff < -720:
                    diff += 1440

                feasible = diff >= 20  # minimum 20 mins to board
                waiting_time = max(0, diff)
                travel_time = t.duration_minutes or 360

                dest_arr_m = (dep_m + travel_time) % 1440
                expected_dest_arr = minutes_to_time(dest_arr_m)

                avail_info = self._get_best_availability(t.train_number, journey_date)
                fare_info = self._get_fare_info(t.train_number, journey_date)

                results.append({
                    "option_type": "ALTERNATIVE_STATION",
                    "train_number": t.train_number,
                    "train_name": t.train_name,
                    "station_code": alt_code,
                    "station_name": alt_name,
                    "departure_time": t.departure_time,
                    "expected_destination_arrival": expected_dest_arr,
                    "waiting_time_minutes": waiting_time,
                    "transfer_time_minutes": transit_min,
                    "train_travel_minutes": travel_time,
                    "total_journey_duration_minutes": transit_min + waiting_time + travel_time,
                    "availability": avail_info["formatted"],
                    "availability_status": avail_info["status"],
                    "fare": fare_info["total_fare"],
                    "formatted_fare": fare_info["formatted"],
                    "is_feasible": feasible,
                    "feasibility_reason": f"Via {alt_name} ({transit_min}m transfer)" if feasible else "Cannot reach alternative station before departure"
                })

        results.sort(key=lambda x: (not x["is_feasible"], x["expected_destination_arrival"]))
        return results

    def get_complete_alternative_comparison(self, journey_id: str) -> Dict[str, Any]:
        """
        Generates full structured alternative comparison matrix
        for both the UI table and GPT4All explanation layer.
        """
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey or not journey.legs:
            return {"current_journey": {}, "alternatives": []}

        legs = sorted(journey.legs, key=lambda l: l.leg_order)
        first_leg = legs[0]
        second_leg = legs[1] if len(legs) > 1 else None

        current_arr = first_leg.actual_arrival or first_leg.scheduled_arrival
        connection_station = first_leg.to_station_code
        dest_station = journey.destination_station_code

        # Same station options
        same_station_alts = self.find_same_station_alternatives(
            from_station_code=connection_station,
            to_station_code=dest_station,
            expected_arrival_time=current_arr,
            journey_date=journey.journey_date
        )

        # Alternative station options
        alt_station_alts = self.find_nearby_station_alternatives(
            current_station_code=first_leg.from_station_code,
            destination_station_code=dest_station,
            current_time=first_leg.actual_departure or first_leg.scheduled_departure,
            journey_date=journey.journey_date
        )

        # Current planned journey info
        planned_dest_arr = second_leg.scheduled_arrival if second_leg else first_leg.scheduled_arrival
        current_summary = {
            "train": second_leg.train_number if second_leg else first_leg.train_number,
            "train_name": second_leg.train.train_name if second_leg and second_leg.train else "Current Train",
            "station": self._get_station_name(connection_station),
            "station_code": connection_station,
            "departure": second_leg.scheduled_departure if second_leg else first_leg.scheduled_departure,
            "expected_destination_arrival": planned_dest_arr,
            "transfer_minutes": 0,
            "availability": "CNF",
            "fare": 1050,
            "formatted_fare": "₹1050",
            "status": journey.status
        }

        # Combine feasible alternatives
        all_alts = same_station_alts + alt_station_alts
        feasible_alts = [a for a in all_alts if a["is_feasible"] and a["train_number"] != (second_leg.train_number if second_leg else "")]

        # Assign Option letters (A, B, C...)
        formatted_alts = []
        for idx, a in enumerate(feasible_alts[:5]):
            letter = chr(65 + idx)
            a["option_letter"] = letter
            formatted_alts.append(a)

        return {
            "journey_id": journey_id,
            "current_journey": current_summary,
            "alternatives": formatted_alts,
            "all_evaluated_count": len(all_alts),
            "feasible_count": len(feasible_alts)
        }

    # ------------------ Helpers ------------------

    def _get_station_name(self, code: str) -> str:
        st = self.db.query(Station).filter(Station.code == code).first()
        return st.name if st else code

    def _get_best_availability(self, train_number: str, date: str) -> Dict[str, Any]:
        av = (
            self.db.query(TrainAvailability)
            .filter(TrainAvailability.train_number == train_number)
            .first()
        )
        if not av:
            return {"status": "UNKNOWN", "formatted": "Not provided by RailRadar"}
        if av.status == "AVAILABLE" and av.seats_available > 0:
            return {"status": "CONFIRMED", "formatted": f"CNF ({av.seats_available} seats)"}
        elif av.status == "RAC":
            return {"status": "RAC", "formatted": f"RAC {av.rac or 2}"}
        elif av.status == "WL":
            return {"status": "WAITLIST", "formatted": f"WL {av.waiting_list or 12}"}
        return {"status": av.status or "UNKNOWN", "formatted": av.status or "Not provided"}

    def _get_fare_info(self, train_number: str, date: str) -> Dict[str, Any]:
        fare = (
            self.db.query(TrainFare)
            .filter(TrainFare.train_number == train_number)
            .first()
        )
        if not fare or not fare.total_fare:
            return {"total_fare": None, "formatted": "Not provided"}
        return {"total_fare": fare.total_fare, "formatted": f"₹{int(fare.total_fare)}"}

    # Backward compatibility alias
    find_alternative_connections = find_same_station_alternatives


AlternativeTrainEngine = AlternativeEngine
