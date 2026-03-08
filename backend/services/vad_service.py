"""
Voice Activity Detection (VAD) Service
Detects speech segments and end-of-utterance in audio streams
"""

import asyncio
import logging
import numpy as np
from typing import Tuple, List, Optional
from collections import deque

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class VADService:
    """
    Voice Activity Detection service.
    Determines when speech starts, ends, and identifies end-of-utterance.
    
    Uses energy-based detection with adaptive thresholds.
    Can be enhanced with webrtcvad or Silero VAD for better accuracy.
    """
    
    def __init__(
        self,
        sample_rate: int = None,
        frame_duration_ms: int = 30,
        silence_threshold: float = None,
        min_speech_duration: float = None,
        max_silence_duration: float = 0.7
    ):
        self.sample_rate = sample_rate or settings.AUDIO_SAMPLE_RATE
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(self.sample_rate * frame_duration_ms / 1000)
        
        self.silence_threshold = silence_threshold or settings.VAD_SILENCE_THRESHOLD
        self.min_speech_duration = min_speech_duration or settings.VAD_MIN_SPEECH_DURATION
        self.max_silence_duration = max_silence_duration
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = 0
        self.silence_start_time = 0
        self.total_speech_duration = 0
        
        # Energy history for adaptive threshold
        self.energy_history = deque(maxlen=100)
        self.adaptive_threshold = self.silence_threshold
        
        # Audio buffer for accumulating speech
        self.speech_buffer = bytearray()
        
    async def process(self, audio_chunk: bytes) -> Tuple[bool, bool]:
        """
        Process an audio chunk and detect voice activity.
        
        Args:
            audio_chunk: Raw audio bytes (16-bit PCM)
            
        Returns:
            Tuple of (is_speech, is_end_of_utterance)
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
        
        # Normalize
        if audio_array.max() > 0:
            audio_array = audio_array / 32768.0
        
        # Calculate frame energy (RMS)
        energy = np.sqrt(np.mean(audio_array ** 2))
        
        # Update energy history
        self.energy_history.append(energy)
        
        # Update adaptive threshold
        if len(self.energy_history) > 20:
            noise_floor = np.percentile(list(self.energy_history), 10)
            self.adaptive_threshold = max(
                self.silence_threshold,
                noise_floor * 2  # Threshold at 2x noise floor
            )
        
        # Detect speech
        is_speech = energy > self.adaptive_threshold
        is_end_of_utterance = False
        
        current_time = len(self.speech_buffer) / (self.sample_rate * 2)  # 2 bytes per sample
        
        if is_speech:
            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.speech_start_time = current_time
                self.silence_start_time = 0
                logger.debug("Speech started")
            
            # Add to buffer
            self.speech_buffer.extend(audio_chunk)
            self.total_speech_duration = current_time - self.speech_start_time
            
        else:
            if self.is_speaking:
                # Silence during speech - might be end of utterance
                if self.silence_start_time == 0:
                    self.silence_start_time = current_time
                
                silence_duration = current_time - self.silence_start_time
                
                # Add to buffer even during short silences
                self.speech_buffer.extend(audio_chunk)
                
                # Check if silence is long enough to indicate end of utterance
                if silence_duration >= self.max_silence_duration:
                    # Check minimum speech duration
                    if self.total_speech_duration >= self.min_speech_duration:
                        is_end_of_utterance = True
                        logger.debug(f"End of utterance detected (speech: {self.total_speech_duration:.2f}s, silence: {silence_duration:.2f}s)")
                    
                    # Reset state
                    self.is_speaking = False
                    self.speech_start_time = 0
                    self.silence_start_time = 0
                    self.total_speech_duration = 0
        
        return is_speech, is_end_of_utterance
    
    def get_speech_buffer(self) -> bytes:
        """Get accumulated speech audio and clear buffer"""
        audio = bytes(self.speech_buffer)
        self.speech_buffer.clear()
        return audio
    
    def reset(self):
        """Reset VAD state"""
        self.is_speaking = False
        self.speech_start_time = 0
        self.silence_start_time = 0
        self.total_speech_duration = 0
        self.speech_buffer.clear()
        self.energy_history.clear()
    
    async def process_stream(self, audio_stream) -> List[bytes]:
        """
        Process an audio stream and yield complete utterances.
        
        Args:
            audio_stream: Async iterator of audio chunks
            
        Yields:
            Complete speech utterances
        """
        utterances = []
        
        async for chunk in audio_stream:
            is_speech, is_end_of_utterance = await self.process(chunk)
            
            if is_end_of_utterance:
                utterance = self.get_speech_buffer()
                if utterance:
                    utterances.append(utterance)
        
        # Handle any remaining audio
        if self.speech_buffer and self.total_speech_duration >= self.min_speech_duration:
            utterances.append(self.get_speech_buffer())
        
        return utterances


class SileroVAD:
    """
    Silero VAD wrapper for more accurate voice activity detection.
    Uses a pre-trained neural network model.
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Silero VAD model"""
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            self.model = model
            self.get_speech_timestamps = utils[0]
            logger.info("Silero VAD model loaded")
        except Exception as e:
            logger.warning(f"Could not load Silero VAD: {e}")
            self.model = None
    
    async def detect_speech(self, audio: np.ndarray) -> List[dict]:
        """
        Detect speech segments in audio.
        
        Returns:
            List of {'start': ms, 'end': ms} dictionaries
        """
        if self.model is None:
            return []
        
        import torch
        
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).float()
        
        # Get speech timestamps
        timestamps = self.get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=self.sample_rate,
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100
        )
        
        return timestamps
