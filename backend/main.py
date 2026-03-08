"""
2Care.ai Voice AI Agent - Main Application
Real-time multilingual voice AI for clinical appointment booking
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.config.settings import settings
from backend.api.routes import appointments, doctors, patients, websocket, campaigns
from backend.models.database import init_db, close_db
from backend.memory.session_memory import SessionMemory
from backend.scheduler.campaign_manager import campaign_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting 2Care.ai Voice AI Agent...")
    await init_db()
    app.state.session_memory = SessionMemory(settings.REDIS_URL)
    await app.state.session_memory.connect()
    await campaign_manager.start()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await campaign_manager.stop()
    await app.state.session_memory.disconnect()
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time multilingual voice AI agent for clinical appointment booking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])
app.include_router(doctors.router, prefix="/api/v1", tags=["doctors"])
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])
app.include_router(campaigns.router, prefix="/api/v1", tags=["campaigns"])
app.include_router(websocket.router, prefix="/api/v1", tags=["voice"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to 2Care.ai Voice AI Agent",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/api/v1/ws/voice"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
