# ETHAN

**ETHAN** is a local-first, extensible AI platform — not a chatbot.

It is a cognitive runtime made of a **Core** (intelligence), **Runtime services** (orchestration & execution) and **replaceable interfaces** (WebUI, CLI, API). ETHAN thinks, plans, remembers, uses tools and agents, and reasons over documents — and it does this **independently of any interface**.

> **Status** : 🟡 Active development — ready for local use & experimentation.

```
                         ETHAN
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
       CORE           RUNTIME SERVICES     INTERFACES
   intelligence         orchestration      WebUI (Next.js)
   LLM providers        kernel             CLI (shell)
   agents · planner     modules            API (FastAPI gateway)
   memory · knowledge   event bus (NATS)   Desktop (planned)
   tools · MCP · RAG    state (Redis/PG)   Voice  (planned)
        │                  │                  │
        └──────────────────┴──────────────────┘
              Core + Runtime = source of truth
```

**The first rule of ETHAN** : a capability belongs to Core or Runtime if it still makes sense when every interface is shut down. Interfaces reveal ETHAN; they never define it.

---

## Architecture

### Core — the brain (`core/`)

All intelligence lives here. The Core owns:

| Capability | Implementation |
|---|---|
| **LLM providers** | Ollama, OpenAI, Anthropic, Gemini, vLLM, custom OpenAI-compatible (`core/llm/providers/`) — configurable & swappable |
| **Models** | Unified catalog discovered from providers (`core/llm`) |
| **Agents** | Stateful agents with capabilities, skills, knowledge, tools & goals (`core/agents`) |
| **Planner** | Task decomposition & goal planning (`core/planner`) |
| **Chat pipeline** | Conversations, streaming, message tree, persistence (`core/chat`) |
| **Memory** | Facts & experiences, short-term (Redis) + long-term (PostgreSQL) (`core/memory`, `core/facts`, `core/state`) |
| **Knowledge** | Document collections & indexing (`core/knowledge`) |
| **RAG** | Contextual retrieval (`core/rag`) |
| **Tools & MCP** | Builtin tools + external MCP servers (`core/tools`) |
| **Skills** | Composable agent skills (`core/skills`) |
| **Kernel** | Event routing & system state — orchestrator only, never reasons (`core/kernel.py`) |
| **Event bus** | NATS JetStream — event-driven, no direct module-to-module calls (`core/bus`, `core/events`) |
| **Security** | Auth (JWT), security gateway, data protection, approval engine, audit store (`core/auth`, `core/security`, `core/approval`, `core/audit`) |

### Runtime services — orchestration & execution

ETHAN has no monolithic `runtime/` folder: the runtime is the set of services composed by Docker Compose and driven by Core code:

| Service (container) | Role |
|---|---|
| `ethan-kernel` | Core Kernel — event routing, system state (`core/kernel.py`) |
| `ethan-modules` | Cognitive modules launcher (`core/modules`) |
| `ethan-api` | FastAPI gateway — thin HTTP surface over Core (`interfaces/api`) |
| `ethan-nats` / `ethan-redis` / `ethan-postgres` | Event bus / live state / persistence |
| `ethan-ui` | WebUI (Next.js build) |
| `ethan-pg_backup` | PostgreSQL backups |

### Interfaces — they reveal, they don't define

Interfaces may render, configure, trigger and supervise. They must never own business logic, providers, agents, memory, RAG or missions. If the WebUI, CLI and Desktop were all stopped, ETHAN would keep running.

- **WebUI** (Next.js, port 3001) — see below.
- **CLI** (`interfaces/cli`) — interactive shell over the same Core capabilities.
- **API** (`interfaces/api`) — FastAPI gateway used by every interface.
- **Desktop** (planned) · **Voice** (planned) · **autonomous agents** (planned).

---
## Memory, Knowledge & RAG — three distinct things

| Concept | What it is | Where |
|---|---|---|
| **Memory** | Persistent information & experiences about the user and past interactions (facts, preferences, outcomes) | `core/memory`, `core/facts`, `core/state` — Redis (live) + PostgreSQL (persistent) |
| **Knowledge** | Documents and sources of truth ingested into collections | `core/knowledge` |
| **RAG** | The retrieval mechanism: given a query, find and inject relevant context | `core/rag` |

**Direction** : ETHAN must progressively favor **verified, validated procedures** over indiscriminately memorizing every attempt — memory should store what worked, not everything that happened.

---

## Agents

Agents are a **Core capability** (`core/agents`): stateful units combining a personality (instructions), a default provider/model, and resolved capabilities (skills, knowledge bases, tools). The chat pipeline resolves the selected agent server-side; interfaces only select and display.

Agents are created and managed via the Core API — the WebUI (`/agents`) and the CLI are two views on the same store.

