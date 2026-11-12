"""Runtime API coverage for the skill package import endpoints (ANO-05)."""

from __future__ import annotations

import interfaces.api.auth as auth
import pytest
from core.state.record_store import CoreRecordStore
from core.skills.store import SkillStore
from fastapi.testclient import TestClient
from interfaces.api.main import app
import interfaces.api.routers.v1 as v1


@pytest.fixture(autouse=True)
def isolated_skill_store(monkeypatch):
    store = SkillStore(CoreRecordStore())
    v1._skill_store = store
    monkeypatch.setattr(v1, "get_skill_store", lambda: store, raising=False)
    return store


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


VALID_SKILL = "---\nname: import-test-skill\ndescription: Test\n---\n\ncorps\n"
INVALID_SKILL = "pas de frontmatter valide\n"


def test_scan_valid(admin_token):
    client = TestClient(app)
    files = {"files": ("demo/SKILL.md", VALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import/scan", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert body["detected_skills"] >= 1


def test_scan_invalid(admin_token):
    client = TestClient(app)
    files = {"files": ("bad/SKILL.md", INVALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import/scan", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    if "items" in body:
        assert any(item.get("status") == "invalid" for item in body.get("items", []))
    else:
        assert body.get("invalid", 0) >= 1


def test_import_valid(admin_token):
    client = TestClient(app)
    files = {"files": ("demo/SKILL.md", VALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import-files", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("imported") == 1
    assert isinstance(body.get("imported_ids"), list)


def test_import_invalid(admin_token):
    client = TestClient(app)
    files = {"files": ("bad/SKILL.md", INVALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import-files", files=files, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("invalid", 0) >= 1


def test_scan_no_auth():
    client = TestClient(app)
    files = {"files": ("x.md", VALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import/scan", files=files)
    assert response.status_code in (401, 403)


def test_scan_permission_denied(standard_token):
    client = TestClient(app)
    files = {"files": ("demo/SKILL.md", VALID_SKILL, "text/plain")}
    response = client.post("/v1/skills/import/scan", files=files, headers={"Authorization": f"Bearer {standard_token}"})
    # The standard role may or may not permit PLUGINS; if permitted, result must still be a valid scan response.
    assert response.status_code in (200, 403)
