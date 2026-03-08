"""
Outbound Campaign API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.scheduler.campaign_manager import (
    campaign_manager,
    CampaignType,
    CampaignStatus,
    OutboundCampaign
)
from backend.scheduler.reminder_service import reminder_service

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CreateCampaignRequest(BaseModel):
    campaign_type: str
    patient_id: str
    patient_name: str
    patient_phone: str
    language: str = "en"
    scheduled_time: Optional[datetime] = None
    doctor_name: Optional[str] = None
    appointment_id: Optional[str] = None
    appointment_time: Optional[datetime] = None
    custom_message: Optional[str] = None


class CreateReminderRequest(BaseModel):
    appointment_id: str
    patient_id: str
    patient_name: str
    patient_phone: str
    doctor_name: str
    appointment_time: datetime
    language: str = "en"
    hours_before: int = 24


@router.post("/", response_model=dict)
async def create_campaign(request: CreateCampaignRequest):
    """Create a new outbound campaign"""
    try:
        campaign_type = CampaignType(request.campaign_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid campaign type. Must be one of: {[t.value for t in CampaignType]}"
        )
    
    campaign = await campaign_manager.create_campaign(
        campaign_type=campaign_type,
        patient_id=request.patient_id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        language=request.language,
        scheduled_time=request.scheduled_time,
        doctor_name=request.doctor_name,
        appointment_id=request.appointment_id,
        appointment_time=request.appointment_time,
        custom_message=request.custom_message
    )
    
    return {
        "success": True,
        "campaign_id": campaign.id,
        "scheduled_time": campaign.scheduled_time.isoformat()
    }


@router.post("/reminder", response_model=dict)
async def create_appointment_reminder(request: CreateReminderRequest):
    """Create an appointment reminder campaign"""
    campaign = await campaign_manager.create_appointment_reminder(
        patient_id=request.patient_id,
        patient_name=request.patient_name,
        patient_phone=request.patient_phone,
        appointment_id=request.appointment_id,
        doctor_name=request.doctor_name,
        appointment_time=request.appointment_time,
        language=request.language,
        hours_before=request.hours_before
    )
    
    return {
        "success": True,
        "campaign_id": campaign.id,
        "scheduled_time": campaign.scheduled_time.isoformat(),
        "message": f"Reminder scheduled for {request.hours_before} hours before appointment"
    }


@router.get("/", response_model=List[dict])
async def list_campaigns(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    campaign_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """List campaigns with optional filters"""
    status_filter = None
    type_filter = None
    
    if status:
        try:
            status_filter = CampaignStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if campaign_type:
        try:
            type_filter = CampaignType(campaign_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid campaign type")
    
    campaigns = campaign_manager.list_campaigns(
        patient_id=patient_id,
        status=status_filter,
        campaign_type=type_filter
    )[:limit]
    
    return [
        {
            "id": c.id,
            "campaign_type": c.campaign_type,
            "patient_id": c.patient_id,
            "patient_name": c.patient_name,
            "status": c.status,
            "scheduled_time": c.scheduled_time.isoformat(),
            "language": c.language
        }
        for c in campaigns
    ]


@router.get("/{campaign_id}", response_model=dict)
async def get_campaign(campaign_id: str):
    """Get campaign details"""
    campaign = campaign_manager.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "id": campaign.id,
        "campaign_type": campaign.campaign_type,
        "patient_id": campaign.patient_id,
        "patient_name": campaign.patient_name,
        "patient_phone": campaign.patient_phone,
        "language": campaign.language,
        "status": campaign.status,
        "scheduled_time": campaign.scheduled_time.isoformat(),
        "retry_count": campaign.retry_count,
        "appointment_id": campaign.appointment_id,
        "doctor_name": campaign.doctor_name,
        "outcome": campaign.outcome
    }


@router.delete("/{campaign_id}", response_model=dict)
async def cancel_campaign(campaign_id: str):
    """Cancel a pending campaign"""
    success = await campaign_manager.cancel_campaign(campaign_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Campaign not found or cannot be cancelled"
        )
    
    return {"success": True, "message": "Campaign cancelled"}


@router.get("/types/list", response_model=List[str])
async def list_campaign_types():
    """List available campaign types"""
    return [t.value for t in CampaignType]


@router.get("/status/list", response_model=List[str])
async def list_campaign_statuses():
    """List campaign status values"""
    return [s.value for s in CampaignStatus]
