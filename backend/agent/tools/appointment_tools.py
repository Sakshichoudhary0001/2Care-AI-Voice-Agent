"""
Appointment Tools
Tools for interacting with the appointment system
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
import uuid
import logging

from backend.models.database import async_session
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class AppointmentTools:
    """
    Tools for appointment management operations.
    Each method represents a tool the agent can call.
    """
    
    async def book_appointment(
        self,
        patient_id: Optional[str],
        doctor_spec: str,
        date: str,
        time: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book a new appointment.
        
        Args:
            patient_id: Patient UUID or None for new patient
            doctor_spec: Doctor name or specialty
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            reason: Reason for visit
            
        Returns:
            Dict with success status and appointment details
        """
        try:
            async with async_session() as session:
                # Find doctor
                doctor = await self._find_doctor(session, doctor_spec)
                if not doctor:
                    return {
                        "success": False,
                        "error": "Doctor not found",
                        "message": f"Could not find a doctor matching '{doctor_spec}'"
                    }
                
                # Parse date and time
                appt_date = datetime.strptime(date, "%Y-%m-%d").date()
                appt_time = datetime.strptime(time, "%H:%M").time()
                end_time = (datetime.combine(appt_date, appt_time) + timedelta(minutes=30)).time()
                
                # Check availability
                is_available = await self._check_slot_available(
                    session, doctor["id"], appt_date, appt_time, end_time
                )
                
                if not is_available:
                    # Get alternative slots
                    alternatives = await self._get_alternative_slots(
                        session, doctor["id"], appt_date
                    )
                    return {
                        "success": False,
                        "error": "Slot not available",
                        "alternatives": alternatives,
                        "doctor_name": doctor["full_name"]
                    }
                
                # Create appointment
                appointment_id = str(uuid.uuid4())
                await session.execute(
                    """
                    INSERT INTO appointments 
                    (id, patient_id, doctor_id, appointment_date, start_time, end_time, reason, status)
                    VALUES (:id, :patient_id, :doctor_id, :date, :start_time, :end_time, :reason, 'scheduled')
                    """,
                    {
                        "id": appointment_id,
                        "patient_id": patient_id,
                        "doctor_id": doctor["id"],
                        "date": appt_date,
                        "start_time": appt_time,
                        "end_time": end_time,
                        "reason": reason
                    }
                )
                await session.commit()
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "doctor_name": doctor["full_name"],
                    "date": date,
                    "time": time,
                    "status": "scheduled"
                }
                
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_appointment(
        self,
        appointment_identifier: str,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an existing appointment.
        
        Args:
            appointment_identifier: Appointment ID or date
            patient_id: Patient ID for verification
            
        Returns:
            Dict with success status
        """
        try:
            async with async_session() as session:
                # Find the appointment
                appointment = await self._find_appointment(
                    session, appointment_identifier, patient_id
                )
                
                if not appointment:
                    return {
                        "success": False,
                        "error": "Appointment not found"
                    }
                
                # Update status to cancelled
                await session.execute(
                    """
                    UPDATE appointments 
                    SET status = 'cancelled', updated_at = NOW()
                    WHERE id = :id
                    """,
                    {"id": appointment["id"]}
                )
                await session.commit()
                
                return {
                    "success": True,
                    "appointment_id": str(appointment["id"]),
                    "doctor_name": appointment.get("doctor_name", ""),
                    "date": str(appointment["appointment_date"]),
                    "time": str(appointment["start_time"])
                }
                
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return {"success": False, "error": str(e)}
    
    async def reschedule_appointment(
        self,
        appointment_identifier: str,
        new_date: str,
        new_time: str,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reschedule an existing appointment.
        
        Args:
            appointment_identifier: Current appointment ID or date
            new_date: New date in YYYY-MM-DD format
            new_time: New time in HH:MM format
            patient_id: Patient ID for verification
            
        Returns:
            Dict with success status and new appointment details
        """
        try:
            async with async_session() as session:
                # Find current appointment
                appointment = await self._find_appointment(
                    session, appointment_identifier, patient_id
                )
                
                if not appointment:
                    return {
                        "success": False,
                        "error": "Appointment not found"
                    }
                
                # Parse new date/time
                appt_date = datetime.strptime(new_date, "%Y-%m-%d").date()
                appt_time = datetime.strptime(new_time, "%H:%M").time()
                end_time = (datetime.combine(appt_date, appt_time) + timedelta(minutes=30)).time()
                
                # Check new slot availability
                is_available = await self._check_slot_available(
                    session, appointment["doctor_id"], appt_date, appt_time, end_time
                )
                
                if not is_available:
                    return {
                        "success": False,
                        "error": "New time slot not available"
                    }
                
                # Update appointment
                await session.execute(
                    """
                    UPDATE appointments 
                    SET appointment_date = :date, start_time = :start_time, 
                        end_time = :end_time, status = 'rescheduled', updated_at = NOW()
                    WHERE id = :id
                    """,
                    {
                        "id": appointment["id"],
                        "date": appt_date,
                        "start_time": appt_time,
                        "end_time": end_time
                    }
                )
                await session.commit()
                
                return {
                    "success": True,
                    "appointment_id": str(appointment["id"]),
                    "doctor_name": appointment.get("doctor_name", ""),
                    "new_date": new_date,
                    "new_time": new_time
                }
                
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_availability(
        self,
        doctor_spec: str,
        date: str
    ) -> Dict[str, Any]:
        """
        Check doctor's availability for a specific date.
        
        Args:
            doctor_spec: Doctor name or specialty
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dict with available slots
        """
        try:
            async with async_session() as session:
                # Find doctor
                doctor = await self._find_doctor(session, doctor_spec)
                if not doctor:
                    return {
                        "success": False,
                        "error": "Doctor not found",
                        "slots": []
                    }
                
                appt_date = datetime.strptime(date, "%Y-%m-%d").date()
                
                # Get available slots
                slots = await self._get_available_slots(session, doctor["id"], appt_date)
                
                return {
                    "success": True,
                    "doctor_name": doctor["full_name"],
                    "date": date,
                    "slots": [s.strftime("%H:%M") for s in slots]
                }
                
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"success": False, "error": str(e), "slots": []}
    
    async def get_appointment_details(
        self,
        appointment_identifier: str,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a specific appointment.
        """
        try:
            async with async_session() as session:
                appointment = await self._find_appointment(
                    session, appointment_identifier, patient_id
                )
                
                if not appointment:
                    return {"found": False}
                
                return {
                    "found": True,
                    "appointment_id": str(appointment["id"]),
                    "doctor_name": appointment.get("doctor_name", ""),
                    "date": str(appointment["appointment_date"]),
                    "time": str(appointment["start_time"]),
                    "status": appointment["status"],
                    "reason": appointment.get("reason", "")
                }
                
        except Exception as e:
            logger.error(f"Error getting appointment details: {e}")
            return {"found": False, "error": str(e)}
    
    async def list_doctors(
        self,
        specialty: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available doctors, optionally filtered by specialty.
        """
        try:
            async with async_session() as session:
                query = "SELECT id, full_name, specialty, experience_years, consultation_fee FROM doctors WHERE is_active = true"
                params = {}
                
                if specialty:
                    query += " AND specialty ILIKE :specialty"
                    params["specialty"] = f"%{specialty}%"
                
                query += " ORDER BY full_name LIMIT 10"
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                doctors = [
                    {
                        "id": str(row[0]),
                        "name": row[1],
                        "specialty": row[2],
                        "experience_years": row[3],
                        "consultation_fee": row[4]
                    }
                    for row in rows
                ]
                
                return {"success": True, "doctors": doctors}
                
        except Exception as e:
            logger.error(f"Error listing doctors: {e}")
            return {"success": False, "doctors": [], "error": str(e)}
    
    async def get_doctor_info(
        self,
        doctor_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific doctor.
        """
        try:
            async with async_session() as session:
                doctor = await self._find_doctor(session, doctor_name)
                
                if not doctor:
                    return {"found": False}
                
                return {
                    "found": True,
                    "id": str(doctor["id"]),
                    "name": doctor["full_name"],
                    "specialty": doctor["specialty"],
                    "department": doctor.get("department", ""),
                    "qualification": doctor.get("qualification", ""),
                    "experience_years": doctor.get("experience_years", 0),
                    "consultation_fee": doctor.get("consultation_fee", 0),
                    "languages": doctor.get("languages", ["en"])
                }
                
        except Exception as e:
            logger.error(f"Error getting doctor info: {e}")
            return {"found": False, "error": str(e)}
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    async def _find_doctor(self, session, doctor_spec: str) -> Optional[Dict[str, Any]]:
        """Find a doctor by name or specialty"""
        # Try exact name match first
        result = await session.execute(
            "SELECT * FROM doctors WHERE full_name ILIKE :name AND is_active = true LIMIT 1",
            {"name": f"%{doctor_spec}%"}
        )
        row = result.fetchone()
        
        if not row:
            # Try specialty match
            result = await session.execute(
                "SELECT * FROM doctors WHERE specialty ILIKE :spec AND is_active = true LIMIT 1",
                {"spec": f"%{doctor_spec}%"}
            )
            row = result.fetchone()
        
        if row:
            return dict(row._mapping)
        return None
    
    async def _find_appointment(
        self,
        session,
        identifier: str,
        patient_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Find appointment by ID or date"""
        # Try as UUID first
        try:
            uuid.UUID(identifier)
            query = """
                SELECT a.*, d.full_name as doctor_name 
                FROM appointments a 
                JOIN doctors d ON a.doctor_id = d.id 
                WHERE a.id = :id
            """
            params = {"id": identifier}
        except ValueError:
            # Try as date
            query = """
                SELECT a.*, d.full_name as doctor_name 
                FROM appointments a 
                JOIN doctors d ON a.doctor_id = d.id 
                WHERE a.appointment_date = :date AND a.status != 'cancelled'
            """
            params = {"date": identifier}
            if patient_id:
                query += " AND a.patient_id = :patient_id"
                params["patient_id"] = patient_id
            query += " LIMIT 1"
        
        result = await session.execute(query, params)
        row = result.fetchone()
        
        if row:
            return dict(row._mapping)
        return None
    
    async def _check_slot_available(
        self,
        session,
        doctor_id: str,
        appt_date: date,
        start_time: time,
        end_time: time
    ) -> bool:
        """Check if a time slot is available"""
        result = await session.execute(
            """
            SELECT COUNT(*) FROM appointments
            WHERE doctor_id = :doctor_id
            AND appointment_date = :date
            AND status NOT IN ('cancelled', 'no_show')
            AND (
                (start_time <= :start_time AND end_time > :start_time)
                OR (start_time < :end_time AND end_time >= :end_time)
                OR (start_time >= :start_time AND end_time <= :end_time)
            )
            """,
            {
                "doctor_id": doctor_id,
                "date": appt_date,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        count = result.scalar()
        return count == 0
    
    async def _get_available_slots(
        self,
        session,
        doctor_id: str,
        appt_date: date
    ) -> List[time]:
        """Get all available slots for a doctor on a specific date"""
        day_of_week = appt_date.weekday()
        
        # Get doctor's schedule for this day
        schedule_result = await session.execute(
            """
            SELECT start_time, end_time, slot_duration_minutes
            FROM doctor_schedules
            WHERE doctor_id = :doctor_id AND day_of_week = :day AND is_active = true
            """,
            {"doctor_id": doctor_id, "day": day_of_week}
        )
        schedules = schedule_result.fetchall()
        
        if not schedules:
            return []
        
        # Get booked appointments
        appointments_result = await session.execute(
            """
            SELECT start_time, end_time FROM appointments
            WHERE doctor_id = :doctor_id AND appointment_date = :date
            AND status NOT IN ('cancelled', 'no_show')
            """,
            {"doctor_id": doctor_id, "date": appt_date}
        )
        booked = appointments_result.fetchall()
        booked_times = [(row[0], row[1]) for row in booked]
        
        # Generate available slots
        available = []
        for schedule in schedules:
            schedule_start, schedule_end, duration = schedule
            duration = duration or 30
            
            current = datetime.combine(appt_date, schedule_start)
            end = datetime.combine(appt_date, schedule_end)
            
            while current + timedelta(minutes=duration) <= end:
                slot_start = current.time()
                slot_end = (current + timedelta(minutes=duration)).time()
                
                # Check if slot is free
                is_free = all(
                    not (booked_start <= slot_start < booked_end or 
                         booked_start < slot_end <= booked_end)
                    for booked_start, booked_end in booked_times
                )
                
                if is_free:
                    available.append(slot_start)
                
                current += timedelta(minutes=duration)
        
        return available
    
    async def _get_alternative_slots(
        self,
        session,
        doctor_id: str,
        appt_date: date,
        num_slots: int = 3
    ) -> List[str]:
        """Get alternative available slots"""
        slots = await self._get_available_slots(session, doctor_id, appt_date)
        return [s.strftime("%H:%M") for s in slots[:num_slots]]
