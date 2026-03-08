"""
Database Configuration and Models
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Date, Time, Enum, JSON, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

from backend.config.settings import settings

# Create async engine
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(DATABASE_URL, pool_size=settings.DATABASE_POOL_SIZE)

# Session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base model
Base = declarative_base()


async def get_db():
    """Dependency for getting database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database connection"""
    async with engine.begin() as conn:
        # Test connection
        await conn.execute(text("SELECT 1"))


async def close_db():
    """Close database connection"""
    await engine.dispose()


# =============================================================================
# Database Models
# =============================================================================

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    preferred_language = Column(String(10), default="en")
    address = Column(Text)
    medical_record_number = Column(String(50), unique=True)
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    insurance_provider = Column(String(255))
    insurance_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    specialty = Column(String(100), nullable=False)
    department = Column(String(100))
    qualification = Column(String(255))
    experience_years = Column(Integer)
    languages = Column(ARRAY(String), default=["en"])
    phone_number = Column(String(20))
    email = Column(String(255))
    consultation_fee = Column(Integer)
    is_active = Column(Boolean, default=True)
    bio = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    appointment_type = Column(String(50), default="consultation")
    reason = Column(Text)
    status = Column(String(20), default="scheduled", index=True)
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    booked_via = Column(String(50), default="voice_ai")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    phone_number = Column(String(20))
    call_direction = Column(String(20), default="inbound")
    call_start_time = Column(DateTime, nullable=False)
    call_end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    language_used = Column(String(10))
    intent_detected = Column(String(100))
    outcome = Column(String(50))
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    transcript = Column(Text)
    sentiment_score = Column(Integer)
    escalated_to_human = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_log_id = Column(UUID(as_uuid=True), ForeignKey("call_logs.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String(20), nullable=False)  # 'user' or 'agent'
    text = Column(Text, nullable=False)
    language = Column(String(10))
    intent = Column(String(100))
    confidence = Column(Integer)
    latency_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
