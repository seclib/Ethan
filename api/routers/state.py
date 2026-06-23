"""State router — expose kernel state to interfaces."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from nats.aio.client import Client as NatsClient

from api.models.state_response import StateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["state"])

_nats: NatsClient | None = None


def set_nats_client(client: NatsClient):
    global _nats
    _nats = client


async def get_nats() -> NatsClient | None:
    return _nats


@router.get("/state", response_model=StateResponse)
async def get_state() -> StateResponse:
    """Return current kernel state."""
    return StateResponse(
        mode="idle",
        modules_active=["cli", "api"],
    )