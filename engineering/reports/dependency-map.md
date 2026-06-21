# Dependency Map — Ethan

> RFC-001 — Carte des dépendances entre composants
> Date : 2026-06-21

---

## 1. Dépendances Inter-Projets

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────►│   Backend    │────►│   Ollama     │
│  (React)     │     │  (FastAPI)   │     │  (LLM local) │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                    ┌───────┴───────┐
                    │   Providers   │
                    │  Ollama/OpenAI│
                    │  /Anthropic   │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────┴─────┐ ┌────┴────┐ ┌──────┴──────┐
       │   Core     │ │ Plugins │ │   Rust      │
       │  LLM/Events│ │ Browser │ │  Workspace  │
       │  Auth/Mem  │ │ Terminal│ │  16 crates  │
       └────────────┘ └─────────┘ └─────────────┘
```

---

## 2. Dépendances Python (pyproject.toml)

### 2.1 Dépendances obligatoires

```
click >=8              → CLI framework
httpx >=0.27           → HTTP client
openai >=1.30          → OpenAI API + embeddings
rich >=13              → Terminal UI
tomlkit >=0.12         → TOML parsing
websockets >=15.0.1    → WebSocket support
datasets >=4.5.0       → Dataset management
ddgs >=9.11.4          → DuckDuckGo search
nvidia-ml-py >=12.560  → GPU metrics
posthog >=3.0          → Telemetry
python-telegram-bot    → Telegram channel
```

### 2.2 Dépendances optionnelles (extras)

| Extra | Dépendances | Usage |
|-------|-------------|-------|
| `server` | fastapi, uvicorn, pydantic | API server |
| `inference-cloud` | anthropic | Anthropic provider |
| `inference-google` | google-genai | Gemini provider |
| `inference-litellm` | litellm | Multi-provider |
| `inference-vllm` | vllm | GPU inference |
| `inference-mlx` | mlx-lm | Apple Silicon |
| `memory-faiss` | faiss-cpu, sentence-transformers | Vector search |
| `memory-colbert` | colbert-ai, torch | Neural search |
| `memory-bm25` | rank-bm25 | Keyword search |
| `memory-pdf` | pdfplumber | PDF parsing |
| `speech` | faster-whisper | Speech-to-text |
| `browser` | playwright | Browser automation |
| `sandbox-wasm` | wasmtime | WASM sandbox |
| `sandbox-docker` | docker | Docker sandbox |
| `scheduler` | croniter | Job scheduling |
| `security-signing` | cryptography | Code signing |
| `channels-*` (15+) | discord, slack, twitter, etc. | Communication |

### 2.3 Dépendances de développement

| Dépendance | Usage |
|------------|-------|
| pytest, pytest-asyncio, pytest-cov | Tests |
| ruff | Linting |
| pre-commit | Git hooks |
| maturin | Rust build |
| respx | HTTP mocking |

---

## 3. Dépendances Frontend (package.json)

### 3.1 Production

```
react 19              → UI framework
react-dom 19          → DOM rendering
react-router 7        → Routing
zustand 5             → State management
@base-ui/react        → UI primitives
tailwindcss 4         → CSS framework
lucide-react          → Icons
recharts              → Charts
react-markdown        → Markdown rendering
katex                 → Math rendering
sonner                → Toast notifications
motion                → Animations
posthog-js            → Analytics
```

### 3.2 Desktop (Tauri)

```
@tauri-apps/api 2         → Tauri core API
@tauri-apps/plugin-shell  → Shell commands
@tauri-apps/plugin-dialog → File dialogs
@tauri-apps/plugin-notification → Notifications
@tauri-apps/plugin-global-shortcut → Keyboard shortcuts
@tauri-apps/plugin-autostart → Auto-start
@tauri-apps/plugin-updater → Auto-update
@tauri-apps/plugin-process → Process management
```

### 3.3 Développement

```
typescript 5.7       → Type checking
vite 6               → Build tool
vitest 3.2           → Testing
@vitejs/plugin-react → React integration
vite-plugin-pwa      → PWA support
```

---

## 4. Dépendances Rust (Cargo.toml)

### 4.1 Workspace (16 crates)

| Crate | Rôle |
|-------|------|
| ethan-core | Core types et traits |
| ethan-engine | Moteur d'inférence |
| ethan-agents | Système d'agents |
| ethan-tools | Outils système |
| ethan-learning | Apprentissage |
| ethan-telemetry | Télémétrie |
| ethan-traces | Tracing distribué |
| ethan-security | Sécurité et chiffrement |
| ethan-mcp | MCP protocol |
| ethan-python | Python FFI (PyO3) |
| ethan-sessions | Gestion de sessions |
| ethan-workflow | Moteur de workflows |
| ethan-skills | Compétences |
| ethan-recipes | Recettes |
| ethan-templates | Templates |
| ethan-a2a | Agent-to-Agent |
| ethan-scheduler | Planification |

### 4.2 Dépendances principales

```
serde / serde_json     → Serialization
tokio                  → Async runtime
reqwest                → HTTP client
rusqlite               → SQLite (bundled)
rig-core 0.31          → LLM framework
pyo3 0.23              → Python bindings
ed25519-dalek          → Signatures
tracing                → Logging
```

---

## 5. Dépendances Docker

### 5.1 Images utilisées

| Image | Tag | Source |
|-------|-----|--------|
| python | 3.12-slim | Docker Hub |
| node | 22-slim | Docker Hub |
| nginx | alpine | Docker Hub |
| postgres | 16-alpine | Docker Hub |
| redis | 7-alpine | Docker Hub |
| chromadb/chroma | latest | Docker Hub |
| qdrant/qdrant | latest | Docker Hub |
| ollama/ollama | latest | Docker Hub |
| traefik | v3.1 | Docker Hub |
| prom/prometheus | latest | Docker Hub |
| grafana/grafana | latest | Docker Hub |

### 5.2 Multi-stage builds

**Backend** (Dockerfile.backend) :
1. `python-builder` — Installation des dépendances
2. `python-runtime` — Image finale légère

**Frontend** (Dockerfile.frontend) :
1. `node-builder` — Build TypeScript
2. `nginx-runtime` — Image Nginx statique

---

## 6. Dépendances de Service

### 6.1 Démarrage

```
traefik (indépendant)
    │
    ├── backend (dépend: ollama)
    │       └── ollama (indépendant)
    │
    └── frontend (dépend: backend)
    
postgres, redis, chromadb, qdrant (indépendants)
prometheus (indépendant)
    └── grafana (dépend: prometheus)
```

### 6.2 Communication

```
Service A ───► jarvis-network ───► Service B
                (bridge)
```

---

## 7. Dépendances de Données

```
Backend
    │
    ├── SQLite (fichier local) ou PostgreSQL (service)
    ├── Redis (cache/sessions)
    ├── ChromaDB (vectorielle dev) ou Qdrant (vectorielle prod)
    └── Ollama (modèles LLM locaux)
```

---

## 8. Risques Identifiés

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Dualité src/ vs core/ | Duplication de code | Haute | Migration planifiée |
| 15+ channels | Complexité maintenance | Haute | Standardisation |
| Dépendances optionnelles nombreuses | Résolution lente | Moyenne | Lock file (uv.lock) |
| Rust workspace large (16 crates) | Build time | Haute | CI caching |
| PyO3 bindings | Version mismatch | Moyenne | CI matrix |