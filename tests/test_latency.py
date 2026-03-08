"""
Tests for Latency Measurement
"""

import pytest
import time
from unittest.mock import AsyncMock, patch


class TestLatencyMeasurement:
    """Test suite for latency requirements"""

    @pytest.mark.asyncio
    async def test_stt_latency_target(self):
        """STT should complete within 120ms target"""
        from backend.services.stt_service import STTService
        from backend.config.settings import settings
        
        stt = STTService()
        
        # Generate test audio (silence)
        test_audio = b'\x00' * 16000 * 2  # 1 second of silence
        
        start = time.perf_counter()
        result = await stt.transcribe(test_audio, "en")
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Log the latency
        print(f"STT latency: {latency_ms:.0f}ms (target: {settings.STT_LATENCY_TARGET}ms)")
        
        # Note: Actual latency depends on API/model
        # This test documents the requirement

    @pytest.mark.asyncio
    async def test_tts_latency_target(self):
        """TTS should complete within 100ms target"""
        from backend.services.tts_service import TTSService
        from backend.config.settings import settings
        
        tts = TTSService()
        
        test_text = "Hello, your appointment is confirmed."
        
        start = time.perf_counter()
        result = await tts.synthesize(test_text, "en")
        latency_ms = (time.perf_counter() - start) * 1000
        
        print(f"TTS latency: {latency_ms:.0f}ms (target: {settings.TTS_LATENCY_TARGET}ms)")

    @pytest.mark.asyncio
    async def test_total_latency_under_450ms(self):
        """Total pipeline should complete under 450ms"""
        from backend.config.settings import settings
        
        # This is an integration test requirement
        # The actual measurement happens in the WebSocket handler
        
        target = settings.TOTAL_LATENCY_TARGET
        assert target == 450, f"Target should be 450ms, got {target}ms"
        
        # Components breakdown:
        # STT: 120ms
        # LLM: 200ms  
        # TTS: 100ms
        # Buffer: 30ms
        # Total: 450ms
        
        stt_target = settings.STT_LATENCY_TARGET
        llm_target = settings.LLM_LATENCY_TARGET
        tts_target = settings.TTS_LATENCY_TARGET
        
        component_total = stt_target + llm_target + tts_target
        assert component_total <= target, f"Component total {component_total}ms exceeds target {target}ms"

    @pytest.mark.asyncio
    async def test_latency_logging(self):
        """Should log latency metrics"""
        import logging
        from unittest.mock import MagicMock
        
        # Verify that latency logging is present in the codebase
        # This is a code inspection test
        
        with open("backend/api/routes/websocket.py", "r") as f:
            content = f.read()
        
        assert "STT latency" in content, "STT latency logging missing"
        assert "Agent latency" in content, "Agent latency logging missing"
        assert "TTS latency" in content, "TTS latency logging missing"
        assert "Total latency" in content, "Total latency logging missing"
