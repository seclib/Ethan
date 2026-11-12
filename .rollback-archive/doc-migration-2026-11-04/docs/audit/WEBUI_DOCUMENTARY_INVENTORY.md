# ETHAN WebUI Documentary Inventory

This document provides a comprehensive inventory of all Markdown files relevant to the transformation of the ETHAN WebUI, as part of the initial audit phase.

## Inventory Table

| File Path | Objective | Apparent Status | Dependencies |
| :--- | :--- | :--- | :--- |
| `/Audit Architecture — WebUI vs Core Runtime.md` | Identify structural duplicates in Core and misplaced business logic in the API layer to define a clean boundary. | Analysis / Audit | Proposes creation of `docs/architecture/webui-core-audit.md` |
| `/docs/Audit Fonctionnel WebUI Dashboard (PLAN MODE).md` | Catalog "dead features" (frontend placeholders) and missing API routes to prioritize frontend-backend connectivity fixes. | Final Audit Report | References various UI components and API routes |
| `/docs/frontend_auth_audit.md` | Debug the authentication flow, specifically identifying a stale closure bug in the login process. | Bug Analysis | `interfaces/webui/src/app/(auth)/login/page.tsx`, `loading-overlay.tsx` |
| `/docs/design/ETHAN_WEBUI_UX_ANALYSIS.md` | Define the visual and UX target for ETHAN WebUI using Open-WebUI as a reference to move toward an "AI OS Cockpit" feel. | UX Analysis | `examples/open-webui` |
| `/docs/audit/ETHAN_WEBUI_INITIAL_ARCHITECTURE_AUDIT.md` | Compare the technical stacks and architectural patterns of the current ETHAN WebUI (React) vs Open-WebUI (SvelteKit). | Initial Audit | None explicit |
| `/docs/audit/ETHAN_WEBUI_GAP_ANALYSIS.md` | Identify missing API capabilities in ETHAN that are required to support an Open-WebUI-like frontend. | Gap Analysis | ETHAN API, Open-WebUI features |
| `/docs/audit/OPENWEBUI_FORK_FEASIBILITY.md` | Evaluate the technical risks and strategies (Rewrite vs Shim) for forking Open-WebUI. | Feasibility Analysis | Tech stacks of both projects |
| `/docs/development/ETHAN_WEBUI_FORK_STRATEGY.md` | Define the Git workflow and maintenance plan for the Open-WebUI fork to ensure upstream synchronization. | Reference Strategy | `FORK_FEASIBILITY.md`, `UX_ANALYSIS.md`, `API_MIGRATION.md`, `V2_ARCHITECTURE.md` |
| `/docs/plans/ETHAN_WEBUI_V2_ARCHITECTURE.md` | Provide a high-level blueprint for the v2 WebUI, including the tech stack (Next.js 15, Zustand) and real-time data flow. | Draft (Design Phase) | `FORK_FEASIBILITY.md`, `UX_ANALYSIS.md`, `API_MIGRATION.md` |
| `/docs/architecture/webui-core-audit.md` | Audit specific dashboard pages to identify where business logic is incorrectly stored in-memory instead of in the Core. | Audit / Plan | `core/llm`, `plugins/`, `core/planner`, `core/tools` |
| `/docs/architecture/migration-report.md` | Document the consolidation of LLM providers from the legacy `core/providers/` to the primary `core/llm/providers/`. | Migration Report | `AGENTS.md` |
| `/docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | Provide a detailed mapping to replace the Open-WebUI backend routers and models with ETHAN Core equivalents. | Migration Proposal | `examples/open-webui/backend/open_webui` |
| `/interfaces/webui/README.md` | Provide setup instructions and a detailed overview of the current WebUI architecture and implemented features. | Documentation | `WEBUI_ROADMAP.md` |
| `/examples/open-webui/README.md` | Overview of the Open-WebUI project features and installation methods (used as a reference for ETHAN). | External Documentation | None (External project) |
