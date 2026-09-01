# ETHAN — Architecture Reference

> Companion of the root `README.md`. This document describes the architecture
> **as it actually exists in the code** — every element below is verifiable in
> the repository, or explicitly marked Planned.

## 1. The three layers

### Core (`core/`) — intelligence

Owns every smart capability. Key modules (all present in the tree):

- `core/llm` — provider abstraction (Ollama, OpenAI, Anthropic, Gemini, vLLM,
  OpenAI-compatible) + unified model catalog.
- `core/agents` — agent manager: stateful agents, capabilities, executions.
- `core/chat` — chat pipeline: completion, streaming, agent resolution,
  skill/knowledge/tool merging.
- `core/planner` — task decomposition & goals.
- `core/memory`, `core/facts`, `core/state` — memory stores (Redis live /
  PostgreSQL persistent via `CompositeStateBackend`).
- `core/knowledge`, `core/rag` — collections, ingestion, retrieval.
- `core/tools` — builtin tools, external MCP/tool servers, executor.
- `core/skills` — composable skills (sources, resolution).
- `core/kernel.py` — **orchestrator only**: routes events, maintains system
  state, never reasons.
- `core/bus`, `core/events` — NATS JetStream event bus. Event-driven only:
  modules never call each other directly.
- `core/auth`, `core/security`, `core/approval`, `core/audit`, `core/safety`,
  `core/capabilities` — security foundations (see §3).

### Runtime services — orchestration & execution

There is **no top-level `runtime/` directory**. The runtime is realized as
Docker Compose services executing Core code:

| Container | Entry point | Role |
|---|---|---|
| `ethan-kernel` | `core/kernel.py` | event routing, system state |
| `ethan-modules` | `core/modules` | cognitive modules launcher |
| `ethan-api` | `interfaces/api` (FastAPI) | HTTP gateway over Core |
| `ethan-nats` | — | event bus (JetStream) |
| `ethan-redis` | — | live state |
| `ethan-postgres` | — | persistent state |
| `ethan-ui` | `interfaces/webui` build | WebUI (host :3001 → container :3000) |
| `ethan-pg_backup` | — | backups |

Observability stack (optional profile): Prometheus (:9090), Grafana, Loki.

### Interfaces — replaceable viewers

- `interfaces/api` — FastAPI gateway; the only HTTP surface; used by all
  interfaces.
- `interfaces/webui` — Next.js 15 / React 19. Presentation only: it renders
  Core capabilities and sends user actions (see `docs/webui/`).
- `interfaces/cli` — Python interactive shell.
- `interfaces/channels` — messaging integrations.
- `interfaces/desktop` — early stage (Planned as a full interface).

**Rule** : interfaces must not implement business logic, providers, agents,
memory, RAG or missions. ETHAN runs with all interfaces stopped.

## 2. Data flow (chat example)

```
WebUI (page.tsx)
  → POST /v1/chat/completions/stream  (FastAPI gateway)
    → core/chat/pipeline.py
        resolves agent → provider/model/skills/knowledge/tools
        streams via LLM provider (core/llm)
        persists in ChatStore (core/state/chats.py, PostgreSQL)
  ← SSE events (content / tool calls / done)
```

## 3. Security architecture

**Implemented** :

- `core/auth` — JWT users & groups.
- `core/security` — gateway, policy module, data protection, validation.
- `core/approval` — approval engine for sensitive actions.
- `core/audit` — audit store.
- `core/safety` — circuit breaker.
- `core/capabilities` — capability registry (LLM, memory…).
- Secrets layer — env vars / Docker secrets / Vault; never in code, git, logs,
  events.

**Planned (see `docs/security/`)** : full Policy Engine enforcing the ETHAN
Constitution on every action; complete Capability System for sensitive
operations (filesystem, system administration, Docker, voice); systematic
verification of tool/MCP results. The Constitution
(`docs/security/ETHAN_CONSTITUTION.md`, v1.0) is normative text, not yet
end-to-end enforcement.

## 4. Plugins & SDK

- `plugins/` — extensible plugins (browser, terminal, sandbox, memory,
  builtin) with loader, validator, versioning, tool registry.
- `sdk/` — Python & TypeScript client SDKs; `proto/ethan` definitions.

## 5. Status summary

See the root `README.md` → **Project Status** (Implemented / In Progress /
Planned). This document never describes planned work as existing.
