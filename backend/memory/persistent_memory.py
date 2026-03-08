"""
Persistent Memory
Long-term memory using PostgreSQL for patient context and history
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from backend.models.database import async_session
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class PersistentMemory:
    """
    PostgreSQL-based persistent memory for:
    - Patient profiles and preferences
    - Appointment history
    - Conversation logs
    - Long-term context for personalization
    """
    
    async def get_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """
        Get comprehensive patient context for personalization.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dict containing patient info, history, preferences
        """
        try:
            async with async_session() as session:
                # Get patient info
                patient_result = await session.execute(
                    """
                    SELECT id, full_name, phone_number, preferred_language, 
                           date_of_birth, gender
                    FROM patients WHERE id = :id
                    """,
                    {"id": patient_id}
                )
                patient = patient_result.fetchone()
                
                if not patient:
                    return {}
                
                # Get recent appointments
                appointments_result = await session.execute(
                    """
                    SELECT a.id, a.appointment_date, a.start_time, a.status,
                           d.full_name as doctor_name, d.specialty
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = :patient_id
                    ORDER BY a.appointment_date DESC, a.start_time DESC
                    LIMIT 5
                    """,
                    {"patient_id": patient_id}
                )
                appointments = appointments_result.fetchall()
                
                # Get frequently visited doctors
                freq_doctors_result = await session.execute(
                    """
                    SELECT d.full_name, d.specialty, COUNT(*) as visit_count
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = :patient_id AND a.status = 'completed'
                    GROUP BY d.id, d.full_name, d.specialty
                    ORDER BY visit_count DESC
                    LIMIT 3
                    """,
                    {"patient_id": patient_id}
                )
                frequent_doctors = freq_doctors_result.fetchall()
                
                return {
                    "patient_id": str(patient[0]),
                    "name": patient[1],
                    "phone": patient[2],
                    "preferred_language": patient[3] or "en",
                    "date_of_birth": str(patient[4]) if patient[4] else None,
                    "gender": patient[5],
                    "recent_appointments": [
                        {
                            "id": str(a[0]),
                            "date": str(a[1]),
                            "time": str(a[2]),
                            "status": a[3],
                            "doctor_name": a[4],
                            "specialty": a[5]
                        }
                        for a in appointments
                    ],
                    "frequent_doctors": [
                        {
                            "name": d[0],
                            "specialty": d[1],
                            "visits": d[2]
                        }
                        for d in frequent_doctors
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting patient context: {e}")
            return {}
    
    async def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Look up patient by phone number.
        Used for caller ID matching.
        """
        try:
            async with async_session() as session:
                result = await session.execute(
                    """
                    SELECT id, full_name, preferred_language, date_of_birth
                    FROM patients WHERE phone_number = :phone
                    """,
                    {"phone": phone_number}
                )
                patient = result.fetchone()
                
                if patient:
                    return {
                        "patient_id": str(patient[0]),
                        "name": patient[1],
                        "preferred_language": patient[2] or "en",
                        "date_of_birth": str(patient[3]) if patient[3] else None
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error looking up patient: {e}")
            return None
    
    async def log_conversation(
        self,
        session_id: str,
        patient_id: Optional[str],
        phone_number: Optional[str],
        language: str,
        intent: Optional[str],
        outcome: Optional[str],
        appointment_id: Optional[str],
        transcript: str,
        duration_seconds: int,
        escalated: bool = False
    ) -> Optional[str]:
        """
        Log a completed conversation to the database.
        
        Returns:
            Call log ID if successful
        """
        try:
            async with async_session() as session:
                call_log_id = str(uuid.uuid4())
                
                await session.execute(
                    """
                    INSERT INTO call_logs (
                        id, session_id, patient_id, phone_number, language_used,
                        intent_detected, outcome, appointment_id, transcript,
                        duration_seconds, escalated_to_human, call_start_time
                    ) VALUES (
                        :id, :session_id, :patient_id, :phone, :language,
                        :intent, :outcome, :appointment_id, :transcript,
                        :duration, :escalated, :start_time
                    )
                    """,
                    {
                        "id": call_log_id,
                        "session_id": session_id,
                        "patient_id": patient_id,
                        "phone": phone_number,
                        "language": language,
                        "intent": intent,
                        "outcome": outcome,
                        "appointment_id": appointment_id,
                        "transcript": transcript,
                        "duration": duration_seconds,
                        "escalated": escalated,
                        "start_time": datetime.utcnow() - timedelta(seconds=duration_seconds)
                    }
                )
                await session.commit()
                
                return call_log_id
                
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            return None
    
    async def log_conversation_turn(
        self,
        call_log_id: str,
        turn_number: int,
        speaker: str,
        text: str,
        language: str,
        intent: Optional[str] = None,
        slots: Optional[Dict] = None,
        latency_ms: Optional[int] = None
    ) -> bool:
        """Log individual conversation turns"""
        try:
            async with async_session() as session:
                await session.execute(
                    """
                    INSERT INTO conversation_turns (
                        id, call_log_id, turn_number, speaker, text,
                        language, intent, slots, total_latency_ms
                    ) VALUES (
                        :id, :call_log_id, :turn_number, :speaker, :text,
                        :language, :intent, :slots, :latency
                    )
                    """,
                    {
                        "id": str(uuid.uuid4()),
                        "call_log_id": call_log_id,
                        "turn_number": turn_number,
                        "speaker": speaker,
                        "text": text,
                        "language": language,
                        "intent": intent,
                        "slots": str(slots) if slots else None,
                        "latency": latency_ms
                    }
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging turn: {e}")
            return False
    
    async def get_upcoming_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get patient's upcoming appointments"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    """
                    SELECT a.id, a.appointment_date, a.start_time, a.status,
                           a.reason, d.full_name as doctor_name, d.specialty
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = :patient_id
                    AND a.status IN ('scheduled', 'confirmed')
                    AND (a.appointment_date > CURRENT_DATE 
                         OR (a.appointment_date = CURRENT_DATE AND a.start_time > CURRENT_TIME))
                    ORDER BY a.appointment_date, a.start_time
                    """,
                    {"patient_id": patient_id}
                )
                appointments = result.fetchall()
                
                return [
                    {
                        "id": str(a[0]),
                        "date": str(a[1]),
                        "time": str(a[2]),
                        "status": a[3],
                        "reason": a[4],
                        "doctor_name": a[5],
                        "specialty": a[6]
                    }
                    for a in appointments
                ]
                
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {e}")
            return []
    
    async def get_patient_preferences(self, patient_id: str) -> Dict[str, Any]:
        """Get learned patient preferences"""
        try:
            context = await self.get_patient_context(patient_id)
            
            preferences = {
                "preferred_language": context.get("preferred_language", "en"),
                "preferred_doctors": [],
                "usual_appointment_time": None,
                "common_visit_reasons": []
            }
            
            # Extract preferences from history
            freq_doctors = context.get("frequent_doctors", [])
            if freq_doctors:
                preferences["preferred_doctors"] = [d["name"] for d in freq_doctors]
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {"preferred_language": "en"}
    
    async def update_patient_language(self, patient_id: str, language: str) -> bool:
        """Update patient's preferred language"""
        try:
            async with async_session() as session:
                await session.execute(
                    """
                    UPDATE patients 
                    SET preferred_language = :language, updated_at = NOW()
                    WHERE id = :patient_id
                    """,
                    {"patient_id": patient_id, "language": language}
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating language: {e}")
            return False
