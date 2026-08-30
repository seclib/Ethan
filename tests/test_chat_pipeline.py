"""Contract tests for the Core-owned chat pipeline and message tree.

ETHAN Core owns chat persistence and orchestration.  These tests validate:
- the message tree contract (parent_id / children_ids / get_branch)
- the ChatPipeline orchestration (persistence + generation + branch)
- the streaming route contract (SSE events)
"""

from __future__ import annotations

import asyncio
import json

from core.chat import ChatPipeline
from core.state import CoreRecordStore
from core.state.chats import ChatStore


def test_chat_store_message_tree_branching():
    """Messages form a tree: editing creates children, get_branch returns the path."""

    async def scenario():
        store = ChatStore(store=CoreRecordStore())
        chat = await store.create_chat("Tree test", user_id="alice")

        # Racine : message utilisateur
        root = await store.add_message(chat["id"], "user", "Hello", user_id="alice")
        assert root["parent_id"] is None
        assert root["children_ids"] == []

        # Réponse assistant (enfant de root)
        assistant = await store.add_message(
            chat["id"], "assistant", "Hi!", user_id="alice", parent_id=root["id"]
        )
        assert assistant["parent_id"] == root["id"]

        # Branche alternative : régénération (nouvel enfant de root)
        regenerated = await store.add_message(
            chat["id"], "assistant", "Hello there!", user_id="alice", parent_id=root["id"]
        )
        assert regenerated["parent_id"] == root["id"]

        # Le parent référence ses deux enfants
        root_updated = await store.get_message(chat["id"], root["id"])
        assert root_updated is not None
        assert set(root_updated["children_ids"]) == {assistant["id"], regenerated["id"]}

        # get_branch remonte de la feuille à la racine
        branch = await store.get_branch(chat["id"], regenerated["id"])
        assert [m["id"] for m in branch] == [root["id"], regenerated["id"]]

        # get_branch sans message_id → feuille la plus récente
        latest_branch = await store.get_branch(chat["id"])
        assert latest_branch[-1]["id"] == regenerated["id"]

    asyncio.run(scenario())


def test_chat_pipeline_persists_user_and_assistant_messages():
    """ChatPipeline orchestrates: conversation, user message, generation, assistant message."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)  # ProviderManager None → fallback écho

        result = await pipeline.run(
            message="Bonjour ETHAN",
            user_id="alice",
            provider_id="ollama",
            model="qwen2.5-coder",
        )

        assert result["chat_id"]
        assert result["user_message"]["role"] == "user"
        assert result["user_message"]["content"] == "Bonjour ETHAN"
        assert result["assistant_message"]["role"] == "assistant"
        assert result["assistant_message"]["content"].startswith("[ECHO]")
        assert result["assistant_message"]["parent_id"] == result["user_message"]["id"]

        # La branche contient user → assistant
        branch = result["branch"]
        assert [m["role"] for m in branch] == ["user", "assistant"]

        # Les messages sont persistés dans le store Core
        messages = await chat_store.list_messages(result["chat_id"])
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    asyncio.run(scenario())


def test_chat_pipeline_reuses_existing_conversation():
    """ChatPipeline reuses an existing chat_id instead of creating a new one."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)

        first = await pipeline.run(message="Premier message", user_id="alice")
        second = await pipeline.run(
            message="Deuxième message", user_id="alice", chat_id=first["chat_id"]
        )

        assert second["chat_id"] == first["chat_id"]
        messages = await chat_store.list_messages(first["chat_id"])
        assert len(messages) == 4  # 2 tours : user + assistant × 2

        # La branche du second tour remonte jusqu'à la racine
        branch = second["branch"]
        assert [m["role"] for m in branch] == ["user", "assistant", "user", "assistant"]

    asyncio.run(scenario())


