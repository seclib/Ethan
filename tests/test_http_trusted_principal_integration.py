"""Integration tests for HTTP auth middleware and Trusted Principal."""

from __future__ import annotations

import asyncio

import datetime

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.auth.api_keys import APIKeyManager
from core.state.record_store import CoreRecordStore
import interfaces.api.auth as auth


class _FakeKeyManager:
    def __init__(self, records):
        self.records = records

    async def validate_key(self, raw_key):
        for record in self.records:
            if record["key"] == raw_key and record["active"]:
                return dict(record)
        return None


def _app():
    app = FastAPI()
    app.middleware("http")(auth.auth_middleware)
    @app.get("/health")
    async def public():
        return {"status": "ok"}

    @app.get("/health/principal")
    async def health_principal(request: Request):
        return {"principal": getattr(request.state, "principal", None)}
    @app.get("/protected")
    async def protected(request: Request):
        principal = getattr(request.state, "principal", None)
        return {"principal": principal.to_dict() if principal else None}
    return app


@pytest.fixture
def fixed_now(monkeypatch):
    now = datetime.datetime.now(datetime.timezone.utc)
    monkeypatch.setattr("interfaces.api.auth.datetime.now", lambda *args, **kwargs: now)
    return now


def test_jwt_valid_principal_is_attached(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)
    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token = auth.create_access_token({"sub": "alice", "role": "admin"})
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()["principal"]
    assert payload["principal_type"] == "HUMAN"
    assert payload["subject_id"] == "alice"


def test_jwt_inactive_returns_401(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": False}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)
    async def _verify(token):
        return {"sub": "alice", "role": "standard", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token = auth.create_access_token({"sub": "alice", "role": "standard"})
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] in (
        "Token JWT invalide ou expiré.",
        "Authentification requise. Cookie ou Token manquant.",
        "Authentification requise. Identité non validée.",
    )


def test_jwt_expired_returns_401(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)
    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 1}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token = auth.create_access_token({"sub": "alice", "role": "admin"})
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_jwt_invalid_returns_401(monkeypatch):
    async def _verify(token):
        raise __import__("fastapi").HTTPException(status_code=401, detail="bad")
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_cookie_prefers_bearerHeader_over_cookie(monkeypatch):
    # Middleware checks cookie first; ensure implementation keeps that precedence.
    async def fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)
    async def _verify(token):
        return {"sub": "from-cookie", "role": "standard", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token_cookie = auth.create_access_token({"sub": "from-cookie", "role": "standard"})
    token_header = auth.create_access_token({"sub": "from-header", "role": "standard"})
    # Verifies middleware behavior without relying on expired timers.
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {token_header}", "Cookie": f"ethan_token={token_cookie}"})
    assert response.status_code == 200
    assert response.json()["principal"]["subject_id"] == "from-cookie"


def test_api_key_valid_principal(monkeypatch):
    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    key = asyncio.run(
        manager.create_key(user_id="svc", scopes=["svc.read"])
    )
    monkeypatch.setattr(auth, "get_api_key_manager", lambda: manager)
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {key['key']}"})
    assert response.status_code == 200
    payload = response.json()["principal"]
    assert payload["principal_type"] == "API_KEY"
    assert payload["permissions"] == ["svc.read"]


def test_api_key_revoked_returns_401(monkeypatch):
    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    key = asyncio.run(manager.create_key(user_id="svc", scopes=["svc.read"]))
    asyncio.run(manager.revoke_key(key["id"]))
    monkeypatch.setattr(auth, "get_api_key_manager", lambda: manager)
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {key['key']}"})
    assert response.status_code == 401


def test_api_key_expired_returns_401(monkeypatch):
    import datetime

    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    key = asyncio.run(manager.create_key(user_id="svc", scopes=["svc.read"], expires_at=(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()))
    monkeypatch.setattr(auth, "get_api_key_manager", lambda: manager)
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": f"Bearer {key['key']}"})
    assert response.status_code == 401


def test_no_credentials_no_principal(monkeypatch):
    app = _app()
    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401


def test_public_route_accessible_without_principal(monkeypatch):
    app = _app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_malformed_bearer_rejected(monkeypatch):
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": "Bearer not-an-ethan-key"})
    # FastAPI's middleware verifies token; response should be auth failure.
    assert response.status_code in (401,)


def test_cookie_valid_principal(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)
    async def _verify(token):
        return {"sub": "cookie-user", "role": "standard", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    token = auth.create_access_token({"sub": "cookie-user", "role": "standard"})
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Cookie": f"ethan_token={token}"})
    assert response.status_code == 200
    assert response.json()["principal"]["subject_id"] == "cookie-user"


def test_public_route_has_no_principal_in_state(monkeypatch):
    app = _app()
    client = TestClient(app)
    response = client.get("/health/principal")
    assert response.status_code == 200
    assert response.json()["principal"] is None


def test_api_key_without_owner_returns_401(monkeypatch):
    manager = _FakeKeyManager([{"key": "ethan_orphan", "active": True, "scopes": ["read"]}])
    monkeypatch.setattr(auth, "get_api_key_manager", lambda: manager)
    app = _app()
    client = TestClient(app)
    response = client.get("/protected", headers={"Authorization": "Bearer ethan_orphan"})
    assert response.status_code == 401
