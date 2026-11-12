"""Authentification et politique d'abonnement du WebSocket realtime.

Ces tests couvrent le lot 1B : connexion authentifiée avant ``accept``,
refus des connexions anonymes/invalides, et refus des sujets clients.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi", reason="openjarvis[server] not installed")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from interfaces.api.auth import create_access_token
from interfaces.api.routers.realtime import router

TEST_ORIGIN = "http://testserver"
DEFAULT_USER = "ethan-tester"


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    application = FastAPI()
    application.include_router(router)

    monkeypatch.setenv("ETHAN_ALLOWED_WS_ORIGINS", TEST_ORIGIN)

    async def user_record(username: str):
        if username != DEFAULT_USER:
            return None
        return {"username": username, "roles": ["standard"], "is_active": True}

    monkeypatch.setattr("interfaces.api.routers.realtime.fetch_user_record", user_record)
    return application


def _token(username: str = DEFAULT_USER, *, expires_delta: timedelta | None = None) -> str:
    data = {"sub": username, "role": "standard"}
    if expires_delta is None:
        return create_access_token(data=data)
    return create_access_token(data=data, expires_delta=expires_delta)


def test_anonymous_connection_is_rejected(app: FastAPI):
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/v1/ws") as websocket:
            websocket.receive_json()


def test_invalid_token_is_rejected(app: FastAPI):
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/v1/ws?token=not-a-token") as websocket:
            websocket.receive_json()


def test_expired_token_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token(expires_delta=timedelta(seconds=-1))
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/ws?token={token}") as websocket:
            websocket.receive_json()


def test_unknown_user_is_rejected(app: FastAPI, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "interfaces.api.routers.realtime.fetch_user_record",
        lambda username: __import__("asyncio").coroutine(lambda user: None)(username),
    )

    # Keep the test simple and deterministic with an explicit coroutine.
    async def missing_user(_username: str):
        return None

    monkeypatch.setattr(
        "interfaces.api.routers.realtime.fetch_user_record", missing_user
    )

    client = TestClient(app)
    token = _token("missing-user")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
            websocket.receive_json()


def test_disabled_user_is_rejected(app: FastAPI, monkeypatch: pytest.MonkeyPatch):
    async def disabled_user(_username: str):
        return {"username": DEFAULT_USER, "roles": ["standard"], "is_active": False}

    monkeypatch.setattr(
        "interfaces.api.routers.realtime.fetch_user_record", disabled_user
    )
    client = TestClient(app)
    token = _token()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
            websocket.receive_json()


def test_valid_token_is_accepted(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
        payload = websocket.receive_json()
    assert payload["type"] == "connected"
    assert payload["user"] == DEFAULT_USER
    assert payload["contract_version"] == "2026-ws-auth-1"


def test_arbitrary_subscription_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "subscribe", "channel": "ethan.cti.object.created"})
        payload = websocket.receive_json()
    assert payload["type"] == "error"
    assert payload["code"] == "WS_TOPIC_DENIED"
    assert payload["detail"] == "client-controlled topics are not allowed"


def test_wildcard_subscription_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "subscribe", "channel": "ethan.>"})
        payload = websocket.receive_json()
    assert payload["type"] == "error"
    assert payload["code"] == "WS_TOPIC_DENIED"


def test_invalid_json_is_rejected_safely(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
        websocket.receive_json()
        websocket.send_text("not-json")
        payload = websocket.receive_json()
    assert payload["code"] == "WS_BAD_MESSAGE"


def test_connection_keeps_ping_pong(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/ws?token={token}", headers={"origin": TEST_ORIGIN}) as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "ping"})
        payload = websocket.receive_json()
    assert payload["type"] == "pong"


def test_unauthorized_origin_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/v1/ws?token={token}", headers={"origin": "https://attacker.example"}
        ) as websocket:
            websocket.receive_json()
