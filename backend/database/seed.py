import datetime
import json
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal, init_db
from backend.models.schema import (
    Passenger, PassengerContact, NotificationRecord, Station, Train, TrainSchedule,
    TrainLiveStatus, TrainAvailability, TrainFare, Booking, Journey, JourneyLeg,
    Decision, Recommendation, DataRefreshLog
)
from backend.engines.journey_state import JourneyStateEngine
from backend.engines.action_engine import ActionEngine


def seed_database(db: Session):
    """Populate database with initial realistic demo data."""
    # Check if already seeded
    if db.query(Journey).filter(Journey.pnr == "DEMO123456").first():
        return

    # 1. Stations
    stations = [
        Station(code="CBE", name="Coimbatore Junction", city="Coimbatore", state="Tamil Nadu", platforms=6),
        Station(code="MAS", name="Chennai Central (MGR)", city="Chennai", state="Tamil Nadu", platforms=12),
        Station(code="NDLS", name="New Delhi", city="New Delhi", state="Delhi", platforms=16),
        Station(code="SBC", name="KSR Bengaluru City", city="Bengaluru", state="Karnataka", platforms=10),
        Station(code="ED", name="Erode Junction", city="Erode", state="Tamil Nadu", platforms=4),
        Station(code="SA", name="Salem Junction", city="Salem", state="Tamil Nadu", platforms=6),
        Station(code="KPD", name="Katpadi Junction", city="Vellore", state="Tamil Nadu", platforms=5),
        Station(code="TUP", name="Tiruppur", city="Tiruppur", state="Tamil Nadu", platforms=2)
    ]
    for st in stations:
        existing = db.query(Station).filter(Station.code == st.code).first()
        if not existing:
            db.add(st)
    db.commit()

    # 2. Trains
    trains = [
        Train(
            train_number="12601",
            train_name="Cheran Superfast Express",
            source_station_code="CBE",
            destination_station_code="MAS",
            departure_time="22:30",
            arrival_time="08:30",
            duration_minutes=600,
            running_days="Daily",
            train_type="Superfast Express"
        ),
        Train(
            train_number="12615",
            train_name="Grand Trunk (GT) Express",
            source_station_code="MAS",
            destination_station_code="NDLS",
            departure_time="09:20",
            arrival_time="06:30",
            duration_minutes=2110,
            running_days="Daily",
            train_type="Superfast Express"
        ),
        Train(
            train_number="12676",
            train_name="Kovai Express",
            source_station_code="CBE",
            destination_station_code="MAS",
            departure_time="15:15",
            arrival_time="22:50",
            duration_minutes=455,
            running_days="Daily",
            train_type="InterCity Superfast"
        ),
        Train(
            train_number="22625",
            train_name="Chennai AC Double Decker",
            source_station_code="CBE",
            destination_station_code="MAS",
            departure_time="06:10",
            arrival_time="13:30",
            duration_minutes=440,
            running_days="Mon,Tue,Wed,Thu,Fri,Sat",
            train_type="Double Decker AC"
        ),
        Train(
            train_number="12679",
            train_name="Coimbatore InterCity SF",
            source_station_code="CBE",
            destination_station_code="MAS",
            departure_time="14:20",
            arrival_time="22:15",
            duration_minutes=475,
            running_days="Daily",
            train_type="Superfast Express"
        ),
        Train(
            train_number="12621",
            train_name="Tamil Nadu Express",
            source_station_code="MAS",
            destination_station_code="NDLS",
            departure_time="22:00",
            arrival_time="07:05",
            duration_minutes=1985,
            running_days="Daily",
            train_type="Superfast Express"
        ),
        Train(
            train_number="12433",
            train_name="Chennai Rajdhani Express",
            source_station_code="MAS",
            destination_station_code="NDLS",
            departure_time="06:05",
            arrival_time="10:40",
            duration_minutes=1715,
            running_days="Fri,Sun",
            train_type="Rajdhani Express"
        )
    ]
    for tr in trains:
        existing = db.query(Train).filter(Train.train_number == tr.train_number).first()
        if not existing:
            db.add(tr)
    db.commit()

    # 3. Train Schedules (Halts)
    schedules = [
        TrainSchedule(train_number="12601", station_code="CBE", station_name="Coimbatore Jn", arrival_time="22:30", departure_time="22:30", day=1, sequence=1),
        TrainSchedule(train_number="12601", station_code="TUP", station_name="Tiruppur", arrival_time="23:13", departure_time="23:15", day=1, sequence=2),
        TrainSchedule(train_number="12601", station_code="ED", station_name="Erode Jn", arrival_time="00:05", departure_time="00:10", day=2, sequence=3),
        TrainSchedule(train_number="12601", station_code="SA", station_name="Salem Jn", arrival_time="01:02", departure_time="01:05", day=2, sequence=4),
        TrainSchedule(train_number="12601", station_code="KPD", station_name="Katpadi Jn", arrival_time="05:18", departure_time="05:20", day=2, sequence=5),
        TrainSchedule(train_number="12601", station_code="MAS", station_name="Chennai Central", arrival_time="08:30", departure_time="08:30", day=2, sequence=6),
        # 12615 GT Express
        TrainSchedule(train_number="12615", station_code="MAS", station_name="Chennai Central", arrival_time="09:20", departure_time="09:20", day=1, sequence=1),
        TrainSchedule(train_number="12615", station_code="NDLS", station_name="New Delhi", arrival_time="06:30", departure_time="06:30", day=3, sequence=2)
    ]
    for sch in schedules:
        db.add(sch)
    db.commit()

    # 4. Train Fares
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    fares = [
        TrainFare(train_number="12601", journey_date=today_str, class_code="1A", quota="GN", base_fare=2280.0, other_charges=200.0, total_fare=2480.0, source="simulation", is_live=False),
        TrainFare(train_number="12601", journey_date=today_str, class_code="2A", quota="GN", base_fare=1340.0, other_charges=150.0, total_fare=1490.0, source="simulation", is_live=False),
        TrainFare(train_number="12601", journey_date=today_str, class_code="3A", quota="GN", base_fare=950.0, other_charges=100.0, total_fare=1050.0, source="simulation", is_live=False),
        TrainFare(train_number="12601", journey_date=today_str, class_code="SL", quota="GN", base_fare=340.0, other_charges=50.0, total_fare=390.0, source="simulation", is_live=False),
        # 12615 GT Express
        TrainFare(train_number="12615", journey_date=today_str, class_code="2A", quota="GN", base_fare=2980.0, other_charges=230.0, total_fare=3210.0, source="simulation", is_live=False),
        TrainFare(train_number="12615", journey_date=today_str, class_code="3A", quota="GN", base_fare=2080.0, other_charges=160.0, total_fare=2240.0, source="simulation", is_live=False),
        # 12621 TN Express
        TrainFare(train_number="12621", journey_date=today_str, class_code="1A", quota="GN", base_fare=5120.0, other_charges=300.0, total_fare=5420.0, source="simulation", is_live=False),
        TrainFare(train_number="12621", journey_date=today_str, class_code="2A", quota="GN", base_fare=2980.0, other_charges=230.0, total_fare=3210.0, source="simulation", is_live=False),
        TrainFare(train_number="12621", journey_date=today_str, class_code="3A", quota="GN", base_fare=2080.0, other_charges=160.0, total_fare=2240.0, source="simulation", is_live=False)
    ]
    for fare in fares:
        db.add(fare)
    db.commit()

    # 5. Train Live Status (Baseline)
    live_statuses = [
        TrainLiveStatus(train_number="12601", station_code="CBE", expected_arrival="08:30", expected_departure="22:30", delay_minutes=0, status="ON_TIME", source="simulation", is_live=False),
        TrainLiveStatus(train_number="12615", station_code="MAS", expected_arrival="06:30", expected_departure="09:20", delay_minutes=0, status="ON_TIME", source="simulation", is_live=False)
    ]
    for ls in live_statuses:
        db.add(ls)
    db.commit()

    # 6. Train Availabilities
    availabilities = [
        TrainAvailability(train_number="12601", journey_date=today_str, class_type="1A", quota="GN", status="AVAILABLE", seats_available=6, fare=2480.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12601", journey_date=today_str, class_type="2A", quota="GN", status="AVAILABLE", seats_available=18, fare=1490.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12601", journey_date=today_str, class_type="3A", quota="GN", status="AVAILABLE", seats_available=42, fare=1050.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12601", journey_date=today_str, class_type="SL", quota="GN", status="RAC", seats_available=12, rac=12, fare=390.0, source="simulation", is_live=False),
        # 12615 GT Express
        TrainAvailability(train_number="12615", journey_date=today_str, class_type="2A", quota="GN", status="AVAILABLE", seats_available=14, fare=3210.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12615", journey_date=today_str, class_type="3A", quota="GN", status="AVAILABLE", seats_available=38, fare=2240.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12615", journey_date=today_str, class_type="SL", quota="GN", status="AVAILABLE", seats_available=85, fare=850.0, source="simulation", is_live=False),
        # 12621 TN Express (Alternative)
        TrainAvailability(train_number="12621", journey_date=today_str, class_type="1A", quota="GN", status="AVAILABLE", seats_available=4, fare=5420.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12621", journey_date=today_str, class_type="2A", quota="GN", status="AVAILABLE", seats_available=22, fare=3210.0, source="simulation", is_live=False),
        TrainAvailability(train_number="12621", journey_date=today_str, class_type="3A", quota="GN", status="AVAILABLE", seats_available=56, fare=2240.0, source="simulation", is_live=False)
    ]
    for av in availabilities:
        db.add(av)
    db.commit()

    # 7. Passenger & Contact
    passenger = Passenger(
        id="PASS-DEMO-01",
        name="Kishore Stalin",
        email="kishore@example.com",
        phone="+91 98401 23456"
    )
    db.add(passenger)
    db.commit()

    contact = PassengerContact(
        contact_id="CONT-DEMO-01",
        passenger_id=passenger.id,
        name="Kishore Stalin",
        email="kishore@example.com",
        phone="+91 98401 23456",
        email_notifications_enabled=True,
        sms_notifications_enabled=True
    )
    db.add(contact)
    db.commit()

    # 8. Demo Journey: Coimbatore -> Chennai Central -> New Delhi
    journey = Journey(
        id="JRN-DEMO-01",
        pnr="DEMO123456",
        source_station_code="CBE",
        destination_station_code="NDLS",
        journey_date=today_str,
        status="SAFE"
    )
    db.add(journey)
    db.commit()

    # 9. Journey Legs
    leg1 = JourneyLeg(
        journey_id=journey.id,
        leg_order=1,
        train_number="12601",
        from_station_code="CBE",
        to_station_code="MAS",
        scheduled_departure="22:30",
        scheduled_arrival="08:30",
        actual_departure="22:30",
        actual_arrival="08:30",
        delay_departure_min=0,
        delay_arrival_min=0,
        status="ON_TIME"
    )
    leg2 = JourneyLeg(
        journey_id=journey.id,
        leg_order=2,
        train_number="12615",
        from_station_code="MAS",
        to_station_code="NDLS",
        scheduled_departure="09:20",
        scheduled_arrival="06:30",
        actual_departure="09:20",
        actual_arrival="06:30",
        delay_departure_min=0,
        delay_arrival_min=0,
        status="ON_TIME"
    )
    db.add(leg1)
    db.add(leg2)
    db.commit()

    # 10. Booking
    booking = Booking(
        pnr="DEMO123456",
        passenger_id=passenger.id,
        journey_id=journey.id,
        booking_status="CNF",
        booking_class="3A",
        coach="B2",
        berth_number=34
    )
    db.add(booking)
    db.commit()

    # 11. Trigger Initial Decision and Recommendation
    action_engine = ActionEngine(db)
    action_engine.generate_recommendation(journey.id)


def reset_demo_journey(db: Session):
    """Reset the demo journey back to baseline state (+0 delay, 50 min safe buffer)."""
    journey = db.query(Journey).filter(Journey.pnr == "DEMO123456").first()
    if not journey:
        seed_database(db)
        return

    legs = sorted(journey.legs, key=lambda l: l.leg_order)
    if legs:
        legs[0].delay_arrival_min = 0
        legs[0].delay_departure_min = 0
        legs[0].actual_arrival = "08:30"
        legs[0].status = "ON_TIME"

        if len(legs) > 1:
            legs[1].delay_arrival_min = 0
            legs[1].delay_departure_min = 0
            legs[1].actual_arrival = "06:30"
            legs[1].status = "ON_TIME"

    journey.status = "SAFE"
    journey.updated_at = datetime.datetime.utcnow()

    # Reset live status
    live_status = db.query(TrainLiveStatus).filter(TrainLiveStatus.train_number == "12601").first()
    if live_status:
        live_status.delay_minutes = 0
        live_status.expected_arrival = "08:30"
        live_status.status = "ON_TIME"

    db.commit()

    # Regenerate fresh safe decision and recommendation
    action_engine = ActionEngine(db)
    action_engine.generate_recommendation(journey.id)
