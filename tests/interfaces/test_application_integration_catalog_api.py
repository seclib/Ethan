import interfaces.api.auth as auth
import pytest
from fastapi.testclient import TestClient
from interfaces.api.main import app


@pytest.fixture
def admin_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "alice", "role": "admin"})


def test_application_manifests_and_integration_catalog_live(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    client = TestClient(app)

    manifests = client.get("/v1/application-manifests", headers=headers)
    assert manifests.status_code == 200
    manifest_rows = manifests.json()["manifests"]
    comfy_manifests = [
        row for row in manifest_rows
        if row["manifest"]["identity"]["app_id"] == "comfyui"
        and row["validation_status"] == "valid"
    ]
    assert len(comfy_manifests) == 1

    catalog = client.get("/v1/application-integration/catalog", headers=headers)
    assert catalog.status_code == 200
    payload = catalog.json()
    comfy_items = [item for item in payload["items"] if item["repository_name"] == "ComfyUI"]
    assert len(comfy_items) == 1
    item = comfy_items[0]
    assert item["manifest_validation_status"] == "valid"
    assert item["states"]["validated"] is True
    assert item["application_type"] == "web_application"
    assert item["declared_capabilities"] == ["runtime-observation"]
