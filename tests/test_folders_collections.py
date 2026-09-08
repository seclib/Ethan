"""Tests Core — Collections Knowledge & Dossiers (navigation local-first).

Vrai FolderManager + vrai KnowledgeCollectionManager + vrai KnowledgeManager
sur CoreRecordStore mémoire : aucun mock du domaine.  Couvre le périmètre
approuvé : création collection, dossier **dans** une collection, navigation
(filtre d'arbre), renommage, suppression (ré-parentage, ressources conservées),
chemins invalides et boundary filesystem (aucune écriture disque).
"""

from __future__ import annotations

import asyncio

import pytest

from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


@pytest.fixture()
def ctx(tmp_path):
    """Managers Core réels (store mémoire) + garde du répertoire racine."""
    store = CoreRecordStore()
    collections = KnowledgeCollectionManager(store=store, rag=RAGPipeline(store=store))
    knowledge = KnowledgeManager(store=store)
    folders = FolderManager(store=store, knowledge=knowledge, collections=collections)
    return {
        "folders": folders,
        "collections": collections,
        "knowledge": knowledge,
        "root": tmp_path,  # boundary : doit rester vide après toutes les opérations
    }


def test_collection_creation(ctx):
    """Une collection est un record Core (stratégie incluse), pas un dossier."""
    col = asyncio.run(ctx["collections"].create_collection(
        "OSINT", description="Sources ouvertes", retrieval_strategy="hybrid",
    ))
    assert col["name"] == "OSINT"
    assert col["retrieval_strategy"] == "hybrid"
    got = asyncio.run(ctx["collections"].get_collection(col["id"]))
    assert got is not None and got["id"] == col["id"]


def test_folder_inside_collection(ctx):
    """`collection_id` est une référence validée (fail-closed), dissociable."""
    col = asyncio.run(ctx["collections"].create_collection("Recon"))
    folder = asyncio.run(ctx["folders"].create_folder(
        "Sources", collection_id=col["id"],
    ))
    assert folder["collection_id"] == col["id"]

    # Collection inexistante → rejet (jamais de relation fantôme)
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(ctx["folders"].create_folder("Ghost", collection_id="nope"))

    # Dissociation explicite (None remet à racine de navigation)
    detached = asyncio.run(ctx["folders"].update_folder(
        folder["id"], collection_id=None,
    ))
    assert detached["collection_id"] is None


def test_folder_navigation_by_collection(ctx):
    """Le filtre d'arbre ne montre que les dossiers de la collection + ancêtres."""
    col_a = asyncio.run(ctx["collections"].create_collection("A"))
    col_b = asyncio.run(ctx["collections"].create_collection("B"))

    parent_a = asyncio.run(ctx["folders"].create_folder("PA", collection_id=col_a["id"]))
    asyncio.run(ctx["folders"].create_folder(
        "PA-child", parent_id=parent_a["id"], collection_id=col_a["id"],
    ))
    asyncio.run(ctx["folders"].create_folder("PB", collection_id=col_b["id"]))
    asyncio.run(ctx["folders"].create_folder("Sans collection"))

    tree_a = asyncio.run(ctx["folders"].list_tree(collection_id=col_a["id"]))
    names_a = {n["name"] for n in tree_a}
    assert "PA" in names_a and "PB" not in names_a
    pa = next(n for n in tree_a if n["name"] == "PA")
    assert {c["name"] for c in pa["children"]} == {"PA-child"}

    # Vue globale : tout est présent (le filtre ne détruit rien)
    full = asyncio.run(ctx["folders"].list_tree())
    assert len(full) == 3


def test_rename_folder_and_collection(ctx):
    col = asyncio.run(ctx["collections"].create_collection("Old"))
    folder = asyncio.run(ctx["folders"].create_folder("F1", collection_id=col["id"]))

    renamed_folder = asyncio.run(ctx["folders"].rename_folder(folder["id"], "F2"))
    assert renamed_folder["name"] == "F2"

    renamed_col = asyncio.run(ctx["collections"].update_collection(
        col["id"], {"name": "New"},
    ))
    assert renamed_col["name"] == "New"

    with pytest.raises(ValueError):
        asyncio.run(ctx["folders"].rename_folder(folder["id"], "  "))


def test_delete_folder_reparents_and_keeps_resources(ctx):
    """Supprimer un dossier : sous-dossiers ré-attachés au grand-parent,
    ressources conservées (relation, pas possession)."""
    col = asyncio.run(ctx["collections"].create_collection("C"))
    root = asyncio.run(ctx["folders"].create_folder("Root", collection_id=col["id"]))
    mid = asyncio.run(ctx["folders"].create_folder("Mid", parent_id=root["id"]))
    leaf = asyncio.run(ctx["folders"].create_folder("Leaf", parent_id=mid["id"]))

    node = asyncio.run(ctx["knowledge"].create(
        "Playbook", content="osint steps",
    ))
    asyncio.run(ctx["folders"].attach_resource(mid["id"], "knowledge", node.id))

    deleted = asyncio.run(ctx["folders"].delete_folder(mid["id"]))
    assert deleted["id"] == mid["id"]

    # Leaf ré-attachée au grand-parent (root), ressource intacte et non classée
    leaf_after = asyncio.run(ctx["folders"].get_folder(leaf["id"]))
    assert leaf_after["parent_id"] == root["id"]
    kept = asyncio.run(ctx["knowledge"].get(node.id))
    assert kept is not None
    assert asyncio.run(ctx["folders"].list_folder_resources(root["id"])) == []

    # Le dossier supprimé disparaît ; la collection et root subsistent
    assert asyncio.run(ctx["folders"].get_folder(mid["id"])) is None
    assert asyncio.run(ctx["collections"].get_collection(col["id"])) is not None


def test_invalid_paths_rejected(ctx):
    """Nom vide, parent inconnu, collection inconnue : tous rejetés."""
    with pytest.raises(ValueError):
        asyncio.run(ctx["folders"].create_folder("   "))
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(ctx["folders"].create_folder("X", parent_id="ghost"))
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(ctx["folders"].create_folder("X", collection_id="ghost"))
    col = asyncio.run(ctx["collections"].create_collection("K"))
    folder = asyncio.run(ctx["folders"].create_folder("K1", collection_id=col["id"]))
    with pytest.raises(ValueError):
        asyncio.run(ctx["folders"].update_folder(
            folder["id"], parent_id=folder["id"],  # cycle
        ))


def test_filesystem_boundary_untouched(ctx, tmp_path):
    """Boundary racine : dossiers/collections = records Core ; AUCUNE écriture
    disque, aucun répertoire créé — le stockage physique reste sous le contrôle
    exclusif de FileStore (hors périmètre de ce module)."""
    col = asyncio.run(ctx["collections"].create_collection("FS"))
    asyncio.run(ctx["folders"].create_folder(
        "../escape", description="../../etc/passwd", collection_id=col["id"],
    ))
    tree = asyncio.run(ctx["folders"].list_tree(collection_id=col["id"]))
    # Le nom est une donnée libre, jamais un chemin : rien n'a été résolu/traversé
    assert tree[0]["name"] == "../escape"
    assert list(tmp_path.iterdir()) == []

