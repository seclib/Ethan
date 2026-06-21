# Runtime Flow — Ethan

> RFC-002 — Analyse du comportement runtime
> Date : 2026-06-21

---

## 1. Processus de Démarrage

### 1.1 CLI Startup

```
Terminal → jarvis serve
    │
    ├── 1. Click CLI group initialization
    │       ├── Version check
    │       └── Environment detection
    │
    ├── 2. Configuration loading
    │       ├── Env vars (.env file)
    │       ├── config.toml
    │       └── CLI arguments
    │
    ├── 3. Registry initialization
    │       ├── AgentRegistry
    │       ├── EngineRegistry
    │       ├── ChannelRegistry
    │       ├── MemoryRegistry
    │       ├── ToolRegistry
    │       └── ... (15 registries total)
    │
    ├── 4. Hardware detection
    │       ├── GPU (NVIDIA, AMD)
    │       ├── Apple Silicon
    │       └── CPU capabilities
    │
    ├── 5. Engine initialization
    │       ├── Default engine (configurable)
    │       ├── Model loading (optional)
    │       └── Provider connection
    │
    └── 6. Server startup (uvicorn)
            ├── FastAPI app
            ├── WebSocket handler
            ├── Health endpoint
            └── OpenAPI docs
```

### 1.2 Docker Container Startup

```
Docker → docker compose up
    │
    ├── 1. Network creation (jarvis-network)
    │
    ├── 2. Volume mounting
    │       ├── configs/
    │       ├── memory/
    │       ├── logs/
    │       ├── models/
    │       └── uploads/
    │
    ├── 3. Service dependency resolution
    │       ├── ollama (healthcheck: ollama list)
    │       └── backend (waits for ollama healthy)
    │
    ├── 4. Healthcheck loops
    │       └── Each service pings its health endpoint
    │
    └── 5. Traefik routing activation
            └── / → frontend /api → backend
```

---

## 2. Request Flow

### 2.1 API Request Flow

```
Client (HTTP)
    │
    ▼
Traefik (80/443)
    │
    ├── Path: /api/* → backend:8000
    ├── Path: /*     → frontend:80
    └── Path: /ws    → backend:8000 (WebSocket)
            │
            ▼
    FastAPI Server
    │
    ├── 1. Middleware stack
    │       ├── CORS middleware
    │       ├── Auth middleware (JWT/API Key)
    │       ├── Rate limiting (à venir)
    │       ├── Request logging
    │       └── Metrics (Prometheus)
    │
    ├── 2. Route matching
    │       ├── /health → health handler
    │       ├── /api/chat → chat handler
    │       ├── /api/agents → agent handler
    │       └── ...
    │
    ├── 3. Business logic
    │       ├── Chat → LLM provider → Response
    │       ├── Agent → AgentRegistry → Execute
    │       ├── Memory → MemoryRegistry → Store/Search
    │       └── Tool → ToolRegistry → Execute
    │
    └── 4. Response
            ├── JSON response
            ├── Streaming (SSE/WebSocket)
            └── Error handling
```

### 2.2 Chat Flow

```
User: "Hello"
    │
    ├── 1. Message received
    │       ├── Session lookup
    │       └── Context loading
    │
    ├── 2. Engine selection
    │       ├── Default engine (ollama/openai/anthropic)
    │       └── Model selection
    │
    ├── 3. LLM inference
    │       ├── Prompt construction
    │       ├── Provider API call
    │       └── Streaming (optional)
    │
    ├── 4. Memory update
    │       ├── Short-term (Redis/SQLite)
    │       └── Long-term (ChromaDB/Qdrant)
    │
    └── 5. Response
            ├── Text response
            ├── Tool calls (if any)
            └── Follow-up actions
```

### 2.3 Agent Execution Flow

```
User: "Research X"
    │
    ├── 1. Agent selection
    │       ├── Planner agent
    │       │   └── Plan task decomposition
    │       ├── Research agent
    │       │   └── Execute research steps
    │       └── Memory agent
    │           └── Store results
    │
    ├── 2. Event Bus communication
    │       ├── Event: task:plan → PlannerAgent
    │       ├── Event: research:query → ResearchAgent
    │       └── Event: memory:store → MemoryAgent
    │
    └── 3. Result aggregation
            ├── Collect sub-results
            ├── Synthesize response
            └── Return to user
```

