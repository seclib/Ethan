"""tests/test_integrations.py — App Integrations Core model.

Couverture : identité (kind/nom uniques), permissions ETHAN validées,
credential handling (jamais de secret dans le public/events), lifecycle
connect/disconnect, healthcheck par kind (délégation MCP sans duplication).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from core.auth import Permission
from core.integrations import (
    INTEGRATION_KINDS,
    IntegrationError,
    IntegrationManager,
)
from core.state.record_store import CoreRecordStore


SECRET = "sk-super-secret-token-12345"


@pytest.fixture()
def manager():
    return IntegrationManager(store=CoreRecordStore())


class FakeToolServers:
    """ToolServerManager factice (délégation healthcheck MCP)."""

    def __init__(self, servers: dict[str, dict] | None = None):
        self._servers = servers or {}

    async def get(self, server_id: str):
        return self._servers.get(server_id)


# ── Identité ────────────────────────────────────────────────────────────────


class TestIdentity:
    @pytest.mark.asyncio
    async def test_register_returns_public_record(self, manager):
        integration = await manager.register(
            name="github-prod",
            kind="developer",
            capabilities=["repos.read"],
        )
        assert integration["name"] == "github-prod"
        assert integration["kind"] == "developer"
        assert integration["status"] == "disconnected"
        assert integration["id"]

    @pytest.mark.asyncio
    async def test_duplicate_name_rejected(self, manager):
        await manager.register(name="dup", kind="storage")
        with pytest.raises(IntegrationError, match="already exists"):
            await manager.register(name="DUP ", kind="storage")

    @pytest.mark.asyncio
    async def test_unknown_kind_rejected(self, manager):
        with pytest.raises(IntegrationError, match="Unknown integration kind"):
            await manager.register(name="x", kind="demo-thing")

    @pytest.mark.asyncio
    async def test_all_supported_kinds_accepted(self, manager):
        for i, kind in enumerate(INTEGRATION_KINDS):
            integration = await manager.register(name=f"i-{kind}", kind=kind)
            assert integration["kind"] == kind

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, manager):
        assert await manager.get("does-not-exist") is None


# ── Permissions ETHAN (le Core valide) ─────────────────────────────────────


class TestPermissionValidation:
    @pytest.mark.asyncio
    async def test_valid_permissions_normalized(self, manager):
        integration = await manager.register(
            name="perm-ok",
            kind="storage",
            required_permissions=["EXECUTE", "read"],
        )
        assert integration["required_permissions"] == ["execute", "read"]

    @pytest.mark.asyncio
    async def test_invalid_permission_rejected(self, manager):
        with pytest.raises(IntegrationError, match="Unknown ETHAN permission"):
            await manager.register(
                name="perm-bad", kind="storage", required_permissions=["fly"]
            )

    @pytest.mark.asyncio
    async def test_permissions_match_permission_enum(self, manager):
        valid = {p.value for p in Permission}
        integration = await manager.register(
            name="perm-enum",
            kind="automation",
            required_permissions=["execute", "files", "admin"],
        )
        assert set(integration["required_permissions"]) <= valid

    @pytest.mark.asyncio
    async def test_update_revalidates_permissions(self, manager):
        integration = await manager.register(name="perm-upd", kind="mcp")
        with pytest.raises(IntegrationError, match="Unknown ETHAN permission"):
            await manager.update(
                integration["id"], {"required_permissions": ["bypass"]}
            )


# ── Credential handling (jamais de secret exposé) ───────────────────────────


class TestCredentialHandling:
    @pytest.mark.asyncio
    async def test_public_record_never_contains_secret(self, manager):
        integration = await manager.register(
            name="cred-safe",
            kind="web-search",
            credentials={"api_key": SECRET},
        )
        assert SECRET not in str(integration)

    @pytest.mark.asyncio
    async def test_get_and_list_never_contain_secret(self, manager):
        await manager.register(
            name="cred-safe-2", kind="storage", credentials={"token": SECRET}
        )
        for integration in await manager.list():
            assert SECRET not in str(integration)

    @pytest.mark.asyncio
    async def test_credential_keys_only_names(self, manager):
        integration = await manager.register(
            name="cred-keys",
            kind="developer",
            credentials={"token": SECRET, "client_secret": "abc"},
        )
        keys = await manager.credential_keys(integration["id"])
        assert keys == ["client_secret", "token"]
        assert all(SECRET not in k for k in keys)

    @pytest.mark.asyncio
    async def test_credentials_stored_in_dedicated_domain(self, manager):
        """Les credentials vivent dans un domaine séparé du record public."""
        integration = await manager.register(
            name="cred-domain", kind="storage", credentials={"token": SECRET}
        )
        raw_integration = await manager._store.get("integrations", integration["id"])
        assert SECRET not in str(raw_integration)
        raw_creds = await manager._store.get(
            "integration-credentials", integration["id"]
        )
        assert raw_creds["token"] == SECRET  # runtime-only access

    @pytest.mark.asyncio
    async def test_get_credentials_runtime_only(self, manager):
        integration = await manager.register(
            name="cred-runtime", kind="storage", credentials={"token": SECRET}
        )
        creds = await manager.get_credentials(integration["id"])
        assert creds == {"token": SECRET}

    @pytest.mark.asyncio
    async def test_update_replaces_credentials(self, manager):
        integration = await manager.register(
            name="cred-update", kind="storage", credentials={"token": SECRET}
        )
        new_secret = "sk-rotated-token-67890"
        await manager.update(
            integration["id"], {"credentials": {"token": new_secret}}
        )
        creds = await manager.get_credentials(integration["id"])
        assert creds == {"token": new_secret}
        assert SECRET not in str(await manager.get(integration["id"]))

    @pytest.mark.asyncio
    async def test_delete_purges_credentials(self, manager):
        integration = await manager.register(
            name="cred-delete", kind="storage", credentials={"token": SECRET}
        )
        assert await manager.delete(integration["id"]) is True
        creds = await manager.get_credentials(integration["id"])
        assert creds == {}


# ── Lifecycle connect / disconnect ─────────────────────────────────────────


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, manager):
        integration = await manager.register(
            name="lifecycle",
            kind="web-search",
            credentials={"api_key": "k"},
            metadata={"required_credentials": ["api_key"]},
        )
        connected = await manager.connect(integration["id"])
        assert connected["status"] == "connected"
        assert connected["last_connected_at"]
        assert SECRET not in str(connected)

        disconnected = await manager.disconnect(integration["id"])
        assert disconnected["status"] == "disconnected"
        # Les credentials sont conservées après disconnect
        assert await manager.get_credentials(integration["id"]) == {"api_key": "k"}

    @pytest.mark.asyncio
    async def test_connect_missing_config_reports_error(self, manager):
        """connect() sans config requise → statut error + message explicite."""
        integration = await manager.register(
            name="no-creds",
            kind="web-search",
            metadata={"required_credentials": ["api_key"]},
        )
        result = await manager.connect(integration["id"])
        assert result["status"] == "error"
        assert "api_key" in result["health"]

    @pytest.mark.asyncio
    async def test_connect_disabled_rejected(self, manager):
        integration = await manager.register(name="off", kind="storage", enabled=False)
        with pytest.raises(IntegrationError, match="disabled"):
            await manager.connect(integration["id"])

    @pytest.mark.asyncio
    async def test_connect_unknown_raises(self, manager):
        with pytest.raises(IntegrationError, match="not found"):
            await manager.connect("does-not-exist")


# ── Healthcheck par kind (délégation MCP) ──────────────────────────────────


class TestHealthcheck:
    @pytest.mark.asyncio
    async def test_mcp_delegates_to_tool_servers(self):
        """Le healthcheck MCP délègue au ToolServerManager (pas de duplication)."""
        manager = IntegrationManager(
            store=CoreRecordStore(),
            tool_servers=FakeToolServers({"srv-1": {"name": "fs", "status": "connected"}}),
        )
        integration = await manager.register(
            name="mcp-fs",
            kind="mcp",
            config={"server_id": "srv-1"},
        )
        health = await manager.test_connection(integration["id"])
        assert health["connected"] is True
        assert "fs" in health["message"]

    @pytest.mark.asyncio
    async def test_mcp_bound_server_missing(self):
        manager = IntegrationManager(
            store=CoreRecordStore(), tool_servers=FakeToolServers({})
        )
        integration = await manager.register(
            name="mcp-lost", kind="mcp", config={"server_id": "gone"}
        )
        health = await manager.test_connection(integration["id"])
        assert health["connected"] is False
        assert "gone" in health["message"]

    @pytest.mark.asyncio
    async def test_missing_required_config_fails(self, manager):
        integration = await manager.register(
            name="storage-incomplete",
            kind="storage",
            config={"bucket": ""},
            metadata={"required_config": ["bucket"]},
        )
        health = await manager.test_connection(integration["id"])
        assert health["connected"] is False
        assert "bucket" in health["message"]
