import datetime
import json
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
)
from sqlalchemy.orm import relationship
from backend.database.database import Base


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bookings = relationship("Booking", back_populates="passenger")
    contacts = relationship("PassengerContact", back_populates="passenger", cascade="all, delete-orphan")
    notifications = relationship("NotificationRecord", back_populates="passenger", cascade="all, delete-orphan")


class Station(Base):
    __tablename__ = "stations"

    code = Column(String(16), primary_key=True, index=True)  # e.g., CBE, MAS, NDLS
    name = Column(String(128), nullable=False)
    city = Column(String(64), nullable=False)
    state = Column(String(64), nullable=False)
    platforms = Column(Integer, default=4)


class Train(Base):
    __tablename__ = "trains"

    train_number = Column(String(32), primary_key=True, index=True)
    train_name = Column(String(128), nullable=False)
    source_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    destination_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    departure_time = Column(String(16), nullable=False)  # HH:MM format e.g. "08:30"
    arrival_time = Column(String(16), nullable=False)    # HH:MM format e.g. "14:45"
    duration_minutes = Column(Integer, default=360)
    running_days = Column(String(64), default="Mon,Tue,Wed,Thu,Fri,Sat,Sun")
    train_type = Column(String(32), default="Superfast Express")

    source_station = relationship("Station", foreign_keys=[source_station_code])
    dest_station = relationship("Station", foreign_keys=[destination_station_code])
    availabilities = relationship("TrainAvailability", back_populates="train")
    schedules = relationship("TrainSchedule", back_populates="train", cascade="all, delete-orphan")
    fares = relationship("TrainFare", back_populates="train", cascade="all, delete-orphan")


class TrainSchedule(Base):
    __tablename__ = "train_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_number = Column(String(32), ForeignKey("trains.train_number"), nullable=False, index=True)
    station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    station_name = Column(String(128), nullable=False)
    arrival_time = Column(String(16), nullable=False)
    departure_time = Column(String(16), nullable=False)
    day = Column(Integer, default=1)
    sequence = Column(Integer, default=1)

    train = relationship("Train", back_populates="schedules")
    station = relationship("Station")


class TrainLiveStatus(Base):
    __tablename__ = "train_live_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_number = Column(String(32), ForeignKey("trains.train_number"), nullable=False, index=True)
    station_code = Column(String(16), nullable=False)
    expected_arrival = Column(String(16), nullable=False)
    expected_departure = Column(String(16), nullable=False)
    delay_minutes = Column(Integer, default=0)
    status = Column(String(32), default="ON_TIME")  # ON_TIME, DELAYED, CANCELLED
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String(64), default="railway_api")
    is_live = Column(Boolean, default=False)


class TrainAvailability(Base):
    __tablename__ = "train_availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_number = Column(String(32), ForeignKey("trains.train_number"), nullable=False, index=True)
    journey_date = Column(String(32), nullable=False)  # YYYY-MM-DD
    class_type = Column(String(16), nullable=False)    # 1A, 2A, 3A, SL, CC, 2S
    quota = Column(String(16), default="GN")           # General quota
    status = Column(String(32), default="AVAILABLE")    # AVAILABLE, RAC, WL
    seats_available = Column(Integer, default=24)
    rac = Column(Integer, default=0)
    waiting_list = Column(Integer, default=0)
    fare = Column(Float, default=750.0)
    source = Column(String(64), default="simulation")
    is_live = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    train = relationship("Train", back_populates="availabilities")


class TrainFare(Base):
    __tablename__ = "train_fares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_number = Column(String(32), ForeignKey("trains.train_number"), nullable=False, index=True)
    journey_date = Column(String(32), nullable=False)
    class_code = Column(String(16), nullable=False)
    quota = Column(String(16), default="GN")
    base_fare = Column(Float, default=650.0)
    other_charges = Column(Float, default=100.0)
    total_fare = Column(Float, default=750.0)
    source = Column(String(64), default="simulation")
    is_live = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    train = relationship("Train", back_populates="fares")


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(String(64), primary_key=True, index=True)
    pnr = Column(String(32), unique=True, index=True, nullable=False)
    source_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    destination_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    journey_date = Column(String(32), nullable=False)
    status = Column(String(32), default="SAFE")  # SAFE, CONNECTION_AT_RISK, MISSED, DISRUPTED, COMPLETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    legs = relationship("JourneyLeg", back_populates="journey", cascade="all, delete-orphan", order_by="JourneyLeg.leg_order")
    booking = relationship("Booking", back_populates="journey", uselist=False)
    decisions = relationship("Decision", back_populates="journey", cascade="all, delete-orphan")


