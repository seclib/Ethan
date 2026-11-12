import os
import tempfile
from pathlib import Path

import interfaces.api.auth as auth
import interfaces.api.routers.local_repositories as lr
import pytest
from core.state.record_store import CoreRecordStore
from core.applications.application_registry import ApplicationIntegrationRegistry
from fastapi.testclient import TestClient
from interfaces.api.main import app

VALID_MANIFEST = """identity:
  app_id: demo-app
  instance_id: i
  name: Demo
  version: 1.0.0
  contract_version: 1.0.0
  publisher: P
  manifest_version: 1
capabilities:
  - name: application.health.read
    description: Health
"""

@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch, tmp_path):
    root = Path(tmp_path) / "root"
    repo = root / "demo"
    repo.mkdir(parents=True)
    (repo / ".git").mkdir()
    (repo / "ethan-application-manifest.yaml").write_text(VALID_MANIFEST)
    os.environ["ETHAN_LOCAL_REPOSITORY_ROOT"] = str(root)
    monkeypatch.setattr(lr, "_APPLICATION_REGISTRY", ApplicationIntegrationRegistry())

    monkeypatch.setattr(lr, "_local_discovery_root", lambda: root)
    # clear lazy roots
    return root


@pytest.fixture
def admin_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "alice", "role": "admin"})


def test_compatibility(admin_token):
    client = TestClient(app)
    response = client.get("/v1/local-repositories/demo/compatibility", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_register_without_approval(admin_token):
    client = TestClient(app)
    response = client.post("/v1/local-repositories/demo/register", json={"approved": False}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 403


def test_register_valid_repository(admin_token):
    client = TestClient(app)
    response = client.post("/v1/local-repositories/demo/register", json={"approved": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "registered"
    assert body["app_id"] == "demo-app"

    repeat = client.post("/v1/local-repositories/demo/register", json={"approved": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "already_registered"
