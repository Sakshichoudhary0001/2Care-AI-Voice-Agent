"""
Application Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "2Care.ai Voice Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://care2ai:care2ai_secret@localhost:5432/care2ai_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_TTL_SECONDS: int = 1800  # 30 minutes
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    
    # Azure Speech Services
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "eastus"
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Latency Targets (ms)
    STT_LATENCY_TARGET: int = 120
    LLM_LATENCY_TARGET: int = 200
    TTS_LATENCY_TARGET: int = 100
    TOTAL_LATENCY_TARGET: int = 450
    
    # Voice Settings
    VAD_SILENCE_THRESHOLD: float = 0.5
    VAD_MIN_SPEECH_DURATION: float = 0.25
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    
    # Security
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
