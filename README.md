# ETHAN

**ETHAN** — Cognitive Operating System Runtime.

An event-driven, modular AI runtime: intelligent capabilities (Core / Runtime) exposed through replaceable interfaces (WebUI, CLI).

> **Statut** : 🟡 Active development — ready for local use & experimentation.

---

## Overview

ETHAN is an **independent AI runtime**. It thinks, plans, remembers, uses tools and agents, and reasons over documents (RAG/Knowledge) — and it does this **without** any particular interface.

The WebUI is only one way to talk to ETHAN. The CLI, future Desktop, Voice, or autonomous agents can all use the same core capabilities.

```
      ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌────────┐
      │   WebUI   │  │     CLI    │  │  Desktop │  │ Others │
      │ (Next.js) │  │ (shell)    │  │ (future) │  │ (API)  │
      └──────┬────┘  └─────┬──────┘  └─────┬────┘  └────┬───┘
             │             │               │            │
             └─────────────┼───────────────┼────────────┘
                           │    API & Events
                           ▼
                   ┌────────────────┐
                   │   ETHAN Core  │   ← intelligence
                   │   + Runtime    │   ← orchestration
                   └────────┬───────┘
              ┌─────────────┼─────────────┐
              │             │             │
          ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
          │ Nats  │    │Redis  │    │Postgres│
          │Bus+JS │    │state  │    │persist │
          └───────┘    └───────┘    └───────┘
```

---

## What it does (Core capabilities)

| Capability | Role |
|---|---|
| **LLM providers** | Ollama, OpenAI, Anthropic, Gemini, vLLM, custom — configurable & swappable (`core/llm`) |
| **Models** | Discovered from active providers — unified catalog (`core/llm`) |
| **Agents** | Stateful agents with capabilities, executions & goals (`core/agents`) |
| **Planner** | Task decomposition & goal planning (`core/planner`) |
| **Memory** | Short-term (Redis) + long-term (PostgreSQL) (`core/memory`) |
| **Tools** | Browser, code, terminal, sandbox, MCP servers (`core/tools`) |
| **MCP** | Model Context Protocol server management & client (`core/tools`) |
| **Skills** | Composable agent skills (`core/skills`) |
| **Knowledge / RAG** | Document indexing & retrieval (`core/knowledge`, `core/rag`) |
| **Chat** | Conversational pipeline, streaming, persistence (`core/chat`) |

> Intelligence lives in **Core/Runtime**. Interfaces only present & act on it.

---

## WebUI

The web interface — where ETHAN is revealed, not defined.

- **URL** : `http://localhost:3001`
- **Inspiration UX** : patterns from Open WebUI — Open WebUI is a *reference for interaction*, never a backend fork.
- **Experience** : chat-centric. Sidebar conversation-organized, Agent/Model selectors in header, full-width chat as the center.

### Pages available

| Path | Purpose |
|---|---|
| `/` | Chat (conversation-centric, streaming) |
| `/agents` | List / inspect agents |
| `/models` | List & manage models |
| `/providers` | Connect & configure LLM providers |
| `/skills` | Browse & use composable skills |
| `/knowledge` | Documents & RAG collections |
| `/tools` | Manage tools & MCP servers |
| `/missions` | Task tracking |
| `/settings` | Preferences & configuration |
| `/login` | Authentication |

### Quick start (WebUI only)

```bash
# Terminal 1 — Core API + services
./ethan

# Terminal 2 — WebUI (dev, hot reload)
./ethan webui
```

Open `http://localhost:3001`.

---

## CLI

ETHAN's command-line launcher. All commands are thin wrappers over Docker Compose + Core API.

```bash
./ethan help           # show help
./ethan up             # start Docker services (options: --dev, --observability, --skip-preflight, --skip-pull)
./ethan down           # stop services
./ethan restart        # restart services
./ethan webui          # start WebUI (dev, Next.js hot reload)
./ethan api            # start API gateway (dev)
./ethan cli            # attach to the interactive CLI shell
./ethan logs api       # live logs (option:  )
./ethan status         # service health
./ethan doctor         # full diagnostics
```

