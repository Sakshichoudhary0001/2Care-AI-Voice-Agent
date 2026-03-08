"""
Doctors API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, time
import uuid

from backend.models.database import get_db
from backend.models.schemas import DoctorResponse, DoctorAvailability, TimeSlot

router = APIRouter(prefix="/doctors")


@router.get("", response_model=List[DoctorResponse])
async def list_doctors(
    specialty: Optional[str] = None,
    department: Optional[str] = None,
    available_date: Optional[date] = None,
    language: Optional[str] = Query(None, description="Filter by language: en, hi, ta"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List doctors with optional filters"""
    query = "SELECT * FROM doctors WHERE is_active = true"
    params = {}
    
    if specialty:
        query += " AND specialty ILIKE :specialty"
        params["specialty"] = f"%{specialty}%"
    if department:
        query += " AND department ILIKE :department"
        params["department"] = f"%{department}%"
    if language:
        query += " AND :language = ANY(languages)"
        params["language"] = language
    
    query += " ORDER BY full_name LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = await db.execute(query, params)
    return result.fetchall()


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get doctor by ID"""
    result = await db.execute(
        "SELECT * FROM doctors WHERE id = :id AND is_active = true",
        {"id": doctor_id}
    )
    doctor = result.fetchone()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    return doctor


@router.get("/{doctor_id}/availability", response_model=DoctorAvailability)
async def get_doctor_availability(
    doctor_id: uuid.UUID,
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(None, description="End date (defaults to date_from)"),
    db: AsyncSession = Depends(get_db)
):
    """Get doctor's available time slots"""
    doctor = await get_doctor(doctor_id, db)
    date_to = date_to or date_from
    
    # Get doctor's schedule
    schedule_result = await db.execute(
        """
        SELECT day_of_week, start_time, end_time, slot_duration_minutes
        FROM doctor_schedules 
        WHERE doctor_id = :doctor_id AND is_active = true
        """,
        {"doctor_id": doctor_id}
    )
    schedules = schedule_result.fetchall()
    
    # Get existing appointments
    appointments_result = await db.execute(
        """
        SELECT appointment_date, start_time, end_time
        FROM appointments
        WHERE doctor_id = :doctor_id
        AND appointment_date BETWEEN :date_from AND :date_to
        AND status NOT IN ('cancelled', 'no_show')
        """,
        {"doctor_id": doctor_id, "date_from": date_from, "date_to": date_to}
    )
    booked_slots = appointments_result.fetchall()
    
    # Calculate available slots
    available_slots = []
    current_date = date_from
    
    while current_date <= date_to:
        day_of_week = current_date.weekday()
        day_schedule = [s for s in schedules if s.day_of_week == day_of_week]
        
        for schedule in day_schedule:
            slot_start = schedule.start_time
            slot_duration = schedule.slot_duration_minutes or 30
            
            while slot_start < schedule.end_time:
                slot_end_minutes = slot_start.hour * 60 + slot_start.minute + slot_duration
                slot_end = time(slot_end_minutes // 60, slot_end_minutes % 60)
                
                # Check if slot is available
                is_booked = any(
                    b.appointment_date == current_date and
                    b.start_time <= slot_start and b.end_time > slot_start
                    for b in booked_slots
                )
                
                if not is_booked:
                    available_slots.append(TimeSlot(
                        date=current_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        is_available=True
                    ))
                
                slot_start = slot_end
        
        current_date = date(current_date.year, current_date.month, current_date.day + 1)
    
    return DoctorAvailability(
        doctor_id=doctor_id,
        doctor_name=doctor.full_name,
        slots=available_slots
    )


@router.get("/specialties/list")
async def list_specialties(db: AsyncSession = Depends(get_db)):
    """List all available specialties"""
    result = await db.execute(
        "SELECT DISTINCT specialty FROM doctors WHERE is_active = true ORDER BY specialty"
    )
    return [row[0] for row in result.fetchall()]


@router.get("/departments/list")
async def list_departments(db: AsyncSession = Depends(get_db)):
    """List all departments"""
    result = await db.execute(
        "SELECT DISTINCT department FROM doctors WHERE is_active = true ORDER BY department"
    )
    return [row[0] for row in result.fetchall()]
