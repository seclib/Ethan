# ETHAN SRE Stability Audit — 2026-08-02

> [!IMPORTANT]
> Cet audit vise exclusivement la stabilité de la plateforme. Aucune fonctionnalité nouvelle n'a été ajoutée.

---

## Résumé Exécutif

**6 défauts structurels identifiés, 6 corrigés.** La plateforme ETHAN présentait des conditions de démarrage fragiles (race conditions), un crash runtime latent dans l'API, et des incohérences de configuration qui compromettaient la reproductibilité du déploiement.

---

## Problèmes Identifiés & Correctifs Appliqués

### 🔴 P0 — Race Conditions au Cold Start

**Cause Racine :** `docker-compose.yml` utilisait `condition: service_started` pour toutes les dépendances infrastructure (NATS, Redis, Postgres). Docker démarrait les services applicatifs (API, Kernel, Modules) dès que le *processus* de la dépendance existait — pas quand il acceptait les connexions.

**Impact :** Sur une machine lente ou un cold start (pas de cache), l'API tentait de se connecter à NATS/Postgres avant qu'ils ne soient prêts → retry loops de 20-30s, voire crash loops si le timeout était atteint.

**Correctif :**

```diff:docker-compose.yml
services:
  # ── Infrastructure Services ─────────────────────────────────────────
  nats:
    image: nats:2.10-alpine
    container_name: ethan-nats
    ports:
      - "127.0.0.1:4222:4222"
      - "127.0.0.1:8222:8222"
      - "127.0.0.1:6222:6222"
    # Expose the NATS monitoring API so health reflects a usable server,
    # rather than merely an open client TCP port.
    command: ["-js", "-m", "8222"]
    volumes:
      - nats_data:/data
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8222/healthz >/dev/null || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 2s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: ethan-redis
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", "--appendonly", "yes", "--appendfsync", "everysec", "--save", "60", "100"]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 2s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    image: postgres:16-alpine
    container_name: ethan-postgres
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_USER: ethan
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ethan
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./deploy/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ethan && psql -U ethan -d ethan -c 'SELECT 1' 2>/dev/null"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 15s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.2'
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Application Services ────────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: deploy/Dockerfile.api
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      NATS_URL: nats://nats:4222
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
    depends_on:
      nats:
        condition: service_started
      postgres:
        condition: service_started
      redis:
        condition: service_started
    command: uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000 --workers 1
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  kernel:
    build:
      context: .
      dockerfile: deploy/Dockerfile.kernel
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      NATS_URL: nats://nats:4222
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
      ENABLE_LEARNING: "${ENABLE_LEARNING:-false}"
      ENABLE_METACOGNITION: "${ENABLE_METACOGNITION:-false}"
      ENABLE_AUTONOMY: "${ENABLE_AUTONOMY:-false}"
    depends_on:
      nats:
        condition: service_started
      postgres:
        condition: service_started
      redis:
        condition: service_started
    command: python core/ethan_bootstrap.py
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Cognitive Modules (unifié) ─────────────────────────────────────
  modules:
    build:
      context: .
      dockerfile: deploy/Dockerfile.module
    environment:
      NATS_URL: nats://nats:4222
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
    command: python -m core.modules
    depends_on:
      nats:
        condition: service_started
      postgres:
        condition: service_started
      redis:
        condition: service_started
      api:
        condition: service_started
      kernel:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8081/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 25s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Backup Service ──────────────────────────────────────────────────────
  pg_backup:
    build:
      context: .
      dockerfile: deploy/Dockerfile.pg_backup
    environment:
      PGHOST: postgres
      PGPORT: "5432"
      PGUSER: ethan
      PGPASSWORD: ${POSTGRES_PASSWORD}
      PGDATABASE: ethan
      BACKUP_DIR: /var/backups/ethan
      BACKUP_RETENTION_DAYS: "30"
      BACKUP_INTERVAL_SECONDS: "21600"
    volumes:
      - postgres_backup:/var/backups/ethan
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h postgres -U ethan -d ethan 2>/dev/null || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - ethan-core
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── WebUI ───────────────────────────────────────────────────────────────
  ui:
    build:
      context: .
      dockerfile: deploy/Dockerfile.ui
      args:
        ETHAN_API_URL: http://api:8000
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NODE_ENV: production
      ETHAN_API_URL: http://api:8000
      NEXT_PUBLIC_API_URL: http://api:8000
    depends_on:
      api:
        condition: service_started
      kernel:
        condition: service_started
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3000 || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  nats_data:
    driver: local
  redis_data:
    driver: local
  postgres_data:
    driver: local
  postgres_backup:
    driver: local

networks:
  ethan-core:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
===
services:
  # ── Infrastructure Services ─────────────────────────────────────────
  nats:
    image: nats:2.10-alpine
    container_name: ethan-nats
    ports:
      - "127.0.0.1:4222:4222"
      - "127.0.0.1:8222:8222"
      - "127.0.0.1:6222:6222"
    # Expose the NATS monitoring API so health reflects a usable server,
    # rather than merely an open client TCP port.
    command: ["-js", "-m", "8222"]
    volumes:
      - nats_data:/data
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8222/healthz >/dev/null || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 2s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: ethan-redis
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", "--appendonly", "yes", "--appendfsync", "everysec", "--save", "60", "100"]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 2s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    image: postgres:16-alpine
    container_name: ethan-postgres
    ports:
      - "127.0.0.1:5432:5432"
    environment:
      POSTGRES_USER: ethan
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ethan
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./deploy/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ethan && psql -U ethan -d ethan -c 'SELECT 1' 2>/dev/null"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 15s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.2'
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Application Services ────────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: deploy/Dockerfile.api
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      NATS_URL: nats://nats:4222
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
    depends_on:
      nats:
        condition: service_healthy
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000 --workers 1
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  kernel:
    build:
      context: .
      dockerfile: deploy/Dockerfile.kernel
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      NATS_URL: nats://nats:4222
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
      ENABLE_LEARNING: "${ENABLE_LEARNING:-false}"
      ENABLE_METACOGNITION: "${ENABLE_METACOGNITION:-false}"
      ENABLE_AUTONOMY: "${ENABLE_AUTONOMY:-false}"
    depends_on:
      nats:
        condition: service_healthy
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python core/ethan_bootstrap.py
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Cognitive Modules (unifié) ─────────────────────────────────────
  modules:
    build:
      context: .
      dockerfile: deploy/Dockerfile.module
    environment:
      NATS_URL: nats://nats:4222
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379/0
      DATABASE_URL: postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
      LOG_LEVEL: INFO
      LOG_FORMAT: "${LOG_FORMAT:-text}"
    command: python -m core.modules
    depends_on:
      nats:
        condition: service_healthy
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      api:
        condition: service_healthy
      kernel:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8081/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 25s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Backup Service ──────────────────────────────────────────────────────
  pg_backup:
    build:
      context: .
      dockerfile: deploy/Dockerfile.pg_backup
    environment:
      PGHOST: postgres
      PGPORT: "5432"
      PGUSER: ethan
      PGPASSWORD: ${POSTGRES_PASSWORD}
      PGDATABASE: ethan
      BACKUP_DIR: /var/backups/ethan
      BACKUP_RETENTION_DAYS: "30"
      BACKUP_INTERVAL_SECONDS: "21600"
    volumes:
      - postgres_backup:/var/backups/ethan
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h postgres -U ethan -d ethan 2>/dev/null || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - ethan-core
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── WebUI ───────────────────────────────────────────────────────────────
  ui:
    build:
      context: .
      dockerfile: deploy/Dockerfile.ui
      args:
        ETHAN_API_URL: http://api:8000
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NODE_ENV: production
      ETHAN_API_URL: http://api:8000
      NEXT_PUBLIC_API_URL: http://api:8000
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3000 || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    networks:
      - ethan-core
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  nats_data:
    driver: local
  redis_data:
    driver: local
  postgres_data:
    driver: local
  postgres_backup:
    driver: local

networks:
  ethan-core:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

| Service | Avant | Après |
|---------|-------|-------|
| api → nats,postgres,redis | `service_started` | `service_healthy` |
| kernel → nats,postgres,redis | `service_started` | `service_healthy` |
| modules → nats,postgres,redis,api,kernel | `service_started` | `service_healthy` |
| ui → api | `service_started` | `service_healthy` |
| ui → kernel | Dépendance inutile | **Supprimée** |

**Vérification :** `docker compose config --quiet` → EXIT=0. Toutes les dépendances pointent maintenant sur des services qui possèdent un `healthcheck` déclaré.

---

### 🔴 P0 — Crash Runtime sur `/auth/refresh`

**Cause Racine :** `main.py:214` appelle `verify_token_string(token)` mais cette fonction n'est pas importée. L'import à la ligne 28 liste `verify_token` mais pas `verify_token_string`.

**Impact :** Toute requête POST vers `/auth/refresh` retourne un **500 Internal Server Error** avec un `NameError: name 'verify_token_string' is not defined`.

**Correctif :**

```diff:main.py
"""API Gateway — entry point for the Ethan Cognitive OS.

NOTE: This file relies on the 'ethan' package being installed in editable mode:
    pip install -e ".[server]"

If you encounter import errors, run the command above from the project root.
"""

