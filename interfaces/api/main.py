"""API Gateway — Entry point for the Ethan Cognitive OS."""

from __future__ import annotations

import json
import logging
import os

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

import nats

from api.routers import message as message_router
from api.routers import state as state_router
from api.routers.internal import router as internal_router, init_modules

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PROMETHEUS = False

    def generate_latest(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("prometheus_client is not installed")

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ethan Cognitive OS API",
    version="0.2.0",
    description="Event-driven cognitive operating system API Gateway",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router.router)
app.include_router(state_router.router)
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
    message_router.set_nats_client(nc)
    logger.info("API Gateway connected to NATS")

    # Initialiser les nouveaux modules (Audit, Budget, Facts, Approval, SkillLab)
    init_modules(pg_conn=None)


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
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")
        nc = await nats.connect(nats_url, timeout=2)
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
    nc = message_router._nats
    if nc:
        await nc.drain()
        logger.info("API Gateway NATS connection closed")
