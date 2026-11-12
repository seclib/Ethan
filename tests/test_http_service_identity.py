"""HTTP authentication tests for SERVICE identities."""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from core.auth.service_identities import (
    SERVICE_ALGORITHM,
    SERVICE_AUDIENCE,
    SERVICE_ISSUER,
    SERVICE_KEY_ID,
    ServiceIdentityManager,
    ServiceRegistryUnavailable,
    ServiceTokenValidator,
)
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import (
    auth_middleware,
    require_service_operation,
    set_service_identity_manager,
)


def _manager_and_token(operations=None):
    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("audit-writer", "audit", operations or ["audit.events.write"]))
    token = asyncio.run(manager.issue_token("audit-writer", allowed_operations=operations or ["audit.events.write"]))
    return manager, token


@pytest.fixture()
def service_app(monkeypatch):
    manager, token = _manager_and_token()
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    set_service_identity_manager(manager)

    app = FastAPI()
    app.middleware("http")(auth_middleware)

    @app.get("/service-resource")
    async def service_resource(request: Request, _: bool = Depends(require_service_operation("audit.events.write"))):
        principal = getattr(request.state, "principal", None)
        return {"principal": principal.to_dict() if principal else None}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        yield client, manager, token
    set_service_identity_manager(None)


def test_valid_service_token_is_propagated(service_app):
    client, manager, token = service_app
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()["principal"]
    assert body["principal_type"] == "SERVICE"
    assert body["subject_id"] == "audit-writer"
    assert "audit.events.write" in body["permissions"]


def test_missing_service_token_is_refused(service_app):
    client, manager, token = service_app
    response = client.get("/service-resource")
    assert response.status_code == 401


def test_service_token_without_required_operation_is_refused(service_app):
    client, manager, token = service_app
    other_manager = ServiceIdentityManager(store=manager._store)
    asyncio.run(other_manager.create_service("reader", "audit", ["audit.events.read"]))
    other_token = asyncio.run(other_manager.issue_token("reader", allowed_operations=["audit.events.read"]))
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403


def test_expired_service_token_is_refused(service_app):
    client, manager, token = service_app
    payload = dict(ServiceTokenValidator(registry=manager, signing_secret=manager.secret)._decode_without_verify(token) if False else {})
    expired = manager.__dict__
    # Build an expired token using the registry's issued credentials.
    record = asyncio.run(manager.service_record("audit-writer"))
    from datetime import datetime, timezone

    now = int(time.time())
    claims = {
        "typ": "service",
        "iss": "ethan.service",
        "aud": "ethan.internal",
        "sub": "audit-writer",
        "service_id": "audit-writer",
        "component": record["component"],
        "credential_id": record["credential_id"],
        "rotation_id": record["rotation_id"],
        "allowed_operations": ["audit.events.write"],
        "iat": now - 100,
        "exp": now - 1,
        "jti": "expired-jti",
    }
    bad = jose_jwt.encode(claims, manager.secret, algorithm="HS256", headers={"kid": "service-hmac-v1"})
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {bad}"})
    assert response.status_code == 401


def test_revoked_service_token_is_refused(service_app):
    client, manager, token = service_app
    asyncio.run(manager.revoke_service("audit-writer"))
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_human_token_is_not_accepted_as_service(service_app):
    from interfaces.api.auth import create_access_token

    client, manager, token = service_app
    human_token = create_access_token({"sub": "alice", "role": "admin"})
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {human_token}"})
    assert response.status_code in (401, 403)


def test_invalid_signature_is_refused(service_app):
    client, manager, token = service_app
    tampered = token[:-5] + "AAAAA"
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


def test_registry_unavailable_fails_closed(monkeypatch):
    manager, token = _manager_and_token()
    original_service_record = manager.service_record

    async def unavailable(_service_id):
        raise ServiceRegistryUnavailable("db down")

    monkeypatch.setattr(manager, "service_record", unavailable)
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    set_service_identity_manager(manager)

    app = FastAPI()
    app.middleware("http")(auth_middleware)

    @app.get("/service-resource")
    async def service_resource(request: Request, _: bool = Depends(require_service_operation("audit.events.write"))):
        principal = getattr(request.state, "principal", None)
        return {"principal": principal.to_dict() if principal else None}

    with TestClient(app) as client:
        response = client.get("/service-resource", headers={"Authorization": f"Bearer {token}"})
    set_service_identity_manager(None)
    assert response.status_code == 503

    # restore (not strictly needed)
    monkeypatch.setattr(manager, "service_record", original_service_record)


def test_service_principal_type_remains_service(service_app):
    client, manager, token = service_app
    response = client.get("/service-resource", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["principal"]["principal_type"] == "SERVICE"
