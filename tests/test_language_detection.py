"""
Tests for Language Detection
"""

import pytest


class TestLanguageDetection:
    """Test suite for language detection"""

    @pytest.mark.asyncio
    async def test_detect_english(self):
        """Should detect English"""
        from backend.services.language_detection import LanguageDetector
        
        detector = LanguageDetector()
        
        test_cases = [
            "I want to book an appointment",
            "Hello, how are you?",
            "Schedule visit with doctor",
        ]
        
        for text in test_cases:
            result = await detector.detect(text)
            assert result == "en", f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_detect_hindi(self):
        """Should detect Hindi"""
        from backend.services.language_detection import LanguageDetector
        
        detector = LanguageDetector()
        
        test_cases = [
            "मुझे डॉक्टर से मिलना है",
            "अपॉइंटमेंट बुक करना है",
            "नमस्ते, कैसे हैं आप?",
        ]
        
        for text in test_cases:
            result = await detector.detect(text)
            assert result == "hi", f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_detect_tamil(self):
        """Should detect Tamil"""
        from backend.services.language_detection import LanguageDetector
        
        detector = LanguageDetector()
        
        test_cases = [
            "நாளை மருத்துவரை பார்க்க வேண்டும்",
            "வணக்கம்",
            "சந்திப்பை முன்பதிவு செய்ய வேண்டும்",
        ]
        
        for text in test_cases:
            result = await detector.detect(text)
            assert result == "ta", f"Failed for: {text}"

    @pytest.mark.asyncio
    async def test_mixed_language(self):
        """Should handle code-mixed text"""
        from backend.services.language_detection import LanguageDetector
        
        detector = LanguageDetector()
        
        # Hindi-English mixed
        result = await detector.detect("Doctor से appointment book करना है")
        assert result in ["hi", "en"]  # Either is acceptable for mixed
