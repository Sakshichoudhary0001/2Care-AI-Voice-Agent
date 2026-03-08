"""
Outbound Campaign Manager
Handles proactive calling for reminders and follow-ups
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
import uuid

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class CampaignType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    FOLLOWUP_CHECKUP = "followup_checkup"
    VACCINATION_REMINDER = "vaccination_reminder"
    HEALTH_SCREENING = "health_screening"
    PRESCRIPTION_REFILL = "prescription_refill"


class CampaignStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutboundCampaign(BaseModel):
    """Represents an outbound calling campaign"""
    id: str
    campaign_type: CampaignType
    patient_id: str
    patient_name: str
    patient_phone: str
    language: str = "en"
    scheduled_time: datetime
    retry_count: int = 0
    max_retries: int = 3
    status: CampaignStatus = CampaignStatus.PENDING
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_time: Optional[datetime] = None
    custom_message: Optional[str] = None
    call_duration_seconds: Optional[int] = None
    outcome: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        use_enum_values = True


class CampaignManager:
    """
    Manages outbound calling campaigns.
    
    Features:
    - Schedule appointment reminders (24 hours before)
    - Follow-up checkup calls
    - Vaccination reminders
    - Retry failed calls with exponential backoff
    - Multi-language support
    """
    
    # Message templates for each campaign type and language
    TEMPLATES: Dict[CampaignType, Dict[str, str]] = {
        CampaignType.APPOINTMENT_REMINDER: {
            "en": "Hello {patient_name}, this is a reminder about your appointment with {doctor_name} tomorrow at {time}. Would you like to confirm, reschedule, or cancel?",
            "hi": "नमस्ते {patient_name}, यह कल {time} बजे {doctor_name} के साथ आपकी अपॉइंटमेंट की याद दिलाने के लिए है। क्या आप कन्फर्म, रीशेड्यूल या कैंसल करना चाहते हैं?",
            "ta": "வணக்கம் {patient_name}, நாளை {time} மணிக்கு {doctor_name} உடன் உங்கள் சந்திப்பை நினைவூட்டுகிறோம். உறுதிப்படுத்த, மறுதிட்டமிட அல்லது ரத்து செய்ய விரும்புகிறீர்களா?"
        },
        CampaignType.FOLLOWUP_CHECKUP: {
            "en": "Hello {patient_name}, this is 2Care.ai calling. It's time for your follow-up checkup with {doctor_name}. Would you like to schedule an appointment?",
            "hi": "नमस्ते {patient_name}, यह 2Care.ai है। {doctor_name} के साथ आपके फॉलो-अप चेकअप का समय हो गया है। क्या आप अपॉइंटमेंट बुक करना चाहते हैं?",
            "ta": "வணக்கம் {patient_name}, இது 2Care.ai. {doctor_name} உடன் உங்கள் பின்தொடர்தல் பரிசோதனைக்கான நேரம் வந்துவிட்டது. சந்திப்பை திட்டமிட விரும்புகிறீர்களா?"
        },
        CampaignType.VACCINATION_REMINDER: {
            "en": "Hello {patient_name}, this is a reminder that your {vaccine_name} vaccination is due. Would you like to schedule it?",
            "hi": "नमस्ते {patient_name}, यह याद दिलाने के लिए कि आपका {vaccine_name} टीकाकरण बाकी है। क्या आप इसे शेड्यूल करना चाहते हैं?",
            "ta": "வணக்கம் {patient_name}, உங்கள் {vaccine_name} தடுப்பூசி நிலுவையில் உள்ளது என்பதை நினைவூட்டுகிறோம். இதை திட்டமிட விரும்புகிறீர்களா?"
        },
        CampaignType.HEALTH_SCREENING: {
            "en": "Hello {patient_name}, this is 2Care.ai. Based on your health profile, we recommend a {screening_type} screening. Would you like to book an appointment?",
            "hi": "नमस्ते {patient_name}, यह 2Care.ai है। आपकी स्वास्थ्य प्रोफाइल के आधार पर, हम {screening_type} स्क्रीनिंग की सलाह देते हैं।",
            "ta": "வணக்கம் {patient_name}, இது 2Care.ai. உங்கள் உடல்நல சுயவிவரத்தின் அடிப்படையில், {screening_type} பரிசோதனையை பரிந்துரைக்கிறோம்."
        },
        CampaignType.PRESCRIPTION_REFILL: {
            "en": "Hello {patient_name}, your prescription for {medication} is about to expire. Would you like to schedule an appointment for a refill?",
            "hi": "नमस्ते {patient_name}, {medication} के लिए आपका प्रिस्क्रिप्शन समाप्त होने वाला है। क्या आप रिफिल के लिए अपॉइंटमेंट बुक करना चाहते हैं?",
            "ta": "வணக்கம் {patient_name}, {medication} க்கான உங்கள் மருந்து சீட்டு காலாவதியாகப் போகிறது. நிரப்புவதற்கு சந்திப்பை திட்டமிட விரும்புகிறீர்களா?"
        }
    }

    def __init__(self):
        self.campaigns: Dict[str, OutboundCampaign] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the campaign scheduler"""
        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Campaign manager started")
    
    async def stop(self):
        """Stop the campaign scheduler"""
        self.running = False
        if self._task:
            self._task.cancel()
        logger.info("Campaign manager stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop - checks for pending campaigns"""
        while self.running:
            try:
                await self._process_pending_campaigns()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def _process_pending_campaigns(self):
        """Process all pending campaigns that are due"""
        now = datetime.utcnow()
        
        for campaign_id, campaign in list(self.campaigns.items()):
            if (campaign.status == CampaignStatus.PENDING and 
                campaign.scheduled_time <= now):
                await self._execute_campaign(campaign)
    
    async def _execute_campaign(self, campaign: OutboundCampaign):
        """Execute a single outbound campaign"""
        campaign.status = CampaignStatus.IN_PROGRESS
        campaign.updated_at = datetime.utcnow()
        
        try:
            # Generate the message
            message = self._generate_message(campaign)
            
            # In production, this would initiate an actual call
            # For now, we log and simulate
            logger.info(f"Executing campaign {campaign.id}: {campaign.campaign_type}")
            logger.info(f"Calling {campaign.patient_phone} with message: {message[:100]}...")
            
            # Simulate call (in production: integrate with Twilio/Vonage)
            # await self._make_call(campaign.patient_phone, message, campaign.language)
            
            campaign.status = CampaignStatus.COMPLETED
            campaign.outcome = "call_completed"
            logger.info(f"Campaign {campaign.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Campaign {campaign.id} failed: {e}")
            campaign.retry_count += 1
            
            if campaign.retry_count < campaign.max_retries:
                # Schedule retry with exponential backoff
                backoff = 2 ** campaign.retry_count * 5  # 10, 20, 40 minutes
                campaign.scheduled_time = datetime.utcnow() + timedelta(minutes=backoff)
                campaign.status = CampaignStatus.PENDING
                logger.info(f"Retrying campaign {campaign.id} in {backoff} minutes")
            else:
                campaign.status = CampaignStatus.FAILED
                campaign.outcome = f"failed_after_{campaign.max_retries}_retries"
        
        campaign.updated_at = datetime.utcnow()
    
    def _generate_message(self, campaign: OutboundCampaign) -> str:
        """Generate the outbound message from template"""
        template = self.TEMPLATES.get(
            CampaignType(campaign.campaign_type), {}
        ).get(campaign.language, "")
        
        if campaign.custom_message:
            return campaign.custom_message
        
        # Format template with campaign data
        return template.format(
            patient_name=campaign.patient_name,
            doctor_name=campaign.doctor_name or "your doctor",
            time=campaign.appointment_time.strftime("%I:%M %p") if campaign.appointment_time else "",
            vaccine_name=getattr(campaign, 'vaccine_name', 'scheduled'),
            screening_type=getattr(campaign, 'screening_type', 'health'),
            medication=getattr(campaign, 'medication', 'your medication')
        )
    
    async def create_campaign(
        self,
        campaign_type: CampaignType,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        language: str = "en",
        scheduled_time: datetime = None,
        **kwargs
    ) -> OutboundCampaign:
        """
        Create a new outbound campaign.
        
        Args:
            campaign_type: Type of campaign
            patient_id: Patient identifier
            patient_name: Patient's name
            patient_phone: Phone number to call
            language: Preferred language
            scheduled_time: When to make the call
            **kwargs: Additional campaign-specific data
        
        Returns:
            Created campaign object
        """
        campaign = OutboundCampaign(
            id=str(uuid.uuid4()),
            campaign_type=campaign_type,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            language=language,
            scheduled_time=scheduled_time or datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )
        
        self.campaigns[campaign.id] = campaign
        logger.info(f"Created campaign: {campaign.id} ({campaign.campaign_type})")
        
        return campaign
    
    async def create_appointment_reminder(
        self,
        patient_id: str,
        patient_name: str,
        patient_phone: str,
        appointment_id: str,
        doctor_name: str,
        appointment_time: datetime,
        language: str = "en",
        hours_before: int = 24
    ) -> OutboundCampaign:
        """Create an appointment reminder campaign"""
        scheduled_time = appointment_time - timedelta(hours=hours_before)
        
        return await self.create_campaign(
            campaign_type=CampaignType.APPOINTMENT_REMINDER,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_phone=patient_phone,
            language=language,
            scheduled_time=scheduled_time,
            appointment_id=appointment_id,
            doctor_name=doctor_name,
            appointment_time=appointment_time
        )
    
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """Cancel a pending campaign"""
        if campaign_id in self.campaigns:
            campaign = self.campaigns[campaign_id]
            if campaign.status == CampaignStatus.PENDING:
                campaign.status = CampaignStatus.CANCELLED
                campaign.updated_at = datetime.utcnow()
                logger.info(f"Campaign cancelled: {campaign_id}")
                return True
        return False
    
    def get_campaign(self, campaign_id: str) -> Optional[OutboundCampaign]:
        """Get campaign by ID"""
        return self.campaigns.get(campaign_id)
    
    def list_campaigns(
        self,
        patient_id: str = None,
        status: CampaignStatus = None,
        campaign_type: CampaignType = None
    ) -> List[OutboundCampaign]:
        """List campaigns with optional filters"""
        campaigns = list(self.campaigns.values())
        
        if patient_id:
            campaigns = [c for c in campaigns if c.patient_id == patient_id]
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        if campaign_type:
            campaigns = [c for c in campaigns if c.campaign_type == campaign_type]
        
        return sorted(campaigns, key=lambda c: c.scheduled_time)


# Singleton instance
campaign_manager = CampaignManager()
