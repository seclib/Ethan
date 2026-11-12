"""Tests de sûreté des serveurs d'outils MCP — politique Core fail-closed.

Périmètre (extensions non fiables par défaut) :

- **identité** : ``name``/``auth_type`` validés ;
- **transport** : allowlist stricte ; stdio exige une allowlist explicite
  (``ETHAN_MCP_STDIO_ALLOWLIST``) et un chemin absolu — sans elle, stdio est
  désactivé ;
- **destination (SSRF)** : publique par défaut ; loopback/RFC1918 seulement
  via ``ETHAN_MCP_ALLOW_PRIVATE_HOSTS=1`` ; link-local/métadonnées cloud
  toujours refusés ; credentials dans l'URL refusés ;
- **TLS** : ``verify_ssl=false`` refusé ;
- **management** : ``ToolServerManager`` applique la politique à
  l'enregistrement, à la mise à jour (record fusionné) et re-vérifie à la
  connexion (défense en profondeur) ; un serveur désactivé ne se synchronise
  pas ;
- **secrets** : aucun message d'erreur ne contient la valeur du token.

Aucun réseau : les validations utilisent des littéraux IP (aucune résolution
DNS) ou un résolveur injecté.
"""

from __future__ import annotations

import asyncio
import sys

import pytest
from core.tools.server_policy import (
    ServerPolicyError,
    validate_server_config,
)
from core.tools.servers import ToolServerManager

PUBLIC_IP_URL = "http://8.8.8.8:9/mcp"
SECRET = "super-secret-token-42"


@pytest.fixture(autouse=True)
def _clean_mcp_policy_env(monkeypatch):
    """Défauts fail-closed : aucune allowlist, aucune destination privée."""
    monkeypatch.delenv("ETHAN_MCP_STDIO_ALLOWLIST", raising=False)
    monkeypatch.delenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", raising=False)


def _manager() -> ToolServerManager:
    return ToolServerManager()


# ── Transport stdio ─────────────────────────────────────────────────────────


def test_stdio_disabled_without_allowlist():
    with pytest.raises(ServerPolicyError, match="stdio transport is disabled"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={"transport": "stdio", "command": sys.executable},
        )


def test_stdio_allowlisted_absolute_command_accepted(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", sys.executable)
    config = validate_server_config(
        name="local",
        url="stdio://local",
        metadata={"transport": "stdio", "command": sys.executable, "args": ["server.py"]},
    )
    assert config["metadata"]["transport"] == "stdio"
    assert config["metadata"]["command"] == sys.executable


def test_stdio_relative_command_refused(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", sys.executable)
    with pytest.raises(ServerPolicyError, match="absolute path"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={"transport": "stdio", "command": "python3"},
        )


def test_stdio_command_not_allowlisted_refused(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", "/usr/bin/other-binary")
    with pytest.raises(ServerPolicyError, match="ETHAN_MCP_STDIO_ALLOWLIST"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={"transport": "stdio", "command": sys.executable},
        )


def test_stdio_args_must_be_string_list(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", sys.executable)
    with pytest.raises(ServerPolicyError, match="list of strings"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={"transport": "stdio", "command": sys.executable, "args": "server.py"},
        )


def test_stdio_env_and_cwd_refused(monkeypatch):
    monkeypatch.setenv("ETHAN_MCP_STDIO_ALLOWLIST", sys.executable)
    with pytest.raises(ServerPolicyError, match="env"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={
                "transport": "stdio",
                "command": sys.executable,
                "env": {"LD_PRELOAD": "/tmp/evil.so"},
            },
        )
    with pytest.raises(ServerPolicyError, match="cwd"):
        validate_server_config(
            name="local",
            url="stdio://local",
            metadata={"transport": "stdio", "command": sys.executable, "cwd": "/tmp"},
        )


# ── Destination (SSRF) ──────────────────────────────────────────────────────


def test_http_public_destination_accepted():
    config = validate_server_config(name="remote", url=PUBLIC_IP_URL)
    assert config["url"] == "http://8.8.8.8:9/mcp"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:9/mcp",
        "http://10.0.0.5:9/mcp",
        "http://192.168.1.10:9/mcp",
        "http://[::1]:9/mcp",
    ],
)
def test_http_private_destination_refused_by_default(url):
    with pytest.raises(ServerPolicyError):
        validate_server_config(name="internal", url=url)


@pytest.mark.parametrize("url", ["http://127.0.0.1:9/mcp", "http://10.0.0.5:9/mcp"])
def test_http_private_destination_allowed_with_explicit_optin(monkeypatch, url):
    monkeypatch.setenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", "1")
    assert validate_server_config(name="internal", url=url)["url"] == url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
    ],
)
def test_metadata_endpoints_refused_even_with_optin(monkeypatch, url):
    monkeypatch.setenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", "1")
    with pytest.raises(ServerPolicyError):
        validate_server_config(name="imds", url=url, resolver=lambda _host: ["169.254.169.254"])


