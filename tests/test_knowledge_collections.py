"""Contract tests for Core-owned knowledge collections and memory injection."""

from __future__ import annotations

import asyncio

from core.chat import ChatPipeline
from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from core.state.chats import ChatStore
from core.state.webui_store import CoreWebUIStore


def test_knowledge_collection_groups_rag_documents():
    """Collections group RAG documents and scope retrieval."""

    async def scenario():
        store = CoreRecordStore()
        rag = RAGPipeline(store=store)
        manager = KnowledgeCollectionManager(store=store, rag=rag)

        # Créer une collection
        collection = await manager.create_collection(
            "Documentation ETHAN", "Docs du projet", user_id="alice"
        )
        assert collection["name"] == "Documentation ETHAN"
        assert collection["document_ids"] == []

        # Ingérer un document RAG et l'attacher
        document = await rag.ingest(
            "ETHAN Core owns the chat pipeline and RAG retrieval.",
            title="Architecture",
            source="architecture.md",
        )
        updated = await manager.add_document(collection["id"], document.id)
        assert updated is not None
        assert document.id in updated["document_ids"]

        # Lister les documents de la collection
        documents = await manager.list_documents(collection["id"])
        assert len(documents) == 1
        assert documents[0]["title"] == "Architecture"

        # Détacher le document
        detached = await manager.remove_document(collection["id"], document.id)
        assert detached is not None
        assert document.id not in detached["document_ids"]

    asyncio.run(scenario())


def test_knowledge_collection_retrieval_scoped():
    """Retrieval is restricted to the collection's documents."""

    async def scenario():
        store = CoreRecordStore()
        rag = RAGPipeline(store=store)
        manager = KnowledgeCollectionManager(store=store, rag=rag)

        collection = await manager.create_collection("Docs", user_id="alice")

        # Document dans la collection
        doc_in = await rag.ingest(
            "ETHAN is a headless intelligent runtime.",
            title="ETHAN",
            source="ethan.md",
        )
        await manager.add_document(collection["id"], doc_in.id)

        # Document hors collection
        await rag.ingest(
            "Open-WebUI is a chat interface.",
            title="OpenWebUI",
            source="openwebui.md",
        )

        # Retrieval scoped : seuls les chunks du document de la collection
        # sont retournés (le chunking peut produire plusieurs fragments).
        results = await manager.retrieve("ETHAN runtime", collection["id"])
        assert len(results) > 0
        assert all(r["document_title"] == "ETHAN" for r in results)
        assert all(r["document_source"] == "ethan.md" for r in results)

    asyncio.run(scenario())


def test_chat_pipeline_injects_memory_facts():
    """Memory facts are injected into the system prompt, distinct from RAG."""

    async def scenario():
        store = CoreRecordStore()
        webui_store = CoreWebUIStore(store=store)
        chat_store = ChatStore(store=store)

        # Créer un fait mémoire
        await webui_store.create_fact({
            "subject": "l'utilisateur",
            "predicate": "préfère",
            "object": "Python",
            "category": "preference",
        })

        pipeline = ChatPipeline(chat_store=chat_store, memory_store=webui_store)

        # Construire les messages LLM
        messages = await pipeline._build_llm_messages(
            chat_id="",
            user_message="Bonjour",
            user_id="alice",
            skill_ids=None,
            knowledge_ids=None,
            file_ids=None,
        )

        # Le system prompt contient les faits mémoire
        system_messages = [m for m in messages if m.role == "system"]
        assert len(system_messages) == 1
        assert "Faits mémoire utilisateur" in system_messages[0].content
        assert "l'utilisateur préfère Python" in system_messages[0].content

    asyncio.run(scenario())


def test_chat_pipeline_without_memory_store_has_no_facts():
    """Without a memory store, no facts are injected."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)

        messages = await pipeline._build_llm_messages(
            chat_id="",
            user_message="Bonjour",
            user_id="alice",
            skill_ids=None,
            knowledge_ids=None,
            file_ids=None,
        )

        system_messages = [m for m in messages if m.role == "system"]
        assert len(system_messages) == 0

    asyncio.run(scenario())