> **Atreus — PLANNED / FUTURE AGENT ARCHITECTURE.** Atreus is the planned specialized agent of the ETHAN ecosystem (planning & controlled action on top of the Core agent manager). It is **not implemented yet**; only design notes exist in `docs/plans/`.

---

# ETHAN WebUI

The WebUI is the visual interface of ETHAN: a control center, not a second brain.

- **URL** : `http://localhost:3001` (Docker service `ethan-ui`, or `./ethan webui` in dev)
- **Experience** : chat-centric — sidebar (conversations, assistants, navigation), chat header with `[Agent ▼] [Model ▼] [Provider ▼]` selectors, composer (Act / Plan / Send), streaming with real Stop.

The WebUI lets you:

- access conversations (list, pin, rename, history, streaming)
- select agents, models and providers (selections propagated to the Core)
- manage LLM providers (`/providers`)
- browse knowledge & RAG collections (`/knowledge`)
- manage tools & MCP servers (`/tools`)
- inspect skills, missions, memory (`/skills`, `/missions`, `/workspace`)
- configure ETHAN (`/settings` — General, Appearance, Models, Providers, RAG, MCP…)
- administer (Diagnostics on `/health/detailed`, Security, Grafana links)

> Projects & chat folders are **planned** — they require a Core store first (see Roadmap).

The user experience takes inspiration from Open-WebUI's clarity and interaction model, while keeping ETHAN's Core and Runtime as the source of truth. ETHAN WebUI is **not** a fork of Open-WebUI.

### Open-WebUI reference (`examples/open-webui`)

The repository ships a local copy of Open-WebUI under `examples/open-webui`, used **as a reference only** for:

- UX, navigation and interaction patterns
- model / provider / agent selection ergonomics
- chat ergonomics (composer, streaming, message actions)

Open-WebUI is **not** ETHAN's backend. ETHAN does not depend on any Open-WebUI business logic and keeps its own Core, Runtime, Agents, Providers, LLM abstraction, Memory, Knowledge and Tools. Details: [`docs/webui/open-webui-reference.md`](docs/webui/open-webui-reference.md).

---

# Security & ETHAN Constitution

The ETHAN ecosystem evolves toward a **Constitution** of fundamental principles applying to Core, Runtime, Agents, LLMs, Tools, Plugins, MCP, Interfaces and Memory: protection of the user and of data, confidentiality, prevention of unauthorized exfiltration, no bypassing of protections, **separation between reasoning and authorization** (an LLM decision is never an authorization), verification of actions, least privilege, and auditability.

The normative text lives in [`docs/security/ETHAN_CONSTITUTION.md`](docs/security/ETHAN_CONSTITUTION.md), with design documents in [`docs/security/`](docs/security/).

**Implemented today** : JWT authentication & users (`core/auth`), security gateway & data protection module (`core/security`), approval engine (`core/approval`), audit store (`core/audit`), circuit breaker (`core/safety`), capability registry (`core/capabilities`), secrets layer (env / Docker secrets / Vault — never in code, git, logs or events).

**PLANNED SECURITY ARCHITECTURE** : full Policy Engine enforcing the Constitution on every action, complete Capability System for sensitive operations, systematic verification of tool/MCP results. Do not assume these are enforced end-to-end yet.

---

## System capabilities — future direction

Future capabilities include filesystem access, system administration, Docker & service management, and voice (STT/TTS). The goal is **not** to give ETHAN unlimited access:

- **Capabilities** → explicitly granted, never implicit
- **Policies** → applied independently of what the LLM decides
- **Sensitive actions** → auditable, approvable, revocable
- **External data transmission** → must never be implicit (explicit consent, auditable)

---

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ (FastAPI, uvicorn) |
| Frontend | Next.js 15, React 19, Tailwind CSS, zustand, React Query, Playwright |
| CLI | Python interactive shell |
| Event bus | NATS JetStream |
| Live state | Redis 7 |
| Persistence | PostgreSQL 16 (Qdrant / ChromaDB optional for RAG dev) |
| Auth | JWT |
| Infra | Docker + Docker Compose, systemd (watchdog), Prometheus / Grafana / Loki (observability), Vault (secrets, optional) |
| SDK | Python & TypeScript clients (`sdk/`, `proto/ethan`) |

---

## Project structure

