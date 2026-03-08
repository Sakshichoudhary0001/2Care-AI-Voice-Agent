"""
Tests for Intent Classification
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestIntentClassifier:
    """Test suite for intent classification"""

    @pytest.mark.asyncio
    async def test_book_intent_english(self):
        """Should detect booking intent in English"""
        from backend.agent.reasoning.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        test_cases = [
            "I want to book an appointment",
            "Schedule a visit with doctor",
            "Can I see a cardiologist tomorrow?",
            "Book appointment please",
        ]
        
        for text in test_cases:
            result = await classifier.classify(text, "en")
            assert result["intent"] == "book_appointment", f"Failed for: {text}"
            assert result["confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_cancel_intent_english(self):
        """Should detect cancellation intent"""
        from backend.agent.reasoning.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        test_cases = [
            "Cancel my appointment",
            "I need to cancel",
            "Remove my booking",
        ]
        
        for text in test_cases:
            result = await classifier.classify(text, "en")
            assert result["intent"] == "cancel_appointment", f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_reschedule_intent(self):
        """Should detect reschedule intent"""
        from backend.agent.reasoning.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        test_cases = [
            "Reschedule my appointment",
            "Move it to Friday",
            "Change the time",
        ]
        
        for text in test_cases:
            result = await classifier.classify(text, "en")
            assert result["intent"] == "reschedule_appointment", f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_hindi_intent_detection(self):
        """Should detect intent in Hindi"""
        from backend.agent.reasoning.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        result = await classifier.classify("मुझे डॉक्टर से मिलना है", "hi")
        assert result["intent"] == "book_appointment"

    @pytest.mark.asyncio
    async def test_tamil_intent_detection(self):
        """Should detect intent in Tamil"""
        from backend.agent.reasoning.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        
        result = await classifier.classify("நாளை மருத்துவரை பார்க்க வேண்டும்", "ta")
        assert result["intent"] == "book_appointment"
