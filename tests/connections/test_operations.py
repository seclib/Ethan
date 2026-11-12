"""Tests des OPÉRATIONS des connecteurs (Core) — HTTP fictif, aucun secret.

Vérifient : déclaration explicite, enforcement de scope/permission, appel
réel des endpoints officiels (simulés), jamais de token dans le résultat,
et révocation upstream best-effort à la déconnexion.
"""

from __future__ import annotations

import base64

import pytest
from core.integrations.connections import ConnectionError
from core.integrations.connections.base import ClientCredentials

from .conftest import FakeHttp, FakeResponse, FakeSecrets, make_manager

CREDS = ClientCredentials(client_id="id-test", client_secret="secret-test")


def _secrets() -> FakeSecrets:
    return FakeSecrets(
        {
            "CONN_GITHUB_CLIENT_ID": "gh-id",
            "CONN_GITHUB_CLIENT_SECRET": "gh-secret",
            "CONN_EMAIL_CLIENT_ID": "g-id",
            "CONN_EMAIL_CLIENT_SECRET": "g-secret",
            "CONN_MEDIUM_CLIENT_ID": "m-id",
            "CONN_MEDIUM_CLIENT_SECRET": "m-secret",
            "CONN_NOTION_CLIENT_ID": "n-id",
            "CONN_NOTION_CLIENT_SECRET": "n-secret",
        }
    )


async def _connect(
    provider: str, *, token: dict, verify_url: str, verify_payload: dict
) -> tuple[FakeHttp, any]:
    http = FakeHttp()
    http.queue("POST", "token", FakeResponse(200, token))
    http.queue("GET", verify_url, FakeResponse(200, verify_payload))
    mgr = make_manager(http=http, secrets=_secrets())
    flow = await mgr.start("u1", provider)
    await mgr.callback("u1", provider, "code-123", flow["state"])
    return http, mgr


