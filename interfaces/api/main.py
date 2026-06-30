"""API Gateway — Entry point for the Ethan Cognitive OS."""

from __future__ import annotations

import json
import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nats

from api.routers import message as message_router
from api.routers import state as state_router
from api.routers.internal import router as internal_router, init_modules
from kernel.telemetry.logger import setup_logging

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
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"API Gateway connecting to NATS: {nats_url}")

    nc = await nats.connect(nats_url, name="api-gateway")
    message_router.set_nats_client(nc)
    logger.info("API Gateway connected to NATS")

    # Initialiser les nouveaux modules (Audit, Budget, Facts, Approval, SkillLab)
    init_modules(pg_conn=None)


@app.on_event("shutdown")
async def shutdown():
    """Close NATS on shutdown."""
    nc = message_router._nats
    if nc:
        await nc.drain()
        logger.info("API Gateway NATS connection closed")