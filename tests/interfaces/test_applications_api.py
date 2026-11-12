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


def test_list_applications_does_not_require_lifespan(admin_token):
    client = TestClient(app)
    response = client.get("/v1/applications", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    entries = response.json()
    assert isinstance(entries, list)
    app_ids = [entry["app_id"] for entry in entries]
    assert "odin" in app_ids or "frame" in app_ids
    if entries:
        assert "validated" in entries[0]
        assert "manifest_digest" in entries[0]


def test_list_applications_without_auth():
    client = TestClient(app)
    response = client.get("/v1/applications")
    assert response.status_code in (401, 403)


def test_refresh_applications_requires_admin(admin_token):
    client = TestClient(app)
    response = client.post("/v1/applications/refresh", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "refreshed"


def test_get_application_unknown_returns_404(admin_token):
    client = TestClient(app)
    response = client.get("/v1/applications/definitely-missing", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404


def test_get_application_known_returns_record(admin_token):
    client = TestClient(app)
    list_response = client.get("/v1/applications", headers={"Authorization": f"Bearer {admin_token}"})
    entries = list_response.json()
    assert entries
    app_id = entries[0]["app_id"]
    response = client.get(f"/v1/applications/{app_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["app_id"] == app_id
