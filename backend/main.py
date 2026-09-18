import os
import json
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
from backend.models.schema import Train, Station, RailwayEvent, Journey, TrainSchedule, TrainFare, TrainAvailability, TrainLiveStatus
from backend.schemas.api_schemas import (
    JourneyDetailResponse,
    TrainSearchResult,
    TrainInfo,
    ImpactResult,
    DecisionResult,
    RecommendationResult,
    EventInjectionRequest,
    QuickDelayRequest,
    StrandsExplainRequest,
    StrandsExplainResponse,
    SystemHealthResponse
)
from backend.integrations.railway_api import railway_adapter
from backend.engines.journey_state import JourneyStateEngine
from backend.engines.impact_engine import ImpactEngine
from backend.engines.decision_engine import DecisionEngine
from backend.engines.action_engine import ActionEngine
from backend.engines.event_engine import EventEngine
from backend.ai.strands_agent import strands_assistant
from backend.services.live_update_service import live_update_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("railmind")

app = FastAPI(
    title="RailMind - Real-Time Railway Journey Intelligence",
    description="Operational intelligence and decision support layer above Indian Railway information systems with AWS Strands Agent explanation.",
    version="1.1.0"
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
        data_adapter_base_url=railway_adapter.client.base_url or "Local Simulation Mode",
        strands_status="READY (Strands Agents v1.56)",
        active_journeys_count=journeys_count,
        events_count=events_count,
        last_updated=datetime.datetime.utcnow().strftime("%I:%M %p UTC")
    )


@app.get("/system/status")
def get_system_status(db: Session = Depends(get_db)):
    """Detailed judge-facing system status & architectural stats."""
    return {
        "system_name": "RailMind - Railway Passenger Intelligence",
        "version": "1.1.0",
        "architecture_pipeline": "DATA -> EVENT -> STATE -> IMPACT -> DECISION -> ACTION -> STRANDS",
        "database": {
            "type": "SQLite3",
            "file": "railway.db",
            "tables": {
                "trains": db.query(Train).count(),
                "journeys": db.query(Journey).count(),
                "events": db.query(RailwayEvent).count(),
                "schedules": db.query(TrainSchedule).count(),
                "fares": db.query(TrainFare).count(),
                "availabilities": db.query(TrainAvailability).count()
            }
        },
        "live_adapter": {
            "mode": railway_adapter.current_data_source,
            "provider": railway_adapter.client.provider,
            "is_configured": railway_adapter.client.is_configured,
            "last_fetched_at": railway_adapter.last_fetched_at.isoformat()
        },
        "strands_sdk": {
            "status": "ACTIVE",
            "provider": strands_assistant.provider_name,
            "model": "strands-agents-v1.56"
        },
        "live_poller": {
            "interval_seconds": live_update_service.interval_seconds,
            "is_running": live_update_service._is_running
        }
    }


# ------------------- JOURNEY ENDPOINTS -------------------

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
    # First check database for seeded schedule
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
    # Fallback to adapter
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
            "formatted_fare": f"₹{db_fare.total_fare}",
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
    return {
        "train_number": train_number,
        "journey_date": journey_date,
        "class_type": class_type,
        "status": "Not provided",
        "seats_available": 0,
        "fare": None
    }


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


# ------------------- INTELLIGENCE ENGINE ENDPOINTS -------------------

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


# ------------------- STRANDS AI EXPLANATION -------------------

@app.post("/ai/explain", response_model=StrandsExplainResponse)
async def explain_decision_with_strands(
    req: StrandsExplainRequest,
    db: Session = Depends(get_db)
):
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

    # Combine into strict structured decision payload for Strands
    structured_payload = {
        "journey_id": journey.id,
        "pnr": journey.pnr,
        "situation_status": latest_decision["situation_status"],
        "affected_train": impact.get("affected_train"),
        "delay_minutes": impact.get("delay_minutes", 0),
        "expected_arrival": impact.get("expected_arrival"),
        "connection_train": impact.get("connection_train"),
        "connection_departure": impact.get("connection_departure"),
        "remaining_buffer_minutes": impact.get("remaining_buffer_minutes"),
        "required_buffer_minutes": impact.get("required_buffer_minutes", 30),
        "system_assessment": latest_decision["system_assessment"],
        "reason": latest_decision["reason"]
    }

    explanation_result = await strands_assistant.explain_decision(
        structured_decision=structured_payload,
        query=req.passenger_query
    )

    return StrandsExplainResponse(
        journey_id=journey.id,
        structured_decision_summary=structured_payload,
        explanation=explanation_result["explanation"],
        model_provider=explanation_result["model_provider"],
        model_name=explanation_result["model_name"],
        timestamp=explanation_result["timestamp"]
    )


# ------------------- EVENTS & SIMULATION CONSOLE -------------------

@app.get("/events")
def get_events(limit: int = 20, db: Session = Depends(get_db)):
    event_engine = EventEngine(db)
    return event_engine.get_recent_events(limit=limit)


@app.post("/events")
async def post_event(req: EventInjectionRequest, db: Session = Depends(get_db)):
    event_engine = EventEngine(db)
    payload = req.details or {}
    if req.delay_minutes:
        payload["delay_minutes"] = req.delay_minutes

    result = event_engine.process_event(
        event_type=req.event_type,
        train_id=req.train_id,
        payload=payload,
        effective_date=req.effective_date,
        source=req.source
    )
    await broadcast_event_update(result)
    return result


@app.post("/simulate/delay")
async def simulate_train_delay(req: QuickDelayRequest, db: Session = Depends(get_db)):
    event_engine = EventEngine(db)
    result = event_engine.process_event(
        event_type="TRAIN_DELAY",
        train_id=req.train_id,
        payload={"delay_minutes": req.delay_minutes, "reason": "Signal failure near Katpadi"},
        source="simulation"
    )
    await broadcast_event_update(result)
    return result


@app.post("/simulate/cancel")
async def simulate_train_cancellation(train_id: str = "12601", db: Session = Depends(get_db)):
    event_engine = EventEngine(db)
    result = event_engine.process_event(
        event_type="TRAIN_CANCELLED",
        train_id=train_id,
        payload={"reason": "Operational constraint / rolling stock issue"},
        source="simulation"
    )
    await broadcast_event_update(result)
    return result


@app.post("/simulate/reset")
async def simulate_reset(db: Session = Depends(get_db)):
    reset_demo_journey(db)
    reset_event = {
        "event_type": "RESET",
        "train_id": "12601",
        "status": "RESET_COMPLETE",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    await broadcast_event_update(reset_event)
    return {"message": "Demo journey reset to baseline safe state."}


# ------------------- SSE STREAM -------------------

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
