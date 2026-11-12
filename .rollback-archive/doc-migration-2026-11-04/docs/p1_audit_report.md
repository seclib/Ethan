# P1 Audit Report — ETHAN WebUI

> **Date:** 2026-08-14
> **Scope:** All P1 capabilities (Models, Providers, Knowledge, Skills, Tools/MCP, Prompts, Documents/Files)

## Executive Summary

The API client layer (`lib/api/*`) and backend routers are **solid** — proper Core delegation, typed interfaces, CRUD operations. However, the **page-level** implementations have critical functional gaps: missing CRUD actions, stale monolith imports, and no React Query mutation wiring on several pages.

**Verdict: P1 pages "exist" but are not fully functional.**

---

## Findings by Component

### 🔴 P1-01 — Models Page (`models/page.tsx`)

| Gap | Severity |
|-----|----------|
| No "Create custom model" action | **Critical** — API client has `createModel()`, page doesn't wire it |
| No "Delete model" action | **Critical** — API client has `deleteModel()`, page doesn't wire it |
| No "Toggle model" action | **High** — API client has `toggleModel()`, page doesn't wire it |
| Uses inline `useQuery` — no dedicated hook with mutations | **Medium** — inconsistent with other pages (knowledge, skills have hooks) |

### 🟡 P1-01 — Providers Page (`providers/page.tsx`)

| Gap | Severity |
|-----|----------|
| No "Create provider" action | **Critical** — API has `createProvider()`, not exposed in UI |
| No "Delete provider" action | **Critical** — API has `deleteProvider()`, not exposed in UI |
| No "Test connection" button | **High** — API has `testProviderConnection()`, not wired |
| No "Set as default" button | **High** — API has `setDefaultProvider()`, not wired |
| Uses inline `useQuery/useMutation` — no dedicated hook | **Medium** |

### 🔴 P1-04 — Tools/MCP Page (`tools/page.tsx`)

| Gap | Severity |
|-----|----------|
| No "Register MCP server" action | **Critical** — API has `registerToolServer()`, not exposed |
| No "Enable/Disable" toggle | **Critical** — API has `setToolServerStatus()`, not wired |
| No "Delete server" action | **Critical** — API has `deleteToolServer()`, not wired |
| Read-only listing only | — |

### 🔴 P1-Documents — Documents Page (`documents/page.tsx`)

| Gap | Severity |
|-----|----------|
| Uses **monolith** `ragService` from `@/core/api/api-client` | **Critical** — violates modular architecture |
| No delete document action | **High** — API has `deleteRagDocument()`, not wired |
| No React Query (manual state mgmt) | **High** — inconsistent with all other P1/P2 pages |

### ✅ P1-02 — Knowledge Page — Good
- Uses `useKnowledge` hook → `knowledgeService` → `lib/api/knowledge.ts`
- Collections: create, delete, search ✅
- RAG documents: ingest, list ✅
- Missing: delete RAG document button (minor)

### ✅ P1-03 — Skills Page — Good
- Uses `useSkills` hook → `skillsService` → `lib/api/skills.ts`
- Create, toggle, delete, search ✅

### ✅ P1-05 — Prompts Page — Good
- Uses modular `lib/api/prompts.ts` directly with React Query
- Create, delete, search ✅

---

## Fix Plan

1. **Models page** → Add create/delete/toggle model dialogs + dedicated mutations
2. **Providers page** → Add create/delete/test/set-default actions
3. **Tools/MCP page** → Add register/enable-disable/delete server actions
4. **Documents page** → Migrate from monolith `ragService` to modular `lib/api/knowledge.ts` + React Query
5. **Knowledge page** → Add delete RAG document button
