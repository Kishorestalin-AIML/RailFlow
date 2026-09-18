"""
Unit tests for RailRadar integration, Alternative Engine, Notifications, and GPT4All Agent.
"""

import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base
from backend.models.schema import (
    Station, Train, TrainSchedule, TrainFare, TrainAvailability,
    Journey, JourneyLeg, Booking, Passenger, PassengerContact, NotificationRecord
)
from backend.integrations.railradar_client import (
    RailRadarClient, RailRadarAuthError, RailRadarRateLimitError, RailRadarServiceError
)
from backend.integrations.railway_api import RailwayApiAdapter
from backend.engines.alternative_engine import AlternativeEngine
from backend.services.notification_service import NotificationService
from backend.ai.gpt4all_agent import gpt4all_agent


@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # Seed test stations
    s1 = Station(code="CBE", name="Coimbatore Junction", city="Coimbatore", state="Tamil Nadu", platforms=6)
    s2 = Station(code="ED", name="Erode Junction", city="Erode", state="Tamil Nadu", platforms=4)
    s3 = Station(code="MAS", name="Chennai Central", city="Chennai", state="Tamil Nadu", platforms=12)
    s4 = Station(code="NDLS", name="New Delhi", city="New Delhi", state="Delhi", platforms=16)
    session.add_all([s1, s2, s3, s4])
    session.commit()

    # Trains
    t1 = Train(
        train_number="12601",
        train_name="Cheran SF Express",
        source_station_code="CBE",
        destination_station_code="MAS",
        departure_time="22:30",
        arrival_time="08:30",
        duration_minutes=600
    )
    t2 = Train(
        train_number="12615",
        train_name="GT Express",
        source_station_code="MAS",
        destination_station_code="NDLS",
        departure_time="09:20",
        arrival_time="06:30",
        duration_minutes=2110
    )
    # Alternative from MAS
    t3 = Train(
        train_number="12621",
        train_name="Tamil Nadu Express",
        source_station_code="MAS",
        destination_station_code="NDLS",
        departure_time="22:00",
        arrival_time="07:05",
        duration_minutes=1985
    )
    # Alternative from nearby station ED
    t4 = Train(
        train_number="12626",
        train_name="Kerala Express",
        source_station_code="ED",
        destination_station_code="NDLS",
        departure_time="19:00",
        arrival_time="13:40",
        duration_minutes=2560
    )
    session.add_all([t1, t2, t3, t4])
    session.commit()

    # Passenger & Contact
    p = Passenger(id="P1", name="Kishore Stalin", email="kishore@example.com", phone="+91 98401 23456")
    session.add(p)
    session.commit()

    contact = PassengerContact(
        contact_id="C1",
        passenger_id="P1",
        name="Kishore Stalin",
        email="kishore@example.com",
        phone="+91 98401 23456",
        email_notifications_enabled=True,
        sms_notifications_enabled=True
    )
    session.add(contact)
    session.commit()

    # Journey
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    j = Journey(
        id="JRN-TEST-02",
        pnr="PNRTEST789",
        source_station_code="CBE",
        destination_station_code="NDLS",
        journey_date=today_str,
        status="SAFE"
    )
    session.add(j)
    session.commit()

    leg1 = JourneyLeg(
        journey_id="JRN-TEST-02",
        leg_order=1,
        train_number="12601",
        from_station_code="CBE",
        to_station_code="MAS",
        scheduled_departure="22:30",
        scheduled_arrival="08:30",
        actual_departure="22:30",
        actual_arrival="08:30",
        delay_arrival_min=0,
        status="ON_TIME"
    )
    leg2 = JourneyLeg(
        journey_id="JRN-TEST-02",
        leg_order=2,
        train_number="12615",
        from_station_code="MAS",
        to_station_code="NDLS",
        scheduled_departure="09:20",
        scheduled_arrival="06:30",
        actual_departure="09:20",
        actual_arrival="06:30",
        delay_arrival_min=0,
        status="ON_TIME"
    )
    session.add_all([leg1, leg2])

    bk = Booking(
        pnr="PNRTEST789",
        passenger_id="P1",
        journey_id="JRN-TEST-02",
        booking_status="CNF",
        booking_class="3A",
        coach="B1",
        berth_number=21
    )
    session.add(bk)
    session.commit()

    yield session
    session.close()


