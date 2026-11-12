"""HTTP tests for SERVICE token issue and renewal."""

from __future__ import annotations

import asyncio
import jwt as pyjwt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.service_identities import ServiceIdentityManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, create_access_token, set_service_identity_manager
from interfaces.api.routers import internal as internal_router


def _requester():
    from interfaces.api.auth import create_access_token
    return {"Authorization": f"Bearer {create_access_token({'sub':'operator','role':'admin'})}"}

def _approver():
    from interfaces.api.auth import create_access_token
    return {"Authorization": f"Bearer {create_access_token({'sub':'admin','role':'admin'})}"}

def _hrot_approval(client, operation):
    r = client.post("/internal/hrot/requests", headers=_requester(), json={"service_id": "svc-life", "operation": operation, "parameters": {"service_id": "svc-life"}, "ttl_seconds": 300})
    aid = r.json()["approval_id"]
    client.post(f"/internal/hrot/requests/{aid}/resolve", headers=_approver(), json={"approved": True, "reason": "test"})
    return aid

@pytest.fixture()
def app_and_manager(monkeypatch):
    manager = ServiceIdentityManager(store=CoreRecordStore())
    asyncio.run(manager.create_service("svc-life", "audit", ["audit.events.write", "service.token.renew"]))
    internal_router.init_modules(pg_conn=None, publish_fn=None)

    async def _fetch(username): return {"username": username, "roles": ["standard"] if username == "alice" else ["admin"], "is_active": True}
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


def _admin_headers():
    return {"Authorization": f"Bearer {create_access_token({'sub':'admin','role':'admin'})}"}


def test_issue_token(app_and_manager):
    client, manager = app_and_manager
    approval_id = _hrot_approval(client, "service.issue")
    response = client.post("/internal/services/svc-life/issue-token", headers={**_requester(), "X-HROT-Approval-Id": approval_id})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_renewal_preserves_credential_and_rotation(app_and_manager):
    client, manager = app_and_manager
    issued = client.post("/internal/services/svc-life/issue-token", headers={**_requester(), "X-HROT-Approval-Id": _hrot_approval(client, "service.issue")}).json()["token"]
    old_payload = pyjwt.decode(issued, manager.secret, algorithms=["HS256"], options={"verify_exp": False, "verify_aud": False, "verify_iss": False})
    renewed = client.post("/internal/services/renew", headers={"Authorization": f"Bearer {issued}"})
    assert renewed.status_code == 200
    new_payload = pyjwt.decode(renewed.json()["token"], manager.secret, algorithms=["HS256"], options={"verify_exp": False, "verify_aud": False, "verify_iss": False})
    assert new_payload["jti"] != old_payload["jti"]
    assert new_payload["credential_id"] == old_payload["credential_id"]
    assert new_payload["rotation_id"] == old_payload["rotation_id"]
    assert new_payload["allowed_operations"] == old_payload["allowed_operations"]


def test_renewal_refuses_human_token(app_and_manager):
    client, manager = app_and_manager
    human_token = create_access_token({"sub": "admin", "role": "admin"})
    response = client.post("/internal/services/renew", headers={"Authorization": f"Bearer {human_token}"})
    assert response.status_code in (401, 403)


def test_issue_requires_admin(app_and_manager):
    client, manager = app_and_manager
    response = client.post("/internal/services/svc-life/issue-token", headers={"Authorization": f"Bearer {create_access_token({'sub':'alice','role':'standard'})}"})
    assert response.status_code == 403


def test_renew_disabled_service_refused(app_and_manager, monkeypatch):
    client, manager = app_and_manager
    issued = client.post("/internal/services/svc-life/issue-token", headers={**_requester(), "X-HROT-Approval-Id": _hrot_approval(client, "service.issue")}).json()["token"]

    original_service_record = manager.service_record
    async def disabled_record(_service_id):
        record = await original_service_record("svc-life")
        record = dict(record or {})
        record["status"] = "disabled"
        return record

    monkeypatch.setattr(manager, "service_record", disabled_record)
    response = client.post("/internal/services/renew", headers={"Authorization": f"Bearer {issued}"})
    assert response.status_code == 401


def test_issue_and_renew_registry_unavailable(app_and_manager, monkeypatch):
    client, manager = app_and_manager
    from core.auth.service_identities import ServiceRegistryUnavailable

    async def unavailable(_service_id):
        raise ServiceRegistryUnavailable("db down")

    monkeypatch.setattr(manager, "service_record", unavailable)
    approval_id = _hrot_approval(client, "service.issue")
    response = client.post("/internal/services/svc-life/issue-token", headers={**_requester(), "X-HROT-Approval-Id": approval_id})
    assert response.status_code == 503
