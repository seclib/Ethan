# 🔬 ETHAN Boot Sequence Audit — Verified Report

## Verification Status

| Bug | Claimed | **Verified** | Notes |
|-----|---------|-------------|-------|
| P0-1 | Redis Auth RESP3 | ✅ **Confirmed** | `redis_state.py:26` uses `from_url()` without `protocol=2`. Docker-compose already uses `redis://default:...` but `redis-py` defaults to RESP3 which requires auth before HELLO. |
| P0-2 | Shadowing bootstrap | ⚠️ **Partially** | `core/bootstrap/` is a package (has `__init__.py`), but `ethan_bootstrap.py` imports `from core.bootstrap.bootstrapper import SystemBootstrapper` — NOT `from core.bootstrap import main`. The entrypoint is `core/ethan_bootstrap.py` not `core/bootstrap.py`. **No shadowing crash on current entrypoint.** |
| P0-3 | Dual Event | ✅ **Confirmed** | 17 files import `sdk/event.py` (uses `data=`), 21 files import `ethan_types/event.py` (uses `payload=`), `nats_bus.py` defines a 3rd `Event` class. Critical incompatibility. |
| P1-1 | Kernel healthcheck | ✅ **Confirmed** | Line 180: NATS-only Python check. |
| P1-2 | Modules healthcheck | ✅ **Confirmed** | Line 214: same NATS-only check. |
| P1-3 | Circular dep modules | ✅ **Confirmed** | Line 211: `kernel: condition: service_healthy`. |
| P1-4 | API healthcheck Redis | ✅ **Confirmed** | Line 159: `from_url(redis_url)` then `ping()` — same RESP3 issue. Returns 503 → container unhealthy. |
| P1-5 | Bus interface mismatch | ✅ **Confirmed** | `interface.py:55` `connect(servers: str)` vs `nats_bus.py:70` `connect()` — LSP violation. |
| P1-6 | No bootstrap timeout | ✅ **Confirmed** | `bootstrapper.py:36` `await bootstrapper.run()` — no `wait_for`. |
| P1-7 | Flags default true | ✅ **Confirmed** | `docker-compose.yml:157-159` all `"true"`. |
| P2-1 | EventType duplicated | ✅ **Confirmed** | `ethan_types/event.py` uses `ethan.*`, SDK uses flat `system.*`. |
| P2-2 | No events table | ✅ **Confirmed** | `deploy/postgres/init.sql` is an **empty directory**, not a file. |
| P2-3 | Modules empty | ✅ **Confirmed** | `modules/__main__.py` just connects NATS and waits. |
| P2-4 | Version unchecked | ✅ **Confirmed** | `sdk/event.py:21` `version` field unused. |
| P2-5 | JSON logs | ✅ **Confirmed** | `telemetry/logger.py` JSONFormatter. |

---

## Fix Execution Plan

### Sprint 1 — P0: Unblock the Boot

- [x] **P0-1**: Fix Redis RESP3 auth — force `protocol=2` in `redis_state.py` + API healthcheck
- [ ] **P0-3**: Unify Event classes — migrate all SDK Event users to canonical `ethan_types/event.py`

### Sprint 2 — P1: Stabilize Healthchecks

- [ ] **P1-1/P1-2**: Replace NATS-only healthchecks with proper HTTP endpoints
- [ ] **P1-3**: Make modules depend on kernel with `service_started` instead of `service_healthy`
- [ ] **P1-4**: Fix API `/health/detailed` Redis check (same RESP3 fix)
- [ ] **P1-5**: Align bus interface `connect()` signature
- [ ] **P1-6**: Add `asyncio.wait_for()` to bootstrapper
- [ ] **P1-7**: Default learning/metacognition/autonomy to `"false"`

### Sprint 3 — P2: Cleanup

- [ ] **P2-1**: Unify EventType enums
- [ ] **P2-2**: Create proper `init.sql` file with events table
- [ ] **P2-3**: Wire cognitive modules in `__main__.py`
- [ ] **P2-5**: Dual-format logger (JSON + human-readable)
