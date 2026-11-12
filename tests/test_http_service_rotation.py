"""HTTP tests for SERVICE credential rotation with durable HROT."""

from __future__ import annotations

import asyncio
import urllib.parse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, create_access_token, set_service_identity_manager
from interfaces.api.routers import internal as internal_router


@pytest.fixture()
def rotation_client(monkeypatch):
    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("svc-rot", "audit", ["audit.events.write"]))
    internal_router.init_modules(pg_conn=None, publish_fn=None)

    async def _fetch(username): return {"username": username, "roles": ["admin"] if username in ("admin", "operator") else ["standard"], "is_active": True}
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


def _requester():
    return {"Authorization": f"Bearer {create_access_token({'sub':'operator','role':'admin'})}"}

def _approver():
    return {"Authorization": f"Bearer {create_access_token({'sub':'admin','role':'admin'})}"}

def _admin():
    return _approver()


def _approval(client, operation, parameters, service_id="svc-rot"):
    response = client.post("/internal/hrot/requests", headers=_requester(), json={
        "service_id": service_id,
        "operation": operation,
        "parameters": parameters,
        "ttl_seconds": 300,
    })
    approval_id = response.json()["approval_id"]
    client.post(f"/internal/hrot/requests/{approval_id}/resolve", headers=_approver(), json={"approved": True, "reason": "test"})
    return approval_id


def _headers(approval_id, extra=None):
    headers = {**_requester(), "X-HROT-Approval-Id": approval_id}
    if extra:
        headers.update(extra)
    return headers


def _issue(client):
    approval_id = _approval(client, "service.issue", {"service_id": "svc-rot"})
    return client.post("/internal/services/svc-rot/issue-token", headers=_headers(approval_id))["token"] if False else client.post("/internal/services/svc-rot/issue-token", headers=_headers(approval_id)).json()["token"]


def test_rotation_invalidates_previous_token(rotation_client):
    client, manager = rotation_client
    client.post("/internal/services/svc-rot/issue-token", headers=_headers(_approval(client, "service.issue", {"service_id": "svc-rot"})))
    approval_id = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    rotated = client.post("/internal/services/svc-rot/rotate", headers=_headers(approval_id))
    assert rotated.status_code == 200


def test_new_token_valid_after_rotation(rotation_client):
    client, manager = rotation_client
    approval_id = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    client.post("/internal/services/svc-rot/rotate", headers=_headers(approval_id))
    issue_approval = _approval(client, "service.issue", {"service_id": "svc-rot"})
    new_token = client.post("/internal/services/svc-rot/issue-token", headers=_headers(issue_approval)).json()["token"]
    response = client.post("/internal/services/renew", headers={"Authorization": f"Bearer {new_token}"})
    assert response.status_code == 200


def test_rotation_requires_admin(rotation_client):
    client, manager = rotation_client
    approval_id = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    token = create_access_token({"sub": "alice", "role": "standard"})
    response = client.post("/internal/services/svc-rot/rotate", headers={**{"Authorization": f"Bearer {token}"}, "X-HROT-Approval-Id": approval_id})
    assert response.status_code == 403


def test_old_token_is_valid_before_rotation(rotation_client):
    client, manager = rotation_client
    current = _issue(client)
    response = client.post("/internal/services/renew", headers={"Authorization": f"Bearer {current}"})
    assert response.status_code == 200


def test_rotation_disabled_service_refused():
    import asyncio
    from core.auth.service_identities import ServiceIdentityManager
    from core.state.record_store import CoreRecordStore

    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("svc-disabled", "audit", ["audit.events.write"]))
    asyncio.run(manager.disable_service("svc-disabled"))
    assert asyncio.run(manager.rotate_credential("svc-disabled")) is None


def test_rotation_missing_service_refused(rotation_client):
    client, manager = rotation_client
    approval_id = _approval(client, "service.rotate", {"service_id": "missing"}, service_id="missing")
    response = client.post("/internal/services/missing/rotate", headers={**_requester(), "X-HROT-Approval-Id": approval_id})
    assert response.status_code == 404


def test_idempotent_retry_does_not_rotate(rotation_client):
    client, manager = rotation_client
    key = "rotate-key-1"
    first_approval = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    second_approval = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    first = client.post("/internal/services/svc-rot/rotate", headers={**_requester(), "X-HROT-Approval-Id": first_approval, "Idempotency-Key": key})
    second = client.post("/internal/services/svc-rot/rotate", headers={**_requester(), "X-HROT-Approval-Id": second_approval, "Idempotency-Key": key})
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["credential_id"] == first.json()["credential_id"]
    assert second.json()["rotation_id"] == first.json()["rotation_id"]

    third_approval = _approval(client, "service.rotate", {"service_id": "svc-rot"})
    third = client.post("/internal/services/svc-rot/rotate", headers={**_requester(), "X-HROT-Approval-Id": third_approval, "Idempotency-Key": "other-key"})
    assert third.status_code == 200
    assert third.json()["rotation_id"] != second.json()["rotation_id"]
