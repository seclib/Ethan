# ETHAN WebUI — Master Implementation Plan

> **Status:** Phase 0 (P0) — Core infrastructure & chat ✅ | Phase 1 (P1) — Workspace ✅ | Phase 2 (P2) — COMPLETE ✅
> **Last updated:** 2026-08-14

## Architecture

```
ETHAN Core / Runtime  ←→  ETHAN API (FastAPI)  ←→  WebUI (Next.js)
                                                            ↓
                                               Modular API clients (@/lib/api/*)
                                               Thin feature services (@/features/*/services)
                                               React Query hooks (@/features/*/hooks)
```

The WebUI is a **thin client**. It never calls Ollama, providers, databases, MCP servers, or RAG engines directly. All intelligence lives in Core/Runtime.

---

## Phase 0 — P0 (COMPLETE ✅)

Priority: frontend architecture, API integration, auth, layout, sidebar, navigation, chat, model selection.

| # | Task | Status | Evidence |
|---|------|--------|----------|
| P0-01 | Frontend architecture — modular API client layer | ✅ | `lib/api/client.ts` (apiFetch, streamEvents, ApiError) |
| P0-02 | API integration — modular clients for all Core entities | ✅ | `lib/api/{models,providers,knowledge,skills,tools,prompts,agents,missions,goals,chat,memory}.ts` |
| P0-03 | Authentication — ETHAN JWT via HttpOnly cookie | ✅ | `lib/auth/client.ts`, `core/providers/auth-provider.tsx` (normalizeUser) |
| P0-04 | Layout — dashboard layout with motion transitions | ✅ | `app/(dashboard)/layout.tsx` |
| P0-05 | Sidebar — navigation + authenticated user display | ✅ | `components/layout/sidebar.tsx` (useAuth) |
| P0-06 | Navigation — grouped nav items, breadcrumbs | ✅ | `sidebar.tsx`, `topbar.tsx` |
| P0-07 | Chat — SSE streaming via Core pipeline | ✅ | `features/assistant/services/chat.service.ts`, `use-chats.ts` |
| P0-08 | Model selection — provider/model picker with pinning | ✅ | `use-active-model.ts`, `components/shared/model-selector.tsx` |

**Validation:** `tsc --noEmit` → EXIT 0 | `next lint` → EXIT 0 | `npm run test` → PASS
*(Audit complet du Senior Engineer : P0 validé avec 0 erreur sur toute la stack WebUI le 2026-08-15)*

### Key fixes applied during P0
- `use-chats.ts`: fixed `createNewChat` → `createChat`, added `pinnedChats`/`regularChats`/`addMessage`/`EthMessage`, imported `apiFetch` from modular client
- `chat.service.ts`: migrated from monolith `apiClient` to `apiFetch`
- `use-active-model.ts`: migrated from `apiClient` to modular `listProviders`/`setDefaultProvider`
- `sidebar.tsx`: replaced static "User" with `useAuth()` user data
- `use-agents.ts`: added `useAgent(id)` and `useUpdateAgent()` for inspector/editor
- `use-goals.ts`: added `useGoal(id)` for inspector
- `model-selector.tsx`: fixed `providerId` → `provider` (ModelInfo field)
- `models/page.tsx`: fixed `unknown` type cast on `model.meta?.tags`
- All `lib/api/*` types aligned with canonical `@/types/index`

---

## Phase 1 — P1 (COMPLETE ✅)

### P1-01 — Models & Providers
- **Core:** `core/llm/model_store.py` (ModelStore, persistent custom cards)
- **API:** `interfaces/api/routers/models.py` (aggregated `/models` endpoint)
- **WebUI:** `lib/api/models.ts`, `lib/api/providers.ts`, pages Models & Providers, `use-models.ts`
- **Tests:** `tests/test_model_store.py` (11 tests)

### P1-02 — Workspace Knowledge
- **WebUI:** `features/knowledge/services/knowledge.service.ts`, `hooks/use-knowledge.ts`, `(dashboard)/knowledge/page.tsx`

