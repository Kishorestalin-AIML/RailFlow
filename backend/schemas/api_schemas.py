from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StationInfo(BaseModel):
    code: str
    name: str
    city: str
    state: str
    platforms: int = 4


class TrainInfo(BaseModel):
    train_number: str
    train_name: str
    source_station_code: str
    destination_station_code: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    running_days: str
    train_type: str = "Superfast Express"
    status: str = "ON_TIME"
    delay_minutes: int = 0
    data_source: str = "SIMULATED DATA"


class TrainAvailabilityItem(BaseModel):
    class_type: str
    status: str
    seats_available: int
    fare: float


class TrainSearchResult(BaseModel):
    train_number: str
    train_name: str
    source: str
    destination: str
    departure_time: str
    arrival_time: str
    duration_formatted: str
    running_days: str
    running_status: str
    delay_minutes: int
    availabilities: List[TrainAvailabilityItem] = []
    data_source: str = "SIMULATED DATA"


class JourneyLegState(BaseModel):
    leg_order: int
    train_number: str
    train_name: str
    from_station: StationInfo
    to_station: StationInfo
    scheduled_departure: str
    scheduled_arrival: str
    actual_departure: Optional[str] = None
    actual_arrival: Optional[str] = None
    delay_arrival_min: int = 0
    status: str = "ON_TIME"


class JourneyDetailResponse(BaseModel):
    journey_id: str
    pnr: str
    passenger_name: str
    passenger_email: Optional[str] = None
    source_station: StationInfo
    destination_station: StationInfo
    journey_date: str
    journey_status: str
    legs: List[JourneyLegState]
    connection_buffer_minutes: Optional[int] = None
    minimum_safe_buffer_minutes: int = 30
    booking_status: str
    booking_class: str
    coach: str
    berth_number: int
    updated_at: str
    data_source: str = "SIMULATED DATA"


class ImpactResult(BaseModel):
    impact_type: str  # NO_IMPACT, DELAY_ABSORBED, CONNECTION_RISK, MISSED_CONNECTION, TRAIN_CANCELLED
    severity: str     # LOW, MEDIUM, HIGH, CRITICAL
    affected_train: str
    delay_minutes: int
    remaining_buffer_minutes: Optional[int] = None
    required_buffer_minutes: int = 30
    connection_train: Optional[str] = None
    connection_departure: Optional[str] = None
    expected_arrival: Optional[str] = None
    status_summary: str


class FeasibleAction(BaseModel):
    action_type: str  # CONTINUE_CURRENT_JOURNEY, REVIEW_ALTERNATIVE_CONNECTION, WAIT_FOR_UPDATED_INFORMATION, MONITOR_CONNECTION
    feasibility: str  # FEASIBLE, NOT_FEASIBLE, REQUIRES_USER_ACTION, INFORMATION_ONLY
    title: str
    description: str


class DecisionResult(BaseModel):
    decision_id: str
    journey_id: str
    situation_status: str  # SAFE, AT_RISK, MISSED, CANCELLED
    system_assessment: str
    reason: str
    feasible_actions: List[FeasibleAction]
    timestamp: str


class RecommendationActionItem(BaseModel):
    type: str
    label: str
    variant: str = "primary"  # primary, secondary, danger
    payload: Optional[Dict[str, Any]] = None


class RecommendationResult(BaseModel):
    id: str
    journey_id: str
    title: str
    status: str  # SAFE, ACTION_REQUIRED, CRITICAL_ALERT
    what_happened: str
    why_it_matters: str
    options: List[Dict[str, Any]]
    actions: List[RecommendationActionItem]
    ai_explanation: Optional[str] = None
    created_at: str


class EventInjectionRequest(BaseModel):
    event_type: str = Field(..., description="TRAIN_DELAY, TRAIN_CANCELLED, ETA_CHANGED, etc.")
    train_id: str = Field(..., description="Train number, e.g. 12601")
    delay_minutes: Optional[int] = 0
    effective_date: Optional[str] = None
    source: str = "simulation"
    details: Optional[Dict[str, Any]] = None


class QuickDelayRequest(BaseModel):
    train_id: str = "12601"
    delay_minutes: int = 75


class StrandsExplainRequest(BaseModel):
    journey_id: str
    passenger_query: Optional[str] = None


class StrandsExplainResponse(BaseModel):
    journey_id: str
    structured_decision_summary: Dict[str, Any]
    explanation: str
    model_provider: str
    model_name: str
    timestamp: str


class PassengerRegistrationRequest(BaseModel):
    name: str = Field(..., description="Passenger full name")
    email: str = Field(..., description="Passenger email address")
    phone: str = Field(..., description="International format mobile number, e.g. +91 98401 23456")
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = True


class PassengerResponse(BaseModel):
    passenger_id: str
    name: str
    email: str
    phone: str
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = True
    created_at: str


class JourneyCreateRequest(BaseModel):
    passenger_id: Optional[str] = None
    from_station: str
    to_station: str
    journey_date: str
    train_number: str


class NotificationItem(BaseModel):
    notification_id: str
    passenger_id: Optional[str] = None
    journey_id: Optional[str] = None
    channel: str
    notification_type: str
    subject: Optional[str] = None
    message: str
    status: str
    provider_response: Optional[str] = None
    created_at: str
    sent_at: Optional[str] = None


class GPT4AllExplainRequest(BaseModel):
    journey_id: str
    passenger_query: Optional[str] = None


class GPT4AllExplainResponse(BaseModel):
    journey_id: str
    structured_decision_summary: Dict[str, Any]
    explanation: str
    model_provider: str
    model_name: str
    timestamp: str


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    data_adapter_mode: str
    data_adapter_base_url: Optional[str] = None
    strands_status: str
    active_journeys_count: int
    events_count: int
    last_updated: str
