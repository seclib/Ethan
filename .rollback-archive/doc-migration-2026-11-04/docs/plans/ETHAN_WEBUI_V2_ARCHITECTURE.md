# ETHAN WebUI v2 – Architecture Overview

**Date** : 11/08/2026
**Status** : Draft – design phase (no code changes yet)
**References** :
- `docs/audit/OPENWEBUI_FORK_FEASIBILITY.md`
- `docs/design/ETHAN_WEBUI_UX_ANALYSIS.md`
- `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md`

---

## 1. Front‑end Architecture

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Framework** | **Next.js 15 (App Router)** + **React 19** | Provides SSR, static generation, and seamless integration with the existing ETHAN `interfaces/webui` codebase.
| **Component Library** | **shadcn/ui** (Button, Card, Dialog, etc.) + **Open‑WebUI component concepts** (Chat, Sidebar, ModelSelector, Terminal, Rich‑Text editor) | shadcn/ui gives us a solid accessible base; we will recreate the visual look & feel of Open‑WebUI components as React equivalents (see UX analysis).
| **Styling** | **Tailwind CSS 3** + CSS variables for theming | Enables rapid prototyping and theming (light/dark/custom) while staying compatible with the current Tailwind version used in the repo.
| **State Management** | **Zustand (persist)** for UI‑only state + **TanStack Query** for data fetching/caching | Keeps UI thin – all business data lives in ETHAN Core; Zustand manages UI flags (sidebar collapsed, selected chat, theme), TanStack Query handles async server data.
| **Rich Text / Code Editor** | **Tiptap** (React wrapper) for markdown‑rich chat input + **CodeMirror 6** for embedded code editing. | Directly re‑uses the proven editors from Open‑WebUI.
| **Terminal** | **xterm.js** React component | Provides the terminal pane (already present in Open‑WebUI).
| **Internationalisation** | **i18next** (React) – same as Open‑WebUI | Multi‑language UI support.
| **Design System** | Shared token file `design/tokens.css` + `components/` directory mirroring Open‑WebUI UI concepts. | Guarantees visual consistency; future theming via CSS variables.

### 1.1 UI Page Layout
- **Three‑column layout** (sidebar ← main content → optional context pane) – identical to Open‑WebUI.
- **Responsive**: on ≤ 768 px the sidebar collapses to a hamburger menu, the main area becomes full‑width (chat or selected page).
- **Global Command Palette** (`Ctrl+K`) – already in ETHAN WebUI; extended with Open‑WebUI shortcuts.

---

## 2. API Architecture

| Concern | Implementation | Notes |
|---------|----------------|-------|
| **Gateway** | `interfaces/api/main.py` – FastAPI entry point, lives behind a reverse‑proxy. | Handles CORS, JWT auth, NATS connection, ProviderManager injection.
| **Domain Routers** | `interfaces/api/routers/domains.py` exposing `/v1/chats`, `/v1/files`, `/v1/users`, `/v1/groups`. | Thin HTTP façade; all business logic resides in Core stores (`core/state/*`, `core/auth/*`).
| **Core Services** | `core/state/*` (ChatStore, FileStore, ChannelStore, NoteStore) + `core/auth/*` (UserManager, GroupManager, OAuthManager, LDAPManager, APIKeyManager, SCIMManager). | Source of truth – persisted via `CoreRecordStore` (PostgreSQL + Redis + in‑process fallback).
| **LLM / Provider Layer** | `core/llm/provider_manager.py` + `core/llm/store.py`. | Unified access to Ollama, OpenAI, Azure, Anthropic, Gemini, vLLM, custom providers.
| **Event Bus** | **NATS** – asynchronous messaging for intents, agent execution, system metrics. | `interfaces/api/routers/message.py` publishes `ethan.intent.user`; other services subscribe (`core/agents`, `core/missions`).
| **WebSocket / Real‑time** | Future router `interfaces/api/routers/realtime.py` will expose `GET /v1/ws` forwarding NATS events to the browser. | Enables chat streaming, agent status updates, system health notifications.
| **Permissions** | `core/auth/Permission` enum + `interfaces/api/auth.require_permission`. | Front‑end routes guarded by role (`admin`, `agent`, `user`).
| **Configuration** | `core/config/ConfigurationService` – single source of truth for runtime settings. | UI settings page reads/writes via `/config` routes.

