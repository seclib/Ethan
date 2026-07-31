"""API Gateway — entry point for the Ethan Cognitive OS.

NOTE: This file relies on the 'ethan' package being installed in editable mode:
    pip install -e ".[server]"

If you encounter import errors, run the command above from the project root.
"""

from __future__ import annotations

import json
import logging
import os

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

import nats

from interfaces.api.routers.message import router as message_router, set_nats_client
from interfaces.api.routers.state import router as state_router
from interfaces.api.routers.internal import router as internal_router, init_modules
from interfaces.api.auth import auth_middleware, create_access_token
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

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

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


@app.on_event("startup")
async def startup():
    """Connect to NATS on startup."""
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"API Gateway connecting to NATS: {nats_url}")

    nc = await nats.connect(nats_url, name="api-gateway")
    set_nats_client(nc)
    logger.info("API Gateway connected to NATS")

    # Initialiser les nouveaux modules (Audit, Budget, Facts, Approval, SkillLab)
    init_modules(pg_conn=None)

    # Initialize OpenTelemetry if available
    if HAS_TELEMETRY:
        try:
            init_telemetry("ethan-api")
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry tracing enabled for API Gateway")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")


@app.post("/auth/login")
async def login(request: Request):
    """Login endpoint — returns a JWT token.

    In production, replace this with proper credential validation (API key, OAuth2, etc.).
    For development, accepts any valid JSON body with a 'username' field.
    Rate limited to 5 requests per minute.
    """
    import json

    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username", "developer")
    token = create_access_token(data={"sub": username, "role": "user"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
    }


@app.get("/health")
async def health():
    """Healthcheck endpoint used by Docker and scripts."""
    return {"status": "ok", "service": "api"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check verifying connectivity to dependencies."""
    import asyncio
    import os
    import json

    results = {}

    # NATS check
    try:
        import nats
        import asyncio
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")
        nc = await asyncio.wait_for(nats.connect(nats_url), timeout=2)
        await nc.close()
        results["nats"] = "connected"
    except Exception as e:
        results["nats"] = f"error: {e}"

    # Redis check
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = await aioredis.from_url(redis_url)
        pong = await r.ping()
        await r.close()
        results["redis"] = "connected" if pong else "error"
    except Exception as e:
        results["redis"] = f"error: {e}"

    # PostgreSQL check
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
        conn = await asyncpg.connect(db_url, timeout=2)
        await conn.close()
        results["postgresql"] = "connected"
    except Exception as e:
        results["postgresql"] = f"error: {e}"

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
        await nc.drain()
        logger.info("API Gateway NATS connection closed")