def test_railradar_error_handling():
    """Verify RailRadar custom exceptions and error messages per Section 32."""
    client = RailRadarClient(api_key="TEST_KEY")
    assert client.is_configured is True

    # Check exception messages
    auth_err = RailRadarAuthError()
    assert auth_err.status_code == 401
    assert "authentication failed" in auth_err.message

    rate_err = RailRadarRateLimitError()
    assert rate_err.status_code == 429
    assert "rate limit reached" in rate_err.message

    svc_err = RailRadarServiceError()
    assert svc_err.status_code == 503
    assert "temporarily unavailable" in svc_err.message


def test_alternative_engine_comparison(db_session):
    """Verify AlternativeEngine generates complete comparison matrix with expected arrival times."""
    engine = AlternativeEngine(db_session)
    matrix = engine.get_complete_alternative_comparison("JRN-TEST-02")

    assert "current_journey" in matrix
    assert "alternatives" in matrix
    assert len(matrix["alternatives"]) >= 1

    # Check first alternative fields per Section 11 & 27
    alt = matrix["alternatives"][0]
    assert "train_number" in alt
    assert "station_code" in alt
    assert "departure_time" in alt
    assert "expected_destination_arrival" in alt
    assert "waiting_time_minutes" in alt
    assert "transfer_time_minutes" in alt
    assert "availability" in alt
    assert "is_feasible" in alt


@pytest.mark.asyncio
async def test_notification_service(db_session):
    """Verify NotificationService threshold checking and dispatch logic."""
    notif_svc = NotificationService(db_session)

    # 1. Should not notify for negligible 5m delay
    assert not notif_svc.should_notify(
        journey_id="JRN-TEST-02",
        event_type="TRAIN_DELAY",
        delay_minutes=5,
        previous_status="SAFE",
        current_status="SAFE"
    )

    # 2. Should notify when delay >= 30m or state becomes AT_RISK
    assert notif_svc.should_notify(
        journey_id="JRN-TEST-02",
        event_type="TRAIN_DELAY",
        delay_minutes=65,
        previous_status="SAFE",
        current_status="AT_RISK"
    )

    # 3. Test alert dispatch
    results = await notif_svc.send_disruption_alert(
        journey_id="JRN-TEST-02",
        passenger_id="P1",
        passenger_name="Kishore Stalin",
        train_number="12601",
        delay_minutes=65,
        expected_arrival="20:45",
        journey_status="AT_RISK",
        alternatives=[
            {
                "train": "12621",
                "station": "Chennai Central",
                "departure": "22:00",
                "expected_destination_arrival": "07:05",
                "transfer_time": 0,
                "availability": "CNF (Available 22)",
                "fare": 2240
            }
        ]
    )
    assert len(results) == 2  # SMS + Email
    assert results[0]["status"] in ["SENT", "SIMULATED"]
    assert results[1]["status"] in ["SENT", "SIMULATED"]

    # Verify stored in database
    records = db_session.query(NotificationRecord).filter(NotificationRecord.journey_id == "JRN-TEST-02").all()
    assert len(records) == 2


def test_gpt4all_agent_trade_off_explanation():
    """Verify GPT4All structured explanation answers all required sections and compares trade-offs."""
    payload = {
        "journey_status": "AT_RISK",
        "current_train": {
            "number": "12601",
            "delay_minutes": 65,
            "expected_arrival": "20:45"
        },
        "alternatives": [
            {
                "option": "A",
                "station": "Erode",
                "train": "12626",
                "departure": "18:20",
                "expected_destination_arrival": "22:40",
                "transfer_minutes": 35,
                "availability": "RAC 2",
                "fare": 850,
                "feasible": True
            },
            {
                "option": "B",
                "station": "Chennai Central",
                "train": "12621",
                "departure": "22:00",
                "expected_destination_arrival": "07:05",
                "transfer_minutes": 0,
                "availability": "CNF",
                "fare": 2240,
                "feasible": True
            }
        ]
    }

    explanation = gpt4all_agent.explain_journey(payload)
    assert "What changed?" in explanation
    assert "Why does it matter?" in explanation
    assert "Alternative ways to reach your destination" in explanation
    assert "Important trade-offs" in explanation
    assert "65 minutes" in explanation
    # Verifies trade-off analysis between RAC earlier arrival vs CNF
    assert "RAC" in explanation or "trade-off" in explanation.lower()