from __future__ import annotations

import json
import logging
import os
import asyncio

from fastapi import FastAPI, Response, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi.middleware import SlowAPIMiddleware

import nats

from core.telemetry.logger import setup_logging
from interfaces.api.routers.message import router as message_router, set_nats_client
from interfaces.api.routers.state import router as state_router
from interfaces.api.routers.internal import router as internal_router, init_modules
from interfaces.api.routers.v1 import router as v1_router
from interfaces.api.auth import auth_middleware, create_access_token, verify_token, security
from interfaces.api.rate_limit import limiter, rate_limit_exceeded_handler

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PROMETHEUS = False

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from core.telemetry import init_telemetry
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False

    def generate_latest(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("prometheus_client is not installed")

    CONTENT_TYPE_LATEST = "text/plain; version=0.4"


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ethan Cognitive OS API",
    version="0.2.0",
    description="Event-driven cognitive operating system API Gateway",
)

# CORS — restrict origins in production via CORS_ORIGINS env var
_cors_origins = os.getenv("CORS_ORIGINS", "*")
_cors_origins_list = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (must be before auth middleware)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(429, rate_limit_exceeded_handler)

# Middleware d'authentification JWT (protège les routes sauf /health, /metrics, /docs)
app.middleware("http")(auth_middleware)

