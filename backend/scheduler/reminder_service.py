"""
Reminder Service
Automatically schedules reminders for booked appointments
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from backend.scheduler.campaign_manager import (
    campaign_manager,
    CampaignManager,
    CampaignType,
    OutboundCampaign
)

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Service for automatically managing appointment reminders.
    
    Integrates with the booking system to:
    - Create reminders when appointments are booked
    - Cancel reminders when appointments are cancelled
    - Update reminders when appointments are rescheduled
    """
    
    def __init__(self, manager: CampaignManager = None):
        self.manager = manager or campaign_manager
    
    async def on_appointment_booked(
        self,
        appointment_id: str,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        appointment_time: datetime,
        language: str = "en"
    ) -> OutboundCampaign:
        """
        Called when an appointment is booked.
        Creates reminder 24 hours before appointment.
        """
        logger.info(f"Creating reminder for appointment {appointment_id}")
        
        campaign = await self.manager.create_appointment_reminder(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            appointment_id=appointment_id,
            doctor_name=doctor_name,
            appointment_time=appointment_time,
            language=language,
            hours_before=24
        )
        
        logger.info(
            f"Reminder scheduled for {campaign.scheduled_time} "
            f"(24h before {appointment_time})"
        )
        
        return campaign
    
    async def on_appointment_cancelled(self, appointment_id: str) -> int:
        """
        Called when an appointment is cancelled.
        Cancels all pending reminders for this appointment.
        """
        cancelled_count = 0
        
        for campaign in self.manager.list_campaigns():
            if (campaign.appointment_id == appointment_id and 
                campaign.status == "pending"):
                await self.manager.cancel_campaign(campaign.id)
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} reminders for appointment {appointment_id}")
        return cancelled_count
    
    async def on_appointment_rescheduled(
        self,
        appointment_id: str,
        new_time: datetime,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        language: str = "en"
    ) -> Optional[OutboundCampaign]:
        """
        Called when an appointment is rescheduled.
        Cancels old reminders and creates new one.
        """
        # Cancel existing reminders
        await self.on_appointment_cancelled(appointment_id)
        
        # Create new reminder
        return await self.on_appointment_booked(
            appointment_id=appointment_id,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            doctor_name=doctor_name,
            appointment_time=new_time,
            language=language
        )
    
    async def create_followup_reminder(
        self,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        days_after_appointment: int = 30,
        language: str = "en"
    ) -> OutboundCampaign:
        """
        Create a follow-up checkup reminder.
        Typically scheduled 30 days after a visit.
        """
        scheduled_time = datetime.utcnow() + timedelta(days=days_after_appointment)
        
        return await self.manager.create_campaign(
            campaign_type=CampaignType.FOLLOWUP_CHECKUP,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            language=language,
            scheduled_time=scheduled_time,
            doctor_name=doctor_name
        )
    
    async def create_vaccination_reminder(
        self,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        vaccine_name: str,
        due_date: datetime,
        language: str = "en"
    ) -> OutboundCampaign:
        """Create a vaccination reminder"""
        # Remind 7 days before due date
        scheduled_time = due_date - timedelta(days=7)
        
        return await self.manager.create_campaign(
            campaign_type=CampaignType.VACCINATION_REMINDER,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            language=language,
            scheduled_time=scheduled_time,
            vaccine_name=vaccine_name
        )


# Singleton instance
reminder_service = ReminderService()
