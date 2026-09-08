"""Tests réels des routes /knowledge/collections (arbre, move, multi-retrieve)
et de la validation agent → knowledge_collection_ids (interfaces/api/routers/v1.py).

Exécute le vrai KnowledgeCollectionManager (CoreRecordStore mémoire) et le vrai
AgentManager via CoreDomainServices — aucun mock du domaine. Les gates
require_permission sont déclaratives et couvertes par la couche auth.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers import v1
from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


@pytest.fixture(autouse=True)
def real_collections():
    """Vrai KnowledgeCollectionManager + CoreDomainServices injectés."""
    store = CoreRecordStore()
    collections = KnowledgeCollectionManager(store=store, rag=RAGPipeline(store=store))
    v1.set_knowledge_collections(collections)
    v1.set_core_domain_services(v1.CoreDomainServices())
    yield collections
    v1.set_knowledge_collections(None)


def test_create_collection_with_parent_and_update_fields():
    """Création imbriquée + update icon/order via PUT."""
    parent = asyncio.run(v1.create_collection({"name": "Docs", "user_id": "alice"}))
    child = asyncio.run(v1.create_collection({
        "name": "API", "user_id": "alice", "parent_id": parent["id"], "icon": "folder",
    }))
    assert child["parent_id"] == parent["id"]
    assert child["icon"] == "folder"

    # Parent inconnu → 422
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_collection({"name": "Ghost", "parent_id": "nope"}))
    assert exc.value.status_code == 422

    updated = asyncio.run(v1.update_collection(child["id"], {"icon": "book", "order": 3}))
    assert updated["icon"] == "book"
    assert updated["order"] == 3


def test_tree_and_move_routes():
    """GET /tree renvoie l'arbre ; POST /move re-parente avec garde-fous."""
    root = asyncio.run(v1.create_collection({"name": "Root", "user_id": "alice"}))
    folder = asyncio.run(v1.create_collection({
        "name": "Folder", "parent_id": root["id"], "user_id": "alice",
    }))
    leaf = asyncio.run(v1.create_collection({
        "name": "Leaf", "parent_id": folder["id"], "user_id": "alice",
    }))

    tree = asyncio.run(v1.list_collections_tree(user_id="alice"))
    assert len(tree) == 1 and tree[0]["name"] == "Root"
    assert tree[0]["children"][0]["name"] == "Folder"
    assert tree[0]["children"][0]["children"][0]["name"] == "Leaf"

    # Cycle → 422
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.move_collection(root["id"], {"parent_id": leaf["id"]}))
    assert exc.value.status_code == 422

    # Move valide → racine
    moved = asyncio.run(v1.move_collection(folder["id"], {"parent_id": None}))
    assert moved["parent_id"] is None
    tree = asyncio.run(v1.list_collections_tree(user_id="alice"))
    assert {n["name"] for n in tree} == {"Root", "Folder"}  # tri alpha (order égal)


def test_retrieve_multi_route():
    """POST /knowledge/collections/retrieve-multi — un seul passage, union."""
    manager = v1.get_knowledge_collections()
    col_a = asyncio.run(manager.create_collection("A", user_id="alice"))
    doc_a = asyncio.run(manager._rag.ingest(
        "ETHAN is a headless intelligent runtime.",
        title="ETHAN", source="ethan.md",
    ))
    asyncio.run(manager.add_document(col_a["id"], doc_a.id))

    results = asyncio.run(v1.retrieve_collections_multi({
        "query": "ETHAN runtime", "collection_ids": [col_a["id"]],
    }))
    assert results and all(r["document_title"] == "ETHAN" for r in results)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.retrieve_collections_multi({
            "query": "q", "collection_ids": [col_a["id"], "ghost"],
        }))
    assert exc.value.status_code == 422


def test_agent_routes_validate_knowledge_collection_ids():
    """create/put agents : collections validées, compat metadata.knowledge_ids."""
    collections = v1.get_knowledge_collections()
    col = asyncio.run(collections.create_collection("Docs", user_id="alice"))

    # Création avec collections valides
    agent = asyncio.run(v1.create_agent({
        "name": "RAG Agent", "provider": "fake",
        "knowledge_collection_ids": [col["id"]],
    }))
    assert agent["knowledge_collection_ids"] == [col["id"]]

    # Compat ancienne convention metadata.knowledge_ids
    legacy = asyncio.run(v1.create_agent({
        "name": "Legacy", "metadata": {"knowledge_ids": [col["id"]]},
    }))
    assert legacy["knowledge_collection_ids"] == [col["id"]]

    # Collection inconnue → 422
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad", "knowledge_collection_ids": ["ghost"],
        }))
    assert exc.value.status_code == 422

    # Update avec validation
    updated = asyncio.run(v1.update_agent(agent["id"], {
        "knowledge_collection_ids": [],
    }))
    assert updated["knowledge_collection_ids"] == []

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.update_agent(agent["id"], {
            "knowledge_collection_ids": ["ghost"],
        }))
    assert exc.value.status_code == 422
