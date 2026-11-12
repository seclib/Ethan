"""HTTP tests for the SERVICE-only audit events endpoint."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, set_service_identity_manager
from interfaces.api.routers import internal as internal_router


@pytest.fixture()
def service_client(monkeypatch):
    async def _clear_pg():
        try:
            import asyncpg
            import os

            dsn = os.getenv("DATABASE_URL")
            if not dsn:
                return
            pool = await asyncpg.create_pool(dsn, min_size=1, max_size=1)
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM service_audit_events WHERE event_id LIKE 'evt-%' OR event_id LIKE 'broken-%'")
            await pool.close()
        except Exception:
            pass

    asyncio.run(_clear_pg())

    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    token = asyncio.run(manager.issue_token("audit-writer", allowed_operations=["audit.events.write"]))
    internal_router.init_modules(pg_conn=None, publish_fn=None)
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    set_service_identity_manager(manager)

    from pathlib import Path

    registry_path = Path.home() / ".ethan" / "audit" / "service_audit_events.jsonl"
    registry_path.unlink(missing_ok=True)
    (registry_path.parent / "service_audit_events.lock").unlink(missing_ok=True)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(internal_router.router)
    with TestClient(app) as client:
        yield client, manager, token
    set_service_identity_manager(None)
    asyncio.run(_clear_pg())
    registry_path.unlink(missing_ok=True)


def _event(event_id="evt-1"):
    return {
        "event_id": event_id,
        "event_type": "service.test",
        "occurred_at": "2026-11-02T06:00:00Z",
        "resource_type": "service",
        "severity": "info",
        "details": {"message": "hello"},
    }


def test_valid_service_event_is_accepted(service_client):
    client, manager, token = service_client
    response = client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json=_event())
    assert response.status_code == 200
    assert response.json()["status"] == "created"


def test_duplicate_event_is_idempotent(service_client):
    client, manager, token = service_client
    first = client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json=_event())
    second = client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json=_event())
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"


def test_conflicting_event_id_returns_409(service_client):
    client, manager, token = service_client
    client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json=_event())
    response = client.post(
        "/internal/services/audit-events",
        headers={"Authorization": f"Bearer {token}"},
        json=_event(event_id="evt-1") | {"event_type": "changed"},
    )
    assert response.status_code == 409


def test_invalid_payload_returns_422(service_client):
    client, manager, token = service_client
    response = client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json={"event_id": "bad"})
    assert response.status_code == 422


def test_human_token_is_rejected(service_client):
    from interfaces.api.auth import create_access_token

    client, manager, token = service_client
    human_token = create_access_token({"sub": "alice", "role": "admin"})
    response = client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {human_token}"}, json=_event())
    assert response.status_code in (401, 403)


def test_missing_service_token_is_rejected(service_client):
    client, manager, token = service_client
    response = client.post("/internal/services/audit-events", json=_event())
    assert response.status_code == 401


def test_unavailable_registry_returns_503(monkeypatch, service_client):
    # Rebuild a client with a broken registry while preserving the issued token.
    from fastapi import FastAPI

    client, manager, token = service_client
    original_service_record = manager.service_record

    async def unavailable(_service_id):
        from core.auth.service_identities import ServiceRegistryUnavailable

        raise ServiceRegistryUnavailable("db down")

    monkeypatch.setattr(manager, "service_record", unavailable)
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    # token remains validated only until registry lookup, so unavailable storage
    # happens during request handling.

    # Use a fresh app wired with the same broken manager.
    from interfaces.api.auth import auth_middleware

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(internal_router.router)
    with TestClient(app) as broken_client:
        response = broken_client.post("/internal/services/audit-events", headers={"Authorization": f"Bearer {token}"}, json=_event(event_id="broken-1"))
    assert response.status_code == 503

    monkeypatch.setattr(manager, "service_record", original_service_record)
