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


def test_local_repositories_without_auth():
    client = TestClient(app)
    response = client.get("/v1/local-repositories")
    assert response.status_code in (401, 403)


def test_local_repositories_authenticated(admin_token):
    client = TestClient(app)
    response = client.get("/v1/local-repositories", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    entries = response.json()
    assert isinstance(entries, list)
    assert len(entries) > 0
    assert any(entry["path"] == "Ethan" for entry in entries)
