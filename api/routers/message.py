"""Message router — Receives user input, emits event to NATS."""

from __future__ import annotations

import logging
import os
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from nats.aio.client import Client as NatsClient

from api.models.requests import MessageRequest, MessageResponse, IntentRequest
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["messages"])

# Global NATS client — initialized at startup
_nats: NatsClient | None = None


def set_nats_client(client: NatsClient):
    """Inject NATS client into the router."""
    global _nats
    _nats = client


@router.post("/message", response_model=MessageResponse)
async def post_message(request: MessageRequest) -> MessageResponse:
    """Receive a user message and emit it as an event into the cognitive system."""
    if not _nats:
        raise HTTPException(status_code=503, detail="NATS not connected")

    event_id = str(uuid4())
    session_id = request.session_id or str(uuid4())
    trace_id = str(uuid4())

    event = Event(
        id=event_id,
        type=EventType.INTENT_USER,
        source="api-gateway",
        data={
            "intent": {
                "source": "text",
                "user_input": request.input,
                "context": {},
            },
            "session_id": session_id,
        },
        metadata={
            "trace_id": trace_id,
            "session_id": session_id,
            "auth": {"user_id": request.user_id, "roles": ["user"]},
            "correlation_id": event_id,
        },
    )

    await _nats.publish("ethan.intent.user", event.dict())
    logger.info(f"Published intent event {event_id} for user {request.user_id}")

    return MessageResponse(
        success=True,
        event_id=event_id,
        goal_id="",
        message="Event emitted into cognitive system",
    )


@router.post("/intent", response_model=MessageResponse)
async def post_intent(request: IntentRequest) -> MessageResponse:
    """Receive a structured intent and emit it to the system."""
    if not _nats:
        raise HTTPException(status_code=503, detail="NATS not connected")

    event_id = str(uuid4())
    session_id = request.session_id or str(uuid4())
    trace_id = str(uuid4())

    event = Event(
        id=event_id,
        type=EventType.INTENT_USER,
        source="api-gateway",
        data={
            "intent": {
                "source": request.source,
                "user_input": request.input,
                "context": request.context,
            },
            "session_id": session_id,
        },
        metadata={
            "trace_id": trace_id,
            "session_id": session_id,
            "auth": {"user_id": request.user_id, "roles": ["user"]},
        },
    )

    await _nats.publish("ethan.intent.user", event.dict())

    return MessageResponse(
        success=True,
        event_id=event_id,
        message="Intent emitted into cognitive system",
    )


@router.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "service": "api-gateway",
        "nats_connected": _nats is not None and _nats.is_connected,
    }