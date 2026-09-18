import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.database import Base
from backend.models.schema import Station, Train, TrainSchedule, TrainFare, TrainAvailability, TrainLiveStatus, Journey, JourneyLeg, Booking, Passenger
from backend.engines.journey_state import JourneyStateEngine, calculate_connection_buffer_minutes, calculate_eta
from backend.engines.impact_engine import ImpactEngine
from backend.engines.decision_engine import DecisionEngine
from backend.engines.action_engine import ActionEngine
from backend.engines.event_engine import EventEngine
from backend.engines.alternative_engine import AlternativeTrainEngine
from backend.integrations.railway_api import railway_adapter
from backend.ai.strands_agent import strands_assistant


@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # Seed test entities
    s1 = Station(code="CBE", name="Coimbatore", city="Coimbatore", state="TN", platforms=6)
    s2 = Station(code="MAS", name="Chennai Central", city="Chennai", state="TN", platforms=12)
    s3 = Station(code="NDLS", name="New Delhi", city="New Delhi", state="DL", platforms=16)
    session.add_all([s1, s2, s3])
    session.commit()

    t1 = Train(
        train_number="12601",
        train_name="Cheran Express",
        source_station_code="CBE",
        destination_station_code="MAS",
        departure_time="22:30",
        arrival_time="08:30",
        duration_minutes=600,
        running_days="Daily"
    )
    t2 = Train(
        train_number="12615",
        train_name="GT Express",
        source_station_code="MAS",
        destination_station_code="NDLS",
        departure_time="09:20",
        arrival_time="06:30",
        duration_minutes=2110,
        running_days="Daily"
    )
    t3 = Train(
        train_number="12621",
        train_name="Tamil Nadu Express",
        source_station_code="MAS",
        destination_station_code="NDLS",
        departure_time="22:00",
        arrival_time="07:05",
        duration_minutes=1985,
        running_days="Daily"
    )
    session.add_all([t1, t2, t3])
    session.commit()

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    fare = TrainFare(
        train_number="12621",
        journey_date=today_str,
        class_code="3A",
        quota="GN",
        base_fare=2080.0,
        other_charges=160.0,
        total_fare=2240.0
    )
    av = TrainAvailability(
        train_number="12621",
        journey_date=today_str,
        class_type="3A",
        status="AVAILABLE",
        seats_available=56,
        fare=2240.0
    )
    session.add_all([fare, av])
    session.commit()

    p = Passenger(id="P1", name="Test Passenger", email="test@test.com")
    session.add(p)
    session.commit()

    j = Journey(
        id="JRN-TEST-01",
        pnr="TEST123456",
        source_station_code="CBE",
        destination_station_code="NDLS",
        journey_date=today_str,
        status="SAFE"
    )
    session.add(j)
    session.commit()

    leg1 = JourneyLeg(
        journey_id=j.id,
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
        journey_id=j.id,
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
    session.commit()

    yield session
    session.close()


def test_time_calculations():
    assert calculate_connection_buffer_minutes("08:30", "09:20") == 50
    assert calculate_eta("08:30", 75) == "09:45"
    assert calculate_connection_buffer_minutes("09:45", "09:20") == -25


def test_initial_safe_journey_state(db_session):
    state_engine = JourneyStateEngine(db_session)
    res = state_engine.recalculate_journey_state("JRN-TEST-01")
    assert res["status"] == "SAFE"
    assert res["connection_buffer_minutes"] == 50

    impact_engine = ImpactEngine(db_session)
    impact = impact_engine.calculate_journey_impact("JRN-TEST-01")
    assert impact["severity"] == "LOW"
    assert impact["impact_type"] == "SAFE_CONNECTION"


def test_train_delay_and_alternatives(db_session):
    event_engine = EventEngine(db_session)
    result = event_engine.process_event(
        event_type="TRAIN_DELAY",
        train_id="12601",
        payload={"previous_delay": 0, "new_delay": 75, "delay_minutes": 75},
        source="simulation"
    )
    assert result["event_type"] == "TRAIN_DELAY"
    assert result["delay_change"] == 75
    assert len(result["pipeline_steps"]) >= 3

    # Verify Journey State updated
    state_engine = JourneyStateEngine(db_session)
    journey = state_engine.get_journey_by_id_or_pnr("TEST123456")
    legs = sorted(journey.legs, key=lambda l: l.leg_order)
    assert legs[0].delay_arrival_min == 75
    assert legs[0].actual_arrival == "09:45"

    # Verify Alternative Engine finds viable later train
    alt_engine = AlternativeTrainEngine(db_session)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    alts = alt_engine.find_alternative_connections(
        from_station_code="MAS",
        to_station_code="NDLS",
        expected_arrival_time="09:45",
        journey_date=today_str
    )
    assert len(alts) >= 1
    # 12621 leaves at 22:00, which is feasible after 09:45
    tn_exp = next((a for a in alts if a["train_number"] == "12621"), None)
    assert tn_exp is not None
    assert tn_exp["is_feasible"] is True
    assert "₹2240.0" in tn_exp["availabilities"][0]["fare_formatted"]


@pytest.mark.asyncio
async def test_railway_adapter_schedule_and_fares():
    schedule = await railway_adapter.get_train_schedule("12601")
    assert len(schedule) >= 2
    assert schedule[0]["station_code"] == "CBE"

    fare = await railway_adapter.get_train_fare("12601", "2026-09-18", "3A")
    assert "total_fare" in fare
    assert fare["class_code"] == "3A"


@pytest.mark.asyncio
async def test_strands_agent_explanation():
    structured_decision = {
        "situation_status": "AT_RISK",
        "affected_train": "12601",
        "delay_minutes": 75,
        "remaining_buffer_minutes": 10,
        "required_buffer_minutes": 30,
        "expected_arrival": "09:45",
        "connection_train": "12000",
        "system_assessment": "Alternative connection should be reviewed."
    }
    explanation = await strands_assistant.explain_decision(structured_decision)
    assert "explanation" in explanation
    text = explanation["explanation"]
    assert "75 minutes" in text or "75" in text
    assert "10 minutes" in text or "10" in text or "buffer" in text