---

## 3. Data Flow Patterns

### 3.1 Synchronous Flow

```
Client → API → Registry.resolve() → Service → Response
                ↓
            Direct method call
```

### 3.2 Asynchronous Flow (Event Bus)

```
Component A → EventBus.publish() → Event
                ↓
        ┌───────────────────┐
        │ Subscriber list   │
        │ (type: event_type)│
        └───────────────────┘
                ↓
    ┌───────────┴───────────┐
    ▼                       ▼
Handler 1              Handler 2
    │                       │
    ▼                       ▼
Component B           Component C
```

### 3.3 Streaming Flow

```
Client → POST /api/chat (stream=true)
    │
    ├── FastAPI → LLM provider
    │       └── OpenAI/Anthropic streaming API
    │
    └── Response (SSE)
            ├── data: {"token": "Hello"}
            ├── data: {"token": " world"}
            └── data: {"done": true}
```

---

## 4. Configuration Flow

### 4.1 Configuration Priority (high to low)

```
1. CLI arguments ─── jarvis serve --port 9000
2. Environment vars ── OPENJARVIS_PORT=9000
3. .env file ──────── OPENJARVIS_PORT=9000
4. config.toml ────── [server] port = 8000
5. Default values ─── port = 8000
```

### 4.2 Configuration Sources

```
Source              Format      Location
─────────────────────────────────────────────────
.env file           KEY=VALUE   .env (root)
config.toml         TOML        configs/ethan/config.toml
CLI arguments       --flag      Runtime
Environment vars    KEY=VALUE   System
Prompts             Files       configs/ethan/prompts/
```

---

## 5. Error Handling

### 5.1 Error Types

```
ErrorType           Source          Handling
─────────────────────────────────────────────────
ProviderError       LLM API         Retry → Fallback → Error message
ConfigError         Config loading  Default values → Warning
MemoryError         DB/Vector       Fallback to SQLite
AuthError           JWT/API Key     401 → Login prompt
ToolError           Plugin exec     Error message → Continue
RateLimitError      API limits      Wait → Retry
```

### 5.2 Error Propagation

```
LLM Provider Error
    │
    ├── 1. Retry (3 attempts)
    ├── 2. Fallback to next provider
    └── 3. Return error to client
```

---

## 6. Monitoring & Observability

### 6.1 Metrics (Prometheus)

```
Endpoint: /metrics (port 9090)
Collection: every 15s

Metrics:
├── ethan_requests_total
├── ethan_request_duration_seconds
├── ethan_active_agents
├── ethan_active_sessions
├── ethan_errors_total
└── up (service health)
```

### 6.2 Telemetry (PostHog)

```
PostHog (optional)
├── Usage statistics
├── Feature adoption
└── Error reporting
```

### 6.3 Logging

```
Format: JSON structured logs
Levels: debug, info, warning, error
Output: stdout + file (/var/log/ethan/)
Channels: json-file driver (Docker)
```

---

## 7. Threading & Concurrency

### 7.1 Async Runtime

```
Python asyncio (event loop)
├── FastAPI async handlers
├── Async LLM clients (httpx)
├── Async database operations
└── WebSocket connections
```

### 7.2 Concurrency Model

```
Requests     → asyncio tasks (concurrent)
LLM calls    → HTTP(S) (non-blocking)
DB operations → async drivers (aiosqlite)
File I/O     → ThreadPoolExecutor
WebSocket    → asyncio streams
```

---

## 8. State Management

### 8.1 Session State

```
Session (UUID key)
├── Conversation history
├── Context (recent messages)
├── Agent state
└── Preferences

Storage: Redis (memory) / SQLite (persistence)
TTL: 1 hour (default, configurable)
```

### 8.2 Registry State (Singletons)

```
Registries (global instances)
├── AgentRegistry (agents: dict[name, Agent])
├── EngineRegistry (engines: dict[name, Engine])
├── MemoryRegistry (backends: dict[name, Backend])
└── EventBus (handlers: dict[type, Handler[]])

Lifecycle: Created on init, cleared on shutdown
Thread safety: asyncio.Lock()