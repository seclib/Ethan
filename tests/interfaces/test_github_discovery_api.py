import interfaces.api.auth as auth
import pytest
from fastapi.testclient import TestClient
from interfaces.api.main import app
import interfaces.api.routers.github_discovery as gd


@pytest.fixture
def admin_token(monkeypatch):
    async def fetch(username):
        return {"username": username, "roles": ["admin"], "is_active": True}
    monkeypatch.setattr(auth, "fetch_user_record", fetch)

    async def _verify(token):
        return {"sub": "alice", "role": "admin", "exp": 9999999999}
    monkeypatch.setattr(auth, "verify_token_string", _verify)
    return auth.create_access_token({"sub": "alice", "role": "admin"})


def test_discover_github_organization_uses_adapter_without_auth(monkeypatch):
    monkeypatch.setattr(gd, "discover_github_org_repositories", lambda org, **kwargs: [])
    client = TestClient(app)
    response = client.get("/v1/github/organizations/seclib/repositories")
    assert response.status_code in (401, 403)


def test_discover_github_organization_returns_adapter_results(admin_token, monkeypatch):
    from core.applications.github_organization_discovery import GitHubRepositoryMetadata

    result = [
        GitHubRepositoryMetadata(
            organization="seclib",
            name="demo",
            full_name="seclib/demo",
            description="demo",
            default_branch="main",
            html_url="https://github.com/seclib/demo",
            clone_url="https://github.com/seclib/demo.git",
            archived=False,
            visibility="public",
            updated_at="2026-01-01T00:00:00Z",
            topics=("ethan",),
        )
    ]
    monkeypatch.setattr(gd, "discover_github_org_repositories", lambda org, **kwargs: result)

    client = TestClient(app)
    response = client.get(
        "/v1/github/organizations/seclib/repositories",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["full_name"] == "seclib/demo"
    assert body[0]["topics"] == ["ethan"]


def test_discover_github_organization_reports_discovery_error(admin_token, monkeypatch):
    def fail(org, **kwargs):
        raise gd.GitHubOrgDiscoveryError("cannot reach organization")
    monkeypatch.setattr(gd, "discover_github_org_repositories", fail)

    client = TestClient(app)
    response = client.get(
        "/v1/github/organizations/seclib/repositories",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 502


def test_discover_github_user_returns_adapter_results(admin_token, monkeypatch):
    from core.applications.github_organization_discovery import GitHubRepositoryMetadata

    result = [
        GitHubRepositoryMetadata(
            organization="seclib",
            name="demo",
            full_name="seclib/demo",
            description="demo",
            default_branch="main",
            html_url="https://github.com/seclib/demo",
            clone_url="https://github.com/seclib/demo.git",
            archived=False,
            visibility="public",
            updated_at="2026-01-01T00:00:00Z",
            topics=("ethan",),
        )
    ]
    monkeypatch.setattr(gd, "discover_github_user_repositories", lambda org, **kwargs: result)

    client = TestClient(app)
    response = client.get(
        "/v1/github/users/seclib/repositories",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["full_name"] == "seclib/demo"
