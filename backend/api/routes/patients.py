"""
Patients API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from backend.models.database import get_db
from backend.models.schemas import PatientCreate, PatientResponse, PatientUpdate

router = APIRouter(prefix="/patients")


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List patients with optional search"""
    query = "SELECT * FROM patients WHERE 1=1"
    params = {}
    
    if search:
        query += """ AND (
            full_name ILIKE :search 
            OR phone_number LIKE :phone_search
            OR email ILIKE :search
        )"""
        params["search"] = f"%{search}%"
        params["phone_search"] = f"%{search}%"
    
    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = await db.execute(query, params)
    return result.fetchall()


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get patient by ID"""
    result = await db.execute(
        "SELECT * FROM patients WHERE id = :id",
        {"id": patient_id}
    )
    patient = result.fetchone()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.get("/phone/{phone_number}", response_model=PatientResponse)
async def get_patient_by_phone(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get patient by phone number"""
    result = await db.execute(
        "SELECT * FROM patients WHERE phone_number = :phone",
        {"phone": phone_number}
    )
    patient = result.fetchone()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient"""
    # Check if phone already exists
    existing = await db.execute(
        "SELECT id FROM patients WHERE phone_number = :phone",
        {"phone": patient.phone_number}
    )
    if existing.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient with this phone number already exists"
        )
    
    new_id = uuid.uuid4()
    await db.execute(
        """
        INSERT INTO patients (id, full_name, phone_number, email, date_of_birth,
        gender, preferred_language, address)
        VALUES (:id, :name, :phone, :email, :dob, :gender, :language, :address)
        """,
        {
            "id": new_id,
            "name": patient.full_name,
            "phone": patient.phone_number,
            "email": patient.email,
            "dob": patient.date_of_birth,
            "gender": patient.gender,
            "language": patient.preferred_language or "en",
            "address": patient.address
        }
    )
    await db.commit()
    
    return await get_patient(new_id, db)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: uuid.UUID,
    update: PatientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update patient information"""
    await get_patient(patient_id, db)  # Verify exists
    
    update_fields = []
    params = {"id": patient_id}
    
    if update.full_name:
        update_fields.append("full_name = :name")
        params["name"] = update.full_name
    if update.email:
        update_fields.append("email = :email")
        params["email"] = update.email
    if update.preferred_language:
        update_fields.append("preferred_language = :language")
        params["language"] = update.preferred_language
    if update.address:
        update_fields.append("address = :address")
        params["address"] = update.address
    
    if update_fields:
        query = f"UPDATE patients SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = :id"
        await db.execute(query, params)
        await db.commit()
    
    return await get_patient(patient_id, db)


@router.get("/{patient_id}/appointments")
async def get_patient_appointments(
    patient_id: uuid.UUID,
    include_past: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all appointments for a patient"""
    await get_patient(patient_id, db)  # Verify exists
    
    query = """
        SELECT a.*, d.full_name as doctor_name, d.specialty
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = :patient_id
    """
    
    if not include_past:
        query += " AND (a.appointment_date > CURRENT_DATE OR (a.appointment_date = CURRENT_DATE AND a.start_time > CURRENT_TIME))"
    
    query += " ORDER BY a.appointment_date, a.start_time"
    
    result = await db.execute(query, {"patient_id": patient_id})
    return result.fetchall()
