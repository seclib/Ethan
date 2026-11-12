"""HTTP checks for user identity fallback hardening."""

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
    set_capability_managers(
        CapabilityManagers(notes=NoteStore(store=CoreRecordStore()))
    )
    async def _user_record(username: str):
        return {"username": username, "roles": ["user"], "is_active": True}
    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", _user_record)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client
    set_capability_managers(None)


def _auth(user: str) -> dict:
    token = create_access_token({"sub": user, "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def test_cross_user_creation_is_denied(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("alice"),
        json={"title": "x", "content": "y", "user_id": "bob"},
    )
    assert response.status_code == 403


def test_note_creation_uses_authenticated_identity(client):
    response = client.post(
        "/v1/notes",
        headers=_auth("alice"),
        json={"title": "x", "content": "y", "user_id": "bob"},
    )
    assert response.status_code == 403


def test_unauthenticated_route_is_refused(client):
    response = client.get("/v1/notes")
    assert response.status_code == 401
