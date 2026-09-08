"""Tests réels des routes /v1/folders et de la validation agent → folder_ids
(interfaces/api/routers/folders.py et routers/v1.py).

Exécute le vrai FolderManager branché sur de vrais managers Core
(KnowledgeCollectionManager, KnowledgeManager) via CoreRecordStore mémoire —
aucun mock du domaine.  Les gates require_permission sont déclaratives et
couvertes par la couche auth.
"""

from __future__ import annotations

import asyncio

import pytest
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from fastapi import HTTPException
from interfaces.api.routers import folders as folders_module
from interfaces.api.routers.folders import (
    set_folder_manager,
)
from routers import v1


@pytest.fixture()
def folders():
    """Vrai FolderManager (providers Core réels) + wiring v1 pour les agents."""
    store = CoreRecordStore()
    collections = KnowledgeCollectionManager(
        store=store, rag=RAGPipeline(store=store)
    )
    manager = FolderManager(
        store=store,
        knowledge=KnowledgeManager(store=store),
        collections=collections,
    )
    set_folder_manager(manager)
    v1.set_knowledge_collections(collections)
    v1.set_core_domain_services(v1.CoreDomainServices())
    yield manager
    set_folder_manager(None)
    v1.set_knowledge_collections(None)


def test_folder_crud_routes(folders):
    """Création (nom libre), rename/description via PATCH, delete via DELETE."""
    folder = asyncio.run(folders_mod().create_folder(
        {"name": "OSINT", "user_id": "alice", "description": "Recon tools"}
    ))
    assert folder["name"] == "OSINT" and folder["parent_id"] is None

    # Nom vide → 422
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().create_folder({"name": "  "}))
    assert exc.value.status_code == 422

    # PATCH : rename + description
    updated = asyncio.run(folders_mod().update_folder(
        folder["id"], {"name": "Recon", "description": "Forensic & recon"}
    ))
    assert updated["name"] == "Recon"
    assert updated["description"] == "Forensic & recon"

    # GET inconnu → 404
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().get_folder("ghost"))
    assert exc.value.status_code == 404

    # DELETE
    result = asyncio.run(folders_mod().delete_folder(folder["id"]))
    assert result["status"] == "deleted"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().delete_folder(folder["id"]))
    assert exc.value.status_code == 404


def folders_mod():
    """Référence au module du router (même instance que v1.py)."""
    return folders_module


def test_tree_move_and_hierarchy_routes(folders):
    """Sous-dossiers + arbre + move avec garde-fous (cycles → 422)."""
    root = asyncio.run(
        folders_mod().create_folder({"name": "OSINT", "user_id": "alice"})
    )
    child = asyncio.run(folders_mod().create_folder(
        {"name": "Recon", "parent_id": root["id"], "user_id": "alice"}
    ))

    tree = asyncio.run(folders_mod().list_folders_tree(user_id="alice"))
    assert tree[0]["name"] == "OSINT"
    assert tree[0]["children"][0]["name"] == "Recon"

    # Cycle → 422 (root sous son descendant)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().move_folder(root["id"], {"parent_id": child["id"]}))
    assert exc.value.status_code == 422

    # Move vers la racine
    asyncio.run(folders_mod().move_folder(child["id"], {"parent_id": None}))


def test_resource_classification_routes(folders):
    """Classement multi-dossiers, résolution réelle, move-resource, untagged."""
    collections = v1.get_knowledge_collections()
    collection = asyncio.run(collections.create_collection("Docs"))
    osint = asyncio.run(folders_mod().create_folder({"name": "OSINT"}))
    code = asyncio.run(folders_mod().create_folder({"name": "Code"}))

    # Attach réel d'une collection RAG (provider Core) — ressource fantôme → 404
    membership = asyncio.run(folders_mod().attach_resource(
        osint["id"], {"resource_type": "collection", "resource_id": collection["id"]}
    ))
    assert membership["resource_type"] == "collection"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().attach_resource(
            osint["id"], {"resource_type": "collection", "resource_id": "ghost"}
        ))
    assert exc.value.status_code == 404

    # Résolution du contenu classé
    content = asyncio.run(
        folders_mod().list_folder_resources(osint["id"], resource_type=None)
    )
    assert content[0]["record"]["id"] == collection["id"]

    # Multi-membership + move-resource
    asyncio.run(folders_mod().attach_resource(
        code["id"], {"resource_type": "collection", "resource_id": collection["id"]}
    ))
    folders_of = asyncio.run(
        folders_mod().list_folders_of_resource("collection", collection["id"])
    )
    assert {f["name"] for f in folders_of} == {"OSINT", "Code"}

    result = asyncio.run(folders_mod().move_resource_between_folders({
        "resource_type": "collection",
        "resource_id": collection["id"],
        "folder_ids": [code["id"]],
    }))
    assert result["folder_ids"] == [code["id"]]

    # Sans dossier : folder_ids vide + untagged
    asyncio.run(folders_mod().move_resource_between_folders({
        "resource_type": "collection",
        "resource_id": collection["id"],
        "folder_ids": [],
    }))
    untagged = asyncio.run(
        folders_mod().list_untagged_resources(resource_type="collection")
    )
    assert any(c["id"] == collection["id"] for c in untagged)

    # Type inconnu → 422
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().list_untagged_resources(resource_type="ghost"))
    assert exc.value.status_code == 422

    # Detach route
    asyncio.run(folders_mod().attach_resource(
        code["id"], {"resource_type": "collection", "resource_id": collection["id"]}
    ))
    detached = asyncio.run(
        folders_mod().detach_resource(code["id"], "collection", collection["id"])
    )
    assert detached["status"] == "detached"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            folders_mod().detach_resource(code["id"], "collection", collection["id"])
        )
    assert exc.value.status_code == 404


def test_folder_index_route(folders):
    """GET /v1/folders/index — mapping batch ressource → dossiers (filtrage)."""
    collections = v1.get_knowledge_collections()
    collection = asyncio.run(collections.create_collection("Docs"))
    osint = asyncio.run(folders_mod().create_folder({"name": "OSINT"}))
    code = asyncio.run(folders_mod().create_folder({"name": "Code"}))
    for folder_id in (osint["id"], code["id"]):
        asyncio.run(folders_mod().attach_resource(
            folder_id,
            {"resource_type": "collection", "resource_id": collection["id"]},
        ))

    index = asyncio.run(
        folders_mod().get_folder_index(resource_type="collection")
    )
    assert set(index[collection["id"]]) == {osint["id"], code["id"]}

    # Type sans classement → index vide ; type inconnu → 422
    assert asyncio.run(folders_mod().get_folder_index(resource_type="skill")) == {}
    with pytest.raises(HTTPException) as exc:
        asyncio.run(folders_mod().get_folder_index(resource_type="ghost"))
    assert exc.value.status_code == 422


def test_agent_routes_validate_folder_ids(folders):
    """create/put agents : folder_ids validés (dossier inconnu → 422)."""
    folder = asyncio.run(folders_mod().create_folder({"name": "OSINT"}))

    agent = asyncio.run(v1.create_agent({
        "name": "Recon Agent", "provider": "fake", "folder_ids": [folder["id"]],
    }))
    assert agent["folder_ids"] == [folder["id"]]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad", "folder_ids": ["ghost"],
        }))
    assert exc.value.status_code == 422

    updated = asyncio.run(v1.update_agent(agent["id"], {"folder_ids": []}))
    assert updated["folder_ids"] == []

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.update_agent(agent["id"], {"folder_ids": ["ghost"]}))
    assert exc.value.status_code == 422