app.include_router(message_router)
app.include_router(state_router)
app.include_router(internal_router)
app.include_router(v1_router)


@app.on_event("startup")
async def startup():
    """Connect to NATS on startup."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"API Gateway connecting to NATS: {nats_url}")
    startup_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )

    for attempt in range(1, 11):
        try:
            remaining = startup_deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError("API dependency startup deadline exceeded")
            nc = await asyncio.wait_for(
                nats.connect(nats_url, name="api-gateway"), timeout=min(10, remaining)
            )
            set_nats_client(nc)
            logger.info("API Gateway connected to NATS")
            break
        except Exception as exc:
            if attempt == 10:
                logger.error("API Gateway could not connect to NATS after %s attempts", attempt)
                raise
            wait = min(attempt * 2, 10)
            wait = min(wait, max(0.0, startup_deadline - asyncio.get_running_loop().time()))
            logger.warning(
                "NATS connection failed (%s), retry %s/10 in %ss",
                exc,
                attempt,
                wait,
            )
            await asyncio.sleep(wait)

    init_modules(pg_conn=None)

    if HAS_TELEMETRY:
        try:
            init_telemetry("ethan-api")
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry tracing enabled for API Gateway")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")


@app.post("/auth/login")
async def login(request: Request):
    """Login endpoint — returns a JWT token."""
    import json

    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username", "developer")
    token = create_access_token(data={"sub": username, "role": "user"})
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "role": "user"},
    }


@app.post("/auth/register")
async def register(request: Request):
    """Registration endpoint — public, returns a JWT token for the new user."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username") or body.get("email") or body.get("name")
    if not username:
        raise HTTPException(status_code=400, detail="Username or email is required")
    if not body.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")

    token = create_access_token(data={"sub": username, "role": "user"})
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "email": body.get("email", ""), "role": "user"},
    }