class JourneyLeg(Base):
    __tablename__ = "journey_legs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    journey_id = Column(String(64), ForeignKey("journeys.id"), nullable=False)
    leg_order = Column(Integer, default=1)
    train_number = Column(String(32), ForeignKey("trains.train_number"), nullable=False)
    from_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    to_station_code = Column(String(16), ForeignKey("stations.code"), nullable=False)
    scheduled_departure = Column(String(16), nullable=False)  # HH:MM e.g. "00:30"
    scheduled_arrival = Column(String(16), nullable=False)    # HH:MM e.g. "08:30"
    actual_departure = Column(String(16), nullable=True)
    actual_arrival = Column(String(16), nullable=True)
    delay_departure_min = Column(Integer, default=0)
    delay_arrival_min = Column(Integer, default=0)
    status = Column(String(32), default="ON_TIME")  # ON_TIME, DELAYED, CANCELLED, RUNNING, ARRIVED

    journey = relationship("Journey", back_populates="legs")
    train = relationship("Train")
    from_station = relationship("Station", foreign_keys=[from_station_code])
    to_station = relationship("Station", foreign_keys=[to_station_code])


class Booking(Base):
    __tablename__ = "bookings"

    pnr = Column(String(32), primary_key=True, index=True)
    passenger_id = Column(String(64), ForeignKey("passengers.id"), nullable=False)
    journey_id = Column(String(64), ForeignKey("journeys.id"), nullable=False)
    booking_status = Column(String(32), default="CNF")  # CNF, RAC, WL
    booking_class = Column(String(16), default="3A")
    coach = Column(String(16), default="B2")
    berth_number = Column(Integer, default=34)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    passenger = relationship("Passenger", back_populates="bookings")
    journey = relationship("Journey", back_populates="booking")


class RailwayEvent(Base):
    __tablename__ = "events"

    event_id = Column(String(64), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)  # TRAIN_DELAY, TRAIN_CANCELLED, ETA_CHANGED, etc.
    train_id = Column(String(32), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    effective_date = Column(String(32), nullable=True)
    source = Column(String(64), default="simulation")  # live_api, simulation, manual_injection
    payload_json = Column(Text, nullable=True)

    @property
    def payload(self) -> Dict[str, Any]:
        if self.payload_json:
            try:
                return json.loads(self.payload_json)
            except Exception:
                return {}
        return {}


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(64), primary_key=True, index=True)
    journey_id = Column(String(64), ForeignKey("journeys.id"), nullable=False)
    event_id = Column(String(64), nullable=True)
    situation_status = Column(String(64), nullable=False)  # SAFE, AT_RISK, MISSED, CANCELLED
    system_assessment = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    feasible_actions_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    journey = relationship("Journey", back_populates="decisions")
    recommendations = relationship("Recommendation", back_populates="decision", cascade="all, delete-orphan")

    @property
    def feasible_actions(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.feasible_actions_json)
        except Exception:
            return []


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    journey_id = Column(String(64), ForeignKey("journeys.id"), nullable=False)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False)
    title = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False)  # SAFE, ACTION_REQUIRED, CRITICAL_ALERT
    what_happened = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    actions_json = Column(Text, nullable=False)
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    decision = relationship("Decision", back_populates="recommendations")

    @property
    def options(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.options_json)
        except Exception:
            return []

    @property
    def actions(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.actions_json)
        except Exception:
            return []


class DataRefreshLog(Base):
    __tablename__ = "data_refresh_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False)
    train_number = Column(String(32), nullable=True)
    status_code = Column(Integer, default=200)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)
    duration_ms = Column(Float, default=0.0)
    message = Column(String(256), nullable=True)


class PassengerContact(Base):
    __tablename__ = "passenger_contacts"

    contact_id = Column(String(64), primary_key=True, index=True)
    passenger_id = Column(String(64), ForeignKey("passengers.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=False)
    email_notifications_enabled = Column(Boolean, default=True)
    sms_notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    passenger = relationship("Passenger", back_populates="contacts")


class NotificationRecord(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(64), primary_key=True, index=True)
    passenger_id = Column(String(64), ForeignKey("passengers.id"), nullable=True, index=True)
    journey_id = Column(String(64), ForeignKey("journeys.id"), nullable=True, index=True)
    channel = Column(String(16), nullable=False)  # SMS, EMAIL
    notification_type = Column(String(64), nullable=False)  # TRAIN_DELAY, CONNECTION_AT_RISK, CONNECTION_MISSED, etc.
    subject = Column(String(256), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(32), default="SENT")  # SENT, FAILED, SIMULATED
    provider_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    passenger = relationship("Passenger", back_populates="notifications")
    journey = relationship("Journey")
