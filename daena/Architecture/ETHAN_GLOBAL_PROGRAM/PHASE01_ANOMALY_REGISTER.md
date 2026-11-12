# Phase 01 — Anomaly Register

1. ID ANO-01 WebUI/API naming/contract ambiguity
   - Domain WebUI
   - File `interfaces/webui/src/lib/api/capabilities.ts`
   - Observed: calendar/notes methods route to `/v1/calendar`, `/v1/notes`.
   - Cause: naming convention mismatch between file ownership and endpoint.
   - Status: confirmed partial mismatch.

2. ID ANO-02 Application state can look available without runtime proof
   Correction Phase 02: no runtime proof conversion; state representation remains separate.
   - Domain Application lifecycle
   - Files `application_registry.py`, `discovery.py`
   - Observed: `available` is persisted state.
   - Status: confirmed concept.

3. ID ANO-03 Quantar secure provider gateway transport absent
   - Domain Quantar
   - Files `quantar_service.py`, `core/security/hrot_provider_gateway.py`, `quantar_provider_bridge.py`
   - Observed: no secret-safe worker→gateway transport.
   - Status: confirmed block.

4. ID ANO-04 Component lifecycle not located in core
   - Note: `core/components` path absent, yet API router exists.
   - Status: path/ownership remains to verify; no Core manager named `manager.py` at expected path.


5. ID ANO-05 Skill package import endpoints declared in router but not mounted through v1 import
   - Domain: Skills / WebUI → API contract
   - Files: `interfaces/api/routers/skills.py`, `interfaces/api/routers/v1.py`, `interfaces/webui/src/lib/api/skills.ts`
   - Observed: `GET/POST /v1/skills/import/scan` and `/v1/skills/import-files` absent despite WebUI and backend route definitions; contract test failed.
   - Root cause: these operations lived in `skills.py` router but were not included by `interfaces/api/main.py`, and v1 exposed only the JSON-list import.
   - Correction: mounted equivalent endpoints in `v1.py` (file uploads + auth/permission), reusing `SkillImportManager`.
   - Status: corrected and contract test passing.


## Provider campaigns (2026-11-05)

- ISSUE A (provider catalog unreachable): `FIXED` at test level — import real `httpx` inside the async test instead of global dummy; root cause was the test environment's global `sys.modules["httpx"]` substitution in `tests/conftest.py`. Isolated and combined tests pass.
- ISSUE B (Ollama model discovery empty in suite): `FIXED` at test level — import real `httpx` before `register_provider` in `test_ollama_connecte_et_modeles_exposes`.
- ISSUE C (default seed contamination): `FIXED` — test now controls `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` via `pytest.MonkeyPatch`, ensuring expected seeded defaults independent of machine environment.
- Runtime Ollama `/chat` returning `PONG` remains validated.

Evidence bundle:
- Individual tests: 1 pass + 1 pass + 1 pass.
- Combined provider tests: `tests/test_provider_catalog.py::test_unreachable_provider_reports_error_without_raising`, `tests/core/test_provider_manager_ai_surface.py::...test_ollama_connecte_et_modeles_exposes`, `test_restart_with_empty_store_seeds_defaults`, `test_provider_manager`, `test_unified_providers` = 56 passed.
