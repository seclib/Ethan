# Phase 01 — WebUI / API / Core Map (2026-11-05)

## Verified paths
- WebUI API wrappers: `interfaces/webui/src/lib/api/*.ts`.
- Backend routers: `interfaces/api/routers/*.py`.
- Mounted router set: `interfaces/api/main.py` include_router lines (capabilities, plugins, providers, knowledge, frame, odin, quantar, skills, component_lifecycle).
- Core managers/services: `core/llm/provider_manager.py`, `core/security/hrot_provider_gateway.py`, `core/applications/application_registry.py`, `core/applications/discovery.py`, `core/plugins/odin.py`, `frame.py`, `quantar.py`.

## Chain observed
`WebUI page`
→ `src/lib/api/*.ts` (`apiFetch`)
→ FastAPI endpoint
→ Core service/manager
→ runtime status (Docker via service/permissions/state).

## App visibility mechanism
- Discovery produces `DECLARED` capabilities only.
- Application registry handles `registered/validated/available/unavailable` and lifecycle state separately.
- Odin/Frame/Quantar expose `get_status`, start/stop/restart by service.
- `available` is not proof of Docker/container/service reachability.

## Verification
- Targeted tests passing: `tests/core/test_application_capability_discovery.py`, manifest, manifest_robustness, application e2e Phase 14, frame, hrot provider gateway = 53 passed.
