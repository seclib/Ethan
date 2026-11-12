import interfaces.api.auth as auth
import pytest
from core.applications import ApplicationIntegrationRegistry, ApplicationManifest
from core.applications.permissions import HumanAuthority, PermissionService
from fastapi.testclient import TestClient
from interfaces.api.main import app
import interfaces.api.routers.applications as app_router

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

CAPABILITY = {
    "capability_id": "demo.runtime-status",
    "application_id": "demo-app",
    "name": "Runtime status",
    "invocation_interface": "internal",
    "input_schema": {"type": "object", "properties": {"hello": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"application": {"type": "string"}}},
    "required_permissions": ["execute"],
}


@pytest.fixture(autouse=True)
def isolated_registries(monkeypatch):
    awaitable = None
    monkeypatch.setattr(
        app_router, "_application_integration_registry", lambda: None, raising=False
    )

    async def register():
        registry = ApplicationIntegrationRegistry()
        registry.register(ApplicationManifest.from_mapping(VALID_MANIFEST))
        from core.applications.capability_contract import register_application_capability, ApplicationCapabilityContract
        register_application_capability(registry, ApplicationCapabilityContract.from_mapping(CAPABILITY), approved=True)
        return registry
    import asyncio
    registry = asyncio.run(register())
    monkeypatch.setattr(app_router, "_application_integration_registry", lambda: registry)
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


@pytest.fixture
def standard_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["standard"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "bob", "role": "standard", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "bob", "role": "standard"})


def test_bind_capability(admin_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities/demo.runtime-status/bind",
        json={"application_id": "demo-app", "implementation_alias": "odin.runtime-status", "approved": True, "activated": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "bound"
    assert body["binding"]["activated"] is True


def test_invoke_unbound_or_unknown(admin_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities/demo.runtime-status/invoke",
        json={"application_id": "demo-app", "input": {"hello": "world"}, "approved": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 424


def test_bind_and_execute_odin(admin_token, isolated_registries):
    client = TestClient(app)
    bind = client.post(
        "/v1/application-capabilities/demo.runtime-status/bind",
        json={"application_id": "demo-app", "implementation_alias": "odin.runtime-status", "approved": True, "activated": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert bind.status_code == 200

    # Create an HROT permission grant so invocation is authorized.
    registry = isolated_registries
    perm_svc: PermissionService = registry.permission_service
    authority = HumanAuthority(
        principal_id="approver",
        principal_type="HUMAN",
        trusted=True,
        human=True,
    )
    perm_svc.grant_permission(
        app_id="demo-app",
        instance_id="i",
        capability="demo.runtime-status",
        resource="capability",
        action="execute",
        approved_by="approver",
        authority=authority,
    )

    invoked = client.post(
        "/v1/application-capabilities/demo.runtime-status/invoke",
        json={"application_id": "demo-app", "input": {"hello": "world"}},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invoked.status_code == 200
    body = invoked.json()
    assert body["status"] == "success"
    assert body["result"]["application"] == "odin"


def test_invoke_without_hrot_grant_is_denied(admin_token, isolated_registries):
    """Invocation without an HROT permission grant is denied (fail-closed)."""
    client = TestClient(app)
    # Bind + activate but no permission grant → HROT denies.
    bind = client.post(
        "/v1/application-capabilities/demo.runtime-status/bind",
        json={"application_id": "demo-app", "implementation_alias": "odin.runtime-status", "approved": True, "activated": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert bind.status_code == 200

    invoked = client.post(
        "/v1/application-capabilities/demo.runtime-status/invoke",
        json={"application_id": "demo-app", "input": {"hello": "world"}},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invoked.status_code == 424
    body = invoked.json()
    assert "denied" in body["detail"].lower() or "failed" in body["detail"].lower()


def test_unauthorized_invocation(standard_token):
    client = TestClient(app)
    response = client.post(
        "/v1/application-capabilities/demo.runtime-status/invoke",
        json={"application_id": "demo-app", "input": {"hello": "world"}},
        headers={"Authorization": f"Bearer {standard_token}"},
    )
    assert response.status_code in (401, 403)

