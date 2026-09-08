"""Tests Core — arborescence de collections (dossiers organisables).

Complète tests/test_knowledge_collections.py : hiérarchie libre créée par
l'utilisateur (parent_id), détection de cycles, move, tree et retrieve multi
collections en un seul passage RAG.
"""

from __future__ import annotations

import asyncio

import pytest

from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


def _manager() -> KnowledgeCollectionManager:
    store = CoreRecordStore()
    return KnowledgeCollectionManager(store=store, rag=RAGPipeline(store=store))


def test_collection_hierarchy_create_and_tree():
    """L'utilisateur crée librement des dossiers imbriqués (aucune seed)."""

    async def scenario():
        manager = _manager()
        roots = await manager.list_tree()
        assert roots == []  # aucune collection prédéfinie

        docs = await manager.create_collection("Docs", user_id="alice")
        api = await manager.create_collection(
            "API", user_id="alice", parent_id=docs["id"], icon="folder", order=2
        )
        internals = await manager.create_collection(
            "Internals", user_id="alice", parent_id=docs["id"], order=1
        )

        tree = await manager.list_tree(user_id="alice")
        assert [n["name"] for n in tree] == ["Docs"]
        children = tree[0]["children"]
        # Tri par order puis name
        assert [c["name"] for c in children] == ["Internals", "API"]
        assert children[0]["children"] == []
        assert internals["parent_id"] == docs["id"]
        assert api["icon"] == "folder"

    asyncio.run(scenario())


def test_collection_create_unknown_parent_rejected():
    """Impossible de créer une collection sous un parent inexistant."""

    async def scenario():
        manager = _manager()
        with pytest.raises(ValueError, match="not found"):
            await manager.create_collection("Orphelin", parent_id="nope")

    asyncio.run(scenario())


def test_collection_move_and_cycle_protection():
    """Re-parenting validé : parent inconnu, self-parent et cycle rejetés."""

    async def scenario():
        manager = _manager()
        root = await manager.create_collection("Root", user_id="alice")
        child = await manager.create_collection("Child", parent_id=root["id"])
        grandchild = await manager.create_collection("GrandChild", parent_id=child["id"])

        # Move valide : grandchild sous root
        moved = await manager.move_collection(grandchild["id"], root["id"])
        assert moved["parent_id"] == root["id"]

        # Self-parent
        with pytest.raises(ValueError, match="own parent"):
            await manager.move_collection(root["id"], root["id"])

        # Cycle : root sous son descendant grandchild
        with pytest.raises(ValueError, match="descendant"):
            await manager.move_collection(root["id"], grandchild["id"])

        # Parent inconnu
        with pytest.raises(ValueError, match="not found"):
            await manager.move_collection(child["id"], "ghost")

        # Retour à la racine
        back = await manager.move_collection(child["id"], None)
        assert back["parent_id"] is None

    asyncio.run(scenario())


def test_collection_delete_reparents_children():
    """Supprimer un dossier rattache ses enfants au grand-parent."""

    async def scenario():
        manager = _manager()
        root = await manager.create_collection("Root", user_id="alice")
        folder = await manager.create_collection("Folder", parent_id=root["id"])
        leaf = await manager.create_collection("Leaf", parent_id=folder["id"])

        assert await manager.delete_collection(folder["id"]) is True

        leaf_after = await manager.get_collection(leaf["id"])
        assert leaf_after["parent_id"] == root["id"]

        tree = await manager.list_tree()
        assert [c["name"] for c in tree[0]["children"]] == ["Leaf"]

    asyncio.run(scenario())


def test_retrieve_multi_scopes_union_of_collections():
    """retrieve_multi : un seul passage RAG, union des documents des collections."""

    async def scenario():
        store = CoreRecordStore()
        rag = RAGPipeline(store=store)
        manager = KnowledgeCollectionManager(store=store, rag=rag)

        col_a = await manager.create_collection("A", user_id="alice")
        col_b = await manager.create_collection("B", user_id="alice")

        doc_a = await rag.ingest(
            "ETHAN is a headless intelligent runtime.",
            title="ETHAN",
            source="ethan.md",
        )
        doc_b = await rag.ingest(
            "Grafana dashboards visualize observability metrics.",
            title="Grafana",
            source="grafana.md",
        )
        await rag.ingest(
            "Open-WebUI is a chat interface.",
            title="OpenWebUI",
            source="openwebui.md",
        )  # hors collections
        await manager.add_document(col_a["id"], doc_a.id)
        await manager.add_document(col_b["id"], doc_b.id)

        # Un seul passage, scope = union des deux collections : chaque
        # collection répond à sa requête depuis le même appel multi.
        results_a = await manager.retrieve_multi(
            "ETHAN headless runtime", [col_a["id"], col_b["id"]]
        )
        titles_a = {r["document_title"] for r in results_a}
        assert titles_a == {"ETHAN"}

        results_b = await manager.retrieve_multi(
            "Grafana observability metrics", [col_a["id"], col_b["id"]]
        )
        titles_b = {r["document_title"] for r in results_b}
        assert titles_b == {"Grafana"}

        # Collection inconnue → erreur
        with pytest.raises(ValueError, match="not found"):
            await manager.retrieve_multi("q", [col_a["id"], "ghost"])

        # Liste vide → aucun résultat, aucun appel RAG
        assert await manager.retrieve_multi("q", []) == []

        # build_context_multi
        context = await manager.build_context_multi("ETHAN", [col_a["id"]])
        assert "[1] ETHAN" in context

    asyncio.run(scenario())