### 2.1 API Versioning & Compatibility
- **v1** – existing stable endpoints (agents, missions, memory, knowledge, etc.).
- **v2** – new domain routers for chats, files, users, groups (already present) plus future `/v2/*` for UI‑specific extensions (e.g., `/v2/dashboard`).
- All endpoints return **Pydantic** models; where possible we keep the same JSON contract as Open‑WebUI for smoother migration.

---

## 3. Required Pages (Front‑end Routes)
| Page | Path (Next.js) | Core API Endpoints Used | Description |
|------|----------------|------------------------|-------------|
| **Dashboard** | `/` | `/v1/state`, `/v1/health`, `/v1/metrics` | Overview of system health, active agents, recent chats, resource usage.
| **Chat** | `/assistant` | `/v1/chats`, `/v1/chats/{id}/messages`, `/v1/message` (POST) | Full‑featured chat UI: streaming, model selector, rich‑text input, terminal toggle.
| **Agents** | `/agents` | `/v1/agents`, `/v1/agents/{id}`, `/v1/agents/{id}/execute` | List, inspect, create, edit, execute agents.
| **Providers** | `/providers` | `/providers` router (exposes provider CRUD) | Manage LLM providers, credentials, test connections.
| **Models** | `/models` | `/v1/models` (via ProviderManager) | View, pin, set default, delete models.
| **Memory** | `/memory` | `/v1/memory/*` | Browse ETHAN memory (facts, events), search, purge.
| **Knowledge** | `/knowledge` | `/v1/knowledge/*` | Document ingestion, RAG index status, query.
| **MCP (Tool Server)** | `/tools` | `/v1/tools`, `/v1/functions` | Register/inspect tool servers, view pipelines.
| **Skills** | `/skills` | `/v1/skills` | Create, edit, test skills used by agents.
| **Runtime** | `/runtime` | `/v1/agents`, `/v1/missions`, `/v1/flux` | Visualise running missions, agent executions, event streams.
| **System Health** | `/system` | `/health`, `/health/detailed`, `/metrics` | Detailed health checks, logs, telemetry, alerts.
| **Settings** | `/settings` | `/config/*` | User preferences, theme, auth methods, API keys.
| **Admin Panel** (optional) | `/admin` | all admin‑only routers (`/v1/users`, `/v1/groups`, `/v1/config`) | Manage users, groups, permissions.

---

## 4. Data Flow (High‑level)
1. **User Interaction** – UI components trigger a **REST call** (e.g., `POST /v1/chats`, `POST /v1/message`).
2. **API Gateway** authenticates the request (JWT cookie), checks permissions, forwards to the appropriate **Domain Manager**.
3. **Domain Manager** (e.g., `ChatStore`) performs CRUD via `CoreRecordStore` → persists to PostgreSQL (primary) and optionally caches in Redis.
4. After mutation, the manager emits a **domain event** (e.g., `CHAT_CREATED`) through the **NATS bus**.
5. **Event Consumers** – agents, RAG pipeline, analytics – listen to NATS topics and react (e.g., start an LLM inference, update metrics).
6. **Response** – API returns the created/updated resource; for streaming responses (chat generation) the **Message** router publishes an intent event and the client opens a **WebSocket** to receive incremental `CHAT_MESSAGE` events.
7. **Front‑end** consumes the WebSocket stream, updates UI state (Zustand), and optionally refetches via TanStack Query to keep data in sync.

```
[Browser] ↔ (HTTPS) ↔ [API Gateway] ↔ (NATS) ↔ [Core Services]
   │                                          │
   └─→ PostgreSQL / Redis (persistent store) └─→ Agents / RAG / Metrics
```

