"""Tests ConnectionManager : lifecycle, sécurité, events — sans réseau.

Couvre : connecter (state + URL), callback (échange + test réel + stockage
tokens dans le domaine dédié), reconnecter (purge), tester (succès/échec),
voir les permissions, déconnecter, lister, et ``get_access_token`` avec
refresh automatique — le point d'entrée unique de Chat/Knowledge/Skills/
Missions.
"""

from __future__ import annotations

import time

import pytest
from core.integrations.connections import ConnectionError
from core.integrations.connections.oauth import epoch_in

from .conftest import FakeHttp, FakeResponse, make_manager  # noqa: F401

GITHUB_TOKEN_URL = "github.com/login/oauth/access_token"
GITHUB_USER_URL = "api.github.com/user"


def _github_oauth_http() -> FakeHttp:
    http = FakeHttp()
    http.queue(
        "POST",
        GITHUB_TOKEN_URL,
        FakeResponse(200, {"access_token": "gho_X", "scope": "repo read:user"}),
    )
    http.queue("GET", GITHUB_USER_URL, FakeResponse(200, {"login": "seclib"}))
    return http


# __NEXT__


# ── Reconnecter / Tester / Permissions / Déconnecter ─────────────────────


@pytest.mark.asyncio
async def test_reconnect_purges_tokens_and_restarts(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    again = await manager.reconnect("alice", "github")
    assert again["state"] != started["state"]  # nouveau flux
    # Tokens purgés : le test échoue tant que le nouveau flux n'est pas fini.
    with pytest.raises(ConnectionError, match="No stored credentials"):
        await manager.test("alice", "github")


@pytest.mark.asyncio
async def test_test_connection_success_updates_status(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    http = FakeHttp()
    http.queue("GET", GITHUB_USER_URL, FakeResponse(200, {"login": "seclib2"}))
    manager._http_factory = lambda: http

    result = await manager.test("alice", "github")
    assert result["status"] == "connected"
    assert result["account"] == {"login": "seclib2"}
    record = await manager.get("alice", "github")
    assert record["account"]["login"] == "seclib2"


@pytest.mark.asyncio
async def test_test_connection_failure_sets_error_status(oauth_secrets, fake_bus):
    manager = make_manager(bus=fake_bus, secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    http = FakeHttp()
    http.queue("GET", GITHUB_USER_URL, FakeResponse(401, None, "Bad credentials"))
    manager._http_factory = lambda: http

    with pytest.raises(ConnectionError, match="HTTP 401"):
        await manager.test("alice", "github")
    record = await manager.get("alice", "github")
    assert record["status"] == "error"
    assert "HTTP 401" in record["last_error"]
    assert fake_bus.events[-1][1].type.value == "ethan.connection.error"


@pytest.mark.asyncio
async def test_permissions_shows_requested_vs_granted(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    perms = await manager.permissions("alice", "github")
    assert [s["scope"] for s in perms["requested"]] == [
        "repo",
        "read:user",
        "user:email",
    ]
    assert perms["granted"] == ["repo", "read:user"]


@pytest.mark.asyncio
async def test_disconnect_purges_tokens_and_marks_disconnected(oauth_secrets, fake_bus):
    manager = make_manager(bus=fake_bus, secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    public = await manager.disconnect("alice", "github")
    assert public["status"] == "disconnected"
    assert await manager._store.get("connection-tokens", "alice:github") is None
    assert fake_bus.events[-1][1].type.value == "ethan.connection.disconnected"
    with pytest.raises(ConnectionError):
        await manager.get_access_token("alice", "github")


# ── get_access_token (Chat / Knowledge / Skills / Missions) ──────────────


@pytest.mark.asyncio
async def test_get_access_token_returns_valid_token(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    assert await manager.get_access_token("alice", "github") == "gho_X"


def _gmail_oauth_http() -> FakeHttp:
    """Flux Gmail complet (provider AVEC refresh token documenté)."""
    http = FakeHttp()
    http.queue(
        "POST",
        "oauth2.googleapis.com/token",
        FakeResponse(
            200,
            {
                "access_token": "g1",
                "refresh_token": "gr1",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/gmail.readonly",
            },
        ),
    )
    http.queue(
        "GET",
        "gmail.googleapis.com/gmail/v1/users/me/profile",
        FakeResponse(200, {"emailAddress": "me@test.tld", "messagesTotal": 7}),
    )
    return http


@pytest.mark.asyncio
async def test_get_access_token_auto_refreshes_expired_token(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_gmail_oauth_http())
    started = await manager.start("alice", "email")
    await manager.callback("alice", "email", code="abc", state=started["state"])

    # Token expiré + refresh_token stocké → refresh automatique transparent.
    expired = epoch_in(-60)
    record = await manager._store.get("connections", "alice:email")
    record["token_expires_at"] = expired
    await manager._store.save("connections", "alice:email", record)
    tokens = await manager._store.get("connection-tokens", "alice:email")
    tokens["expires_at"] = expired
    await manager._store.save("connection-tokens", "alice:email", tokens)

    http = FakeHttp()
    http.queue(
        "POST",
        "oauth2.googleapis.com/token",
        FakeResponse(200, {"access_token": "g2", "refresh_token": "gr2", "expires_in": 3600}),
    )
    manager._http_factory = lambda: http

    token = await manager.get_access_token("alice", "email")
    assert token == "g2"
    stored = await manager._store.get("connection-tokens", "alice:email")
    assert stored["access_token"] == "g2"
    # Google ne renvoie PAS de nouveau refresh_token dans la réponse de
    # refresh (comportement officiel) → l'ancien est conservé.
    assert stored["refresh_token"] == "gr1"
    assert stored["expires_at"] > time.time()
    record = await manager._store.get("connections", "alice:email")
    assert record["token_expires_at"] == stored["expires_at"]


@pytest.mark.asyncio
async def test_get_access_token_without_refresh_raises_reconnect(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    expired = epoch_in(-60)
    tokens = await manager._store.get("connection-tokens", "alice:github")
    tokens["expires_at"] = expired  # GitHub : pas de refresh_token disponible
    await manager._store.save("connection-tokens", "alice:github", tokens)

    with pytest.raises(ConnectionError, match="reconnect required"):
        await manager.get_access_token("alice", "github")


# ── Connecter / Callback ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_emits_state_and_oauth_url(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets)
    result = await manager.start("alice", "github")

    assert result["connection_id"] == "alice:github"
    assert "client_id=gh-id-test" in result["authorization_url"]
    assert "state=" + result["state"] in result["authorization_url"]
    assert "client_secret" not in result["authorization_url"]
    assert result["scopes_requested"] == ["repo", "read:user", "user:email"]


@pytest.mark.asyncio
async def test_start_without_oauth_client_config_fails_clean(oauth_secrets):
    from .conftest import FakeSecrets

    manager = make_manager(secrets=FakeSecrets({}))  # aucun client GitHub configuré
    with pytest.raises(ConnectionError, match="OAuth client not configured"):
        await manager.start("alice", "github")


@pytest.mark.asyncio
async def test_full_callback_flow_stores_tokens_and_publishes_event(oauth_secrets, fake_bus):
    manager = make_manager(bus=fake_bus, secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")

    public = await manager.callback("alice", "github", code="abc", state=started["state"])
    assert public["status"] == "connected"
    assert public["account"] == {"login": "seclib"}
    assert public["scopes_granted"] == ["repo", "read:user"]
    # Aucun champ sensible dans la vue publique.
    assert "state" not in public and "access_token" not in str(public)

    # Les tokens vivent dans le domaine dédié, jamais dans le record public.
    stored = await manager._store.get("connection-tokens", "alice:github")
    assert stored["access_token"] == "gho_X"
    record = await manager._store.get("connections", "alice:github")
    assert "access_token" not in str(record)

    # Event sans secret.
    assert fake_bus.events, "CONNECTION_CONNECTED event expected"
    subject, event = fake_bus.events[0]
    assert subject == "alice:github"
    assert event.type.value == "ethan.connection.connected"
    assert "gho_X" not in str(event.payload)


@pytest.mark.asyncio
async def test_callback_rejects_wrong_state_and_single_use(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")

    with pytest.raises(ConnectionError, match="state mismatch"):
        await manager.callback("alice", "github", code="abc", state="forged")

    # Consommé une fois : le second callback même correct est refusé.
    await manager.callback("alice", "github", code="abc", state=started["state"])
    with pytest.raises(ConnectionError, match="No pending"):
        await manager.callback("alice", "github", code="abc", state=started["state"])


@pytest.mark.asyncio
async def test_callback_rejects_expired_state(oauth_secrets):
    import time

    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    record = await manager._store.get("connections", "alice:github")
    record["state_expires_at"] = time.time() - 1
    await manager._store.save("connections", "alice:github", record)

    with pytest.raises(ConnectionError, match="state expired"):
        await manager.callback("alice", "github", code="abc", state=started["state"])


@pytest.mark.asyncio
async def test_user_isolation_between_users(oauth_secrets):
    manager = make_manager(secrets=oauth_secrets, http=_github_oauth_http())
    started = await manager.start("alice", "github")
    await manager.callback("alice", "github", code="abc", state=started["state"])

    with pytest.raises(ConnectionError, match="Connection not found"):
        await manager.test("bob", "github")  # bob n'a pas la connexion d'alice
    assert await manager.get("bob", "github") is None
    assert [c["provider"] for c in await manager.list("bob")] == []