### P1-03 — Workspace Skills
- **WebUI:** `lib/api/skills.ts`, `features/skills/services/skills.service.ts`, `hooks/use-skills.ts`, `(dashboard)/skills/page.tsx`

### P1-04 — Workspace Tools/MCP
- **WebUI:** `lib/api/tools.ts`, `(dashboard)/tools/page.tsx` (MCP server listing)

### P1-05 — Workspace Prompts
- **WebUI:** `lib/api/prompts.ts`, `(dashboard)/prompts/page.tsx`

### P1-06 — Workspace Agents/Missions/Goals
- **WebUI:** `lib/api/{agents,missions,goals}.ts`, services, hooks, pages
- Migrated all hooks from monolith `apiClient` to modular clients

---

## Phase 2 — P2 (IN PROGRESS)

### P2-01 — Memory management UI
- **API:** `/v1/memory/facts` (list, search, get, create, delete), `/v1/memory/events`, `/v1/memory/ingest`
- **WebUI:**
  - Refactor `memory.service.ts` to use modular `lib/api/memory.ts` functions
  - Enhance `use-memory.ts` hook: add `useDeleteFact`, wire search to `useFacts`
  - Improve `memory/page.tsx`: wire search input, use canonical `Fact` type, add delete action
- **Status:** ✅ COMPLETE — service refactored to use modular `lib/api/memory.ts`, hook enhanced with `useDeleteFact` + search, page wired with search/delete/canonical `Fact` type

### P2-02 — Planner & goals workflow UI
- **API:** `/v1/goals` (CRUD), `/v1/missions` (CRUD + verify/approve steps)
- **WebUI:**
  - Connect `planner/page.tsx` to real goals data via `useGoals` hook
  - Add `useUpdateGoal` hook for status transitions
  - `planner/goals/page.tsx` already connected ✅
- **Status:** ✅ COMPLETE — planner connected to `useGoals`, `useUpdateGoal` added, `GoalCreatorDialog` integrated, task progress visualization

### P2-03 — Terminal & logs pages
- **API:** `/v1/flux` (list events), `/v1/flux/{id}` (get event)
- **WebUI:**
  - Create `lib/api/flux.ts` (modular client for flux events)
  - Create `features/flux/services/flux.service.ts` (thin service)
  - Create `features/flux/hooks/use-flux.ts` (React Query hooks)
  - Connect `logs/page.tsx` to real flux events
  - Terminal: connect to ETHAN shell execution API
- **Status:** ✅ COMPLETE — `lib/api/flux.ts` created, `features/flux/` service + hooks created, `logs/page.tsx` connected to `/v1/flux`, `logs/flux/page.tsx` connected to `useFluxEvents`

### P2-04 — Settings page
- **API:** `/v1/settings` (GET, PUT)
- **WebUI:**
  - Create `lib/api/settings.ts` (modular client)
  - Create `features/settings/services/settings.service.ts`
  - Create `features/settings/hooks/use-settings.ts`
  - Migrate `settings/page.tsx` from monolith `apiClient` to modular client
- **Status:** ✅ COMPLETE — `lib/api/settings.ts` created, `features/settings/` service + hooks created, `settings/page.tsx` migrated from monolith `apiClient` to modular `useSettings` hook, `SystemConfig` type added to `@/types/index.ts`

### P2-05 — Plugin manager
- **API:** `/v1/plugins` (list, get), `/v1/plugins/install` (POST), `/v1/plugins/{id}/toggle` (PUT)
- **WebUI:**
  - Create `lib/api/plugins.ts` (modular client)
  - Create `features/plugins/services/plugins.service.ts`
  - Create `features/plugins/hooks/use-plugins.ts`
  - Connect `plugins/page.tsx` to real plugin data
- **Status:** ✅ COMPLETE — `lib/api/plugins.ts` created, `features/plugins/` service + hooks created, `plugins/page.tsx` connected to `/v1/plugins` with toggle/install actions

---

## Phase 3 — P3 (PLANNED)

- Desktop integration
- Voice assistant interface
- Mobile interface
- Autonomous agents