def test_chat_pipeline_unknown_chat_raises():
    """ChatPipeline rejects an unknown chat_id."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)

        try:
            await pipeline.run(message="Hello", chat_id="does-not-exist", user_id="alice")
            raise AssertionError("Expected ValueError for unknown chat_id")
        except ValueError as exc:
            assert "not found" in str(exc)

    asyncio.run(scenario())


def test_chat_store_update_message_streaming_state():
    """Messages support pending → done transitions during streaming."""
    async def scenario():
        store = ChatStore(store=CoreRecordStore())
        chat = await store.create_chat("Streaming", user_id="alice")
        user_msg = await store.add_message(chat["id"], "user", "Stream this", user_id="alice")

        # Message assistant créé en état pending (streaming en cours)
        assistant = await store.add_message(
            chat["id"],
            "assistant",
            content="",
            user_id="alice",
            parent_id=user_msg["id"],
            status="pending",
            done=False,
        )
        assert assistant["status"] == "pending"
        assert assistant["done"] is False

        # Mise à jour progressive du contenu
        await store.update_message(
            chat["id"], assistant["id"], {"content": "Hello", "status": "pending", "done": False}
        )
        await store.update_message(
            chat["id"], assistant["id"], {"content": "Hello world", "status": "done", "done": True}
        )

        final = await store.get_message(chat["id"], assistant["id"])
        assert final is not None
        assert final["content"] == "Hello world"
        assert final["status"] == "done"
        assert final["done"] is True

    asyncio.run(scenario())


def test_chat_store_pinned_and_archived_chats():
    """Chats support pinning (favorites) and archiving for the sidebar."""

    async def scenario():
        store = ChatStore(store=CoreRecordStore())
        chat = await store.create_chat("Favori", user_id="alice")

        await store.update_chat(chat["id"], {"pinned": True})
        pinned = await store.get_chat(chat["id"])
        assert pinned is not None
        assert pinned["pinned"] is True

        await store.update_chat(chat["id"], {"archived": True})
        archived = await store.get_chat(chat["id"])
        assert archived is not None
        assert archived["archived"] is True

        # Filtrage par état
        active = await store.list_chats(user_id="alice", archived=False)
        assert all(c["id"] != chat["id"] for c in active)

    asyncio.run(scenario())


# ── RAG scoped par collection (Open-WebUI-style Knowledge in chat) ────────────


class _FakeCollections:
    """Minimal fake of KnowledgeCollectionManager.build_context()."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def build_context(self, query: str, collection_id: str) -> str:
        self.calls.append((query, collection_id))
        return f"<context-collection:{collection_id}>"


def test_pipeline_injects_context_scoped_to_selected_collections():
    """knowledge_ids restringe le RAG aux collections sélectionnées."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        collections = _FakeCollections()

        class _FakeRag:
            async def build_context(self, query, *, top_k=None):
                return "GLOBAL-CONTEXT"  # ne doit pas être appelé

        pipeline = ChatPipeline(
            chat_store=chat_store,
            rag=_FakeRag(),  # type: ignore[arg-type]
            knowledge_collections=collections,
        )
        messages = await pipeline._build_llm_messages(
            chat_id="",
            user_message="question",
            user_id="alice",
            skill_ids=[],
            knowledge_ids=["col-a", "col-b"],
            file_ids=[],
        )
        text = "\n".join(m.content for m in messages)
        assert "<context-collection:col-a>" in text
        assert "<context-collection:col-b>" in text
        assert "GLOBAL-CONTEXT" not in text
        assert collections.calls == [("question", "col-a"), ("question", "col-b")]

    asyncio.run(scenario())


def test_pipeline_no_rag_when_no_collections_selected():
    """Sans collection sélectionnée et avec manager présent, pas de contexte RAG."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        collections = _FakeCollections()
        rag_called = False

        class _FakeRag:
            nonlocal_flag = None

            async def build_context(self, query, *, top_k=None):
                nonlocal rag_called
                rag_called = True
                return "GLOBAL-CONTEXT"

        pipeline = ChatPipeline(
            chat_store=chat_store,
            rag=_FakeRag(),  # type: ignore[arg-type]
            knowledge_collections=collections,
        )
        messages = await pipeline._build_llm_messages(
            chat_id="",
            user_message="question",
            user_id="alice",
            skill_ids=[],
            knowledge_ids=[],
            file_ids=[],
        )
        text = "\n".join(m.content for m in messages)
        assert rag_called is False
        assert "GLOBAL-CONTEXT" not in text
        assert collections.calls == []

    asyncio.run(scenario())


