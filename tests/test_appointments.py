"""
Tests for Appointment Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch


class TestAppointmentService:
    """Test suite for appointment booking logic"""

    @pytest.mark.asyncio
    async def test_check_availability(self, sample_doctor):
        """Should return available slots"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        
        result = await tools.check_availability(
            doctor_id=sample_doctor["id"],
            date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        )
        
        assert "available_slots" in result
        assert isinstance(result["available_slots"], list)

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, sample_patient, sample_doctor):
        """Should successfully book an appointment"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        
        result = await tools.book_appointment(
            patient_name=sample_patient["name"],
            patient_phone=sample_patient["phone"],
            doctor_id=sample_doctor["id"],
            date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            time="10:00"
        )
        
        assert result["success"] == True
        assert "appointment_id" in result

    @pytest.mark.asyncio
    async def test_prevent_double_booking(self, sample_patient, sample_doctor):
        """Should prevent double booking same slot"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        time = "10:00"
        
        # First booking should succeed
        result1 = await tools.book_appointment(
            patient_name=sample_patient["name"],
            patient_phone=sample_patient["phone"],
            doctor_id=sample_doctor["id"],
            date=date,
            time=time
        )
        
        # Second booking same slot should fail
        result2 = await tools.book_appointment(
            patient_name="Another Patient",
            patient_phone="+9999999999",
            doctor_id=sample_doctor["id"],
            date=date,
            time=time
        )
        
        assert result1["success"] == True
        assert result2["success"] == False
        assert "conflict" in result2.get("error", "").lower() or "already" in result2.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_prevent_past_booking(self, sample_patient, sample_doctor):
        """Should reject bookings in the past"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        
        result = await tools.book_appointment(
            patient_name=sample_patient["name"],
            patient_phone=sample_patient["phone"],
            doctor_id=sample_doctor["id"],
            date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            time="10:00"
        )
        
        assert result["success"] == False

    @pytest.mark.asyncio
    async def test_cancel_appointment(self, sample_appointment):
        """Should cancel an existing appointment"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        
        result = await tools.cancel_appointment(
            appointment_id=sample_appointment["id"]
        )
        
        assert "cancelled" in result.get("message", "").lower() or result.get("success") == True

    @pytest.mark.asyncio
    async def test_reschedule_appointment(self, sample_appointment):
        """Should reschedule to new slot"""
        from backend.agent.tools.appointment_tools import AppointmentTools
        
        tools = AppointmentTools()
        
        new_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        result = await tools.reschedule_appointment(
            appointment_id=sample_appointment["id"],
            new_date=new_date,
            new_time="14:00"
        )
        
        assert result.get("success") == True or "rescheduled" in result.get("message", "").lower()
