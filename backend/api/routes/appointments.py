"""
Appointments API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date
import uuid

from backend.models.database import get_db
from backend.models.schemas import (
    AppointmentCreate, AppointmentResponse, AppointmentUpdate,
    AppointmentStatus
)

router = APIRouter(prefix="/appointments")


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    patient_id: Optional[uuid.UUID] = None,
    doctor_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List appointments with optional filters"""
    # Build query with filters
    query = "SELECT * FROM appointments WHERE 1=1"
    params = {}
    
    if patient_id:
        query += " AND patient_id = :patient_id"
        params["patient_id"] = patient_id
    if doctor_id:
        query += " AND doctor_id = :doctor_id"
        params["doctor_id"] = doctor_id
    if status:
        query += " AND status = :status"
        params["status"] = status.value
    if date_from:
        query += " AND appointment_date >= :date_from"
        params["date_from"] = date_from
    if date_to:
        query += " AND appointment_date <= :date_to"
        params["date_to"] = date_to
    
    query += " ORDER BY appointment_date, start_time LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = await db.execute(query, params)
    return result.fetchall()


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get appointment by ID"""
    result = await db.execute(
        "SELECT * FROM appointments WHERE id = :id",
        {"id": appointment_id}
    )
    appointment = result.fetchone()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return appointment


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new appointment"""
    # Check doctor availability
    conflict = await db.execute(
        """
        SELECT id FROM appointments 
        WHERE doctor_id = :doctor_id 
        AND appointment_date = :date
        AND status NOT IN ('cancelled', 'no_show')
        AND (
            (start_time <= :start_time AND end_time > :start_time)
            OR (start_time < :end_time AND end_time >= :end_time)
        )
        """,
        {
            "doctor_id": appointment.doctor_id,
            "date": appointment.appointment_date,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time
        }
    )
    
    if conflict.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot not available"
        )
    
    # Create appointment
    new_id = uuid.uuid4()
    await db.execute(
        """
        INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, 
        start_time, end_time, appointment_type, reason, status)
        VALUES (:id, :patient_id, :doctor_id, :date, :start_time, :end_time, 
        :type, :reason, 'scheduled')
        """,
        {
            "id": new_id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "date": appointment.appointment_date,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "type": appointment.appointment_type,
            "reason": appointment.reason
        }
    )
    await db.commit()
    
    return await get_appointment(new_id, db)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: uuid.UUID,
    update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment"""
    existing = await get_appointment(appointment_id, db)
    
    update_fields = []
    params = {"id": appointment_id}
    
    if update.appointment_date:
        update_fields.append("appointment_date = :date")
        params["date"] = update.appointment_date
    if update.start_time:
        update_fields.append("start_time = :start_time")
        params["start_time"] = update.start_time
    if update.end_time:
        update_fields.append("end_time = :end_time")
        params["end_time"] = update.end_time
    if update.status:
        update_fields.append("status = :status")
        params["status"] = update.status.value
    if update.reason:
        update_fields.append("reason = :reason")
        params["reason"] = update.reason
    
    if update_fields:
        query = f"UPDATE appointments SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = :id"
        await db.execute(query, params)
        await db.commit()
    
    return await get_appointment(appointment_id, db)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Cancel an appointment"""
    await get_appointment(appointment_id, db)  # Verify exists
    
    await db.execute(
        "UPDATE appointments SET status = 'cancelled', updated_at = NOW() WHERE id = :id",
        {"id": appointment_id}
    )
    await db.commit()
