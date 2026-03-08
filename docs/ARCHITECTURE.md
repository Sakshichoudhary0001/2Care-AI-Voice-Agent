# System Architecture

## High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Frontend (React)"]
        UI[Voice Chat UI]
        WS_Client[WebSocket Client]
        WebSpeech[Web Speech API]
    end

    subgraph Gateway["API Gateway"]
        FastAPI[FastAPI Server]
        WSEndpoint[WebSocket Endpoint]
        REST[REST API Routes]
    end

    subgraph Voice["Voice Pipeline"]
        VAD[Voice Activity Detection]
        STT[Speech-to-Text<br/>Whisper/Azure]
        LangDetect[Language Detection]
        TTS[Text-to-Speech<br/>Azure Speech]
    end

    subgraph Agent["AI Agent"]
        Orchestrator[Agent Orchestrator]
        Intent[Intent Classifier]
        SlotFiller[Slot Filler]
        ResponseGen[Response Generator]
        Tools[Tool Executor]
    end

    subgraph Memory["Memory System"]
        Session[Session Memory<br/>Redis]
        Persistent[Persistent Memory<br/>PostgreSQL]
    end

    subgraph Services["Backend Services"]
        AppointmentSvc[Appointment Service]
        DoctorSvc[Doctor Service]
        PatientSvc[Patient Service]
        Scheduler[Campaign Scheduler]
    end

    subgraph Data["Data Layer"]
        Redis[(Redis)]
        PostgreSQL[(PostgreSQL)]
    end

    %% Client connections
    UI --> WS_Client
    UI --> WebSpeech
    WS_Client <--> WSEndpoint
    
    %% Gateway routing
    WSEndpoint --> VAD
    REST --> Services
    
    %% Voice pipeline flow
    VAD --> STT
    STT --> LangDetect
    LangDetect --> Orchestrator
    ResponseGen --> TTS
    TTS --> WSEndpoint
    
    %% Agent flow
    Orchestrator --> Intent
    Intent --> SlotFiller
    SlotFiller --> Tools
    Tools --> AppointmentSvc
    Tools --> ResponseGen
    
    %% Memory connections
    Orchestrator <--> Session
    Orchestrator <--> Persistent
    Session <--> Redis
    Persistent <--> PostgreSQL
    
    %% Services to DB
    AppointmentSvc --> PostgreSQL
    DoctorSvc --> PostgreSQL
    PatientSvc --> PostgreSQL
    Scheduler --> PostgreSQL
```

## Real-Time Voice Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant WebSocket
    participant VAD
    participant STT
    participant Agent
    participant TTS
    
    User->>Frontend: Speaks
    Frontend->>WebSocket: Audio Stream
    
    loop Real-time Processing
        WebSocket->>VAD: Audio Chunks
        VAD-->>WebSocket: Speech Activity
    end
    
    VAD->>STT: End of Utterance
    Note over STT: ~80-120ms
    STT->>Agent: Transcript + Language
    
    Note over Agent: ~150-200ms
    Agent->>Agent: Intent Classification
    Agent->>Agent: Slot Filling
    Agent->>Agent: Tool Execution
    Agent->>Agent: Response Generation
    
    Agent->>TTS: Response Text
    Note over TTS: ~80-100ms
    TTS->>WebSocket: Audio Stream
    WebSocket->>Frontend: Audio Response
    Frontend->>User: Plays Audio
    
    Note over User,Frontend: Total: <450ms
```

## Memory Architecture

```mermaid
flowchart LR
    subgraph Session["Session Memory (Redis)"]
        direction TB
        S1[Current Intent]
        S2[Collected Slots]
        S3[Conversation History]
        S4[Turn Count]
    end
    
    subgraph Persistent["Persistent Memory (PostgreSQL)"]
        direction TB
        P1[Patient Profile]
        P2[Appointment History]
        P3[Language Preference]
        P4[Interaction Logs]
    end
    
    Agent[Agent Orchestrator]
    
    Agent <-->|Fast Access<br/>TTL: 30min| Session
    Agent <-->|Long-term Storage| Persistent
```

## Component Responsibilities

### Voice Pipeline
| Component | Function | Latency Target |
|-----------|----------|----------------|
| VAD | Detect speech boundaries | Real-time |
| STT | Convert speech to text | 80-120ms |
| Language Detection | Identify en/hi/ta | 10ms |
| TTS | Convert text to speech | 80-100ms |

### AI Agent
| Component | Function |
|-----------|----------|
| Orchestrator | Coordinates all reasoning |
| Intent Classifier | Identifies user intent |
| Slot Filler | Extracts entities |
| Tool Executor | Calls appointment APIs |
| Response Generator | Creates multilingual responses |

### Memory
| Type | Storage | Purpose | TTL |
|------|---------|---------|-----|
| Session | Redis | Current conversation | 30 min |
| Persistent | PostgreSQL | User history | Permanent |

## Data Flow for Appointment Booking

```mermaid
stateDiagram-v2
    [*] --> Greeting
    Greeting --> IntentDetection: User speaks
    IntentDetection --> SlotCollection: Intent = book
    
    state SlotCollection {
        [*] --> AskDoctor
        AskDoctor --> AskDate: Doctor collected
        AskDate --> AskTime: Date collected
        AskTime --> AskPatient: Time collected
        AskPatient --> [*]: All slots filled
    }
    
    SlotCollection --> Confirmation: Slots complete
    Confirmation --> CheckAvailability
    
    CheckAvailability --> BookAppointment: Available
    CheckAvailability --> SuggestAlternatives: Not available
    
    SuggestAlternatives --> SlotCollection: User selects
    BookAppointment --> Success
    Success --> [*]
```

## Deployment Architecture

```mermaid
flowchart TB
    subgraph Docker["Docker Compose"]
        App[Backend Container<br/>Port 8000]
        Frontend[Frontend Container<br/>Port 3000]
        Postgres[PostgreSQL<br/>Port 5432]
        RedisC[Redis<br/>Port 6379]
    end
    
    Internet((Internet)) --> Frontend
    Frontend --> App
    App --> Postgres
    App --> RedisC
```
