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