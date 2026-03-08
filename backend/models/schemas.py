"""
Pydantic Schemas for API Request/Response
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum
import uuid


# =============================================================================
# Enums
# =============================================================================

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    CHECKUP = "checkup"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"


# =============================================================================
# Patient Schemas
# =============================================================================

class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    preferred_language: Optional[Language] = Language.ENGLISH
    address: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Optional[Language] = None
    address: Optional[str] = None


class PatientResponse(PatientBase):
    id: uuid.UUID
    medical_record_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Doctor Schemas
# =============================================================================

class DoctorBase(BaseModel):
    full_name: str
    specialty: str
    department: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    languages: List[str] = ["en"]
    consultation_fee: Optional[int] = None


class DoctorResponse(DoctorBase):
    id: uuid.UUID
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TimeSlot(BaseModel):
    date: date
    start_time: time
    end_time: time
    is_available: bool = True


class DoctorAvailability(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    slots: List[TimeSlot]


# =============================================================================
# Appointment Schemas
# =============================================================================

class AppointmentBase(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    reason: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    status: AppointmentStatus
    notes: Optional[str] = None
    booked_via: str
    created_at: datetime
    updated_at: datetime
    
    # Joined fields
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Voice/Agent Schemas
# =============================================================================

class VoiceSessionStart(BaseModel):
    phone_number: Optional[str] = None
    language: Language = Language.ENGLISH


class VoiceMessage(BaseModel):
    session_id: str
    text: str
    language: Language
    timestamp: datetime


class AgentResponse(BaseModel):
    text: str
    language: Language
    intent: Optional[str] = None
    slots: Optional[dict] = None
    action_taken: Optional[str] = None
    confidence: float = 1.0


class ConversationContext(BaseModel):
    session_id: str
    patient_id: Optional[uuid.UUID] = None
    current_intent: Optional[str] = None
    collected_slots: dict = {}
    conversation_history: List[dict] = []
    language: Language = Language.ENGLISH


# =============================================================================
# Call Log Schemas
# =============================================================================

class CallLogCreate(BaseModel):
    session_id: str
    patient_id: Optional[uuid.UUID] = None
    phone_number: Optional[str] = None
    language_used: Language = Language.ENGLISH
    intent_detected: Optional[str] = None


class CallLogResponse(BaseModel):
    id: uuid.UUID
    session_id: str
    patient_id: Optional[uuid.UUID] = None
    phone_number: Optional[str] = None
    call_start_time: datetime
    call_end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    language_used: str
    intent_detected: Optional[str] = None
    outcome: Optional[str] = None
    appointment_id: Optional[uuid.UUID] = None
    escalated_to_human: bool
    
    class Config:
        from_attributes = True