---

## 5. Real‑time Event Management
### 5.1 Bus d'événements
- **NATS Topics**
  - `ethan.intent.user` – user intents (chat messages, UI commands).
  - `ethan.agent.execution` – status updates for agent runs.
  - `ethan.system.health` – heartbeat / health check events.
  - `ethan.chat.message` – newly created chat messages (published by `ChatStore`).
### 5.2 WebSocket Bridge
- A new router `interfaces/api/routers/realtime.py` will expose `GET /v1/ws` that forwards subscribed NATS topics to the client (filterable by `session_id`).
- **Client‑side** – a `useNats` React hook subscribes to relevant topics, updates Zustand stores, causing UI re‑render.
- **Fallback** – we expose a **Server‑Sent Events** endpoint `/v1/sse` for environments where WebSocket is unavailable.

---

## 6. Authentication & Authorization (ETHAN Core)
1. **Login** – `POST /auth/login` returns a JWT and sets an **HttpOnly** `ethan_token` cookie.
2. **Registration** – `POST /auth/register` creates a user via `UserManager`.
3. **OAuth / LDAP** – `core/auth/oauth.py` and `core/auth/ldap.py` expose provider configuration endpoints (`/config/oauth`, `/config/ldap`). OAuth flow tokens are stored as API keys.
4. **API Keys** – `core/auth/api_keys.py` lets users generate scoped keys for programmatic access.
5. **SCIM** – optional provisioning for enterprise directories (`/config/scim`).
6. **Permission Checks** – each router decorates endpoints with `Depends(require_permission(Permission.X))`. Permissions are stored per‑user/group in the `groups` store.
7. **Refresh** – `POST /auth/refresh` issues a new JWT; client automatically renews token before expiry.
8. **Logout** – clears the cookie.

---

## 7. Migration Roadmap (Implementation Phases)
| Phase | Scope | Key Deliverables |
|------|-------|------------------|
| **0 – Foundations** (already completed) | Core domain stores, routers, JWT auth. | `ChatStore`, `FileStore`, `UserManager`, `GroupManager`, API gateway injection. |
| **1 – Real‑time Bridge (COMPLETE ✅)** | Add `realtime` router, WS client hook, publish chat messages on NATS. | `GET /v1/ws`, React `useWebSocket` hook, UI updates for streaming chat. |
| **2 – Open‑WebUI UI Port** | Implement React equivalents of Open‑WebUI components (Chat, Sidebar, ModelSelector, Terminal, Tiptap editor). | Component library under `components/`, dark/light theme switch, placeholder UI. |
| **3 – Page Assembly** | Wire up routes defined in **Section 3** with the new components, connect to API via TanStack Query. | Fully functional pages: `/assistant`, `/agents`, `/providers`, `/models`, `/knowledge`, etc. |
| **4 – Advanced Features** | Add pagination, search, drag‑&‑drop for chats, notifications (toast, banner). | Scalable UI, performance optimisations, accessibility audit. |
| **5 – Production Readiness** | CI/CD pipeline, end‑to‑end tests, performance benchmarks, observability (Prometheus, OpenTelemetry). | Deployable Docker image, monitoring dashboards. |

---

## 8. Open Issues & Decisions
- **State Synchronisation** – optimistic UI updates vs. waiting for server‑acknowledged events.
- **Terminal Persistence** – should terminal sessions be stored as a Core domain to survive page reloads?
- **Theming System** – evaluate CSS‑variable approach vs. Tailwind config extraction for custom themes (rosepine, etc.).
- **Search Backend** – for full‑text chat and knowledge search, decide between PostgreSQL `tsvector` vs. external Elastic/Meilisearch.

---

## 9. Next Steps
1. **Create React component skeletons** for Chat, Sidebar, ModelSelector. (DONE in P0)
2. **Add unit tests** for the new WebSocket endpoint and for `ChatStore` event publishing.
3. **Update CI** to spin up a temporary NATS container for integration tests.

---

*Prepared by the ETHAN architecture team.*