# ── Phase 2 : Chat → Tools/MCP et Chat → Agent ──────────────────────────────


class _FakeAgent:
    def __init__(self, agent_id: str) -> None:
        from core.agents.types import Agent

        self._agent = Agent(
            id=agent_id,
            name="Analyste",
            description="Analyse les données.",
            model="agent-model",
            provider="agent-provider",
            skill_ids=["skill-agent"],
        )

    async def get(self, agent_id: str):
        return self._agent if agent_id == self._agent.id else None


class _FakeToolManager:
    """ToolManager minimal : registry + executor simulés."""

    def __init__(self) -> None:
        from core.tools.types import Tool

        self.registry = type("R", (), {})()
        self.registry.get = lambda tid: (
            Tool(id="t1", name="web_search", description="Cherche sur le web")
            if tid in ("t1", "web_search")
            else None
        )
        self.registry.list_all = lambda: [self.registry.get("t1")]
        self.executor = type("E", (), {})()

        async def execute(tool, params, context):  # noqa: ANN001
            from core.tools.types import ToolResult

            return ToolResult(status="success", output=f"RESULT:{params}")

        self.executor.execute = execute


def test_agent_routing_resolves_provider_model_and_skills():
    """Chat → Agent : le pipeline résout provider/model et fusionne les skills."""

    async def scenario():
        store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=store)

        info = await pipeline._resolve_agent("agent-1")
        assert info is None  # pas d'AgentManager injecté

        pipeline.set_agent_manager(_FakeAgent("agent-1"))
        info = await pipeline._resolve_agent("agent-1")
        assert info is not None
        assert info["provider"] == "agent-provider"
        assert info["model"] == "agent-model"
        assert "skill-agent" in info["skill_ids"]

        # Agent inconnu → dégradé silencieusement (pas d'erreur).
        assert await pipeline._resolve_agent("unknown") is None

    asyncio.run(scenario())


def test_tools_section_lists_selected_tools():
    """Chat → Tools : le catalogue des outils sélectionnés est injecté."""

    def scenario():
        pipeline = ChatPipeline(chat_store=ChatStore(store=CoreRecordStore()))
        # Sans ToolManager → pas de section (et pas de crash).
        assert pipeline._build_tools_section(["t1"]) is None

        pipeline.set_tool_manager(_FakeToolManager())
        section = pipeline._build_tools_section(["t1"])
        assert section is not None
        assert "web_search" in section
        assert "<tool" in section

        # Aucun outil sélectionné → pas de section.
        assert pipeline._build_tools_section([]) is None

    scenario()


def test_execute_tool_call_runs_via_core_executor():
    """execute_tool_call résout par id ou par nom et exécute réellement."""

    async def scenario():
        pipeline = ChatPipeline(chat_store=ChatStore(store=CoreRecordStore()))
        pipeline.set_tool_manager(_FakeToolManager())

        by_id = await pipeline.execute_tool_call("t1", {"query": "ethan"})
        assert by_id["status"] == "success"
        assert "RESULT:" in by_id["output"]

        by_name = await pipeline.execute_tool_call("web_search", {"query": "x"})
        assert by_name["status"] == "success"

        missing = await pipeline.execute_tool_call("nope", {})
        assert missing["status"] == "failed"
        assert "Unknown tool" in missing["error"]

    asyncio.run(scenario())