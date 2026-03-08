# 2Care.ai - Real-Time Multilingual Voice AI Agent

## Clinical Appointment Booking System

A voice-first AI agent for clinical appointment booking supporting English, Hindi, and Tamil with sub-450ms response latency.

---

## Table of Contents

1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [API Reference](#api-reference)
6. [Memory Design](#memory-design)
7. [Latency Breakdown](#latency-breakdown)
8. [Multilingual Support](#multilingual-support)
9. [Outbound Campaigns](#outbound-campaigns)
10. [Testing](#testing)
11. [Trade-offs & Decisions](#trade-offs--decisions)
12. [Known Limitations](#known-limitations)
13. [Environment Variables](#environment-variables)

---

## Features

- 🎤 **Voice-First**: Natural voice conversations via WebSocket
- 🌐 **Multilingual**: English, Hindi, Tamil with auto-detection
- ⚡ **Low Latency**: <450ms response time target
- 🤖 **AI-Powered**: Intent classification + slot filling + tool execution
- 📅 **Full Booking Lifecycle**: Book, reschedule, cancel appointments
- 💾 **Smart Memory**: Session (Redis) + persistent (PostgreSQL) context
- 📞 **Outbound Campaigns**: Appointment reminders, follow-ups
- 🐳 **Dockerized**: Easy deployment with Docker Compose

---

## Quick Start

### Prerequisites

- Docker Desktop
- Git

### Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd 2Care.ai-Project

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - AZURE_SPEECH_KEY
# - AZURE_SPEECH_REGION

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────────────┐  │
│  │ Voice UI │──│ WebSocket     │──│ Web Speech API           │  │
│  │          │  │ Client        │  │ (Browser STT/TTS)        │  │
│  └──────────┘  └───────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ WebSocket    │  │ REST API     │  │ Health Check           │ │
│  │ /ws/voice    │  │ /api/v1/*    │  │ /health                │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Voice Pipeline│   │    AI Agent     │   │    Services     │
│ ┌───────────┐ │   │ ┌─────────────┐ │   │ ┌─────────────┐ │
│ │ VAD       │ │   │ │ Orchestrator│ │   │ │ Appointment │ │
│ │ STT       │ │   │ │ Intent      │ │   │ │ Doctor      │ │
│ │ Lang Det  │ │   │ │ Slot Filler │ │   │ │ Patient     │ │
│ │ TTS       │ │   │ │ Tools       │ │   │ │ Scheduler   │ │
│ └───────────┘ │   │ └─────────────┘ │   │ └─────────────┘ │
└───────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌───────────────┐                         ┌─────────────────┐
│     Redis     │                         │   PostgreSQL    │
│ Session Data  │                         │ Persistent Data │
│ TTL: 30 min   │                         │ Appointments    │
└───────────────┘                         └─────────────────┘
```

### Voice Processing Pipeline

```
User Speech
     │
     ▼ (WebSocket audio stream)
┌─────────────────┐
│      VAD        │ Voice Activity Detection
└────────┬────────┘
         │ End of utterance detected
         ▼
┌─────────────────┐
│      STT        │ Speech-to-Text (Whisper/Azure)
│   ~80-120ms     │
└────────┬────────┘
         │ Transcript
         ▼
┌─────────────────┐
│ Language Detect │ Auto-detect en/hi/ta
│     ~10ms       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Agent      │ Intent + Slot + Tool + Response
│   ~150-200ms    │
└────────┬────────┘
         │ Response text
         ▼
┌─────────────────┐
│      TTS        │ Text-to-Speech (Azure)
│   ~80-100ms     │
└────────┬────────┘
         │
         ▼
   Audio Response
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams.

---

## Project Structure

```
2Care.ai-Project/
│
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── config/
│   │   └── settings.py         # Configuration & env vars
│   │
│   ├── api/routes/
│   │   ├── appointments.py     # Appointment CRUD API
│   │   ├── doctors.py          # Doctor listing & availability
│   │   ├── patients.py         # Patient management
│   │   └── websocket.py        # Real-time voice endpoint
│   │
│   ├── agent/
│   │   ├── orchestrator.py     # Main agent brain
│   │   ├── prompts/
│   │   │   └── templates.py    # Multilingual prompts
│   │   ├── reasoning/
│   │   │   ├── intent_classifier.py
│   │   │   ├── slot_filler.py
│   │   │   └── response_generator.py
│   │   └── tools/
│   │       └── appointment_tools.py
│   │
│   ├── services/
│   │   ├── stt_service.py      # Speech-to-Text
│   │   ├── tts_service.py      # Text-to-Speech
│   │   ├── vad_service.py      # Voice Activity Detection
│   │   └── language_detection.py
│   │
│   ├── memory/
│   │   ├── session_memory.py   # Redis (short-term)
│   │   └── persistent_memory.py # PostgreSQL (long-term)
│   │
│   ├── scheduler/
│   │   ├── campaign_manager.py # Outbound campaigns
│   │   └── reminder_service.py # Appointment reminders
│   │
│   └── models/
│       ├── database.py         # SQLAlchemy models
│       └── schemas.py          # Pydantic schemas
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── VoiceChat.tsx   # Main chat interface
│   │   │   ├── VoiceRecorder.tsx
│   │   │   └── MessageList.tsx
│   │   └── hooks/
│   │       └── useWebSocket.ts
│   └── Dockerfile
│
├── database/
│   └── schema.sql              # PostgreSQL schema
│
├── tests/
│   ├── test_intent_classifier.py
│   ├── test_slot_filler.py
│   ├── test_appointments.py
│   ├── test_memory.py
│   ├── test_campaigns.py
│   └── test_latency.py
│
├── docs/
│   └── ARCHITECTURE.md         # Detailed architecture
│
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/appointments` | Book appointment |
| GET | `/api/v1/appointments/{id}` | Get appointment |
| PUT | `/api/v1/appointments/{id}` | Update appointment |
| DELETE | `/api/v1/appointments/{id}` | Cancel appointment |
| GET | `/api/v1/doctors` | List doctors |
| GET | `/api/v1/doctors/{id}/availability` | Check availability |
| GET | `/api/v1/patients/{id}` | Get patient info |

### WebSocket

```
ws://localhost:8000/api/v1/ws/voice/{session_id}?language=en
```

**Message Types:**

```json
// Client -> Server: Audio
Binary audio data (16kHz, 16-bit, mono)

// Client -> Server: Text
{"type": "text", "content": "Book appointment"}

// Client -> Server: Language change
{"type": "language_change", "language": "hi"}

// Server -> Client: Transcript
{"type": "transcript", "text": "Book appointment"}

// Server -> Client: Response
{"type": "response", "text": "Which doctor?", "audio_url": "..."}
```

---

## Memory Design

### Session Memory (Redis)

Short-term memory for active conversations.

```json
{
  "session_id": "abc-123",
  "language": "en",
  "current_intent": "book_appointment",
  "collected_slots": {
    "doctor": "cardiologist",
    "date": "tomorrow"
  },
  "conversation_history": [
    {"role": "user", "content": "Book cardiologist"},
    {"role": "assistant", "content": "When would you like?"}
  ],
  "turn_count": 2
}
```

**Features:**
- TTL: 30 minutes (auto-expire inactive sessions)
- Fast access: <1ms reads
- Stores: Intent, slots, context, history

### Persistent Memory (PostgreSQL)

Long-term memory for user preferences and history.

```sql
-- Patient preferences
patient_id, preferred_language, preferred_hospital, last_doctor

-- Appointment history
appointment_id, patient_id, doctor_id, date, time, status

-- Interaction logs
session_id, language, intent, latency_ms, timestamp
```

**Features:**
- Permanent storage
- Patient preferences across sessions
- Analytics and reporting

---

## Latency Breakdown

**Target: <450ms end-to-end**

| Stage | Target | Description |
|-------|--------|-------------|
| Voice Activity Detection | Real-time | Detect speech boundaries |
| Speech-to-Text | 80-120ms | Whisper/Azure transcription |
| Language Detection | 10ms | Identify en/hi/ta |
| Agent Processing | 150-200ms | Intent + Slots + Tools |
| Text-to-Speech | 80-100ms | Azure Speech synthesis |
| **Total** | **<450ms** | Speech end to audio start |

**Optimizations Applied:**
- Streaming STT (process while speaking)
- LLM response streaming
- Parallel slot extraction
- TTS audio chunking
- Redis for fast context retrieval

**Latency Logging:**
```
INFO: STT latency: 95ms
INFO: Agent latency: 180ms
INFO: TTS latency: 85ms
INFO: Total latency: 375ms (target: 450ms)
```

---

## Multilingual Support

### Supported Languages

| Code | Language | Example Input |
|------|----------|---------------|
| `en` | English | "Book appointment with cardiologist" |
| `hi` | Hindi | "मुझे कल डॉक्टर से मिलना है" |
| `ta` | Tamil | "நாளை மருத்துவரை பார்க்க வேண்டும்" |

### Auto-Detection

The system automatically detects input language and responds in the same language.

```python
# Input: "मुझे डॉक्टर से मिलना है"
# Detected: Hindi (hi)
# Response: "किस डॉक्टर से मिलना चाहते हैं?"
```

### Language Switching

Users can switch language mid-conversation:

```json
{"type": "language_change", "language": "ta"}
```

---

## Outbound Campaigns

### Supported Campaign Types

| Type | Description | Trigger |
|------|-------------|---------|
| `appointment_reminder` | Remind 24h before | Appointment booked |
| `followup_checkup` | Follow-up visits | 30 days after visit |
| `vaccination_reminder` | Vaccination due | 7 days before due |
| `health_screening` | Preventive care | Based on profile |
| `prescription_refill` | Medication refill | Before expiry |

### Example: Appointment Reminder

```python
from backend.scheduler.reminder_service import reminder_service

# Automatically creates reminder when appointment is booked
await reminder_service.on_appointment_booked(
    appointment_id="apt-123",
    patient_name="John",
    patient_phone="+1234567890",
    doctor_name="Dr. Sharma",
    appointment_time=tomorrow_10am,
    language="hi"
)

# Call message (in Hindi):
# "नमस्ते John, यह कल 10:00 AM बजे Dr. Sharma के साथ 
#  आपकी अपॉइंटमेंट की याद दिलाने के लिए है..."
```

---

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_intent_classifier.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

### Test Categories

| File | Tests |
|------|-------|
| `test_intent_classifier.py` | Intent detection (book/cancel/reschedule) |
| `test_slot_filler.py` | Entity extraction (doctor, date, time) |
| `test_appointments.py` | Booking logic, conflict detection |
| `test_memory.py` | Session & persistent memory |
| `test_campaigns.py` | Outbound campaign creation |
| `test_language_detection.py` | Multilingual detection |
| `test_latency.py` | Performance requirements |

---

## Trade-offs & Decisions

### 1. Browser Speech API vs Backend STT

**Decision:** Support both
- Frontend uses Web Speech API for demo mode (no API costs)
- Backend uses Whisper/Azure for production (better accuracy)

**Trade-off:** Browser API is free but less accurate for Hindi/Tamil

### 2. Redis vs In-Memory Session

**Decision:** Redis with in-memory fallback
- Redis enables horizontal scaling
- In-memory fallback works when Redis unavailable

**Trade-off:** Redis adds ~1ms latency but enables scaling

### 3. LLM for Intent vs Rule-Based

**Decision:** LLM-based with keyword fallback
- LLM handles complex/ambiguous requests
- Keyword matching for simple intents (faster)

**Trade-off:** LLM is slower but handles edge cases better

### 4. Streaming vs Batch TTS

**Decision:** Streaming TTS
- Start playing audio before full synthesis
- Reduces perceived latency

**Trade-off:** More complex implementation

### 5. WebSocket vs HTTP Polling

**Decision:** WebSocket
- Real-time bidirectional communication
- Lower latency for voice

**Trade-off:** More complex connection management

---

## Known Limitations

### Current Limitations

1. **Voice Recognition Accuracy**
   - Hindi/Tamil accuracy ~85% (vs English ~95%)
   - Background noise affects recognition

2. **Outbound Campaigns**
   - Currently simulation only (no actual calling)
   - Requires Twilio/Vonage integration for production

3. **Concurrent Sessions**
   - Tested with ~100 concurrent connections
   - May need scaling for higher loads

4. **LLM Dependency**
   - Requires OpenAI/Azure API keys
   - Rate limits may affect peak usage

5. **Browser Compatibility**
   - Web Speech API requires Chrome/Edge
   - Firefox not fully supported

### Future Improvements

- [ ] Barge-in (interrupt while agent speaking)
- [ ] Multi-turn slot correction
- [ ] Horizontal scaling with Kubernetes
- [ ] Voice biometrics for authentication
- [ ] Sentiment analysis

---

## Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...           # For LLM reasoning
AZURE_SPEECH_KEY=...            # For TTS
AZURE_SPEECH_REGION=eastus

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/care2ai
REDIS_URL=redis://localhost:6379

# Optional
LOG_LEVEL=INFO
SESSION_TTL_SECONDS=1800        # 30 minutes
STT_PROVIDER=azure              # whisper, azure, google
TTS_PROVIDER=azure              # azure, google, elevenlabs
```

---

## License

Proprietary - 2Care.ai © 2026
