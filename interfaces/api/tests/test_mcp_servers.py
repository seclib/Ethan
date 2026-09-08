"""Tests MCP Servers — gestion réelle des serveurs avec secrets protégés.

Aucun mock de protocole : le test de synchronisation utilise un VRAI serveur
MCP (SDK officiel `mcp`, transport stdio, voir mcp_echo_stdio_server.py).

Couverture :
  - secrets : token jamais présent dans les réponses ni les events
    (auth_config → {token_set}, headers → header_keys) ; conservé en store
  - update sans nouveau token → secret conservé ; avec → remplacé + masqué
  - enabled bascule via update
  - sync_tools avec un VRAI serveur MCP stdio → tool `echo` découvert,
    statut connected, tool enregistré dans le registre (provider mcp)
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.tools.mcp_client import MCP_AVAILABLE
from core.tools.registry import ToolRegistry
from core.tools.servers import ToolServerManager

ECHO_SERVER_SCRIPT = str(Path(__file__).parent / "mcp_echo_stdio_server.py")
SECRET = "super-secret-token-42"


class _RecordingBus(EventBus):
    """EventBus minimal qui capture les events (vérification anti-secret)."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    async def connect(self, servers: str | None = None) -> None:
        return None

    async def publish(self, subject: str, event: Event) -> None:
        self.events.append(event)

    async def subscribe(self, pattern: str, handler, queue: str | None = None):
        return None

    async def request(self, subject: str, event: Event, timeout: float = 30.0):
        return None

    async def close(self) -> None:
        return None

    @property
    def is_connected(self) -> bool:
        return True


def _manager(bus: _RecordingBus | None = None) -> ToolServerManager:
    return ToolServerManager(
        event_bus=bus or _RecordingBus(),
        registry=ToolRegistry(),
    )


def test_register_masks_token_in_response_and_event():
    async def scenario():
        bus = _RecordingBus()
        manager = _manager(bus)
        server = await manager.register(
            name="sec-server",
            url="http://127.0.0.1:9/mcp",
            auth_type="bearer",
            auth_config={"token": SECRET},
        )
        # Réponse publique : pas de secret, seulement le fait qu'il existe.
        assert server["auth_config"] == {"token_set": True}
        assert SECRET not in json.dumps(server)
        # Event : version publique uniquement (règle repo — pas de secret dans
        # les events).
        registered = [
            e for e in bus.events if e.type == EventType.TOOL_SERVER_REGISTERED
        ]
        assert registered, "l'événement d'enregistrement doit être publié"
        assert SECRET not in json.dumps(registered[-1].payload)
        # Le store de configuration dédié conserve le secret (usage interne).
        raw = await manager._get_private(server["id"])
        assert raw["auth_config"]["token"] == SECRET

    asyncio.run(scenario())


def test_update_without_token_keeps_secret_and_masks_headers():
    async def scenario():
        manager = _manager()
        server = await manager.register(
            name="h-server",
            url="http://127.0.0.1:9/mcp",
            auth_type="bearer",
            auth_config={"token": SECRET},
            metadata={"headers": {"Authorization": "Bearer " + SECRET}},
        )
        # Mise à jour SANS token ni headers → conservés côté store, masqués
        # dans la réponse.
        updated = await manager.update(server["id"], {"name": "h-server-2"})
        assert updated["name"] == "h-server-2"
        assert updated["auth_config"] == {"token_set": True}
        assert SECRET not in json.dumps(updated)
        assert updated["metadata"]["header_keys"] == ["Authorization"]
        assert "headers" not in updated["metadata"]
        raw = await manager._get_private(server["id"])
        assert raw["auth_config"]["token"] == SECRET
        assert raw["metadata"]["headers"]["Authorization"] == "Bearer " + SECRET

        # Mise à jour AVEC un nouveau token → remplacé, réponse masquée.
        updated2 = await manager.update(
            server["id"], {"auth_config": {"token": "new-token"}}
        )
        assert "new-token" not in json.dumps(updated2)
        raw2 = await manager._get_private(server["id"])
        assert raw2["auth_config"]["token"] == "new-token"

    asyncio.run(scenario())


def test_enabled_toggle_via_update():
    async def scenario():
        manager = _manager()
        server = await manager.register(name="t", url="http://127.0.0.1:9/mcp")
        assert server["enabled"] is True
        updated = await manager.update(server["id"], {"enabled": False})
        assert updated["enabled"] is False
        listed = await manager.list(enabled=True)
        assert all(s["id"] != server["id"] for s in listed)

    asyncio.run(scenario())


@pytest.mark.skipif(not MCP_AVAILABLE, reason="SDK `mcp` non installé")
def test_sync_with_real_mcp_stdio_server():
    """Round-trip complet avec un VRAI serveur MCP (stdio, SDK officiel)."""

    async def scenario():
        manager = _manager()
        server = await manager.register(
            name="echo-real",
            url="stdio://ethan-echo-test",
            metadata={
                "transport": "stdio",
                "command": sys.executable,
                "args": [ECHO_SERVER_SCRIPT],
            },
        )
        tools = await manager.sync_tools(server["id"])
        assert [t["name"] for t in tools] == ["echo"]
        assert tools[0]["parameters"]["properties"]["message"]["type"] == "string"

        public = await manager.get(server["id"])
        assert public["status"] == "connected"
        assert public["last_connected_at"] is not None

        registered_tool = manager._registry.get(f"mcp_{server['id']}_echo")
        assert registered_tool is not None
        assert registered_tool.provider == "mcp"
        assert registered_tool.metadata["mcp_server_id"] == server["id"]

    asyncio.run(scenario())
