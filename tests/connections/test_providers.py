"""Tests providers Connections : OAuth conforme PAR SERVICE, sans réseau.

Chaque provider doit : construire l'URL d'autorisation avec ses scopes
EXPLICITES (jamais de client_secret dans l'URL), décoder une réponse token
réaliste, parser les scopes accordés, et tester la connexion par un appel
API réel avec une identité diste non secrète.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from core.integrations.connections import (
    ConnectionError,
    get_provider,
    list_providers,
    provider_ids,
)
from core.integrations.connections.base import ClientCredentials, TokenBundle
from core.integrations.connections.oauth import basic_auth_header, pkce_pair

from .conftest import FakeHttp, FakeResponse

CREDS = ClientCredentials(client_id="id-test", client_secret="secret-test")


def test_registry_contains_the_four_launch_connectors():
    assert set(provider_ids()) >= {"email", "github", "medium", "notion"}
    assert all(p.id and p.label and p.description for p in list_providers())


def test_unknown_provider_raises_explicit_error():
    with pytest.raises(ConnectionError, match="Unknown connection provider"):
        get_provider("gitlab")  # pas encore livré — erreur explicite


# ── GitHub ───────────────────────────────────────────────────────────────


def test_github_authorization_url_declares_scopes_without_secret():
    url = get_provider("github").build_authorization_url(
        CREDS, "https://ethan.test/connections/github/callback", "state123"
    )
    params = parse_qs(urlparse(url).query)
    assert url.startswith("https://github.com/login/oauth/authorize")
    assert params["client_id"] == ["id-test"]
    assert params["scope"] == ["repo read:user user:email"]
    assert "client_secret" not in params


@pytest.mark.asyncio
async def test_github_exchange_requires_json_accept_header_and_parses_scopes():
    http = FakeHttp()
    http.queue(
        "POST",
        "github.com/login/oauth/access_token",
        FakeResponse(200, {"access_token": "gho_token", "scope": "repo,read:user"}),
    )
    tokens = await get_provider("github").exchange_code(
        http, CREDS, "code-1", "https://ethan.test/connections/github/callback"
    )
    method, url, kwargs = http.calls[0]
    assert method == "POST" and url.startswith("https://github.com/login/oauth")
    assert kwargs["headers"]["Accept"] == "application/json"
    assert kwargs["data"]["client_secret"] == "secret-test"
    assert tokens.access_token == "gho_token"
    assert tokens.granted_scopes == ["repo", "read:user"]
    assert tokens.refresh_token is None  # GitHub n'émet pas de refresh token


@pytest.mark.asyncio
async def test_github_test_connection_returns_public_identity():
    http = FakeHttp()
    http.queue(
        "GET",
        "api.github.com/user",
        FakeResponse(200, {"login": "seclib", "name": "Sec Lib"}),
    )
    account = await get_provider("github").test_connection(http, TokenBundle(access_token="t"))
    assert account["login"] == "seclib"
    headers = http.calls[0][2]["headers"]
    assert headers["Authorization"] == "Bearer t"


@pytest.mark.asyncio
async def test_github_test_connection_raises_on_http_error():
    http = FakeHttp()
    http.queue("GET", "api.github.com/user", FakeResponse(401, None, "Bad credentials"))
    with pytest.raises(ConnectionError, match="HTTP 401"):
        await get_provider("github").test_connection(http, TokenBundle(access_token="t"))


# __NEXT__


# ── Notion ───────────────────────────────────────────────────────────────


def test_notion_has_no_oauth_scopes_by_design():
    # La granularité Notion = pages sélectionnées au consentement.
    assert get_provider("notion").scopes == []


@pytest.mark.asyncio
async def test_notion_exchange_uses_basic_auth_and_extracts_workspace():
    http = FakeHttp()
    http.queue(
        "POST",
        "api.notion.com/v1/oauth/token",
        FakeResponse(
            200,
            {
                "access_token": "ntn_token",
                "name": "ETHAN integration",
                "bot": {"workspace_name": "Sec Workspace"},
            },
        ),
    )
    tokens = await get_provider("notion").exchange_code(http, CREDS, "c", "https://r")
    method, url, kwargs = http.calls[0]
    assert kwargs["headers"]["Authorization"] == basic_auth_header("id-test", "secret-test")
    assert tokens.access_token == "ntn_token"
    assert tokens.account["workspace_name"] == "Sec Workspace"


# ── Medium ───────────────────────────────────────────────────────────────


def test_medium_declares_publish_scopes_marked_sensitive():
    scopes = {s.scope: s for s in get_provider("medium").scopes}
    assert scopes["publishPost"].sensitive is True
    assert scopes["basicProfile"].sensitive is False
    # Moindre privilège : ``uploadImage`` n'est PAS demandé — l'upload
    # d'images n'est pas implémenté, on ne demande que ce qu'on utilise.
    assert "uploadImage" not in scopes


@pytest.mark.asyncio
async def test_medium_exchange_returns_refresh_token_and_expiry():
    http = FakeHttp()
    http.queue(
        "POST",
        "api.medium.com/v1/tokens",
        FakeResponse(
            200,
            {
                "access_token": "m_token",
                "refresh_token": "m_refresh",
                "expires_in": 3600,
                "scope": "basicProfile publishPost",
            },
        ),
    )
    tokens = await get_provider("medium").exchange_code(http, CREDS, "c", "https://r")
    assert tokens.refresh_token == "m_refresh"
    assert tokens.expires_at is not None and tokens.expires_at > 0
    assert set(tokens.granted_scopes) == {"basicProfile", "publishPost"}


@pytest.mark.asyncio
async def test_medium_has_no_refresh_grant_official_api_limitation():
    """HONNÊTETÉ API : Medium ne documente AUCUN endpoint de refresh token.

    ``refresh_tokens`` suit le contrat de base (``None``) — le Core ne
    fabrique pas d'endpoint inexistant ; en cas d'expiration (401),
    l'utilisateur utilise Reconnecter.
    """
    http = FakeHttp()
    assert await get_provider("medium").refresh_tokens(http, CREDS, "m_refresh") is None
    assert http.calls == []  # aucun appel HTTP inventé


# ── Email (Gmail via Google) ─────────────────────────────────────────────


def test_gmail_forces_offline_access_for_refresh_token():
    provider = get_provider("email")
    params = provider.extra_authorize_params()
    assert params["access_type"] == "offline" and params["prompt"] == "consent"
    scopes = {s.scope for s in provider.scopes}
    assert "https://www.googleapis.com/auth/gmail.send" in scopes


@pytest.mark.asyncio
async def test_gmail_exchange_and_refresh():
    http = FakeHttp()
    http.queue(
        "POST",
        "oauth2.googleapis.com/token",
        FakeResponse(
            200,
            {
                "access_token": "ya29.a",
                "refresh_token": "1//r",
                "expires_in": 3600,
                "scope": "openid",
            },
        ),
    )
    tokens = await get_provider("email").exchange_code(http, CREDS, "c", "https://r")
    assert tokens.refresh_token == "1//r"
    http.queue(
        "POST",
        "oauth2.googleapis.com/token",
        FakeResponse(200, {"access_token": "ya29.b", "expires_in": 3600}),
    )
    refreshed = await get_provider("email").refresh_tokens(http, CREDS, "1//r")
    assert refreshed is not None and refreshed.access_token == "ya29.b"
    assert refreshed.refresh_token is None  # Google ne renvoie pas le refresh


# ── Helpers OAuth communs ────────────────────────────────────────────────


def test_pkce_pair_is_s256_and_verifier_is_urlsafe():
    verifier, challenge = pkce_pair()
    assert 43 <= len(verifier) <= 128
    assert len(challenge) == 43 and "=" not in challenge


def test_urlencoded_token_payload_is_decoded_github_style():
    # GitHub sans Accept: application/json répond en form-urlencoded.
    from core.integrations.connections.oauth import decode_token_response

    class Resp:
        status_code = 200
        text = "access_token=ghu_1&scope=repo&token_type=bearer"

        def json(self):
            raise ValueError("not json")

    data = decode_token_response(Resp(), "GitHub")
    assert data["access_token"] == "ghu_1"
