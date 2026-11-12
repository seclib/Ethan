"""Realtime router — authenticated WebSocket connection status.

The WebSocket is deliberately not a business-event relay in this security lot.
Authenticated clients may keep a connection and exchange keepalive packets, but
the server no longer subscribes them to NATS subjects or lets them choose
topics.  Removing arbitrary forwarding is what closes the realtime exposure
while session-level revocation remains a later independent lot.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from interfaces.api.auth import (
    normalized_ws_origins,
    verify_token_string,
    fetch_user_record,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["realtime"])

#: Maximum number of distinct client-driven subscriptions. Realtime currently
#: does not forward any business event, so all non-ping control messages are
#: peer events and are rejected explicitly rather than being turned into NATS
#: subscriptions.
_MAX_CLIENT_SUBSCRIPTIONS = 0


@dataclass(frozen=True)
class RealtimeIdentity:
    """Server-derived identity for a WebSocket connection.

    Only the server builds this value, from the validated JWT.  A client cannot
    override the subject, and there is no separate NATS identity stored here.
    """

    username: str
    role: str
    max_subscriptions: int = _MAX_CLIENT_SUBSCRIPTIONS


def _extract_ws_token(websocket: WebSocket) -> str | None:
    """Extract a JWT from query string, cookie, or Authorization header."""
    token = websocket.query_params.get("token")
    if token:
        return token
    cookie = websocket.cookies.get("ethan_token")
    if cookie:
        return cookie
    header = websocket.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.split(" ", 1)[1]
    return None


def _origin_is_allowed(websocket: WebSocket) -> bool:
    """Validate browser origin without allowing a wildcard fallback.

    A missing Origin header is accepted because non-browser clients (CLI,
    tests, integration harnesses) commonly do not send one.  Any explicit
    browser origin must be in the configured allow list.
    """
    origin = websocket.headers.get("origin")
    if not origin:
        return True
    allowed = normalized_ws_origins()
    return origin in allowed


async def _authenticate_websocket(websocket: WebSocket) -> RealtimeIdentity | None:
    """Authenticate before websocket.accept().

    This method returns None only after the socket has been closed.  Returning
    a value means the connection may be accepted; the token and account state
    have been checked against the same persisted state used by login.
    """
    if not _origin_is_allowed(websocket):
        await websocket.close(code=4403, reason="origin not allowed")
        return None

    token = _extract_ws_token(websocket)
    if not token:
        await websocket.close(code=4401, reason="authentication required")
        return None

    try:
        payload = await verify_token_string(token)
    except Exception:  # noqa: BLE001 - converted into protocol result
        await websocket.close(code=4401, reason="invalid token")
        return None

    username = str(payload.get("sub") or "").strip()
    role = str(payload.get("role") or "").strip()
    if not username or not role:
        await websocket.close(code=4401, reason="invalid identity")
        return None

    # API keys are intentionally rejected by this lot: their scope/RBAC model
    # is resolved independently and this realtime endpoint must not guess it.
    if role == "api-key":
        await websocket.close(code=4403, reason="permission required for realtime access")
        return None

    user_record = await fetch_user_record(username)
    if user_record is None:
        await websocket.close(code=4401, reason="account not found")
        return None
    if not bool(user_record.get("is_active", False)):
        await websocket.close(code=4403, reason="account disabled")
        return None

    return RealtimeIdentity(username=username, role=role)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """Authenticated realtime endpoint.

    This endpoint intentionally exposes no business NATS events.  It exists so
    that WebUI can establish and monitor an authenticated connection without
    the server forwarding arbitrary NATS subjects.
    """
    identity = await _authenticate_websocket(websocket)
    if identity is None:
        return

    await websocket.accept()
    await websocket.send_json(
        {
            "type": "connected",
            "contract_version": "2026-ws-auth-1",
            "user": identity.username,
            "role": identity.role,
        }
    )
    logger.info("Realtime WebSocket opened for user '%s'", identity.username)

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                if raw_message == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                await websocket.send_json(
                    {"type": "error", "code": "WS_BAD_MESSAGE", "detail": "invalid JSON"}
                )
                continue

            message_type = str(message.get("type") or "").strip()
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif message_type == "subscribe":
                # No client-provided topic may become a NATS subscription.
                # The server intentionally owns the forwards contract; this field
                # is rejected rather than ignored so clients fail visibly.
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "WS_TOPIC_DENIED",
                        "detail": "client-controlled topics are not allowed",
                    }
                )
            elif message_type == "unsubscribe":
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "WS_TOPIC_DENIED",
                        "detail": "client-controlled topics are not allowed",
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "WS_UNKNOWN_TYPE",
                        "detail": f"unsupported message type: {message_type or '<empty>'}",
                    }
                )
    except WebSocketDisconnect:
        logger.info("Realtime WebSocket disconnected for user '%s'", identity.username)
    except Exception as exc:  # noqa: BLE001 - no VM process may be killed by a WS
        logger.warning("Realtime WebSocket error for user '%s': %s", identity.username, exc)
    finally:
        # There are no background NATS subscriptions in this lot, so cleanup
        # is limited to closing an already-accepted connection. Retaining the
        # explicit finally makes the cleanup point obvious when V2 handlers
        # add long-lived tasks.
        pass
