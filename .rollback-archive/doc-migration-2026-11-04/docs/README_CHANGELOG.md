# README Change Log — Refactor (Project Identity & Current Architecture)

> Scope of the `README.md` rewrite. Goal: make the README the single, honest
> entry point of ETHAN — distinguishing IMPLEMENTED / IN PROGRESS / PLANNED.

## Removed (obsolete / incorrect)

- **`runtime/` in the project-structure tree** — this directory does not exist.
  The runtime is a set of Docker Compose services (`ethan-kernel`,
  `ethan-modules`, `ethan-api`, …) executing Core code. The structure section
  now reflects the real tree.
- **Broken Quick Start** — the old README started the stack with `./ethan`
  (which only prints help). Replaced with the verified flow:
  `./ethan install` → `./ethan preflight` → `./ethan up` → `./ethan status` →
  `http://localhost:3001`.
- **Broken dev test command** — `CI=1 npm test -- --watchAll=false` (Create
  React App style) removed; the WebUI uses jest (`npm test`) / playwright
  (`npm run test:e2e`).
- **Marketing-style roadmap mixing vision and shipped features** — replaced by
  an explicit *Project Status* section with three categories and a status table.
- Any trace of former identities: the README contained none, and it was
  verified again (`grep -i odysseus` → 0 results).

## Added

- **Identity statement**: ETHAN as a local-first, extensible AI platform
  (Core + Runtime services + interfaces), not a chatbot — with the "first
  rule" (capabilities live in Core/Runtime, interfaces only reveal).
- **Architecture section**: Core responsibilities (with real module paths),
  Runtime services table (real containers), Interfaces contract.
- **Memory vs Knowledge vs RAG** — three distinct concepts, with the direction
  "prefer verified procedures over memorizing everything".
- **Agents section** — real `core/agents` architecture; **Atreus explicitly
  marked PLANNED** (it exists only in `docs/plans/` design notes).
- **ETHAN WebUI section** — control-center positioning, page list, port 3001,
  Open-WebUI inspiration formulated as inspiration (never a fork).
- **Open-WebUI reference section** — role of `examples/open-webui`, explicit
  non-dependency of ETHAN on Open-WebUI business logic.
- **Security & ETHAN Constitution section** — implemented foundations
  (`core/auth`, `core/security`, `core/approval`, `core/audit`, `core/safety`,
  `core/capabilities`) vs **PLANNED SECURITY ARCHITECTURE** (Policy Engine,
  full Capability System), pointing to `docs/security/ETHAN_CONSTITUTION.md`.
- **System capabilities — future direction** — capabilities explicitly
  granted, policies independent of the LLM, auditable sensitive actions,
  never-implicit external transmission.
- **Technology stack** — verified against the repository (Python 3.11+,
  Next.js 15 / React 19, NATS, Redis 7, PostgreSQL 16, JWT, Docker Compose,
  Prometheus/Grafana/Loki, Vault, Python & TS SDKs).
- **Project Status** (Implemented / In Progress / Planned) and a concise
  **Roadmap** table (WebUI refinement, agents, Atreus, Constitution, Policy
  Engine, Capability System, Projects, workspace access, memory validation,
  Desktop, Voice).
- Documentation table now points to real, verified paths
  (`docs/security/`, `docs/webui/`, `docs/architecture/…`).

## Corrected

- Env-var guidance simplified and aligned with `.env.example`
  (`JWT_SECRET`, `POSTGRES_PASSWORD` mandatory; provider keys optional).
- All module paths cited in tables verified against the actual tree
  (`core/llm`, `core/agents`, `core/chat`, `core/planner`, `core/memory`,
  `core/knowledge`, `core/rag`, `core/tools`, `core/skills`, `core/kernel.py`,
  `core/bus`, `core/modules`, `core/auth`, `core/security`, …).

## Companion documents created

- `docs/architecture/README_ARCHITECTURE_REFERENCE.md` — detailed,
  code-verified architecture reference (Core / Runtime services / Interfaces,
  chat data flow, security status).
- `docs/README_CHANGELOG.md` — this file.

## Verification checklist

- [x] Every described component exists in code or is marked Planned
- [x] Architecture consistent with the code (no `runtime/`, no invented dirs)
- [x] All Quick Start commands verified against `ethan` launcher routing
- [x] WebUI documented on the real port (3001 — Docker mapping & `./ethan webui`)
- [x] Core / Runtime / Interface separation explicit
- [x] Open-WebUI presented as UX reference, not backend
- [x] Atreus marked Planned
- [x] Security presented honestly (implemented vs planned)
- [x] No Odysseus / former-identity traces
- [x] Consistent with `docs/` (links verified)
