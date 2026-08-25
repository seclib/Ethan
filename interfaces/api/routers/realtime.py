"""Realtime router — WebSocket ↔ NATS bridge."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from interfaces.api.routers.message import _nats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["realtime"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str | None = None):
    """WebSocket endpoint bridging client with NATS topics."""
    await websocket.accept()
    
    if not _nats or not _nats.is_connected:
        await websocket.close(code=1011, reason="NATS disconnected")
        return

    # Default topics are always bridged.  The client can additionally
    # subscribe/unsubscribe per channel via JSON messages:
    #   {"type": "subscribe",   "channel": "ethan.chat.message"}
    #   {"type": "unsubscribe", "channel": "ethan.chat.message"}
    topics = [
        "ethan.chat.message",
        "ethan.agent.execution",
        "ethan.system.health"
    ]
    active_topics: set[str] = set(topics)

    subscriptions = []
    queue = asyncio.Queue()

    async def nats_handler(msg):
        # Forward NATS message to async queue
        await queue.put((msg.subject, msg.data))

    async def ensure_subscriptions():
        """Subscribe to any active topic that is not yet subscribed."""
        for topic in list(active_topics):
            if all(getattr(sub, "_subject", None) != topic for sub in subscriptions):
                sub = await _nats.subscribe(topic, cb=nats_handler)
                subscriptions.append(sub)

    try:
        await ensure_subscriptions()

        # Forward NATS events to WebSocket
        async def forward_to_ws():
            while True:
                subject, data = await queue.get()
                try:
                    # Skip topics the client has unsubscribed from.
                    if subject not in active_topics:
                        continue

                    payload = json.loads(data.decode())
                    
                    # Filter by session_id if required and present
                    if session_id:
                        evt_session = payload.get("metadata", {}).get("session_id")
                        if evt_session and evt_session != session_id:
                            continue
                            
                    await websocket.send_json({
                        "topic": subject,
                        "payload": payload
                    })
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding message to WS: {e}")

        # Keep connection alive and handle incoming WS messages.
        # The ETHAN WebUI client speaks JSON: {"type":"ping|subscribe|unsubscribe"}.
        async def read_from_ws():
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    # Legacy raw "ping" text — respond with JSON pong.
                    if data == "ping":
                        await websocket.send_json({"type": "pong"})
                    continue

                msg_type = msg.get("type")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "subscribe":
                    channel = msg.get("channel")
                    if channel:
                        active_topics.add(channel)
                        await ensure_subscriptions()
                elif msg_type == "unsubscribe":
                    channel = msg.get("channel")
                    if channel:
                        active_topics.discard(channel)

        forward_task = asyncio.create_task(forward_to_ws())
        read_task = asyncio.create_task(read_from_ws())

        done, pending = await asyncio.wait(
            [forward_task, read_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected (session_id={session_id})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        for sub in subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
