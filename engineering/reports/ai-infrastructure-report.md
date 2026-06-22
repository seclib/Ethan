# AI Infrastructure Report — RFC-005

## Architecture Overview

This report documents the AI infrastructure layer added to Ethan OS as part of RFC-005. The architecture follows a layered service model with clear startup dependencies and network isolation.

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ethan-network                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           MONITORING LAYER                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │ Traefik  │  │ Prometheus│  │ Grafana  │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │            CORE APP LAYER                        │  │
│  │  ┌──────────┐           ┌──────────┐            │  │
│  │  │  Backend │◄──────────│ Frontend │            │  │
│  │  └────┬─────┘           └──────────┘            │  │
│  │       │ depends_on                               │  │
│  └───────┼──────────────────────────────────────────┘  │
│          │                                              │
│  ┌───────┼──────────────────────────────────────────┐  │
│  │  AI LAYER                                        │  │
│  │  ┌────▼─────┐                                    │  │
│  │  │  Ollama  │  (Local LLM Inference)             │  │
│  │  │  :11434  │                                    │  │
│  │  └──────────┘                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           DATA LAYER                             │  │
│  │  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────┐ │  │
│  │  │ Redis  │  │PostgreSQL│  │ Qdrant │  │Chroma│ │  │
│  │  │:6379   │  │:5432     │  │:6333   │  │:8000 │ │  │
│  │  └────────┘  └──────────┘  └────────┘  └──────┘ │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Service Definitions

### Data Layer (boot order: 1→4)

| Service | Role | Port | Persistence | Healthcheck |
|---------|------|------|-------------|-------------|
| **Redis** | Short-term memory, caching, event buffering | 6379 | redis-data | redis-cli ping |
| **PostgreSQL** | Structured data, long-term memory, conversations | 5432 | postgres-data | pg_isready |
| **Qdrant** | Vector database, semantic memory, embeddings | 6333/6334 | qdrant-data | /healthz |
| **ChromaDB** | Alternative vector store (dev-friendly) | 8000 | chromadb-data | /api/v1/heartbeat |

### AI Layer (boot order: after data)

| Service | Role | Port | Persistence | Healthcheck |
|---------|------|------|-------------|-------------|
| **Ollama** | Local LLM inference runtime | 11434 | ollama-models | ollama list |

### Core App Layer (boot order: after AI)

| Service | Role | Port | Depends On |
|---------|------|------|------------|
| **Backend** | Ethan API (FastAPI) | 8000 | redis, postgres, qdrant, ollama |
| **Frontend** | Web UI (Nginx) | 80 | backend |

### Monitoring Layer (independent)

| Service | Role | Port | Depends On |
|---------|------|------|------------|
| **Prometheus** | Metrics collection & alerting | 9090 | — |
| **Grafana** | Dashboards & visualization | 3000 | prometheus |
| **Traefik** | Reverse proxy & SSL termination | 80/443/8080 | — |

## Environment Variables

### New variables added in this RFC

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama endpoint for API clients |
| `REDIS_HOST` | `redis` | Redis service hostname (Docker) |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant vector DB endpoint |
| `ETHAN_DATABASE_URL_PG` | `postgresql://ethan:...@postgres:5432/ethan` | PostgreSQL connection URL |

## Memory Flow Design

```
User Query
    │
    ▼
┌─────────────┐     ┌───────────┐     ┌────────────┐
│  Short-term  │────▶│  Working  │────▶│  Long-term │
│  Memory      │     │  Memory   │     │  Memory    │
│  (Redis)     │     │ (Backend) │     │ (Postgres) │
└─────────────┘     └───────────┘     └────────────┘
                        │
                        ▼
                  ┌────────────┐
                  │  Semantic  │
                  │  Memory    │
                  │  (Qdrant)  │
                  └────────────┘
```

1. **Short-term (Redis)**: Session state, conversation cache, event buffer, rate limiting
2. **Working (Backend)**: In-memory context window, active agent state
3. **Long-term (PostgreSQL)**: User profiles, conversation history, agent configurations
4. **Semantic (Qdrant)**: Embeddings, vector search, RAG document store, similarity search

## LLM Routing Design (Future-Ready)

The architecture anticipates multi-model routing:

```
Inference Request
    │
    ▼
┌──────────────┐
│  Router      │  ← Model selection logic (heuristic / learned)
└──────┬───────┘
       │
       ├─────────────────────────┐
       ▼                         ▼
┌──────────────┐       ┌──────────────────┐
│  Local       │       │  Cloud Provider  │
│  (Ollama)    │       │  (OpenAI, etc.)  │
│  :11434      │       │  External API    │
└──────────────┘       └──────────────────┘
```

- Local models served by Ollama on internal network
- Cloud providers accessed via API keys (OpenAI, Anthropic, Google)
- Routing policy configurable via `ETHAN_ENGINE_DEFAULT`
- Future: learned routing via Redis-stored performance metrics

## Startup Dependencies

```
redis ──► postgres ──► qdrant ──► chromadb
                                  │
                                  ▼
                               ollama
                                  │
                                  ▼
                              backend ──► frontend
```

All startup dependencies use `condition: service_healthy` to ensure services are ready before dependent services start.

## Network Design

- **Single network**: `ethan-network` (bridge driver)
- **All services** on the same network for internal DNS resolution
- **External ports** only for services requiring user access (backend, frontend, monitoring)
- **Internal services** (Redis, PostgreSQL, Qdrant) accessible by service name

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PostgreSQL password in env | Credential exposure | Placeholder in .env.example, documented as required |
| Redis persistence off by default | Data loss on restart | Configurable via REDIS_PERSISTENCE, documented |
| Qdrant memory usage | Resource exhaustion on small hosts | Documented minimum requirements |
| Ollama GPU passthrough | Nvidia-only, complex setup | Commented-out deploy section, documented |
| Startup ordering | Race conditions | `condition: service_healthy` on all depends_on |
| Network name change (jarvis → ethan) | Existing containers disconnected | Coordinated with codebase rebranding |

## Scaling Considerations

### Vertical Scaling
- **PostgreSQL**: Increase shared_buffers, work_mem for larger datasets
- **Qdrant**: Adjust memory limits via environment variables
- **Ollama**: Model size limited by available GPU memory

### Horizontal Scaling (Future)
- **Redis Cluster**: For high-availability caching layer
- **Qdrant Cluster**: For distributed vector search
- **Read replicas**: PostgreSQL read replicas for analytics queries

### Resource Requirements (Minimum)

| Service | RAM | CPU | Storage |
|---------|-----|-----|---------|
| Redis | 256 MB | 0.5 vCPU | 1 GB |
| PostgreSQL | 512 MB | 1 vCPU | 10 GB |
| Qdrant | 512 MB | 1 vCPU | 10 GB |
| Ollama | 8 GB | 4 vCPU | 20 GB (model-dependent) |

## Future Improvements

1. **Separate compose files**: Split into `docker-compose.{data,ai,monitor}.yml` for modular deployment
2. **Health dashboard**: Dedicated health check endpoint aggregating all service statuses
3. **Backup automation**: Cron-based PostgreSQL + Qdrant snapshots
4. **Resource limits**: Define Docker resource constraints per service
5. **Secrets management**: Move credentials to Docker secrets or external vault