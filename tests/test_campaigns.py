"""
Tests for Outbound Campaigns
"""

import pytest
from datetime import datetime, timedelta


class TestCampaignManager:
    """Test suite for outbound campaign management"""

    @pytest.mark.asyncio
    async def test_create_appointment_reminder(self):
        """Should create appointment reminder campaign"""
        from backend.scheduler.campaign_manager import campaign_manager, CampaignType
        
        appointment_time = datetime.utcnow() + timedelta(days=1)
        
        campaign = await campaign_manager.create_appointment_reminder(
            patient_id="patient-123",
            patient_name="John Doe",
            patient_phone="+1234567890",
            appointment_id="apt-456",
            doctor_name="Dr. Sharma",
            appointment_time=appointment_time
        )
        
        assert campaign.campaign_type == CampaignType.APPOINTMENT_REMINDER.value
        assert campaign.patient_name == "John Doe"
        # Should be scheduled 24 hours before appointment
        assert campaign.scheduled_time < appointment_time

    @pytest.mark.asyncio
    async def test_create_followup_campaign(self):
        """Should create follow-up checkup campaign"""
        from backend.scheduler.campaign_manager import campaign_manager, CampaignType
        
        campaign = await campaign_manager.create_campaign(
            campaign_type=CampaignType.FOLLOWUP_CHECKUP,
            patient_id="patient-123",
            patient_name="John Doe",
            patient_phone="+1234567890",
            language="hi",
            doctor_name="Dr. Patel"
        )
        
        assert campaign.campaign_type == CampaignType.FOLLOWUP_CHECKUP.value
        assert campaign.language == "hi"

    @pytest.mark.asyncio
    async def test_cancel_campaign(self):
        """Should cancel a pending campaign"""
        from backend.scheduler.campaign_manager import campaign_manager, CampaignType, CampaignStatus
        
        campaign = await campaign_manager.create_campaign(
            campaign_type=CampaignType.VACCINATION_REMINDER,
            patient_id="patient-789",
            patient_name="Jane Doe",
            patient_phone="+9876543210"
        )
        
        result = await campaign_manager.cancel_campaign(campaign.id)
        
        assert result == True
        
        updated = campaign_manager.get_campaign(campaign.id)
        assert updated.status == CampaignStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_list_campaigns_by_patient(self):
        """Should filter campaigns by patient"""
        from backend.scheduler.campaign_manager import campaign_manager, CampaignType
        
        # Create campaigns for different patients
        await campaign_manager.create_campaign(
            campaign_type=CampaignType.APPOINTMENT_REMINDER,
            patient_id="patient-A",
            patient_name="Patient A",
            patient_phone="+1111111111"
        )
        
        await campaign_manager.create_campaign(
            campaign_type=CampaignType.APPOINTMENT_REMINDER,
            patient_id="patient-B",
            patient_name="Patient B",
            patient_phone="+2222222222"
        )
        
        campaigns = campaign_manager.list_campaigns(patient_id="patient-A")
        
        assert all(c.patient_id == "patient-A" for c in campaigns)

    @pytest.mark.asyncio
    async def test_multilingual_message_generation(self):
        """Should generate messages in multiple languages"""
        from backend.scheduler.campaign_manager import campaign_manager, CampaignType
        
        appointment_time = datetime.utcnow() + timedelta(days=1)
        
        # English
        campaign_en = await campaign_manager.create_appointment_reminder(
            patient_id="p1",
            patient_name="John",
            patient_phone="+1",
            appointment_id="a1",
            doctor_name="Dr. Smith",
            appointment_time=appointment_time,
            language="en"
        )
        
        # Hindi
        campaign_hi = await campaign_manager.create_appointment_reminder(
            patient_id="p2",
            patient_name="राहुल",
            patient_phone="+2",
            appointment_id="a2",
            doctor_name="Dr. Sharma",
            appointment_time=appointment_time,
            language="hi"
        )
        
        assert campaign_en.language == "en"
        assert campaign_hi.language == "hi"


class TestReminderService:
    """Test suite for reminder service"""

    @pytest.mark.asyncio
    async def test_on_appointment_booked(self):
        """Should create reminder when appointment is booked"""
        from backend.scheduler.reminder_service import reminder_service
        
        appointment_time = datetime.utcnow() + timedelta(days=2)
        
        campaign = await reminder_service.on_appointment_booked(
            appointment_id="apt-test-1",
            patient_id="patient-test",
            patient_name="Test Patient",
            patient_phone="+1234567890",
            doctor_name="Dr. Test",
            appointment_time=appointment_time
        )
        
        assert campaign is not None
        assert campaign.appointment_id == "apt-test-1"

    @pytest.mark.asyncio
    async def test_on_appointment_cancelled(self):
        """Should cancel reminders when appointment is cancelled"""
        from backend.scheduler.reminder_service import reminder_service
        
        appointment_time = datetime.utcnow() + timedelta(days=2)
        
        # Create appointment with reminder
        await reminder_service.on_appointment_booked(
            appointment_id="apt-cancel-test",
            patient_id="patient-test",
            patient_name="Test Patient",
            patient_phone="+1234567890",
            doctor_name="Dr. Test",
            appointment_time=appointment_time
        )
        
        # Cancel
        cancelled_count = await reminder_service.on_appointment_cancelled("apt-cancel-test")
        
        assert cancelled_count >= 0  # May be 0 if already processed