@pytest.mark.parametrize("url", ["file:///etc/passwd", "gopher://8.8.8.8/", "ws://8.8.8.8/mcp"])
def test_non_http_schemes_refused(url):
    with pytest.raises(ServerPolicyError, match="scheme"):
        validate_server_config(name="bad", url=url)


def test_credentials_in_url_refused():
    with pytest.raises(ServerPolicyError, match="credentials"):
        validate_server_config(name="bad", url="https://user:pass@8.8.8.8/mcp")


def test_dns_resolving_to_private_refused():
    with pytest.raises(ServerPolicyError):
        validate_server_config(
            name="sneaky", url="https://internal.example.com/mcp", resolver=lambda _h: ["10.0.0.7"]
        )


# ── Identité / authentification / TLS ───────────────────────────────────────


def test_blank_name_refused():
    with pytest.raises(ServerPolicyError, match="name"):
        validate_server_config(name="   ", url=PUBLIC_IP_URL)


def test_unknown_auth_type_refused():
    with pytest.raises(ServerPolicyError, match="auth_type"):
        validate_server_config(name="p", url=PUBLIC_IP_URL, auth_type="magic")


def test_bearer_requires_token():
    with pytest.raises(ServerPolicyError, match="token"):
        validate_server_config(name="p", url=PUBLIC_IP_URL, auth_type="bearer")


def test_unknown_transport_refused():
    with pytest.raises(ServerPolicyError, match="transport"):
        validate_server_config(name="p", url=PUBLIC_IP_URL, metadata={"transport": "ws"})


def test_verify_ssl_false_refused():
    with pytest.raises(ServerPolicyError, match="verify_ssl"):
        validate_server_config(name="p", url=PUBLIC_IP_URL, metadata={"verify_ssl": False})


def test_invalid_header_name_refused():
    with pytest.raises(ServerPolicyError, match="header name"):
        validate_server_config(
            name="p", url=PUBLIC_IP_URL, metadata={"headers": {"Bad Header": "x"}}
        )


def test_error_message_never_leaks_token():
    with pytest.raises(ServerPolicyError) as exc:
        validate_server_config(
            name="p",
            url=PUBLIC_IP_URL,
            auth_type="bearer",
            auth_config={"token": SECRET},
            metadata={"transport": "ws"},
        )
    assert SECRET not in str(exc.value)


# ── ToolServerManager (application réelle) ──────────────────────────────────


def test_manager_register_refuses_private_url_without_optin():
    async def scenario():
        manager = _manager()
        with pytest.raises(ServerPolicyError):
            await manager.register(name="local-http", url="http://127.0.0.1:9/mcp")
        assert await manager.list() == []

    asyncio.run(scenario())


def test_manager_register_refuses_stdio_without_allowlist():
    async def scenario():
        manager = _manager()
        with pytest.raises(ServerPolicyError, match="stdio transport is disabled"):
            await manager.register(
                name="local-stdio",
                url="stdio://local",
                metadata={"transport": "stdio", "command": sys.executable},
            )
        assert await manager.list() == []

    asyncio.run(scenario())


def test_manager_update_cannot_escalate_to_stdio(monkeypatch):
    """Un update ne peut pas transformer un serveur http en exécution locale."""

    async def scenario():
        monkeypatch.setenv("ETHAN_MCP_ALLOW_PRIVATE_HOSTS", "1")
        manager = _manager()
        server = await manager.register(name="http-local", url="http://127.0.0.1:9/mcp")

        monkeypatch.delenv("ETHAN_MCP_STDIO_ALLOWLIST", raising=False)
        with pytest.raises(ServerPolicyError, match="stdio transport is disabled"):
            await manager.update(
                server["id"],
                {"metadata": {"transport": "stdio", "command": "/bin/sh", "args": ["-c", "id"]}},
            )

        # Le record stocké n'a pas bougé : toujours http, aucune commande.
        raw = await manager._get_private(server["id"])
        assert raw["metadata"].get("transport") in (None, "http")
        assert "command" not in raw["metadata"]

    asyncio.run(scenario())


def test_manager_sync_refuses_disabled_server():
    async def scenario():
        manager = _manager()
        server = await manager.register(name="remote", url=PUBLIC_IP_URL, enabled=False)
        with pytest.raises(ValueError, match="disabled"):
            await manager.sync_tools(server["id"])

    asyncio.run(scenario())


def test_manager_sync_revalidates_stored_record():
    """Un record écrit hors politique (store direct) n'est jamais exécuté."""

    async def scenario():
        manager = _manager()
        legacy_id = "legacy-private-server"
        await manager._store.save(
            manager._DOMAIN,
            legacy_id,
            {
                "id": legacy_id,
                "name": "legacy",
                "url": "http://127.0.0.1:9/mcp",
                "auth_type": "none",
                "auth_config": {},
                "enabled": True,
                "metadata": {"transport": "http"},
            },
        )
        with pytest.raises(ServerPolicyError):
            await manager.sync_tools(legacy_id)

    asyncio.run(scenario())
