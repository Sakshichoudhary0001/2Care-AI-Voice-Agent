"""
Speech-to-Text Service
Supports OpenAI Whisper (primary), Azure Speech, and Google Cloud Speech
"""

import asyncio
import logging
import time
from typing import Optional, Tuple
import io

from openai import AsyncOpenAI
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class STTService:
    """
    Speech-to-Text service with multiple provider support.
    Primary: OpenAI Whisper API (best for multilingual)
    Fallback: Azure Speech Services, Google Cloud Speech
    """
    
    SUPPORTED_LANGUAGES = {
        "en": "english",
        "hi": "hindi", 
        "ta": "tamil"
    }
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.azure_client = None  # Initialize Azure client if needed
        self.google_client = None  # Initialize Google client if needed
        
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        provider: str = "openai"
    ) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes (WAV format, 16kHz, mono)
            language: Language code (en, hi, ta)
            provider: STT provider to use
            
        Returns:
            Transcribed text
        """
        start_time = time.time()
        
        try:
            if provider == "openai" and self.openai_client:
                transcript = await self._transcribe_openai(audio_data, language)
            elif provider == "azure":
                transcript = await self._transcribe_azure(audio_data, language)
            elif provider == "google":
                transcript = await self._transcribe_google(audio_data, language)
            else:
                # Default to OpenAI
                transcript = await self._transcribe_openai(audio_data, language)
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"STT completed in {latency:.0f}ms: '{transcript[:50]}...'")
            
            return transcript
            
        except Exception as e:
            logger.error(f"STT error with {provider}: {e}")
            # Try fallback
            if provider != "azure":
                return await self.transcribe(audio_data, language, "azure")
            return ""
    
    async def _transcribe_openai(self, audio_data: bytes, language: str) -> str:
        """Transcribe using OpenAI Whisper API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        # Create audio file object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        response = await self.openai_client.audio.transcriptions.create(
            model=settings.OPENAI_WHISPER_MODEL,
            file=audio_file,
            language=self.SUPPORTED_LANGUAGES.get(language, "english"),
            response_format="text"
        )
        
        return response.strip()
    
    async def _transcribe_azure(self, audio_data: bytes, language: str) -> str:
        """Transcribe using Azure Speech Services"""
        if not settings.AZURE_SPEECH_KEY:
            raise ValueError("Azure Speech key not configured")
        
        # Azure Speech SDK implementation
        # This is a placeholder - actual implementation would use azure-cognitiveservices-speech
        import aiohttp
        
        language_mapping = {
            "en": "en-IN",  # Indian English
            "hi": "hi-IN",  # Hindi
            "ta": "ta-IN"   # Tamil
        }
        
        url = f"https://{settings.AZURE_SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
            "Content-Type": "audio/wav",
            "Accept": "application/json"
        }
        
        params = {
            "language": language_mapping.get(language, "en-IN")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params, data=audio_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("DisplayText", "")
                else:
                    logger.error(f"Azure STT error: {response.status}")
                    return ""
    
    async def _transcribe_google(self, audio_data: bytes, language: str) -> str:
        """Transcribe using Google Cloud Speech-to-Text"""
        # Placeholder for Google Cloud Speech implementation
        # Would use google-cloud-speech library
        raise NotImplementedError("Google STT not implemented")
    
    async def transcribe_streaming(
        self,
        audio_stream,
        language: str = "en",
        on_partial: callable = None
    ):
        """
        Streaming transcription for real-time processing.
        Yields partial results as they become available.
        """
        # This would implement streaming transcription
        # For now, buffer and transcribe in chunks
        buffer = bytearray()
        
        async for chunk in audio_stream:
            buffer.extend(chunk)
            
            # Transcribe when we have enough audio (e.g., 1 second)
            if len(buffer) >= settings.AUDIO_SAMPLE_RATE * 2:  # 1 second of 16-bit audio
                partial = await self.transcribe(bytes(buffer), language)
                if on_partial:
                    await on_partial(partial)
                buffer.clear()
        
        # Final transcription
        if buffer:
            return await self.transcribe(bytes(buffer), language)
        return ""