# ── GitHub ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_github_list_repos_returns_public_fields_without_token():
    http, mgr = await _connect(
        "github",
        token={
            "access_token": "gho_u1",
            "token_type": "bearer",
            "scope": "repo read:user",
        },
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    http.queue(
        "GET",
        "api.github.com/user/repos",
        FakeResponse(
            200,
            [
                {
                    "full_name": "a/b",
                    "private": True,
                    "html_url": "https://gh/a/b",
                    "updated_at": "2026-01-01",
                }
            ],
        ),
    )
    result = await mgr.run_operation("u1", "github", "list_repos", {"limit": 5})
    assert result["provider"] == "github" and result["operation"] == "list_repos"
    assert result["result"][0]["full_name"] == "a/b"
    assert "gho_u1" not in str(result)  # ANTI-FUITE : jamais de token


@pytest.mark.asyncio
async def test_github_list_issues_filters_pull_requests():
    http, mgr = await _connect(
        "github",
        token={"access_token": "gho_u1", "scope": "repo"},
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    http.queue(
        "GET",
        "api.github.com/issues",
        FakeResponse(
            200,
            [
                {
                    "number": 1,
                    "title": "Bug",
                    "state": "open",
                    "repository_url": "https://api.github.com/repos/a/b",
                    "html_url": "u/1",
                },
                {
                    "number": 2,
                    "title": "PR",
                    "state": "open",
                    "pull_request": {"url": "x"},
                },
            ],
        ),
    )
    result = await mgr.run_operation("u1", "github", "list_issues", {})
    assert [i["number"] for i in result["result"]] == [1]


@pytest.mark.asyncio
async def test_github_operation_requires_declared_scope():
    # Connexion SANS le scope ``repo`` : l'opération doit être refusée.
    http, mgr = await _connect(
        "github",
        token={"access_token": "gho_u1", "scope": "read:user"},
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    with pytest.raises(ConnectionError, match="requires scope 'repo'"):
        await mgr.run_operation("u1", "github", "list_repos", {})


@pytest.mark.asyncio
async def test_unknown_operation_is_rejected():
    http, mgr = await _connect(
        "github",
        token={"access_token": "gho_u1", "scope": "repo"},
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    with pytest.raises(ConnectionError, match="Unknown operation"):
        await mgr.run_operation("u1", "github", "delete_everything", {})


# ── Medium ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_medium_create_post_publishes_via_official_api():
    http, mgr = await _connect(
        "medium",
        token={"access_token": "m_tok", "scope": "basicProfile publishPost"},
        verify_url="api.medium.com/v1/me",
        verify_payload={"data": {"id": "author1", "username": "writer"}},
    )
    http.queue(
        "POST",
        "api.medium.com/v1/users/author1/posts",
        FakeResponse(
            201,
            {
                "data": {
                    "id": "post1",
                    "url": "https://medium.com/p/post1",
                    "publishStatus": "DRAFT",
                }
            },
        ),
    )
    # op_create_post résout l'auteur via GET /me avant publication.
    http.queue(
        "GET",
        "api.medium.com/v1/me",
        FakeResponse(200, {"data": {"id": "author1", "username": "writer"}}),
    )
    result = await mgr.run_operation(
        "u1",
        "medium",
        "create_post",
        {
            "title": "T",
            "content": "<p>C</p>",
            "content_format": "html",
            "tags": ["a", "b", "c", "d", "e", "f"],
        },
    )
    assert result["result"]["id"] == "post1"
    # Le payload a bien été posté sur l'endpoint officiel, tags limités à 5.
    method, url, kwargs = http.calls[-1]
    assert "users/author1/posts" in url
    assert len(kwargs["json"]["tags"]) == 5


@pytest.mark.asyncio
async def test_medium_create_post_validates_publish_status():
    http, mgr = await _connect(
        "medium",
        token={"access_token": "m_tok", "scope": "basicProfile publishPost"},
        verify_url="api.medium.com/v1/me",
        verify_payload={"data": {"id": "author1"}},
    )
    with pytest.raises(ConnectionError, match="publish_status"):
        await mgr.run_operation(
            "u1",
            "medium",
            "create_post",
            {"title": "T", "content": "C", "publish_status": "sponsored"},
        )


# ── Notion ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notion_search_and_create_page_use_api_v1_headers():
    http, mgr = await _connect(
        "notion",
        token={"access_token": "secret_n", "name": "Bot"},
        verify_url="api.notion.com/v1/users/me",
        verify_payload={"name": "Bot", "bot": {"workspace_name": "WS"}},
    )
    http.queue(
        "POST",
        "api.notion.com/v1/search",
        FakeResponse(
            200,
            {
                "results": [
                    {
                        "id": "p1",
                        "object": "page",
                        "url": "u",
                        "properties": {
                            "Title": {
                                "type": "title",
                                "title": [{"plain_text": "Page"}],
                            }
                        },
                    }
                ]
            },
        ),
    )
    result = await mgr.run_operation("u1", "notion", "search", {"query": "Page"})
    assert result["result"][0]["title"] == "Page"
    # Header Notion-Version présent (exigence officielle).
    assert http.calls[-1][2]["headers"]["Notion-Version"]

    http.queue("POST", "api.notion.com/v1/pages", FakeResponse(200, {"id": "p2", "url": "u2"}))
    created = await mgr.run_operation(
        "u1",
        "notion",
        "create_page",
        {
            "parent": {"database_id": "db"},
            "properties": {"Name": {"title": [{"text": {"content": "N"}}]}},
        },
    )
    assert created["result"]["id"] == "p2"


# ── Gmail ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gmail_send_message_builds_mime_and_uses_official_endpoint():
    http, mgr = await _connect(
        "email",
        token={
            "access_token": "ya29_u1",
            "refresh_token": "r1",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send",
        },
        verify_url="gmail.googleapis.com",
        verify_payload={"emailAddress": "me@test"},
    )
    http.queue(
        "POST",
        "gmail.googleapis.com/gmail/v1/users/me/messages/send",
        FakeResponse(200, {"id": "m1", "threadId": "t1"}),
    )
    result = await mgr.run_operation(
        "u1", "email", "send_message", {"to": "x@y.z", "subject": "S", "body": "Hello"}
    )
    assert result["result"]["id"] == "m1"
    raw = http.calls[-1][2]["json"]["raw"]
    decoded = base64.urlsafe_b64decode(raw.encode()).decode()
    assert "To: x@y.z" in decoded and "Subject: S" in decoded
    # Le corps est encodé base64 par MIME (comportement standard) — on le
    # vérifie en décodant la dernière partie du message.
    body_part = decoded.rsplit("\n\n", 1)[-1].strip()
    assert base64.b64decode(body_part).decode() == "Hello"


# ── Révocation upstream (déconnexion) ───────────────────────────────────


@pytest.mark.asyncio
async def test_disconnect_revokes_github_token_upstream():
    http, mgr = await _connect(
        "github",
        token={"access_token": "gho_rev", "scope": "repo"},
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    http.queue("DELETE", "api.github.com/applications/gh-id/token", FakeResponse(204, None))
    await mgr.disconnect("u1", "github")
    method, url, kwargs = http.calls[-1]
    assert method == "DELETE" and "applications/gh-id/token" in url
    assert kwargs["json"] == {"access_token": "gho_rev"}
    record = await mgr.get("u1", "github")
    assert record["status"] == "disconnected"


@pytest.mark.asyncio
async def test_disconnect_survives_upstream_revocation_failure():
    http, mgr = await _connect(
        "github",
        token={"access_token": "gho_rev", "scope": "repo"},
        verify_url="api.github.com/user",
        verify_payload={"login": "octocat"},
    )
    http.queue(
        "DELETE",
        "api.github.com/applications/gh-id/token",
        FakeResponse(500, None, "boom"),
    )
    await mgr.disconnect("u1", "github")  # révocation best effort — NON bloquante
    record = await mgr.get("u1", "github")
    assert record["status"] == "disconnected"
