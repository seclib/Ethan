from __future__ import annotations

import pytest
from core.cti import CTIManager
from core.state import CoreRecordStore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from interfaces.api.auth import auth_middleware, create_access_token
from interfaces.api.routers import cti as cti_router


@pytest.fixture()
def client():
    cti_router.set_cti_manager(CTIManager(CoreRecordStore()))
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(cti_router.router)
    with TestClient(app) as test_client:
        yield test_client
    cti_router.set_cti_manager(None)


def _auth(role: str = "user", user_id: str = "alice") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_cti_api_requires_ethan_authentication(client):
    response = client.get("/v1/cti/status")
    assert response.status_code == 401


def test_manifest_and_status_use_the_core_cti_manager(client):
    headers = _auth()
    manifest = client.get("/v1/cti/manifest", headers=headers)
    status = client.get("/v1/cti/status", headers=headers)

    assert manifest.status_code == 200
    assert manifest.json()["route"] == "/tools/cti"
    assert status.status_code == 200
    assert status.json()["service"] == "ethan-cti"


def test_cti_crud_is_permission_gated_and_user_scoped(client):
    viewer_headers = _auth("viewer")
    denied = client.post(
        "/v1/cti/objects",
        headers=viewer_headers,
        json={"type": "malware", "name": "Denied"},
    )
    assert denied.status_code == 403

    created = client.post(
        "/v1/cti/objects",
        headers=_auth(),
        json={"type": "malware", "name": "Sample"},
    )
    assert created.status_code == 201
    stix_id = created.json()["id"]

    listed = client.get("/v1/cti/objects", headers=_auth()).json()
    assert listed["count"] == 1
    assert listed["items"][0]["stix_object"]["id"] == stix_id
    assert client.get("/v1/cti/objects", headers=_auth("viewer", "bob")).json()["count"] == 0


def test_invalid_objects_return_422_and_duplicates_return_409(client):
    headers = _auth()
    invalid = client.post(
        "/v1/cti/objects",
        headers=headers,
        json={"type": "indicator", "spec_version": "2.0"},
    )
    assert invalid.status_code == 422

    payload = {
        "type": "malware",
        "id": "malware--00000000-0000-4000-8000-000000000001",
        "name": "Duplicate",
    }
    assert client.post("/v1/cti/objects", headers=headers, json=payload).status_code == 201
    duplicate = client.post("/v1/cti/objects", headers=headers, json=payload)
    assert duplicate.status_code == 409
