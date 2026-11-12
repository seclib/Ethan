import interfaces.api.auth as auth
import interfaces.api.routers.applications as app_router
import pytest
from core.applications import ApplicationIntegrationRegistry, ApplicationManifest
from core.applications.capability_contract import ApplicationCapabilityContract
from fastapi.testclient import TestClient
from interfaces.api.main import app

VALID_MANIFEST = {
    "identity": {
        "app_id": "demo-app",
        "instance_id": "i",
        "name": "Demo",
        "version": "1.0.0",
        "contract_version": "1.0.0",
        "publisher": "P",
        "manifest_version": 1,
    }
}


@pytest.fixture(autouse=True)
def isolated_registries(monkeypatch):
    registry = ApplicationIntegrationRegistry()
    registry.register(ApplicationManifest.from_mapping(VALID_MANIFEST))
    monkeypatch.setattr(app_router, "_APPLICATION_REGISTRY", registry)
    # Keep the same registry object for get/register operations.
    return registry


@pytest.fixture
def admin_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "alice", "role": "admin"})


def valid_contract():
    return {
        "capability_id": "demo.find-ports",
        "application_id": "demo-app",
        "name": "Find open ports",
        "category": "analysis",
        "invocation_interface": "application_api",
        "input_schema": {"type": "object", "properties": {"host": {"type": "string"}}},
        "output_schema": {"type": "object", "properties": {"ports": {"type": "array"}}},
        "required_permissions": ["read"],
    }


def test_validate_capability(admin_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities/validate",
        json={"application_id": "demo-app", "contract": valid_contract()},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_list_capabilities_before_registration(admin_token):
    # This endpoint uses a separate module singleton in the current design.
    # It is not the main registry path exercised below.
    client = TestClient(app)
    response = client.get("/v1/application-capabilities", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200


def test_register_capability(admin_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities",
        json={"application_id": "demo-app", "contract": valid_contract(), "approved": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "registered"
    assert body["capability_id"] == "demo.find-ports"


def test_register_without_approval(admin_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities",
        json={"application_id": "demo-app", "contract": valid_contract(), "approved": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403


def test_register_invalid_contract(admin_token):
    client = TestClient(app)
    contract = valid_contract()
    del contract["name"]
    response = client.post(
        "/v1/application-capabilities",
        json={"application_id": "demo-app", "contract": contract, "approved": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422
