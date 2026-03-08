"""
Test Suite for 2Care.ai Voice AI Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta


# Test fixtures
@pytest.fixture
def sample_patient():
    return {
        "id": "patient-123",
        "name": "John Doe",
        "phone": "+1234567890",
        "language": "en"
    }


@pytest.fixture
def sample_doctor():
    return {
        "id": "doctor-456",
        "name": "Dr. Sharma",
        "specialty": "cardiology"
    }


@pytest.fixture
def sample_appointment():
    return {
        "id": "apt-789",
        "patient_id": "patient-123",
        "doctor_id": "doctor-456",
        "date": datetime.now() + timedelta(days=1),
        "time": "10:00 AM",
        "status": "confirmed"
    }
