# Architecture Map — Ethan

> RFC-002 — Carte architecturale complète du dépôt
> Date : 2026-06-21

---

## 1. Entry Points

### 1.1 CLI (Principal)

```
jarvis serve          → Démarre le serveur API (FastAPI)
jarvis chat           → Chat interactif en terminal
jarvis ask            → Question unique en CLI
jarvis agent          → Gestion des agents
jarvis memory         → Opérations mémoire
jarvis tool           → Exécution d'outils
jarvis skill          → Gestion des compétences
jarvis workflow       → Workflows
jarvis scheduler      → Jobs planifiés
jarvis config         → Configuration
jarvis channel        → Gestion des channels de communication
jarvis daemon start   → Démarrage en mode daemon
jarvis telemetry      → Télémétrie
jarvis mine           → Mining (Pearl)
jarvis eval           → Évaluations
jarvis doctor         → Diagnostic système
jarvis registry       → Gestion du registry
jarvis vault          → Gestion des secrets
jarvis compose        → Docker Compose helper
jarvis gateway        → API Gateway
jarvis model          → Gestion des modèles
jarvis feedback       → Feedback utilisateur
jarvis host           → Gestion des hôtes
jarvis self-update    → Auto-update
jarvis scan           → Scan de sécurité
jarvis optimize       → Optimisation
jarvis benchmark      → Benchmarks
jarvis connect        → Connexion à des services
jarvis digest         → Résumés quotidiens
jarvis quickstart     → Guide rapide
jarvis init           → Initialisation
jarvis bootstrap      → Bootstrap
jarvis pearl          → Opérations Pearl
jarvis operators      → Opérateurs
jarvis channel(s)     → Gestion des channels
```

**Total : 35+ commandes CLI**

### 1.2 API Server

```
apps/api/  → Interface API publique (FastAPI)
apps/gateway/ → API Gateway (vide)
Docker: backend expose port 8000
Health endpoint: /health
```

### 1.3 Desktop

```
frontend/src-tauri/ → Application desktop Tauri
- Autostart
- Global shortcuts
- Notifications
- Dialog system
- Auto-updater
- Shell integration
```

---

## 2. Python Package Structure

```
src/ethan/ (~300+ fichiers)
│
├── __init__.py           # Version, sentinel
├── cli/                  # CLI (35+ commandes)
│   ├── __init__.py       # Root Click group
│   ├── _bootstrap.py     # Bootstrap
│   ├── serve.py          # API server
│   ├── chat_cmd.py       # Chat
│   ├── agent_cmd.py      # Agent management
│   └── ... (35+ modules)
│
├── core/                 # Core business logic
│   ├── config.py         # Configuration
│   ├── events.py         # Event system
│   ├── registry.py       # Multi-registry (agents, channels, tools, etc.)
│   └── ... 
│
├── agents/               # Agent implementations
│   ├── base.py           # Base agent class
│   ├── research_loop.py  # Research agent
│   ├── hybrid/           # Hybrid orchestration
│   └── claude_code_runner/ # Claude sandbox runner
│
├── server/               # FastAPI server
│
├── channels/             # 15+ communication channels
│   ├── telegram/
│   ├── discord/
│   ├── slack/
│   ├── whatsapp_baileys_bridge/
│   └── ...
│
├── engine/               # LLM Inference engine
│
├── memory/               # Memory backends
│   ├── chromadb.py
│   ├── faiss.py
│   ├── sqlite.py
│   └── ...
│
├── tools/                # Tools (browser, terminal, db, etc.)
│
├── mining/               # Pearl mining system
│   ├── pearl/
│   └── ...
│
├── evals/                # Evaluation framework
│
├── telemetry/            # Telemetry (PostHog)
│
├── traces/               # Distributed tracing
│
├── sessions/             # Session management
│
├── skills/               # Skills system
│
├── templates/            # Templates
│
├── security/             # Security utilities
│
├── mcp/                  # MCP protocol
│
├── speech/               # Speech-to-text
│
├── analytics/            # Analytics
│
├── connectors/           # External connectors
│
├── hardware/             # Hardware detection (GPU, CPU)
│
├── daemon/               # Daemon management
│
├── deploy/               # Deployment helpers
│
└── scheduler/            # Job scheduling
```

