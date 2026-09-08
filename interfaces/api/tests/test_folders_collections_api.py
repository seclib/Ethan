"""Tests API — Collections & Dossiers (navigation local-first).

Exécute les vrais routers (folders.py + v1.py collections) branchés sur de
vrais managers Core via CoreRecordStore mémoire.  La gate RBAC est testée
directement (require_permission → 403 sans token, sans rôle autorisé).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from core.auth import Permission
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from interfaces.api.auth import require_permission
from interfaces.api.routers import folders as folders_router
from interfaces.api.routers import v1


@pytest.fixture()
def api():
    """Wiring réel : FolderManager + KnowledgeCollectionManager + routes."""
    store = CoreRecordStore()
    collections = KnowledgeCollectionManager(store=store, rag=RAGPipeline(store=store))
    folders = FolderManager(
        store=store,
        knowledge=KnowledgeManager(store=store),
        collections=collections,
    )
    folders_router.set_folder_manager(folders)
    v1.set_knowledge_collections(collections)
    yield {
        "folders": folders,
        "collections": collections,
        "knowledge": KnowledgeManager(store=store),
        "store": store,
    }
    folders_router.set_folder_manager(None)
    v1.set_knowledge_collections(None)


def _fake_request(role: str | None):
    payload = {} if role is None else {"role": role}
    return SimpleNamespace(state=SimpleNamespace(token_payload=payload))


def test_collection_create_rename_metadata_routes(api):
    """POST /v1/knowledge/collections → PUT rename → GET metadata."""
    col = asyncio.run(v1.create_collection({
        "name": "Forensic", "description": "DFIR", "retrieval_strategy": "semantic",
    }))
    assert col["retrieval_strategy"] == "semantic"

    updated = asyncio.run(v1.update_collection(col["id"], {"name": "DFIR"}))
    assert updated["name"] == "DFIR"

    got = asyncio.run(v1.get_collection(col["id"]))
    assert got["description"] == "DFIR"


def test_folder_inside_collection_routes(api):
    """POST /v1/folders avec collection_id ; PATCH dissociation ;
    GET /v1/folders/tree?collection_id= filtre la navigation."""
    col = asyncio.run(v1.create_collection({"name": "OSINT"}))
    other = asyncio.run(v1.create_collection({"name": "Code"}))

    folder = asyncio.run(folders_router.create_folder({
        "name": "Sources", "user_id": "alice", "collection_id": col["id"],
    }))
    assert folder["collection_id"] == col["id"]

    # collection inconnue → 404 (convention router : id inexistant)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_router.create_folder({
            "name": "Ghost", "collection_id": "ghost-id",
        }))
    assert exc.value.status_code == 404

    tree = asyncio.run(folders_router.list_folders_tree(collection_id=col["id"]))
    assert {n["name"] for n in tree} == {"Sources"}

    # Dissociation → le dossier quitte la vue de la collection
    asyncio.run(folders_router.update_folder(
        folder["id"], {"collection_id": None},
    ))
    assert asyncio.run(folders_router.list_folders_tree(collection_id=col["id"])) == []


def test_folder_resources_route(api):
    """Les ressources classées sont résolues par le Core (aucune copie)."""
    node = asyncio.run(api["knowledge"].create("Playbook", content="steps…"))
    folder = asyncio.run(folders_router.create_folder({"name": "Docs"}))
    asyncio.run(folders_router.attach_resource(
        folder["id"], {"resource_type": "knowledge", "resource_id": node.id},
    ))
    resolved = asyncio.run(folders_router.list_folder_resources(folder["id"]))
    assert resolved[0]["resource_type"] == "knowledge"
    assert resolved[0]["record"]["id"] == node.id


def test_delete_folder_route_keeps_resources(api):
    node = asyncio.run(api["knowledge"].create("N", content="c"))
    folder = asyncio.run(folders_router.create_folder({"name": "F"}))
    asyncio.run(folders_router.attach_resource(
        folder["id"], {"resource_type": "knowledge", "resource_id": node.id},
    ))
    result = asyncio.run(folders_router.delete_folder(folder["id"]))
    assert result["status"] == "deleted"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_router.delete_folder(folder["id"]))
    assert exc.value.status_code == 404
    # La ressource survit (relation supprimée, pas la ressource)
    assert asyncio.run(api["knowledge"].get(node.id)).id == node.id


def test_folder_mutations_require_memory_permission():
    """Gate RBAC : sans token → 403 ; rôle autorisé → passe."""
    checker = require_permission(Permission.MEMORY)
    with pytest.raises(HTTPException) as exc:
        checker(_fake_request(None))
    assert exc.value.status_code == 403
    assert "Permission requise" in exc.value.detail
    assert checker(_fake_request("admin")) is True
