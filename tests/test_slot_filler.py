"""
Tests for Slot Filling
"""

import pytest
from datetime import datetime


class TestSlotFiller:
    """Test suite for slot extraction"""

    @pytest.mark.asyncio
    async def test_extract_doctor_specialty(self):
        """Should extract doctor specialty"""
        from backend.agent.reasoning.slot_filler import SlotFiller
        
        filler = SlotFiller()
        
        test_cases = [
            ("cardiologist", "cardiology"),
            ("heart doctor", "cardiology"),
            ("dermatologist", "dermatology"),
            ("skin specialist", "dermatology"),
            ("orthopedic", "orthopedics"),
        ]
        
        for text, expected in test_cases:
            result = await filler.extract_slots(f"I need a {text}", "en", "book_appointment")
            assert result.get("specialty") == expected, f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_extract_date(self):
        """Should extract appointment date"""
        from backend.agent.reasoning.slot_filler import SlotFiller
        
        filler = SlotFiller()
        
        result = await filler.extract_slots(
            "Book for tomorrow at 10 AM",
            "en",
            "book_appointment"
        )
        
        assert "date" in result
        assert "time" in result

    @pytest.mark.asyncio
    async def test_extract_time(self):
        """Should extract appointment time"""
        from backend.agent.reasoning.slot_filler import SlotFiller
        
        filler = SlotFiller()
        
        test_cases = [
            ("10 AM", "10:00"),
            ("2 PM", "14:00"),
            ("morning", "09:00"),
            ("afternoon", "14:00"),
            ("evening", "17:00"),
        ]
        
        for text, expected_contains in test_cases:
            result = await filler.extract_slots(
                f"Schedule at {text}",
                "en",
                "book_appointment"
            )
            assert "time" in result, f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_extract_patient_info(self):
        """Should extract patient information"""
        from backend.agent.reasoning.slot_filler import SlotFiller
        
        filler = SlotFiller()
        
        result = await filler.extract_slots(
            "My name is John and phone is 9876543210",
            "en",
            "book_appointment"
        )
        
        assert result.get("patient_name") == "John"
        assert "phone" in result

    @pytest.mark.asyncio
    async def test_slot_validation(self):
        """Should validate slot values"""
        from backend.agent.reasoning.slot_filler import SlotFiller
        
        filler = SlotFiller()
        
        # Invalid phone should not be extracted
        result = await filler.extract_slots(
            "Call me at abc123",
            "en",
            "book_appointment"
        )
        
        assert result.get("phone") is None