---

## 3. API Layer

### 3.1 REST API Endpoints

```
/health                → Health check
/api/chat              → Chat completion
/api/agents/{name}/run → Agent execution
/api/memory/{...}      → Memory operations
/api/tools/{...}       → Tool execution
/api/models            → Model listing
/ws                    → WebSocket endpoint
/docs                  → Swagger UI
/redoc                 → ReDoc
/openapi.json          → OpenAPI spec
```

### 3.2 Server Stack

```
FastAPI
├── Uvicorn (ASGI server)
├── Pydantic (validation)
├── WebSocket support
└── OpenAPI auto-docs
```

---

## 4. Agent System

### 4.1 Architecture

```
BaseAgent
├── ResearchLoopAgent (research_loop.py)
├── ClaudeCodeRunnerAgent
├── HybridAgent (hybrid/)
│   ├── SkillOrchestra
│   └── ...
└── External framework agents
    ├── OpenHands
    └── ...
```

### 4.2 Registry

```
ethan/core/registry.py
├── AgentRegistry
├── EngineRegistry
├── ChannelRegistry
├── ToolRegistry
├── MemoryRegistry
├── ModelRegistry
├── SkillRegistry
├── SpeechRegistry
├── TTSRegistry
├── BenchmarkRegistry
├── CompressionRegistry
├── ConnectorRegistry
├── MinerRegistry
├── RouterPolicyRegistry
└── (15 registries total)
```

### 4.3 Communication Patterns

```
Agent A → EventBus → Agent B
Agent A → EventBus → Multiple subscribers
CLI → Direct method call → Agent
API → REST → Agent
```

---

## 5. Engine/Provider System

### 5.1 Inference Engines

```
EngineRegistry
├── OpenAI engine
├── Anthropic engine
├── Ollama engine
├── Google engine
├── LiteLLM engine
├── vLLM engine
├── MLX engine (Apple Silicon)
└── Gemma engine
```

### 5.2 Model Registry

```
ModelRegistry
├── Model discovery
├── Model configuration
└── Provider mapping
```

---

## 6. Memory System

### 6.1 Backends

```
MemoryRegistry
├── SQLite backend (persistent storage)
├── ChromaDB backend (vector search)
├── FAISS backend (local vector)
├── ColBERT backend (neural search)
├── BM25 backend (keyword search)
└── Hybrid backends
```

### 6.2 Data Flow

```
User → Agent → Memory operation
                      ↓
         ┌─────────────────────┐
         │ MemoryRegistry       │
         │ → Choose backend     │
         │ → Execute operation  │
         │ → Return result      │
         └─────────────────────┘
```

---

## 7. Channel System

### 7.1 Communication Channels

```
ChannelRegistry
├── Telegram
├── Discord
├── Slack
├── Twitter/X
├── WhatsApp (Baileys bridge)
├── Gmail
├── Twilio (SMS)
├── Reddit
├── Mastodon
├── Zulip
├── RocketChat
├── XMPP
├── Twitch
├── Nostr
├── LINE
├── Messenger
└── Viber
```

**Total : 17 channels**

---

## 8. Frontend Architecture

```
frontend/
├── src/
│   ├── components/       # React components
│   ├── pages/            # Pages (Chat, Dashboard, etc.)
│   ├── stores/           # Zustand stores
│   ├── hooks/            # Custom hooks
│   └── lib/              # Utilities
├── src-tauri/            # Tauri desktop
│   └── src/              # Rust backend
├── public/               # Static assets
├── index.html
├── package.json
└── vite.config.ts
```

### 8.1 Tech Stack

```
React 19
├── React Router 7
├── Zustand 5 (state)
├── shadcn/ui + Base UI
├── TailwindCSS 4
├── React Markdown
├── Recharts
├── Sonner (toasts)
├── Motion (animations)
├── KaTeX (math)
└── Lucide React (icons)
```

### 8.2 Desktop Features (Tauri)

```
Tauri 2
├── Autostart
├── Global shortcuts
├── Notifications
├── File dialogs
├── Shell commands
├── Process management
└── Auto-updater