```
ETHAN/
├── core/               # ETHAN intelligence (llm, agents, chat, memory, knowledge, rag,
│                       #   tools, skills, planner, kernel, bus, security, …)
├── plugins/            # extensible plugins (browser, terminal, sandbox, memory, builtin)
├── interfaces/
│   ├── api/            #   FastAPI gateway (thin, calls Core)
│   ├── webui/          #   Next.js UI (presentation only)
│   ├── cli/            #   interactive shell
│   ├── channels/       #   messaging integrations
│   ├── desktop/        #   desktop app (early)
│   └── shell/
├── sdk/                # client SDKs (python, typescript) + proto/ethan
├── infrastructure/     # infra-as-code (docker, systemd, grafana, …)
├── deploy/             # deployment assets (nats, postgres, Dockerfiles)
├── scripts/            # launcher scripts (cmd-*.sh)
├── install/            # system-wide installer
├── tests/              # test suites (core, api, cli, integration, …)
├── docs/               # documentation (architecture, security, webui, user-guide, adr)
├── examples/           # open-webui — local UX reference, not part of the product
└── cookbook/ design/ engineering/ images/ proto/
```

---

## Quick start

Prerequisites: Docker + Docker Compose, Python 3.11+, Node 18+. All commands go through the official launcher:

```bash
# 1. Install dependencies & configuration
./ethan install

# 2. Check prerequisites (ports, RAM, disk, services)
./ethan preflight

# 3. Start the full stack (Core services + API + WebUI)
./ethan up

# 4. Check service health
./ethan status

# 5. Open the WebUI
#    http://localhost:3001

# WebUI in dev mode (hot reload, still on :3001)
./ethan webui

# Interactive CLI
./ethan cli

# Stop / restart / logs / diagnostics
./ethan down
./ethan restart
./ethan logs api
./ethan doctor
```

Full from-scratch guide: [`docs/boot-from-scratch.md`](docs/boot-from-scratch.md).

### Configuration

Copy `.env.example` → `.env` and set at minimum `JWT_SECRET` and `POSTGRES_PASSWORD`. Provider keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are optional — Ollama works with no key. **Never commit secrets.**

---

# Project Status

## Implemented

- Event-driven Core / Runtime architecture (NATS bus, kernel orchestrator-only)
- Multiple LLM providers (Ollama, OpenAI, Anthropic, Gemini, vLLM, OpenAI-compatible)
- Agents, Planner, Chat pipeline (streaming, message tree, persistence)
- Memory (short + long term), Knowledge collections, RAG
- Tools & MCP server management, Skills
- WebUI: chat-centric, agent/model/provider selection, settings, administration
- CLI launcher (`./ethan …`) & interactive CLI
- JWT authentication, security gateway, approval engine, audit store
- Observability (Prometheus, Grafana, Loki) & SRE scripts (preflight, doctor, watchdog)

## In Progress

- WebUI refinement (Open-WebUI-inspired ergonomics — see `docs/webui/`)
- Security architecture: policy enforcement, capability system extension
- Memory validation (privileging verified procedures)

## Planned

- **Atreus** — future specialized agent architecture
- Policy Engine enforcing the ETHAN Constitution end-to-end
- Projects & chat folders (requires a Core store first)
- Desktop interface, Voice interaction (STT/TTS)
- Local workspace / filesystem access under explicit capability grants
- Multi-user accounts & permissions, cross-interface session sync

---

## Roadmap

| Item | Status |
|---|---|
| WebUI refinement (Open-WebUI reference ergonomics) | 🟡 In Progress |
| Agent architecture (capabilities, skills resolution) | ✅ Implemented |
| Atreus (specialized agent) | ⏳ Planned |
| Security Constitution | 🟡 Normative text v1.0 — enforcement In Progress |
| Policy Engine | ⏳ Planned (foundations in `core/security`) |
| Capability System | 🟡 In Progress (registry in `core/capabilities`) |
| Projects & chat folders | ⏳ Planned |
| Local workspace access | ⏳ Planned (explicit capabilities + policies) |
| Memory validation (verified procedures) | 🟡 In Progress |
| Desktop interface | ⏳ Planned |
| Voice interaction (STT/TTS) | ⏳ Planned |

---

## Documentation

| Document | Content |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Full architecture |
| [`docs/architecture/README_ARCHITECTURE_REFERENCE.md`](docs/architecture/README_ARCHITECTURE_REFERENCE.md) | Architecture reference (Core / Runtime / Interfaces) |
| [`docs/boot-from-scratch.md`](docs/boot-from-scratch.md) | Installation & boot from scratch |
| [`docs/sre-runbook.md`](docs/sre-runbook.md) | Operations runbook |
| [`docs/security/`](docs/security/) | ETHAN Constitution & security design docs |
| [`docs/webui/`](docs/webui/) | WebUI & Open-WebUI reference migration docs |
| [`docs/user-guide/`](docs/user-guide/) | User guides |
| [`docs/adr/`](docs/adr/) | Architecture decision records |

Design decisions: [`docs/adr/`](docs/adr/).

---

## License

Apache-2.0
