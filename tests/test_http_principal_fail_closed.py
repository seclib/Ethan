"""Fail-closed principal and RBAC tests through HTTP middleware."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.state.notes import NoteStore
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, create_access_token
from interfaces.api.routers.capabilities import CapabilityManagers, router, set_capability_managers


@pytest.fixture()
def client(monkeypatch):
    set_capability_managers(CapabilityManagers(notes=NoteStore(store=CoreRecordStore())))

    async def user_record(username: str):
        if username == "persistent-admin":
            return {"username": username, "roles": ["admin"], "is_active": True}
        if username == "persistent-standard":
            return {"username": username, "roles": ["standard"], "is_active": True}
        if username == "downgraded-admin":
            return {"username": username, "roles": ["standard"], "is_active": True}
        return {"username": username, "roles": ["standard"], "is_active": True}

    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", user_record)
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client
    set_capability_managers(None)


def _auth(user: str, role: str = "user") -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user, 'role': role})}"}


def test_jwt_admin_claim_cannot_override_persistent_standard(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("persistent-standard", "admin"),
        json={"title": "x", "content": "y", "user_id": "other-user"},
    )
    assert response.status_code == 403


def test_downgraded_admin_retains_no_privilege(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("downgraded-admin", "admin"),
        json={"title": "x", "content": "y", "user_id": "other-user"},
    )
    assert response.status_code == 403


def test_persistent_admin_retains_authorized_operation(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("persistent-admin", "admin"),
        json={"title": "x", "content": "y", "user_id": "persistent-standard"},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == "persistent-standard"


def test_unavailable_persistent_source_refuses_privileged_operation(monkeypatch):
    set_capability_managers(CapabilityManagers(notes=NoteStore(store=CoreRecordStore())))

    async def unavailable(_username: str):
        return None

    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", unavailable)
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(router)
    with TestClient(app) as test_client:
        response = test_client.post(
            "/v1/notes",
            headers=_auth("persistent-admin", "admin"),
            json={"title": "x", "content": "y", "user_id": "persistent-standard"},
        )
    set_capability_managers(None)
    assert response.status_code == 401
