"""PostgreSQL integration tests for durable service audit idempotency."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tests.test_config_persistence as cfg

_DSN = cfg._dsn()
if _DSN:
    os.environ["DATABASE_URL"] = _DSN
os.environ.setdefault("AUDIT_STORAGE_BACKEND", "postgres")

import asyncio
import concurrent.futures
import uuid

import pytest

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, set_service_identity_manager
from interfaces.api.routers import internal as internal_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

def _pg_available() -> bool:
    return bool(_DSN and cfg._pg_available())

pytestmark = pytest.mark.skipif(not _pg_available(), reason="PostgreSQL not available")


def _make_service_token() -> str:
    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("audit-writer", "audit", ["audit.events.write"]))
    return asyncio.run(manager.issue_token("audit-writer", allowed_operations=["audit.events.write"])), manager


@pytest.fixture(autouse=True)
def _clean_pg():
    async def _clear():
        import asyncpg

        pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM service_audit_events WHERE event_id LIKE 'pgint-%'")
            await conn.execute("DELETE FROM audit_log WHERE id LIKE 'aud_%'")
        await pool.close()

    asyncio.run(_clear())
    yield
    asyncio.run(_clear())


@pytest.fixture()
def pg_service_client(monkeypatch):
    token, manager = _make_service_token()
    internal_router.init_modules(pg_conn=None, publish_fn=None)
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    set_service_identity_manager(manager)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(internal_router.router)
    with TestClient(app) as client:
        yield client, token, manager
    set_service_identity_manager(None)


def _event(event_id: str, event_type: str = "x"):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": "2026-11-02T06:00:00Z",
        "resource_type": "service",
        "severity": "info",
        "details": {"message": "hello"},
    }


def test_pg_first_event_accepted(pg_service_client):
    client, token, manager = pg_service_client
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/internal/services/audit-events", headers=headers, json=_event("pgint-1"))
    assert response.status_code == 200
    assert response.json()["status"] == "created"


def test_pg_duplicate_event(pg_service_client):
    client, token, manager = pg_service_client
    headers = {"Authorization": f"Bearer {token}"}
    first = client.post("/internal/services/audit-events", headers=headers, json=_event("pgint-2"))
    second = client.post("/internal/services/audit-events", headers=headers, json=_event("pgint-2"))
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"


def test_pg_conflicting_event(pg_service_client):
    client, token, manager = pg_service_client
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/internal/services/audit-events", headers=headers, json=_event("pgint-3"))
    response = client.post(
        "/internal/services/audit-events",
        headers=headers,
        json=_event("pgint-3", event_type="changed"),
    )
    assert response.status_code == 409


def test_pg_direct_counts(pg_service_client):
    client, token, manager = pg_service_client
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/internal/services/audit-events", headers=headers, json=_event("pgint-4"))
    import asyncpg

    async def counts():
        pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) AS c FROM service_audit_events WHERE event_id = 'pgint-4'")
            audit = await conn.fetchrow("SELECT COUNT(*) AS c FROM audit_log WHERE id = (SELECT audit_entry_id FROM service_audit_events WHERE event_id='pgint-4')")
        await pool.close()
        return int(row["c"]), int(audit["c"])

    event_count, audit_count = asyncio.run(counts())
    assert event_count == 1
    assert audit_count == 1


def test_pg_multi_instance_concurrency(pg_service_client):
    client, token, manager = pg_service_client
    app2 = None
    from fastapi import FastAPI

    app2 = FastAPI()
    app2.middleware("http")(auth_middleware)
    app2.include_router(internal_router.router)
    set_service_identity_manager(manager)
    client2 = TestClient(app2)

    headers = {"Authorization": f"Bearer {token}"}
    payload = _event("pgint-cross")
    event_id = payload["event_id"]

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(client.post, "/internal/services/audit-events", headers=headers, json=payload)
        f2 = executor.submit(client2.post, "/internal/services/audit-events", headers=headers, json=payload)
        r1 = f1.result()
        r2 = f2.result()

    statuses = {r1.status_code, r2.status_code}
    combined = {r1.json()["status"], r2.json()["status"]}
    assert statuses == {200}
    assert combined == {"created", "duplicate"}

    async def count():
        import asyncpg

        pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=1)
        async with pool.acquire() as conn:
            c = await conn.fetchval("SELECT COUNT(*) FROM service_audit_events WHERE event_id = $1", event_id)
            a = await conn.fetchval("SELECT COUNT(*) FROM audit_log WHERE id = (SELECT audit_entry_id FROM service_audit_events WHERE event_id=$1)", event_id)
        await pool.close()
        return int(c), int(a)

    event_count, audit_count = asyncio.run(count())
    assert event_count == 1
    assert audit_count == 1
