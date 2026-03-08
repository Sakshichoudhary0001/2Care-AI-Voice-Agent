"""
Text-to-Speech Service
Supports Azure Speech (primary for Indian languages), ElevenLabs, OpenAI TTS
"""

import asyncio
import logging
import time
from typing import Optional
import io

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service with multiple provider support.
    - Azure Speech Services: Best for Hindi and Tamil
    - ElevenLabs: Natural English voices
    - OpenAI TTS: Good quality, simple API
    """
    
    # Voice configurations per language
    AZURE_VOICES = {
        "en": "en-IN-NeerjaNeural",     # Indian English female
        "hi": "hi-IN-SwaraNeural",       # Hindi female
        "ta": "ta-IN-PallaviNeural"      # Tamil female
    }
    
    ELEVENLABS_VOICES = {
        "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice
    }
    
    OPENAI_VOICES = {
        "en": "nova",
        "hi": "nova",
        "ta": "nova"
    }
    
    def __init__(self):
        self.azure_key = settings.AZURE_SPEECH_KEY
        self.azure_region = settings.AZURE_SPEECH_REGION
        self.elevenlabs_key = settings.ELEVENLABS_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
    
    async def synthesize(
        self,
        text: str,
        language: str = "en",
        provider: str = None
    ) -> bytes:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            language: Language code (en, hi, ta)
            provider: TTS provider (auto-selects based on language if not specified)
            
        Returns:
            Audio bytes (WAV format)
        """
        if not text or not text.strip():
            return b""
        
        start_time = time.time()
        
        # Auto-select provider based on language
        if provider is None:
            if language in ["hi", "ta"]:
                provider = "azure"  # Azure is best for Indian languages
            elif self.elevenlabs_key:
                provider = "elevenlabs"  # ElevenLabs for natural English
            else:
                provider = "openai"
        
        try:
            if provider == "azure" and self.azure_key:
                audio = await self._synthesize_azure(text, language)
            elif provider == "elevenlabs" and self.elevenlabs_key:
                audio = await self._synthesize_elevenlabs(text, language)
            elif provider == "openai" and self.openai_key:
                audio = await self._synthesize_openai(text, language)
            else:
                # Fallback chain
                audio = await self._synthesize_with_fallback(text, language)
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"TTS completed in {latency:.0f}ms ({len(audio)} bytes)")
            
            return audio
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""
    
    async def _synthesize_azure(self, text: str, language: str) -> bytes:
        """Synthesize using Azure Speech Services"""
        import aiohttp
        
        voice = self.AZURE_VOICES.get(language, self.AZURE_VOICES["en"])
        
        url = f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm"
        }
        
        # SSML for better control
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{language}'>
            <voice name='{voice}'>
                <prosody rate='1.0' pitch='0%'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=ssml.encode('utf-8')) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error = await response.text()
                    logger.error(f"Azure TTS error: {response.status} - {error}")
                    raise Exception(f"Azure TTS failed: {response.status}")
    
    async def _synthesize_elevenlabs(self, text: str, language: str) -> bytes:
        """Synthesize using ElevenLabs API"""
        import aiohttp
        
        voice_id = self.ELEVENLABS_VOICES.get(language, settings.ELEVENLABS_VOICE_ID)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.elevenlabs_key,
            "Content-Type": "application/json",
            "Accept": "audio/wav"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error = await response.text()
                    logger.error(f"ElevenLabs TTS error: {response.status} - {error}")
                    raise Exception(f"ElevenLabs TTS failed: {response.status}")
    
    async def _synthesize_openai(self, text: str, language: str) -> bytes:
        """Synthesize using OpenAI TTS API"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.openai_key)
        voice = self.OPENAI_VOICES.get(language, "nova")
        
        response = await client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=voice,
            input=text,
            response_format="wav"
        )
        
        return response.content
    
    async def _synthesize_with_fallback(self, text: str, language: str) -> bytes:
        """Try multiple providers with fallback"""
        providers = []
        
        if self.azure_key:
            providers.append(("azure", self._synthesize_azure))
        if self.openai_key:
            providers.append(("openai", self._synthesize_openai))
        if self.elevenlabs_key:
            providers.append(("elevenlabs", self._synthesize_elevenlabs))
        
        for name, method in providers:
            try:
                return await method(text, language)
            except Exception as e:
                logger.warning(f"TTS fallback: {name} failed - {e}")
                continue
        
        raise Exception("All TTS providers failed")
    
    async def synthesize_streaming(
        self,
        text: str,
        language: str = "en"
    ):
        """
        Streaming TTS for lower time-to-first-byte.
        Yields audio chunks as they become available.
        """
        # For streaming, we could use Azure's streaming API or
        # chunk the text and synthesize in parallel
        
        # Simple chunking approach
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            audio = await self.synthesize(sentence + ".", language)
            yield audio
