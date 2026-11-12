"""HTTP authorization checks routed through auth_middleware."""

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
    async def _user_record(username: str):
        role = "admin" if username == "admin" else "standard"
        return {"username": username, "roles": [role], "is_active": True}
    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", _user_record)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client
    set_capability_managers(None)


def _auth(user: str, role: str = "user") -> dict:
    token = create_access_token({"sub": user, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_standard_user_can_create_own_note(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("ethan-smoke", "standard"),
        json={"title": "x", "content": "y"},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == "ethan-smoke"


def test_admin_may_create_for_another_user(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("admin", "admin"),
        json={"title": "x", "content": "y", "user_id": "ethan-smoke"},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == "ethan-smoke"


def test_non_admin_targeting_another_user_is_refused(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("ethan-smoke", "standard"),
        json={"title": "x", "content": "y", "user_id": "admin"},
    )
    assert response.status_code == 403


def test_missing_identity_is_refused(client):
    response = client.post("/v1/notes", json={"title": "x", "content": "y"})
    assert response.status_code == 401
