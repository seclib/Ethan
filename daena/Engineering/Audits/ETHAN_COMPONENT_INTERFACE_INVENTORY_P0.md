# ETHAN — Inventaire des interfaces entre composants (P0)

## 1. Diagramme logique

```text
Interfaces (WebUI/API clients/CLI/Desktop)
        -> FastAPI interfaces/api (routers)
        -> Core (core/* managers/state)
        -> Runtime services Docker (kernel, modules, nats, redis, postgres)
        -> External (Ollama/OpenAI/Anthropic, MCP, web)
```

## 2. Interfaces HTTP/FastAPI principales

- Routeur aggregateur: `interfaces/api/main.py` (`app.include_router(...)`). 48 router modules.
- Auth: `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `/auth/me`.
- Capacités: `/providers`, `/models`, `/v1/*`, `/files`, `/config`, `/connections`, `/integrations`, `/knowledge`, `/skills`, etc.
- Santé: `/health`, `/health/live`, `/health/ready`, `/health/detailed`, `/metrics`.
- Conventions: gateway thin; ne pas mettre de logique métier dans routers.

## 3. Contrats internes Core

- Event bus: `core/bus/interface.py`, `core/bus/router.py`, `core/bus/nats_bus.py`.
- Event types: `core/ethan_types/event.py` (mention dans impl).
- State interfaces: `core/state/interface.py`, `core/state/composite_backend.py`, `CoreRecordStore`.
- Knowledge/RAG: `core/knowledge/*`, `core/rag/*`.
- Tools protocol: `core/tools/call_protocol.py`.
- Skills validation/import: `core/skills/validation.py`, `core/skills/import_manager.py` (untracked).
- Security/action types: `core/security/types.py`.

## 4. Ponts inter-processus / FFI

- Rust prototypes: `core/bus/backends/rust_event_store/` lib Rust via PyO3 (contract dans bridge contract doc).
- Rust health prototype: `core/rust/ethan_health` (main, clap, tracing), port default 8080 (attention au conflit avec `ethan-kernel` port 8080; à résoudre par config, pas de déplacement de port existant sans décision).
- Open-WebUI bridge: `interfaces/bridge/openwebui/adapter.py`, `auth/jwt_proxy.py`, `sync/users.py`, event bus contract nullable.

## 5. Persistence/composition

- Composite backend Redis (live) + PostgreSQL (persistent).
- Fact store SQLite (`core/facts/store.py`), imports defaults.
- Core record stores in memory or DB depending bootstrap.
- Docker volumes Postgres/Redis/NATS.

## 6. User flows importants

- Chat request: WebUI → `/v1/chat` (chat pipeline) → provider models → tools/skills/knowledge/memory injection → streaming/persistence.
- Knowledge ingest: WebUI → knowledge/rag endpoints → Core RAG pipeline → vector store → retriever.
- Config install capabilities: ESR install engine, Docker provisioning, requires allowlist and sandbox.
- Odin: API router + UI page; modifications en cours non commitées.

## 7. Points de couplage à surveiller

- `interfaces/api/routers/v1.py` single router très large; gateways multiples; risque de PRs concurrents.
- Duplication `CoreWebUIStore` vs managers réels.
- API TestClient environment issue.
- Rust target artifacts and untracked prototype.
- Open WebUI modified checkout.
