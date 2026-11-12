"""Authentification et autorisation du WebSocket terminal.

Tests isolement sans PostgreSQL : fetch_user_record est monkeypatché, de
même que TerminalService lors du test de connexion autorisée.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

pytest.importorskip("fastapi", reason="openjarvis[server] not installed")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from interfaces.api.auth import create_access_token
from interfaces.api.routers import terminal as terminal_router_module
from interfaces.api.routers.terminal import router

DEFAULT_USER = "ethan-tester"


class FakeTerminalSession:
    def __init__(self, user: str):
        self.id = "term-1"
        self.user = user
        self.state = "EXITED"

    def to_dict(self) -> dict:
        return {"type": "session", "id": self.id, "user": self.user}


def _make_service(user: str = DEFAULT_USER) -> MagicMock:
    service = MagicMock()
    service.create.return_value = FakeTerminalSession(user)
    service.read.return_value = b""
    service._sessions = {}
    service.reap.return_value = None
    return service


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    application = FastAPI()
    application.include_router(router)

    async def user_record(username: str):
        if username != DEFAULT_USER:
            return None
        return {"username": username, "roles": ["admin"], "is_active": True}

    monkeypatch.setattr(terminal_router_module, "fetch_user_record", user_record)
    return application


def _token(username: str = DEFAULT_USER, *, role: str = "admin", expires_delta: timedelta | None = None):
    data = {"sub": username, "role": role}
    if expires_delta is None:
        return create_access_token(data=data)
    return create_access_token(data=data, expires_delta=expires_delta)


def test_terminal_anonymous_is_rejected(app: FastAPI):
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/v1/terminal/ws") as websocket:
            websocket.receive_json()


def test_terminal_invalid_token_is_rejected(app: FastAPI):
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/v1/terminal/ws?token=not-a-token") as websocket:
            websocket.receive_json()


def test_terminal_expired_token_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token(expires_delta=timedelta(seconds=-1))
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/terminal/ws?token={token}") as websocket:
            websocket.receive_json()


def test_terminal_unknown_user_is_rejected(app: FastAPI):
    async def missing_user(_username: str):
        return None

    import interfaces.api.auth as auth_module
    auth_module.fetch_user_record = missing_user

    client = TestClient(app)
    token = _token("missing-user")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/terminal/ws?token={token}") as websocket:
            websocket.receive_json()


def test_terminal_disabled_user_is_rejected(app: FastAPI):
    async def disabled_user(_username: str):
        return {"username": DEFAULT_USER, "roles": ["admin"], "is_active": False}

    import interfaces.api.auth as auth_module
    auth_module.fetch_user_record = disabled_user

    client = TestClient(app)
    token = _token()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/terminal/ws?token={token}") as websocket:
            websocket.receive_json()


def test_terminal_user_without_execute_is_rejected(app: FastAPI):
    client = TestClient(app)
    token = _token(role="standard")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/v1/terminal/ws?token={token}") as websocket:
            websocket.receive_json()


def test_terminal_authorized_is_accepted(app: FastAPI, monkeypatch: pytest.MonkeyPatch):
    from interfaces.api.routers import terminal as router_module
    router_module.set_terminal_service(_make_service())
    monkeypatch.setattr(router_module, "get_terminal_service", lambda: router_module._service)

    client = TestClient(app)
    token = _token()
    with client.websocket_connect(f"/v1/terminal/ws?token={token}") as websocket:
        payload = websocket.receive_json()
    assert payload["type"] == "session"
    assert payload["id"] == "term-1"
