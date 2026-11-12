"""HTTP provisioning tests for SERVICE identities with durable HROT."""

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

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, create_access_token, set_service_identity_manager
from interfaces.api.routers import internal as internal_router


@pytest.fixture()
def admin_client(monkeypatch):
    manager = ServiceIdentityManager(store=CoreRecordStore())
    internal_router.init_modules(pg_conn=None, publish_fn=None)

    async def _fetch(username): return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", _fetch)
    monkeypatch.setattr("interfaces.api.auth.get_service_identity_manager", lambda: manager)
    set_service_identity_manager(manager)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(internal_router.router)
    app.state.service_identity_manager = manager
    with TestClient(app) as client:
        yield client, manager
    set_service_identity_manager(None)


def _admin():
    return _approver()

def _requester():
    return {"Authorization": f"Bearer {create_access_token({'sub':'operator','role':'admin'})}"}

def _approver():
    return {"Authorization": f"Bearer {create_access_token({'sub':'admin','role':'admin'})}"}


def _request_approval(client, service_id, component="audit", allowed_operations=None, status="active"):
    allowed_operations = allowed_operations or ["audit.events.write"]
    params = {"service_id": service_id, "component": component, "allowed_operations": allowed_operations, "status": status}
    response = client.post(
        "/internal/hrot/requests",
        headers=_requester(),
        json={"service_id": service_id, "operation": "service.provision", "parameters": params, "ttl_seconds": 300},
    )
    approval_id = response.json()["approval_id"]
    client.post(
        f"/internal/hrot/requests/{approval_id}/resolve",
        headers=_approver(),
        json={"approved": True, "reason": "test"},
    )
    return approval_id


def test_create_service_by_admin(admin_client):
    client, manager = admin_client
    approval_id = _request_approval(client, "svc-prov")
    response = client.post(
        "/internal/services",
        headers={**_requester(), "X-HROT-Approval-Id": approval_id},
        json={"service_id": "svc-prov", "component": "audit", "allowed_operations": ["audit.events.write"]},
    )
    assert response.status_code == 201
    assert response.json()["service_id"] == "svc-prov"


def test_create_duplicate_conflict(admin_client):
    client, manager = admin_client
    approval_id = _request_approval(client, "dup")
    payload = {"service_id": "dup", "component": "audit", "allowed_operations": ["audit.events.write"]}
    assert client.post("/internal/services", headers={**_requester(), "X-HROT-Approval-Id": approval_id}, json=payload).status_code == 201
    approval_id_2 = _request_approval(client, "dup")
    assert client.post("/internal/services", headers={**_requester(), "X-HROT-Approval-Id": approval_id_2}, json=payload).status_code == 409


def test_non_admin_rejected(admin_client):
    client, manager = admin_client
    response = client.post("/internal/services", headers=_auth("alice", "standard") if False else {"Authorization": f"Bearer {create_access_token({'sub':'alice','role':'standard'})}"}, json={"service_id": "x", "component": "a", "allowed_operations": ["y"]})
    assert response.status_code in (401, 403)


def test_list_and_detail(admin_client):
    client, manager = admin_client
    approval_id = _request_approval(client, "detail-svc")
    client.post("/internal/services", headers={**_requester(), "X-HROT-Approval-Id": approval_id}, json={"service_id": "detail-svc", "component": "audit", "allowed_operations": ["audit.events.write"]})
    listing = client.get("/internal/services", headers=_requester())
    assert listing.status_code == 200
    assert any(item["service_id"] == "detail-svc" for item in listing.json())
    detail = client.get("/internal/services/detail-svc", headers=_requester())
    assert detail.status_code == 200
    assert detail.json()["service_id"] == "detail-svc"