---

## Configuration

Environment-driven. Copy the example:

```bash
cp .env.example .env
# edit .env
./ethan     # services
./ethan  # WebUI
```

| Variable | Description |
|---|---|
| `OLLAMA_BASE_URL` | Ollama provider endpoint |
| `OLLAMA_DEFAULT_MODEL` | Default Ollama model |
| `OPENAI_API_KEY` | OpenAI provider key |
| `ANTHROPIC_API_KEY` | Anthropic provider key |
| `GEMINI_API_KEY` | Google Gemini provider key |
| `VLLM_BASE_URL` | vLLM provider endpoint |
| `CUSTOM_OPENAI_BASE_URL` | Custom OpenAI-compatible provider |
| `ETHAN_API_URL` | Backend API URL (WebUI) |

See `.env.example` for the full list. **Never commit secrets.**

---

## Services

| Service | Role | Port |
|---|---|---|
| **NATS JetStream** | Event bus | 4222 / 8222 (monitoring) |
| **Redis 7** | Live state | 6379 |
| **PostgreSQL 16** | Persistent storage | 5432 |
| **API** | FastAPI gateway | 8000 |
| **WebUI** | Next.js frontend | 3001 |
| **Prometheus** | Metrics | 9090 |

Secrets are managed via the dedicated layer (`core/config/secrets.py` — env / Docker secrets / Vault). **No secrets in code, git, logs, or events.**

---

## Project structure

```
core/                 # ETHAN intelligence (providers, agents, memory, tools, rag, …)
runtime/              # orchestration & bootstrap
interfaces/           # interfaces that present ETHAN
  ├── api/            #   FastAPI gateway (thin, calls Core)
  ├── webui/          #   Next.js UI (presentation only)
  ├── cli/            #   interactive shell
  └── channels/       #   messaging integrations
plugins/              #   extensible plugins (browser, memory, terminal, …)
infrastructure/        # infra-as-code (docker, k8s, systemd, vault, tracing, …)
deploy/               # deployment assets (nats, postgres, …)
scripts/              # CLI launcher scripts (cmd-*.sh)
sdk/                  # client SDKs (python, typescript)
tests/                # test suites (core, api, webui, integration, …)
docs/                 # documentation
```

---

## Development

```bash
# Full dev stack
./ethan

# WebUI only (from interfaces/webui)
npm run dev

# Run tests
./ethan                       # all
CI=1 npm test -- --watchAll=false         # WebUI

# Build & check
npm run build
npm run lint
npx tsc --noEmit
```

See [`docs/development/`](docs/development/) for contribution guides.

---

## Roadmap

### Done
- Modular Core / Runtime architecture (event-driven, NATS bus)
- Multiple LLM providers (Ollama, OpenAI, Anthropic, Gemini, vLLM)
- Agents, Planner, Memory (short + long term)
- Tools & MCP server management
- Knowledge / RAG (Qdrant / PostgreSQL backends)
- WebUI (Open WebUI-inspired UX)
- CLI launcher

### In progress
- Native agents UX parity with Open WebUI agent selectors
- Unified model selector (grouping by provider, availability states)
- Chat folders & projects organization (architecture in progress)

### Planned
- Multi-user accounts & permissions
- Desktop interface
- Voice interface
- Cross-interface session sync

---

## Documentation

| Document | Content |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Full architecture |
| [`docs/boot-from-scratch.md`](docs/boot-from-scratch.md) | Installation & boot |
| [`docs/sre-runbook.md`](docs/sre-runbook.md) | Operations runbook |
| [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md) | Security audit |
| [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) | Production readiness |

Technical design decisions: [`docs/adr/`](docs/adr/). User guides: [`docs/user-guide/`](docs/user-guide/).

---

## License

Apache-2.0