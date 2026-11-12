"""HTTP-to-principal identity construction (READ-ONLY verification scope)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

import pytest
from starlette.requests import Request

from core.auth.api_keys import APIKeyManager
from core.auth.principal import AgentPrincipal, PrincipalType
from core.state.record_store import CoreRecordStore

pytest.importorskip("fastapi")


def _req(cookie: str | None = None, authorization: str | None = None, headers=None):
    h = []
    if cookie:
        h.append((b"cookie", f"ethan_token={cookie}".encode()))
    if authorization:
        h.append((b"authorization", authorization.encode()))
    if headers:
        for key, value in headers:
            h.append((key.encode(), value.encode()))
    return Request({"type": "http", "path": "/", "headers": h, "client": ("test", 1)})


@pytest.mark.asyncio
async def test_jwt_active_user_builds_human_principal(monkeypatch):
    import interfaces.api.auth as auth

    async def fake_fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": True}

    monkeypatch.setattr(auth, "fetch_user_record", fake_fetch)
    scope = {"sub": "alice", "role": "standard", "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()}
    monkeypatch.setattr(auth, "verify_token_string", lambda token: scope)
    # Middleware sets token; emulate authenticating request state minimally.
    req = _req(cookie="jwt-token")
    req.state.token_payload = scope
    req.state.user = "alice"
    principal = await auth.build_agent_principal(req)
    assert isinstance(principal, AgentPrincipal)
    assert principal.principal_type is PrincipalType.HUMAN
    assert principal.permissions == tuple(auth._permission_names("standard"))


@pytest.mark.asyncio
async def test_jwt_inactive_user_is_rejected(monkeypatch):
    import interfaces.api.auth as auth

    async def fake_fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": False}

    monkeypatch.setattr(auth, "fetch_user_record", fake_fetch)
    monkeypatch.setattr(auth, "verify_token_string", lambda token: {"sub": "alice", "role": "standard", "exp": 9999999999})
    req = _req(cookie="jwt-token")
    req.state.user = "alice"
    req.state.token_payload = {"sub": "alice", "role": "standard", "exp": 9999999999}
    assert await auth.build_agent_principal(req) is None


@pytest.mark.asyncio
async def test_jwt_expired_is_rejected(monkeypatch):
    import interfaces.api.auth as auth

    async def fake_fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}

    monkeypatch.setattr(auth, "fetch_user_record", fake_fetch)
    monkeypatch.setattr(auth, "verify_token_string", lambda token: {"sub": "alice", "role": "admin", "exp": 1})
    req = _req(cookie="jwt-token")
    req.state.user = "alice"
    req.state.token_payload = {"sub": "alice", "role": "admin", "exp": 1}
    assert await auth.build_agent_principal(req) is None


@pytest.mark.asyncio
async def test_api_key_active_builds_api_key_principal(monkeypatch):
    import interfaces.api.auth as auth

    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    key = await manager.create_key(user_id="svc", scopes=["execute", "read"])
    auth.set_api_key_manager(manager)
    req = _req(cookie=key["key"])  # cookie path low level
    req.state.user = key["user_id"]
    req.state.token_payload = {"sub": key["user_id"], "role": "api-key", "exp": None}
    # Direct raw key should be resolved from cookie.
    principal = await auth.build_agent_principal(req)
    assert isinstance(principal, AgentPrincipal)
    assert principal.principal_type is PrincipalType.API_KEY
    assert principal.permissions == ("execute", "read")
    assert principal.owner_id == "svc"


@pytest.mark.asyncio
async def test_api_key_revoked_is_rejected(monkeypatch):
    import interfaces.api.auth as auth

    store = CoreRecordStore()
    manager = APIKeyManager(store=store)
    key = await manager.create_key(user_id="svc", scopes=["read"])
    await manager.revoke_key(key["id"])
    auth.set_api_key_manager(manager)
    req = _req(authorization=f"Bearer {key['key']}")
    req.state.user = "api-key"
    req.state.token_payload = {"sub": "svc", "role": "api-key"}
    assert await auth.build_agent_principal(req) is None
