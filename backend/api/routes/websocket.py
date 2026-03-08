"""
WebSocket Route for Real-time Voice Communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import asyncio
import json
import uuid
import logging
import time

from backend.agent.orchestrator import AgentOrchestrator
from backend.services.stt_service import STTService
from backend.services.tts_service import TTSService
from backend.services.vad_service import VADService
from backend.services.language_detection import LanguageDetector
from backend.memory.session_memory import SessionMemory
from backend.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class VoiceSession:
    """Manages a single voice session"""
    
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.language = "en"  # Default language
        self.is_active = True
        
        # Initialize services
        self.stt = STTService()
        self.tts = TTSService()
        self.vad = VADService()
        self.language_detector = LanguageDetector()
        self.agent = AgentOrchestrator(session_id)
        
        # Audio buffer
        self.audio_buffer = bytearray()
        self.last_speech_time = time.time()
    
    async def process_audio(self, audio_data: bytes) -> Optional[bytes]:
        """Process incoming audio and return response audio"""
        start_time = time.time()
        
        # Add to buffer
        self.audio_buffer.extend(audio_data)
        
        # Voice activity detection
        is_speech, is_end_of_utterance = await self.vad.process(audio_data)
        
        if is_speech:
            self.last_speech_time = time.time()
        
        if not is_end_of_utterance:
            return None
        
        # Extract complete utterance
        utterance_audio = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        # STT: Convert speech to text
        stt_start = time.time()
        transcript = await self.stt.transcribe(utterance_audio, self.language)
        stt_latency = (time.time() - stt_start) * 1000
        logger.info(f"STT latency: {stt_latency:.0f}ms")
        
        if not transcript or not transcript.strip():
            return None
        
        # Detect language if needed
        detected_lang = await self.language_detector.detect(transcript)
        if detected_lang and detected_lang != self.language:
            self.language = detected_lang
            logger.info(f"Language switched to: {self.language}")
        
        # Agent: Process and generate response
        agent_start = time.time()
        response_text = await self.agent.process(transcript, self.language)
        agent_latency = (time.time() - agent_start) * 1000
        logger.info(f"Agent latency: {agent_latency:.0f}ms")
        
        # TTS: Convert response to speech
        tts_start = time.time()
        response_audio = await self.tts.synthesize(response_text, self.language)
        tts_latency = (time.time() - tts_start) * 1000
        logger.info(f"TTS latency: {tts_latency:.0f}ms")
        
        # Total latency
        total_latency = (time.time() - start_time) * 1000
        logger.info(f"Total latency: {total_latency:.0f}ms (target: {settings.TOTAL_LATENCY_TARGET}ms)")
        
        return response_audio
    
    async def send_message(self, message_type: str, data: dict):
        """Send JSON message to client"""
        await self.websocket.send_json({
            "type": message_type,
            "session_id": self.session_id,
            **data
        })
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to client"""
        await self.websocket.send_bytes(audio_data)


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for voice communication"""
    await websocket.accept()
    
    session = VoiceSession(session_id, websocket)
    
    logger.info(f"Voice session started: {session_id}")
    
    # Send session initialization
    await session.send_message("session_start", {
        "message": "Welcome to 2Care.ai. How can I help you today?",
        "supported_languages": ["en", "hi", "ta"]
    })
    
    # Generate and send greeting audio
    greeting = "Welcome to 2Care.ai. How can I help you with your appointment today?"
    greeting_audio = await session.tts.synthesize(greeting, "en")
    if greeting_audio:
        await session.send_audio(greeting_audio)
    
    try:
        while session.is_active:
            # Receive data
            message = await websocket.receive()
            
            if message["type"] == "websocket.receive":
                if "bytes" in message:
                    # Audio data
                    audio_data = message["bytes"]
                    response_audio = await session.process_audio(audio_data)
                    
                    if response_audio:
                        await session.send_audio(response_audio)
                
                elif "text" in message:
                    # JSON message
                    data = json.loads(message["text"])
                    
                    if data.get("type") == "language_change":
                        session.language = data.get("language", "en")
                        await session.send_message("language_changed", {
                            "language": session.language
                        })
                    
                    elif data.get("type") == "text_input":
                        # Process text input directly
                        text = data.get("text", "")
                        if text:
                            response = await session.agent.process(text, session.language)
                            await session.send_message("text_response", {
                                "text": response
                            })
                            
                            # Optionally send audio
                            if data.get("with_audio", True):
                                audio = await session.tts.synthesize(response, session.language)
                                if audio:
                                    await session.send_audio(audio)
                    
                    elif data.get("type") == "end_session":
                        session.is_active = False
            
            elif message["type"] == "websocket.disconnect":
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice session error: {e}")
        await session.send_message("error", {"message": str(e)})
    finally:
        logger.info(f"Voice session ended: {session_id}")


@router.websocket("/ws/voice/{session_id}")
async def voice_websocket_with_session(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint with existing session ID"""
    await websocket.accept()
    
    session = VoiceSession(session_id, websocket)
    logger.info(f"Voice session resumed: {session_id}")
    
    # Similar logic as above...
    try:
        while session.is_active:
            message = await websocket.receive()
            
            if message["type"] == "websocket.receive":
                if "bytes" in message:
                    response_audio = await session.process_audio(message["bytes"])
                    if response_audio:
                        await session.send_audio(response_audio)
            
            elif message["type"] == "websocket.disconnect":
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice session error: {e}")
    finally:
        logger.info(f"Voice session ended: {session_id}")
