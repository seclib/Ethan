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


def test_application_runtime_unknown(admin_token):
    client = TestClient(app)
    response = client.get("/v1/applications/definitely-missing/runtime", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404


def test_application_runtime_known_state(admin_token):
    client = TestClient(app)
    response = client.get("/v1/applications/odin/runtime", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["app_id"] == "odin"
    assert body["state"] in {"running", "installed_stopped", "starting", "stopping", "unhealthy", "failed", "unsupported"}
    assert "healthy" in body
    assert "container_id" in body


def test_application_runtime_no_auth():
    client = TestClient(app)
    response = client.get("/v1/applications/odin/runtime")
    assert response.status_code in (401, 403)
