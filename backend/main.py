import os
import json
import uuid
import asyncio
import datetime
import logging
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from backend.database.database import get_db, init_db, SessionLocal
from backend.database.seed import seed_database, reset_demo_journey
from backend.models.schema import (
    Train, Station, RailwayEvent, Journey, JourneyLeg, Booking,
    TrainSchedule, TrainFare, TrainAvailability, TrainLiveStatus,
    Passenger, PassengerContact, NotificationRecord
)
from backend.schemas.api_schemas import (
    JourneyDetailResponse,
    TrainSearchResult,
    TrainInfo,
    ImpactResult,
    DecisionResult,
    RecommendationResult,
    EventInjectionRequest,
    PassengerRegistrationRequest,
    PassengerResponse,
    JourneyCreateRequest,
    NotificationItem,
    GPT4AllExplainRequest,
    GPT4AllExplainResponse,
    SystemHealthResponse
)
from backend.integrations.railway_api import railway_adapter
from backend.integrations.railradar_client import railradar_client
from backend.integrations.sms_provider import sms_provider
from backend.integrations.email_provider import email_provider
from backend.engines.journey_state import JourneyStateEngine
from backend.engines.impact_engine import ImpactEngine
from backend.engines.decision_engine import DecisionEngine
from backend.engines.action_engine import ActionEngine
from backend.engines.event_engine import EventEngine
from backend.engines.alternative_engine import AlternativeEngine
from backend.ai.gpt4all_agent import gpt4all_agent
from backend.services.live_update_service import live_update_service
from backend.services.notification_service import NotificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("railmind")