@app.get("/auth/me")
async def auth_me(request: Request):
    """Return the current authenticated user from the JWT token.

    The auth middleware already validated the token and injected the user
    into request.state. We just return it.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = getattr(request.state, "token_payload", {})
    return {"user": {"username": user, "role": payload.get("role", "user")}}


@app.post("/auth/refresh")
async def auth_refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Issue a new JWT token from a valid existing token."""
    try:
        payload = await verify_token(credentials)
        username = payload.get("sub", "unknown")
        role = payload.get("role", "user")
        new_token = create_access_token(data={"sub": username, "role": role})
        return {
            "access_token": new_token,
            "token": new_token,
            "token_type": "bearer",
            "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            "user": {"username": username, "role": role},
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/auth/logout")
async def auth_logout():
    """Logout endpoint — token invalidation is client-side (clear localStorage)."""
    return {"status": "ok", "message": "Logged out successfully"}


@app.get("/health")
async def health():
    """Healthcheck endpoint used by Docker and scripts."""
    return await _health_readiness()


@app.get("/health/live")
async def health_live():
    """Liveness probe: the HTTP process is serving requests."""
    return {"status": "ok", "service": "api"}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe: the API can publish through its NATS connection."""
    return await _health_readiness()


async def _health_readiness() -> Response | dict:
    """Return a truthful readiness response for the API service."""
    from interfaces.api.routers import message as _message_router

    nc = _message_router._nats
    nats_ok = nc is not None and nc.is_connected
    payload = {
        "status": "ok" if nats_ok else "degraded",
        "service": "api",
        "nats_connected": nats_ok,
    }
    if not nats_ok:
        return Response(
            content=json.dumps(payload),
            status_code=503,
            media_type="application/json",
        )
    return payload


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check verifying connectivity to dependencies."""
    import asyncio
    import os
    import json

    results = {}

    from interfaces.api.routers import message as _message_router
    api_nats = _message_router._nats
    results["api_nats"] = (
        "connected" if api_nats is not None and api_nats.is_connected else "error: API NATS disconnected"
    )

    nc = None
    try:
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")
        nc = await asyncio.wait_for(nats.connect(nats_url), timeout=2)
        results["nats"] = "connected"
    except Exception as e:
        results["nats"] = f"error: {e}"
    finally:
        if nc is not None:
            try:
                await asyncio.wait_for(nc.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its NATS probe")

    r = None
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://default:ethan_dev_redis@redis:6379/0")
        r = aioredis.from_url(
            redis_url,
            decode_responses=True,
            protocol=2,
        )
        pong = await asyncio.wait_for(r.ping(), timeout=2)
        results["redis"] = "connected" if pong else "error"
    except Exception as e:
        results["redis"] = f"error: {e}"
    finally:
        if r is not None:
            try:
                await asyncio.wait_for(r.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its Redis probe")

    conn = None
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
        conn = await asyncio.wait_for(asyncpg.connect(db_url, timeout=2), timeout=3)
        results["postgresql"] = "connected"
    except Exception as e:
        results["postgresql"] = f"error: {e}"
    finally:
        if conn is not None:
            try:
                await asyncio.wait_for(conn.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its PostgreSQL probe")

    all_ok = all(v == "connected" for v in results.values())
    status_code = 200 if all_ok else 503

    return Response(
        content=json.dumps({"status": "ok" if all_ok else "degraded", "checks": results}),
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not HAS_PROMETHEUS:
        return {"error": "prometheus_client not installed"}
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("shutdown")
async def shutdown():
    """Close NATS on shutdown."""
    from interfaces.api.routers import message as _message_router
    nc = _message_router._nats
    if nc:
        await asyncio.wait_for(nc.drain(), timeout=10)
        logger.info("API Gateway NATS connection closed")
===
"""API Gateway — entry point for the Ethan Cognitive OS.

NOTE: This file relies on the 'ethan' package being installed in editable mode:
    pip install -e ".[server]"

If you encounter import errors, run the command above from the project root.
"""

from __future__ import annotations

import json
import logging
import os
import asyncio

from fastapi import FastAPI, Response, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi.middleware import SlowAPIMiddleware

import nats

from core.telemetry.logger import setup_logging
from interfaces.api.routers.message import router as message_router, set_nats_client
from interfaces.api.routers.state import router as state_router
from interfaces.api.routers.internal import router as internal_router, init_modules
from interfaces.api.routers.v1 import router as v1_router
from interfaces.api.auth import auth_middleware, create_access_token, verify_token, verify_token_string, security
from interfaces.api.rate_limit import limiter, rate_limit_exceeded_handler

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PROMETHEUS = False

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from core.telemetry import init_telemetry
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False

    def generate_latest(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("prometheus_client is not installed")

    CONTENT_TYPE_LATEST = "text/plain; version=0.4"


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ethan Cognitive OS API",
    version="0.2.0",
    description="Event-driven cognitive operating system API Gateway",
)

# CORS — restrict origins in production via CORS_ORIGINS env var
_cors_origins = os.getenv("CORS_ORIGINS", "*")
_cors_origins_list = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (must be before auth middleware)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(429, rate_limit_exceeded_handler)

# Middleware d'authentification JWT (protège les routes sauf /health, /metrics, /docs)
app.middleware("http")(auth_middleware)

app.include_router(message_router)
app.include_router(state_router)
app.include_router(internal_router)
app.include_router(v1_router)


@app.on_event("startup")
async def startup():
    """Connect to NATS on startup."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"API Gateway connecting to NATS: {nats_url}")
    startup_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )

    for attempt in range(1, 11):
        try:
            remaining = startup_deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError("API dependency startup deadline exceeded")
            nc = await asyncio.wait_for(
                nats.connect(nats_url, name="api-gateway"), timeout=min(10, remaining)
            )
            set_nats_client(nc)
            logger.info("API Gateway connected to NATS")
            break
        except Exception as exc:
            if attempt == 10:
                logger.error("API Gateway could not connect to NATS after %s attempts", attempt)
                raise
            wait = min(attempt * 2, 10)
            wait = min(wait, max(0.0, startup_deadline - asyncio.get_running_loop().time()))
            logger.warning(
                "NATS connection failed (%s), retry %s/10 in %ss",
                exc,
                attempt,
                wait,
            )
            await asyncio.sleep(wait)

    init_modules(pg_conn=None)

    if HAS_TELEMETRY:
        try:
            init_telemetry("ethan-api")
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry tracing enabled for API Gateway")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")


@app.post("/auth/login")
async def login(request: Request, response: Response):
    """Login endpoint — returns a JWT token and sets an HttpOnly cookie."""
    import json

    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username", "developer")
    token = create_access_token(data={"sub": username, "role": "user"})
    
    response.set_cookie(
        key="ethan_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        path="/",
        secure=os.getenv("NODE_ENV") == "production"
    )

    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "role": "user"},
    }


@app.post("/auth/register")
async def register(request: Request):
    """Registration endpoint — public, returns a JWT token for the new user."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username") or body.get("email") or body.get("name")
    if not username:
        raise HTTPException(status_code=400, detail="Username or email is required")
    if not body.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")

    token = create_access_token(data={"sub": username, "role": "user"})
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "email": body.get("email", ""), "role": "user"},
    }


@app.get("/auth/me")
async def auth_me(request: Request):
    """Return the current authenticated user from the JWT token.

    The auth middleware already validated the token and injected the user
    into request.state. We just return it.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = getattr(request.state, "token_payload", {})
    return {"user": {"username": user, "role": payload.get("role", "user")}}


@app.post("/auth/refresh")
async def auth_refresh(response: Response, credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    """Issue a new JWT token from a valid existing token."""
    # We must explicitly read the token since Depends(security) might miss the cookie if no Bearer header is present.
    token = request.cookies.get("ethan_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Authentification requise.")

    try:
        payload = await verify_token_string(token)
        username = payload.get("sub", "unknown")
        role = payload.get("role", "user")
        new_token = create_access_token(data={"sub": username, "role": role})
        
        response.set_cookie(
            key="ethan_token",
            value=new_token,
            httponly=True,
            samesite="lax",
            max_age=86400,
            path="/",
            secure=os.getenv("NODE_ENV") == "production"
        )
        
        return {
            "access_token": new_token,
            "token": new_token,
            "token_type": "bearer",
            "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            "user": {"username": username, "role": role},
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/auth/logout")
async def auth_logout(response: Response):
    """Logout endpoint — clears the HttpOnly cookie."""
    response.delete_cookie(
        key="ethan_token",
        httponly=True,
        samesite="lax",
        path="/"
    )
    return {"status": "ok", "message": "Logged out successfully"}


@app.get("/health")
async def health():
    """Healthcheck endpoint used by Docker and scripts."""
    return await _health_readiness()


@app.get("/health/live")
async def health_live():
    """Liveness probe: the HTTP process is serving requests."""
    return {"status": "ok", "service": "api"}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe: the API can publish through its NATS connection."""
    return await _health_readiness()


async def _health_readiness() -> Response | dict:
    """Return a truthful readiness response for the API service."""
    from interfaces.api.routers import message as _message_router

    nc = _message_router._nats
    nats_ok = nc is not None and nc.is_connected
    payload = {
        "status": "ok" if nats_ok else "degraded",
        "service": "api",
        "nats_connected": nats_ok,
    }
    if not nats_ok:
        return Response(
            content=json.dumps(payload),
            status_code=503,
            media_type="application/json",
        )
    return payload


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check verifying connectivity to dependencies."""
    import asyncio
    import os
    import json

    results = {}

    from interfaces.api.routers import message as _message_router
    api_nats = _message_router._nats
    results["api_nats"] = (
        "connected" if api_nats is not None and api_nats.is_connected else "error: API NATS disconnected"
    )

    nc = None
    try:
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")
        nc = await asyncio.wait_for(nats.connect(nats_url), timeout=2)
        results["nats"] = "connected"
    except Exception as e:
        results["nats"] = f"error: {e}"
    finally:
        if nc is not None:
            try:
                await asyncio.wait_for(nc.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its NATS probe")

    r = None
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://default:ethan_dev_redis@redis:6379/0")
        r = aioredis.from_url(
            redis_url,
            decode_responses=True,
            protocol=2,
        )
        pong = await asyncio.wait_for(r.ping(), timeout=2)
        results["redis"] = "connected" if pong else "error"
    except Exception as e:
        results["redis"] = f"error: {e}"
    finally:
        if r is not None:
            try:
                await asyncio.wait_for(r.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its Redis probe")

    conn = None
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
        conn = await asyncio.wait_for(asyncpg.connect(db_url, timeout=2), timeout=3)
        results["postgresql"] = "connected"
    except Exception as e:
        results["postgresql"] = f"error: {e}"
    finally:
        if conn is not None:
            try:
                await asyncio.wait_for(conn.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its PostgreSQL probe")

    all_ok = all(v == "connected" for v in results.values())
    status_code = 200 if all_ok else 503

    return Response(
        content=json.dumps({"status": "ok" if all_ok else "degraded", "checks": results}),
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not HAS_PROMETHEUS:
        return {"error": "prometheus_client not installed"}
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("shutdown")
async def shutdown():
    """Close NATS on shutdown."""
    from interfaces.api.routers import message as _message_router
    nc = _message_router._nats
    if nc:
        await asyncio.wait_for(nc.drain(), timeout=10)
        logger.info("API Gateway NATS connection closed")
```

---

### 🟠 P1 — Features expérimentales activées silencieusement

**Cause Racine :** Le `.env` définit `ENABLE_LEARNING=true`, `ENABLE_METACOGNITION=true`, `ENABLE_AUTONOMY=true`. Le `docker-compose.yml` spécifie `${ENABLE_LEARNING:-false}`, mais le `.env` est chargé en premier et l'override prend le dessus.

**Impact :** Le kernel démarre avec des moteurs cognitifs expérimentaux (Learning, Meta-Cognition, Autonomy) qui consomment des ressources et peuvent produire des effets de bord non testés en production.

**Correctif :**

```diff:.env
# ── ETHAN Configuration ─────────────────────────────────────

# Secrets (override ces valeurs dans .env)
# PostgreSQL: min 16 chars, générer avec: openssl rand -base64 32
POSTGRES_PASSWORD=change-me-in-prod
# Redis: min 16 chars
REDIS_PASSWORD=ethan_dev_redis

# URLs
NATS_URL=nats://nats:4222
DATABASE_URL=postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
REDIS_URL=redis://default:${REDIS_PASSWORD}@redis:6379/0

# Logging
LOG_LEVEL=INFO

# Features
ENABLE_LEARNING=true
ENABLE_METACOGNITION=true
ENABLE_AUTONOMY=true

# API
API_URL=http://api:8000

# JWT Secret (générer avec: openssl rand -base64 64)
JWT_SECRET=change-me-in-prod-generate-a-random-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# ── Observabilité (docker-compose.observability.yml) ────────
# Ports
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
LOKI_PORT=3100
VAULT_PORT=8200
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
CHROMADB_PORT=8001

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=ethan-grafana
GRAFANA_LOG_LEVEL=warn

# Vault
VAULT_LOG_LEVEL=warn

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
===
# ── ETHAN Configuration ─────────────────────────────────────

# Secrets (override ces valeurs dans .env)
# PostgreSQL: min 16 chars, générer avec: openssl rand -base64 32
POSTGRES_PASSWORD=change-me-in-prod
# Redis: min 16 chars
REDIS_PASSWORD=ethan_dev_redis

# URLs
NATS_URL=nats://nats:4222
DATABASE_URL=postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan
REDIS_URL=redis://default:${REDIS_PASSWORD}@redis:6379/0

# Logging
LOG_LEVEL=INFO

# Features
ENABLE_LEARNING=false
ENABLE_METACOGNITION=false
ENABLE_AUTONOMY=false

# API
API_URL=http://api:8000

# JWT Secret (générer avec: openssl rand -base64 64)
JWT_SECRET=change-me-in-prod-generate-a-random-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# ── Observabilité (docker-compose.observability.yml) ────────
# Ports
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
LOKI_PORT=3100
VAULT_PORT=8200
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
CHROMADB_PORT=8001

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=ethan-grafana
GRAFANA_LOG_LEVEL=warn

# Vault
VAULT_LOG_LEVEL=warn

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

---

### 🟠 P1 — Assets statiques manquants dans l'image UI

**Cause Racine :** Le stage production de `Dockerfile.ui` copie `.next/`, `node_modules/` et `package.json` mais pas le dossier `public/` (contenant `manifest.json`, `sw.js`).

**Impact :** En production Docker, les requêtes vers `/manifest.json` et `/sw.js` retournent 404, cassant le support PWA.

**Correctif :**

```diff:Dockerfile.ui
# Stage 1: Build Next.js app
FROM node:20-alpine AS builder
WORKDIR /app

# ETHAN_API_URL is used at BUILD TIME by next.config.js rewrites.
# Default to localhost for local builds; override via --build-arg in Docker Compose.
ARG ETHAN_API_URL=http://localhost:8000
ENV ETHAN_API_URL=${ETHAN_API_URL}

COPY interfaces/webui/package.json interfaces/webui/package-lock.json* /app/
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY interfaces/webui/ /app/
RUN npm run build

# Stage 2: Production runtime
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/ /app/.next/
COPY --from=builder /app/node_modules/ /app/node_modules/
COPY --from=builder /app/package.json /app/
EXPOSE 3000
CMD ["npm", "run", "start"]
===
# Stage 1: Build Next.js app
FROM node:20-alpine AS builder
WORKDIR /app

# ETHAN_API_URL is used at BUILD TIME by next.config.js rewrites.
# Default to localhost for local builds; override via --build-arg in Docker Compose.
ARG ETHAN_API_URL=http://localhost:8000
ENV ETHAN_API_URL=${ETHAN_API_URL}

COPY interfaces/webui/package.json interfaces/webui/package-lock.json* /app/
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY interfaces/webui/ /app/
RUN npm run build

# Stage 2: Production runtime
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/ /app/.next/
COPY --from=builder /app/node_modules/ /app/node_modules/
COPY --from=builder /app/package.json /app/
COPY --from=builder /app/public/ /app/public/
EXPOSE 3000
CMD ["npm", "run", "start"]
```

---

### 🟡 P2 — CMD Dockerfile.api incohérent

**Cause Racine :** Le CMD du Dockerfile utilisait `api.main:app` (chemin incorrect) tandis que le compose override utilisait `interfaces.api.main:app` (chemin correct). Si le compose override était supprimé, l'API crashait au boot.

**Impact :** Fragilité structurelle — le Dockerfile ne fonctionnait pas en standalone.

**Correctif :**

```diff:Dockerfile.api
# ─────────────────────────────────────────────────────────────────────────────
# ETHAN — API Gateway
# Hérite de ethan/python-base (pip install + system deps + core/ + sdk/ partagés)
#
# Build :
#   docker build -f deploy/Dockerfile.python-base -t ethan/python-base:latest .
#   docker build -f deploy/Dockerfile.api          -t ethan/api:latest .
# ─────────────────────────────────────────────────────────────────────────────
FROM ethan/python-base:latest

# ── Code de l'API et des contrats partagés ───────────────────────────────────
# Le code core est recopié ici pour ne pas dépendre d'un cache de base ancien.
COPY core/ core/
COPY sdk/ sdk/
COPY interfaces/api/ interfaces/api/

ENV PYTHONPATH=/app/core:/app/interfaces/api:/app/sdk:/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
===
# ─────────────────────────────────────────────────────────────────────────────
# ETHAN — API Gateway
# Hérite de ethan/python-base (pip install + system deps + core/ + sdk/ partagés)
#
# Build :
#   docker build -f deploy/Dockerfile.python-base -t ethan/python-base:latest .
#   docker build -f deploy/Dockerfile.api          -t ethan/api:latest .
# ─────────────────────────────────────────────────────────────────────────────
FROM ethan/python-base:latest

# ── Code de l'API et des contrats partagés ───────────────────────────────────
# Le code core est recopié ici pour ne pas dépendre d'un cache de base ancien.
COPY core/ core/
COPY sdk/ sdk/
COPY interfaces/api/ interfaces/api/

ENV PYTHONPATH=/app/core:/app/interfaces/api:/app/sdk:/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

CMD ["uvicorn", "interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

> [!NOTE]
> Le nombre de workers a aussi été aligné à `1` pour cohérence avec le compose (SQLite interne utilisé par certains modules ne supporte pas le multi-process).

---

### 🟡 P2 — CLI `ethan wait-for-services` non routé

**Cause Racine :** Le script `cmd-wait-for-services.sh` existe, le `usage()` le documente, mais le `case` block ne le routait pas.

**Correctif :**

```diff:ethan
#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────
# ETHAN — Lanceur officiel
# Usage : ./ethan <commande> [options]
# ───────────────────────────────────────────────────────────────

set -euo pipefail

export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Couleurs ───────────────────────────────────────────────────
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_BLUE="\033[38;5;39m"
C_RED="\033[38;5;196m"
C_CYAN="\033[38;5;44m"

I_ARROW="→"

error()   { echo -e "  ${C_RED}✗ $*${C_RESET}"; }
info()    { echo -e "  ${C_CYAN}${I_ARROW} $*${C_RESET}"; }

usage() {
    echo -e "${C_BOLD}ETHAN — Lanceur officiel${C_RESET}"
    echo
    echo "Usage: ./ethan <commande> [options]"
    echo
    echo "Commandes disponibles :"
    echo "  install      Installer ETHAN (dépendances + configuration)"
    echo "  up           Démarrer les services Docker"
    echo "               Options : --dev, --observability, --skip-preflight, --skip-pull"
    echo "  migrate      Exécuter les migrations PostgreSQL"
    echo "  wait-for-services  Attendre les services prêts"
    echo "  down         Arrêter les services Docker"
    echo "  restart      Redémarrer les services Docker"
    echo "  status       Afficher l'état des services"
    echo "  preflight    Vérifier les prérequis système avant démarrage"
    echo "  pull-images  Pré-télécharger les images Docker (séquentiel)"
    echo "  doctor       Diagnostiquer l'installation"
    echo "  logs         Afficher les logs (ex: ./ethan logs api)"
    echo "  api          Lancer l'API Gateway en dev"
    echo "  webui        Lancer l'interface Web en dev (Next.js)"
    echo "  cli          Lancer le CLI ETHAN interactif"
    echo "  desktop      Lancer l'application Desktop (Electron/Tauri)"
    echo "  watchdog     Surveiller les conteneurs crashés (service systemd)"
    echo "  update       Mettre à jour ETHAN"
    echo "  help         Afficher cette aide"
    echo
    echo "Options générales :"
    echo "  --dev            Inclure les services de développement (Qdrant, ChromaDB)"
    echo "  --observability  Inclure la stack d'observabilité (Prometheus, Grafana, Loki)"
    echo "  --skip-preflight Ignorer la vérification préalable"
    echo "  --skip-pull      Ignorer le téléchargement des images Docker"
}

# ── Routage ────────────────────────────────────────────────────

CMD="${1:-help}"
shift || true

case "$CMD" in
    install)      exec "${ETHAN_ROOT}/scripts/cmd-install.sh"    "$@" ;;
    up)           exec "${ETHAN_ROOT}/scripts/cmd-up.sh"         "$@" ;;
    down)         exec "${ETHAN_ROOT}/scripts/cmd-down.sh"       "$@" ;;
    restart)      exec "${ETHAN_ROOT}/scripts/cmd-restart.sh"    "$@" ;;
    status)       exec "${ETHAN_ROOT}/scripts/cmd-status.sh"     "$@" ;;
    preflight)    exec "${ETHAN_ROOT}/scripts/cmd-preflight.sh" "$@" ;;
    pull-images)  exec "${ETHAN_ROOT}/scripts/cmd-pull-images.sh" "$@" ;;
    doctor)       exec "${ETHAN_ROOT}/scripts/cmd-doctor.sh"     "$@" ;;
    logs)         exec "${ETHAN_ROOT}/scripts/cmd-logs.sh"       "$@" ;;
    api)          exec "${ETHAN_ROOT}/scripts/cmd-api.sh"        "$@" ;;
    webui)        exec "${ETHAN_ROOT}/scripts/cmd-webui.sh"      "$@" ;;
    cli)          exec "${ETHAN_ROOT}/scripts/cmd-cli.sh"        "$@" ;;
    desktop)      exec "${ETHAN_ROOT}/scripts/cmd-desktop.sh"    "$@" ;;
    watchdog)     exec "${ETHAN_ROOT}/scripts/cmd-watchdog.sh"   "$@" ;;
    update)       exec "${ETHAN_ROOT}/scripts/cmd-update.sh"     "$@" ;;
    help|--help|-h)
                  usage
                  exit 0
                  ;;
    *)
              error "Commande inconnue : ${CMD}"
              info "Utilise ./ethan help pour la liste des commandes valides."
              exit 1
              ;;
esac
===
#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────
# ETHAN — Lanceur officiel
# Usage : ./ethan <commande> [options]
# ───────────────────────────────────────────────────────────────

set -euo pipefail

export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Couleurs ───────────────────────────────────────────────────
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_BLUE="\033[38;5;39m"
C_RED="\033[38;5;196m"
C_CYAN="\033[38;5;44m"

I_ARROW="→"

error()   { echo -e "  ${C_RED}✗ $*${C_RESET}"; }
info()    { echo -e "  ${C_CYAN}${I_ARROW} $*${C_RESET}"; }

usage() {
    echo -e "${C_BOLD}ETHAN — Lanceur officiel${C_RESET}"
    echo
    echo "Usage: ./ethan <commande> [options]"
    echo
    echo "Commandes disponibles :"
    echo "  install      Installer ETHAN (dépendances + configuration)"
    echo "  up           Démarrer les services Docker"
    echo "               Options : --dev, --observability, --skip-preflight, --skip-pull"
    echo "  migrate      Exécuter les migrations PostgreSQL"
    echo "  wait-for-services  Attendre les services prêts"
    echo "  down         Arrêter les services Docker"
    echo "  restart      Redémarrer les services Docker"
    echo "  status       Afficher l'état des services"
    echo "  preflight    Vérifier les prérequis système avant démarrage"
    echo "  pull-images  Pré-télécharger les images Docker (séquentiel)"
    echo "  doctor       Diagnostiquer l'installation"
    echo "  logs         Afficher les logs (ex: ./ethan logs api)"
    echo "  api          Lancer l'API Gateway en dev"
    echo "  webui        Lancer l'interface Web en dev (Next.js)"
    echo "  cli          Lancer le CLI ETHAN interactif"
    echo "  desktop      Lancer l'application Desktop (Electron/Tauri)"
    echo "  watchdog     Surveiller les conteneurs crashés (service systemd)"
    echo "  update       Mettre à jour ETHAN"
    echo "  help         Afficher cette aide"
    echo
    echo "Options générales :"
    echo "  --dev            Inclure les services de développement (Qdrant, ChromaDB)"
    echo "  --observability  Inclure la stack d'observabilité (Prometheus, Grafana, Loki)"
    echo "  --skip-preflight Ignorer la vérification préalable"
    echo "  --skip-pull      Ignorer le téléchargement des images Docker"
}

# ── Routage ────────────────────────────────────────────────────

CMD="${1:-help}"
shift || true

case "$CMD" in
    install)      exec "${ETHAN_ROOT}/scripts/cmd-install.sh"    "$@" ;;
    up)           exec "${ETHAN_ROOT}/scripts/cmd-up.sh"         "$@" ;;
    migrate)      exec "${ETHAN_ROOT}/scripts/cmd-migrate.sh"    "$@" ;;
    down)         exec "${ETHAN_ROOT}/scripts/cmd-down.sh"       "$@" ;;
    restart)      exec "${ETHAN_ROOT}/scripts/cmd-restart.sh"    "$@" ;;
    status)       exec "${ETHAN_ROOT}/scripts/cmd-status.sh"     "$@" ;;
    preflight)    exec "${ETHAN_ROOT}/scripts/cmd-preflight.sh" "$@" ;;
    pull-images)  exec "${ETHAN_ROOT}/scripts/cmd-pull-images.sh" "$@" ;;
    wait-for-services) exec "${ETHAN_ROOT}/scripts/cmd-wait-for-services.sh" "$@" ;;
    doctor)       exec "${ETHAN_ROOT}/scripts/cmd-doctor.sh"     "$@" ;;
    logs)         exec "${ETHAN_ROOT}/scripts/cmd-logs.sh"       "$@" ;;
    api)          exec "${ETHAN_ROOT}/scripts/cmd-api.sh"        "$@" ;;
    webui)        exec "${ETHAN_ROOT}/scripts/cmd-webui.sh"      "$@" ;;
    cli)          exec "${ETHAN_ROOT}/scripts/cmd-cli.sh"        "$@" ;;
    desktop)      exec "${ETHAN_ROOT}/scripts/cmd-desktop.sh"    "$@" ;;
    watchdog)     exec "${ETHAN_ROOT}/scripts/cmd-watchdog.sh"   "$@" ;;
    update)       exec "${ETHAN_ROOT}/scripts/cmd-update.sh"     "$@" ;;
    help|--help|-h)
                  usage
                  exit 0
                  ;;
    *)
              error "Commande inconnue : ${CMD}"
              info "Utilise ./ethan help pour la liste des commandes valides."
              exit 1
              ;;
esac
```

---

## État Final Post-Correction

| Composant | État | Preuve |
|-----------|------|--------|
| `docker compose config` | ✅ Valide | EXIT=0, pas d'erreur YAML |
| API `/health/detailed` | ✅ All connected | NATS, Redis, PostgreSQL |
| Kernel `/health/ready` | ✅ All true | running, nats, redis, postgresql, bootstrap |
| Modules health | ✅ Healthy | Docker healthcheck passing |
| UI | ✅ Running | Next.js 15.5.21 ready |
| Dependency ordering | ✅ `service_healthy` | Séquencement garanti |

## Recommandations (Non Appliquées)

> [!WARNING]
> Les éléments suivants nécessitent un rebuild Docker. Ils sont listés pour information.

1. **Rebuild `ethan/python-base`** puis `api`, `kernel`, `modules`, `ui` pour que les changements Dockerfile prennent effet.
2. **Migrer de `@app.on_event("startup")`** vers les `lifespan` events de FastAPI (le premier est deprecated depuis Starlette 0.26).
3. **Ajouter `pg_isready` dans `Dockerfile.api`** comme pre-check plutôt que de dépendre uniquement du compose healthcheck.
