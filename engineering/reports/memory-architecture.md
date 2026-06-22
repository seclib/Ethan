# Memory Architecture — RFC-006

## 1. Context

Ethan OS currently has:
- A **MemoryAgent** (`core/agents/memory.py`) that handles `memory:store`, `memory:retrieve`, `memory:search` events via LLM calls
- An AI infrastructure layer (Redis, PostgreSQL, Qdrant) deployed via Docker (RFC-005)

The **MemoryManager** provides a unified abstraction so application components never interact directly with databases. The existing MemoryAgent will route through MemoryManager instead of calling `self.think()` directly.

### Design Principles

- **Provider-agnostic**: same code works regardless of backend
- **Modular**: adding or replacing a provider requires no business logic changes
- **Scalable**: each provider can be scaled independently
- **Extensible**: new storage backends integrate through a common interface

---

## 2. High-Level Architecture

```
                    ┌──────────────────────────────────────┐
                    │          Application Layer            │
                    │  ┌────────┐ ┌────────┐ ┌────────┐   │
                    │  │ Agent  │ │ Skill  │ │ Plugin │   │
                    │  └───┬────┘ └───┬────┘ └───┬────┘   │
                    │      │          │           │        │
                    │      └────┬─────┴─────┬─────┘        │
                    │           │           │              │
                    │           ▼           ▼              │
                    │  ┌──────────────────────────────┐    │
                    │  │      MemoryAgent (existing)   │    │
                    │  │   (event bus: memory:store,   │    │
                    │  │    memory:retrieve, etc.)     │    │
                    │  └──────────────┬───────────────┘    │
                    └─────────────────┼────────────────────┘
                                      │ routes via
                    ┌─────────────────┼────────────────────┐
                    │                 ▼                    │
                    │       ┌─────────────────────┐        │
                    │       │    MemoryManager     │        │
                    │       │ (new service/runtime │        │
                    │       │   core/memory/)       │        │
                    │       └──┬──────────┬───────┘        │
                    │          │          │                │
                    │          ▼          ▼                │
                    │  ┌────────────┐ ┌────────────┐      │
                    │  │   Router   │ │   Cache    │      │
                    │  │ (type→prov)│ │ (LRU)      │      │
                    │  └──────┬─────┘ └────────────┘      │
                    │         │                            │
                    │         ▼                            │
                    │  ┌──────────────────────────────┐   │
                    │  │     MemoryProvider (ABC)     │   │
                    │  │  store()  retrieve() search()│   │
                    │  │  update() delete() health()  │   │
                    │  └────────┬─────────┬──────────┘   │
                    │           │         │               │
                    │     ┌─────┴──┐ ┌────┴─────┐        │
                    │     │ Redis  │ │PostgreSQL │        │
                    │     │Provider│ │ Provider  │        │
                    │     └───┬────┘ └─────┬────┘        │
                    │         │            │              │
                    └─────────┼────────────┼──────────────┘
                              │            │
                         ┌────▼────┐ ┌────▼────┐
                         │  Redis  │ │PostgreSQL│
                         │  :6379  │ │  :5432   │
                         └─────────┘ └─────────┘
```

**Key flow**: Application components publish events → MemoryAgent (existing) catches them → forwards to MemoryManager → Router selects provider → Operation executed → Result propagated back through event bus.

---

## 3. Memory Types

| Type | Backend | Characteristics | TTL | Purpose |
|------|---------|----------------|-----|---------|
| **Working** | Redis | Volatile, fast, session-scoped | minutes | Conversation context, active tasks |
| **Episodic** | PostgreSQL | Persistent, structured, queryable | days | Past conversations, completed tasks |
| **Semantic** | Qdrant | Vector-based, embeddings, similarity | persistent | Knowledge, docs, indexed data |
| **Procedural** | PostgreSQL | Structured, versioned, reference | persistent | Workflows, plugins, automations |

---

## 4. MemoryManager Service

### Responsibilities

- **Route** memory requests to the correct provider based on memory type
- **Cache** frequently accessed items in a local LRU cache
- **Health-check** all providers periodically
- **Enforce** TTL, retention, and promotion policies
- **Log** all operations for audit/debugging
- **Expose metrics** (latency, error rates, throughput)

### Provider Selection Strategy

1. Check memory type → map to primary provider
2. If primary provider unhealthy → fallback to secondary (if configured)
3. If no provider available → return error with details

### Event Bus Integration

The MemoryManager subscribes to the same events as the existing MemoryAgent:

```python
# Existing events (preserved for backward compatibility)
memory:store     → routes to store()
memory:retrieve  → routes to retrieve()
memory:search    → routes to search()
memory:update    → new: routes to update()
memory:delete    → new: routes to delete()
memory:forget    → new: routes to forget()
memory:summarize → new: routes to summarize()
memory:promote   → new: routes to promote()
```

---

## 5. Configuration Schema

```yaml
# configs/memory.yaml or environment variables
memory:
  providers:
    redis:
      enabled: true
      host: redis
      port: 6379
      priority: 1
    postgres:
      enabled: true
      host: postgres
      port: 5432
      db: ethan
      user: ethan
      password: ${POSTGRES_PASSWORD}
      priority: 2
    qdrant:
      enabled: true
      url: http://qdrant:6333
      priority: 3

  routing:
    working:
      provider: redis
      fallback: postgres
    episodic:
      provider: postgres
      fallback: null
    semantic:
      provider: qdrant
      fallback: null
    procedural:
      provider: postgres
      fallback: null

  cache:
    enabled: true
    max_size: 1000
    ttl: 60  # seconds

  lifecycle:
    working:
      ttl: 300
      max_items_per_session: 100
      promotion:
        enabled: true
        threshold: 3
    episodic:
      ttl: 7776000  # 90 days
      retention_days: 90
      promotion:
        enabled: true
        threshold: 10
    semantic:
      ttl: 0  # no expiration
    procedural:
      ttl: 0
      versioning:
        enabled: true
        max_versions: 5
```

---

## 6. Package Structure

Recommended for MVP: **Embedded module** at `core/memory/`:

```
core/memory/
├── __init__.py
├── manager.py          # MemoryManager class
├── provider.py         # MemoryProvider ABC
├── router.py           # Type→provider routing logic
├── cache.py            # LRU cache
├── config.py           # Configuration loading
├── providers/
│   ├── __init__.py
│   ├── redis.py        # RedisProvider
│   ├── postgres.py     # PostgresProvider
│   └── qdrant.py       # QdrantProvider
└── lifecycle/
    ├── __init__.py
    ├── promoter.py     # Promotion worker
    ├── expirer.py      # Expiration worker
    └── summarizer.py   # Summarization worker
```

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Provider failure | Memory ops fail | Health checks, fallback providers, circuit breaker |
| Cache inconsistency | Stale reads | TTL-based expiration, write-through cache |
| Performance overhead | Latency from routing | Local LRU cache, async operations, connection pooling |
| Event bus coupling | Blocking if bus slow | Async handlers, timeout per operation |
| Provider migration | Data loss | Export/import per provider, versioned schemas |

---

## 8. Future Extensions

- **Provider plugins**: dynamically load external providers
- **Multi-region replication**: sync memory across instances
- **Memory federation**: aggregate across multiple Ethan OS instances
- **Audit trail**: full history of memory operations
- **Backup/restore**: snapshot and restore providers independently