app = FastAPI(
    title="RailMind - Real-Time Railway Journey Intelligence",
    description="Operational intelligence and decision support layer above Indian Railway information systems powered by RailRadar API and local GPT4All LLM.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory broadcast event queue for SSE
sse_subscribers: List[asyncio.Queue] = []


async def broadcast_event_update(event_data: Dict[str, Any]):
    """Broadcast real-time events to all connected SSE clients."""
    payload = json.dumps(event_data)
    for queue in list(sse_subscribers):
        try:
            await queue.put(payload)
        except Exception:
            if queue in sse_subscribers:
                sse_subscribers.remove(queue)


@app.on_event("startup")
async def on_startup():
    init_db()
    with SessionLocal() as db:
        seed_database(db)
    logger.info("RailMind database initialized and seeded.")
    # Start the live update background polling service
    await live_update_service.start(broadcast_callback=broadcast_event_update)


@app.on_event("shutdown")
async def on_shutdown():
    await live_update_service.stop()


# ------------------- HEALTH & SYSTEM STATUS -------------------

@app.get("/health", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    journeys_count = db.query(Journey).count()
    events_count = db.query(RailwayEvent).count()
    return SystemHealthResponse(
        status="HEALTHY",
        database="SQLite3 (railway.db)",
        data_adapter_mode=railway_adapter.current_data_source,
        data_adapter_base_url=railradar_client.base_url,
        strands_status="READY (GPT4All Local LLM)",
        active_journeys_count=journeys_count,
        events_count=events_count,
        last_updated=datetime.datetime.utcnow().strftime("%I:%M %p UTC")
    )


@app.get("/system/status")
def get_system_status(db: Session = Depends(get_db)):
    """Detailed judge-facing system status & architectural stats."""
    return {
        "system_name": "RailMind - Railway Passenger Intelligence",
        "version": "2.0.0",
        "architecture_pipeline": "RAILRADAR API -> NORMALIZATION -> EVENT DETECTION -> JOURNEY STATE -> IMPACT -> ALTERNATIVE ENGINE -> DECISION ENGINE -> GPT4ALL -> SMS/EMAIL -> REACT",
        "database": {
            "type": "SQLite3",
            "file": "railway.db",
            "tables": {
                "passengers": db.query(Passenger).count(),
                "passenger_contacts": db.query(PassengerContact).count(),
                "trains": db.query(Train).count(),
                "journeys": db.query(Journey).count(),
                "notifications": db.query(NotificationRecord).count(),
                "events": db.query(RailwayEvent).count(),
                "schedules": db.query(TrainSchedule).count(),
                "fares": db.query(TrainFare).count(),
                "availabilities": db.query(TrainAvailability).count()
            }
        },
        "railradar_api": {
            "base_url": railradar_client.base_url,
            "is_configured": railradar_client.is_configured,
            "mode": railway_adapter.current_data_source,
            "last_fetched_at": railway_adapter.last_fetched_at.isoformat(),
            "last_error": railway_adapter.last_error
        },
        "gpt4all_llm": {
            "status": "ACTIVE (Local Inference)",
            "model_name": gpt4all_agent.model_name,
            "model_path": gpt4all_agent.model_path or "Default Cache"
        },
        "notifications": {
            "sms_provider": sms_provider.provider,
            "sms_configured": sms_provider.is_configured,
            "email_provider": email_provider.provider,
            "email_configured": email_provider.is_configured,
            "total_dispatched": db.query(NotificationRecord).count()
        },
        "live_poller": {
            "interval_seconds": live_update_service.interval_seconds,
            "is_running": live_update_service._is_running
        }
    }


# ------------------- PASSENGER ONBOARDING & CONTACTS -------------------

@app.post("/passengers", response_model=PassengerResponse)
def register_passenger(req: PassengerRegistrationRequest, db: Session = Depends(get_db)):
    """Registers passenger and contact preferences for SMS/Email notifications."""
    p_id = f"PASS-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.utcnow()

    # Create passenger record
    passenger = Passenger(
        id=p_id,
        name=req.name.strip(),
        email=req.email.strip().lower(),
        phone=req.phone.strip(),
        created_at=now
    )
    db.add(passenger)
    db.commit()

    # Create contact preferences
    contact = PassengerContact(
        contact_id=f"CONT-{uuid.uuid4().hex[:8].upper()}",
        passenger_id=p_id,
        name=req.name.strip(),
        email=req.email.strip().lower(),
        phone=req.phone.strip(),
        email_notifications_enabled=req.email_notifications_enabled,
        sms_notifications_enabled=req.sms_notifications_enabled,
        created_at=now,
        updated_at=now
    )
    db.add(contact)
    db.commit()

    return PassengerResponse(
        passenger_id=p_id,
        name=passenger.name,
        email=passenger.email,
        phone=passenger.phone,
        email_notifications_enabled=contact.email_notifications_enabled,
        sms_notifications_enabled=contact.sms_notifications_enabled,
        created_at=now.isoformat()
    )


# ------------------- JOURNEY ENDPOINTS -------------------

@app.post("/journey", response_model=JourneyDetailResponse)
async def create_journey(req: JourneyCreateRequest, db: Session = Depends(get_db)):
    """Creates a new active journey for monitoring."""
    j_id = f"JRN-{uuid.uuid4().hex[:8].upper()}"
    pnr = f"PNR{uuid.uuid4().hex[:6].upper()}"
    now = datetime.datetime.utcnow()

    # Verify stations or add fallback
    from_st = db.query(Station).filter(Station.code == req.from_station.upper()).first()
    if not from_st:
        from_st = Station(code=req.from_station.upper(), name=f"{req.from_station.upper()} Station", city=req.from_station.upper(), state="State")
        db.add(from_st)
        db.commit()

    to_st = db.query(Station).filter(Station.code == req.to_station.upper()).first()
    if not to_st:
        to_st = Station(code=req.to_station.upper(), name=f"{req.to_station.upper()} Station", city=req.to_station.upper(), state="State")
        db.add(to_st)
        db.commit()

    # Verify or fetch train
    train = db.query(Train).filter(Train.train_number == req.train_number).first()
    if not train:
        train = Train(
            train_number=req.train_number,
            train_name=f"Express {req.train_number}",
            source_station_code=req.from_station.upper(),
            destination_station_code=req.to_station.upper(),
            departure_time="08:00",
            arrival_time="16:00",
            duration_minutes=480
        )
        db.add(train)
        db.commit()

    # Associate passenger
    passenger = None
    if req.passenger_id:
        passenger = db.query(Passenger).filter(Passenger.id == req.passenger_id).first()
    if not passenger:
        passenger = db.query(Passenger).first()

    p_id = passenger.id if passenger else "PASS-DEMO-01"

    journey = Journey(
        id=j_id,
        pnr=pnr,
        source_station_code=req.from_station.upper(),
        destination_station_code=req.to_station.upper(),
        journey_date=req.journey_date,
        status="SAFE",
        created_at=now,
        updated_at=now
    )
    db.add(journey)
    db.commit()

    leg = JourneyLeg(
        journey_id=j_id,
        leg_order=1,
        train_number=train.train_number,
        from_station_code=req.from_station.upper(),
        to_station_code=req.to_station.upper(),
        scheduled_departure=train.departure_time,
        scheduled_arrival=train.arrival_time,
        actual_departure=train.departure_time,
        actual_arrival=train.arrival_time,
        delay_departure_min=0,
        delay_arrival_min=0,
        status="ON_TIME"
    )
    db.add(leg)

    booking = Booking(
        pnr=pnr,
        passenger_id=p_id,
        journey_id=j_id,
        booking_status="CNF",
        booking_class="3A",
        coach="B2",
        berth_number=32
    )
    db.add(booking)
    db.commit()

    # Generate initial action / recommendation
    action_engine = ActionEngine(db)
    action_engine.generate_recommendation(j_id)

    state_engine = JourneyStateEngine(db)
    return state_engine.serialize_journey_detail(journey)


@app.get("/journey/{identifier}", response_model=JourneyDetailResponse)
def get_journey(identifier: str, db: Session = Depends(get_db)):
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(identifier)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey with PNR or ID '{identifier}' not found.")
    
    data = state_engine.serialize_journey_detail(journey)
    data["data_source"] = railway_adapter.current_data_source
    return data


# ------------------- TRAINS SEARCH, SCHEDULE, AVAILABILITY, FARE -------------------

@app.get("/trains/search", response_model=List[TrainSearchResult])
async def search_trains(
    origin: str = Query(..., description="Source station code, e.g. CBE"),
    destination: str = Query(..., description="Destination station code, e.g. MAS"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    journey_date = date or datetime.date.today().strftime("%Y-%m-%d")
    results = await railway_adapter.search_trains_between_stations(origin, destination, journey_date)
    return results


@app.get("/trains/{train_number}/status")
async def get_train_status(train_number: str, date: Optional[str] = None):
    journey_date = date or datetime.date.today().strftime("%Y-%m-%d")
    status = await railway_adapter.get_train_running_status(train_number, journey_date)
    return status


@app.get("/trains/{train_number}/schedule")
async def get_train_schedule(train_number: str, db: Session = Depends(get_db)):
    """Fetch station intermediate halts schedule."""
    db_schedules = (
        db.query(TrainSchedule)
        .filter(TrainSchedule.train_number == train_number)
        .order_by(TrainSchedule.sequence.asc())
        .all()
    )
    if db_schedules:
        return [
            {
                "sequence": s.sequence,
                "station_code": s.station_code,
                "station_name": s.station_name,
                "arrival_time": s.arrival_time,
                "departure_time": s.departure_time,
                "day": s.day
            }
            for s in db_schedules
        ]
    return await railway_adapter.get_train_schedule(train_number)


@app.get("/trains/{train_number}/fare")
async def get_train_fare(
    train_number: str,
    date: Optional[str] = None,
    class_type: str = "3A",
    db: Session = Depends(get_db)
):
    """Fetch fare breakdown for train and class."""
    journey_date = date or datetime.date.today().strftime("%Y-%m-%d")
    db_fare = (
        db.query(TrainFare)
        .filter(TrainFare.train_number == train_number, TrainFare.class_code == class_type)
        .first()
    )
    if db_fare:
        return {
            "train_number": train_number,
            "journey_date": journey_date,
            "class_code": class_type,
            "quota": db_fare.quota,
            "base_fare": db_fare.base_fare,
            "other_charges": db_fare.other_charges,
            "total_fare": db_fare.total_fare,
            "formatted_fare": f"₹{int(db_fare.total_fare)}",
            "source": db_fare.source,
            "is_live": db_fare.is_live
        }
    return await railway_adapter.get_train_fare(train_number, journey_date, class_type)


@app.get("/trains/{train_number}/availability")
async def get_train_availability(
    train_number: str,
    date: Optional[str] = None,
    class_type: str = "3A",
    db: Session = Depends(get_db)
):
    """Fetch seat quota availability."""
    journey_date = date or datetime.date.today().strftime("%Y-%m-%d")
    av = (
        db.query(TrainAvailability)
        .filter(TrainAvailability.train_number == train_number, TrainAvailability.class_type == class_type)
        .first()
    )
    if av:
        return {
            "train_number": train_number,
            "journey_date": journey_date,
            "class_type": class_type,
            "status": av.status,
            "seats_available": av.seats_available,
            "rac": av.rac,
            "waiting_list": av.waiting_list,
            "fare": av.fare,
            "source": av.source,
            "is_live": av.is_live
        }
    return await railway_adapter.get_train_availability(train_number, journey_date, class_type)


@app.get("/trains/{train_number}", response_model=TrainInfo)
def get_train_details(train_number: str, db: Session = Depends(get_db)):
    train = db.query(Train).filter(Train.train_number == train_number).first()
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_number} not found.")
    return TrainInfo(
        train_number=train.train_number,
        train_name=train.train_name,
        source_station_code=train.source_station_code,
        destination_station_code=train.destination_station_code,
        departure_time=train.departure_time,
        arrival_time=train.arrival_time,
        duration_minutes=train.duration_minutes,
        running_days=train.running_days,
        train_type=train.train_type,
        status="ON_TIME",
        delay_minutes=0,
        data_source=railway_adapter.current_data_source
    )


# ------------------- INTELLIGENCE & ALTERNATIVE ENGINES -------------------

@app.get("/impact/{journey_id}", response_model=ImpactResult)
def get_journey_impact(journey_id: str, db: Session = Depends(get_db)):
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found.")

    engine = ImpactEngine(db)
    return engine.calculate_journey_impact(journey.id)


@app.get("/decision/{journey_id}", response_model=DecisionResult)
def get_journey_decision(journey_id: str, db: Session = Depends(get_db)):
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found.")

    decision_engine = DecisionEngine(db)
    latest = decision_engine.get_latest_decision(journey.id)
    if not latest:
        latest = decision_engine.evaluate_decision(journey.id)
    return latest


@app.get("/recommendations/{journey_id}", response_model=RecommendationResult)
def get_journey_recommendation(journey_id: str, db: Session = Depends(get_db)):
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found.")

    action_engine = ActionEngine(db)
    rec = action_engine.get_latest_recommendation(journey.id)
    if not rec:
        rec = action_engine.generate_recommendation(journey.id)
    return rec


@app.get("/alternatives/{journey_id}")
def get_journey_alternatives(journey_id: str, db: Session = Depends(get_db)):
    """
    Returns complete comparison matrix of feasible alternative trains and stations
    including expected destination arrival, waiting time, transfer time, and availability.
    """
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found.")

    alt_engine = AlternativeEngine(db)
    return alt_engine.get_complete_alternative_comparison(journey.id)


@app.get("/alternatives/stations/{journey_id}")
def get_nearby_station_alternatives(journey_id: str, db: Session = Depends(get_db)):
    """Returns specifically the alternative junction station options."""
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found.")

    alt_engine = AlternativeEngine(db)
    legs = sorted(journey.legs, key=lambda l: l.leg_order)
    first_leg = legs[0] if legs else None
    if not first_leg:
        return []

    return alt_engine.find_nearby_station_alternatives(
        current_station_code=first_leg.from_station_code,
        destination_station_code=journey.destination_station_code,
        current_time=first_leg.actual_departure or first_leg.scheduled_departure,
        journey_date=journey.journey_date
    )


# ------------------- GPT4ALL LOCAL AI EXPLANATION -------------------

@app.post("/ai/explain", response_model=GPT4AllExplainResponse)
async def explain_decision_with_gpt4all(
    req: GPT4AllExplainRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesizes passenger-friendly explanation with GPT4All strictly based
    on structured backend deterministic decision and alternative data.
    """
    state_engine = JourneyStateEngine(db)
    journey = state_engine.get_journey_by_id_or_pnr(req.journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey {req.journey_id} not found.")

    decision_engine = DecisionEngine(db)
    latest_decision = decision_engine.get_latest_decision(journey.id)
    if not latest_decision:
        latest_decision = decision_engine.evaluate_decision(journey.id)

    impact_engine = ImpactEngine(db)
    impact = impact_engine.calculate_journey_impact(journey.id)

    alt_engine = AlternativeEngine(db)
    alt_matrix = alt_engine.get_complete_alternative_comparison(journey.id)

    # Assemble structured payload per Section 14
    structured_payload = {
        "journey_status": latest_decision["situation_status"],
        "current_train": {
            "number": impact.get("affected_train", "12601"),
            "delay_minutes": impact.get("delay_minutes", 0),
            "expected_arrival": impact.get("expected_arrival", "08:30")
        },
        "alternatives": alt_matrix.get("alternatives", [])
    }

    explanation_text = gpt4all_agent.explain_journey(structured_payload)

    return GPT4AllExplainResponse(
        journey_id=journey.id,
        structured_decision_summary=structured_payload,
        explanation=explanation_text,
        model_provider="GPT4All (Local LLM)",
        model_name=gpt4all_agent.model_name,
        timestamp=datetime.datetime.utcnow().isoformat()
    )


# ------------------- NOTIFICATIONS FEED -------------------

@app.get("/notifications", response_model=List[NotificationItem])
def get_all_notifications(db: Session = Depends(get_db)):
    """Returns complete notification audit log."""
    notifs = (
        db.query(NotificationRecord)
        .order_by(NotificationRecord.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        NotificationItem(
            notification_id=n.notification_id,
            passenger_id=n.passenger_id,
            journey_id=n.journey_id,
            channel=n.channel,
            notification_type=n.notification_type,
            subject=n.subject,
            message=n.message,
            status=n.status,
            provider_response=n.provider_response,
            created_at=n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else "",
            sent_at=n.sent_at.strftime("%Y-%m-%d %H:%M:%S") if n.sent_at else None
        )
        for n in notifs
    ]


@app.get("/notifications/{passenger_id}", response_model=List[NotificationItem])
def get_passenger_notifications(passenger_id: str, db: Session = Depends(get_db)):
    """Returns notifications for a specific passenger."""
    notifs = (
        db.query(NotificationRecord)
        .filter(NotificationRecord.passenger_id == passenger_id)
        .order_by(NotificationRecord.created_at.desc())
        .all()
    )
    return [
        NotificationItem(
            notification_id=n.notification_id,
            passenger_id=n.passenger_id,
            journey_id=n.journey_id,
            channel=n.channel,
            notification_type=n.notification_type,
            subject=n.subject,
            message=n.message,
            status=n.status,
            provider_response=n.provider_response,
            created_at=n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else "",
            sent_at=n.sent_at.strftime("%Y-%m-%d %H:%M:%S") if n.sent_at else None
        )
        for n in notifs
    ]


# ------------------- EVENTS STREAM -------------------

@app.get("/events")
def get_events(limit: int = 20, db: Session = Depends(get_db)):
    event_engine = EventEngine(db)
    return event_engine.get_recent_events(limit=limit)


@app.get("/events/stream")
async def sse_event_stream(request: Request):
    queue = asyncio.Queue()
    sse_subscribers.append(queue)

    async def event_generator():
        try:
            yield {"event": "connected", "data": json.dumps({"status": "connected"})}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "railway_event", "data": data}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            if queue in sse_subscribers:
                sse_subscribers.remove(queue)

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
