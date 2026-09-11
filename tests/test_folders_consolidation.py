"""Tests Core — consolidation de dossiers (merge / copy / move / to-collection).

La consolidation opère sur des RELATIONS (jamais sur des données) : une
ressource est identifiée par id, donc aucun écrasement ni conflit de nom
n'est possible — les modes diffèrent uniquement par le devenir des
classifications existantes :

* merge  → contenu des sources re-classé vers la cible ;
* copy   → ajout de la cible, classifications existantes conservées ;
* move   → la cible devient l'unique dossier de la ressource ;
* to-collection → dossier converti en collection Knowledge (pipeline officiel).

Chaque opération retourne un rapport (operation_id, status completed /
partially_completed / failed, compteurs, errors) — les partiels sont
transparents, jamais masqués.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from core.folders.manager import _utc_now
from uuid import uuid4

_MEMBERSHIPS = "folder-memberships"


class _FakeSkillStore:
    """Double minimal du SkillStore (protocole get_skill/list_skills)."""

    def __init__(self) -> None:
        self._skills: dict[str, dict] = {}

    def add(self, skill: dict) -> None:
        self._skills[skill["id"]] = skill

    async def get_skill(self, skill_id: str):
        return self._skills.get(skill_id)

    async def list_skills(self):
        return list(self._skills.values())


def _manager(
    store: CoreRecordStore | None = None,
    *,
    with_knowledge: bool = False,
    knowledge: Any = None,
    collections: Any = None,
):
    """FolderManager minimal (provider skill suffit pour merge/copy/move).

    ``with_knowledge=True`` branche de vrais managers Knowledge/Collections
    (nécessaire pour ``folder_to_collection`` qui crée une collection).
    ``knowledge=/collections=`` permet d'injecter des doubles (utile pour
    des tests unitaires sans dépendre du pipeline RAG lourd).
    """
    store = store or CoreRecordStore()
    skills = _FakeSkillStore()
    kwargs: dict = {"store": store, "skills": skills}
    if knowledge is not None:
        kwargs["knowledge"] = knowledge
    if collections is not None:
        kwargs["collections"] = collections
    if with_knowledge and knowledge is None and collections is None:
        knowledge = KnowledgeManager(store=store)
        collections = KnowledgeCollectionManager(store=store, rag=RAGPipeline(store=store))
        kwargs["knowledge"] = knowledge
        kwargs["collections"] = collections
    manager = FolderManager(**kwargs)
    return manager, skills, store, collections


# ── Doubles légers pour folder_to_collection (sans pipeline RAG lourd) ───────


class _FakeKnowledgeManager:
    """Double minimal : expose get/list pour le provider resource 'knowledge'."""

    def __init__(self, docs: dict[str, dict] | None = None) -> None:
        self._docs: dict[str, dict] = dict(docs or {})

    async def get(self, doc_id: str):
        return self._docs.get(doc_id)

    async def list(self):
        return list(self._docs.values())


class _FakeCollectionsManager:
    """Double minimal : expose la surface utilisée par folder_to_collection."""

    def __init__(self) -> None:
        self._collections: dict[str, dict] = {}
        self._documents: dict[str, list[dict]] = {}

    async def create_collection(self, name: str, description: str = "", user_id: str = "anonymous"):
        collection = {
            "id": str(uuid4()),
            "name": name,
            "description": description,
            "user_id": user_id,
            "created_at": _utc_now(),
        }
        self._collections[collection["id"]] = collection
        self._documents[collection["id"]] = []
        return collection

    async def get_collection(self, collection_id: str):
        return self._collections.get(collection_id)

    async def list_collections(self):
        return list(self._collections.values())

    async def add_document(self, collection_id: str, document_id: str):
        if collection_id not in self._documents:
            raise ValueError(f"Collection {collection_id} not found")
        self._documents[collection_id].append({"id": document_id})
        return {"collection_id": collection_id, "document_id": document_id}

    async def list_documents(self, collection_id: str):
        return list(self._documents.get(collection_id, []))


async def _seed(manager: FolderManager, skills: _FakeSkillStore, names: list[str]) -> dict[str, str]:
    """Un dossier + un skill par nom ; retourne {nom: folder_id}."""
    folder_ids: dict[str, str] = {}
    for name in names:
        folder = await manager.create_folder(name)
        folder_ids[name] = folder["id"]
        skills.add({"id": f"skill-{name}", "name": f"Skill {name}"})
    return folder_ids


# ── Merge ────────────────────────────────────────────────────────────────────


def test_merge_moves_memberships_to_target_without_touching_sources():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["alpha", "beta", "cible"])
        await manager.attach_resource(ids["alpha"], "skill", "skill-alpha")
        await manager.attach_resource(ids["beta"], "skill", "skill-beta")

        report = await manager.merge_folders([ids["alpha"], ids["beta"]], ids["cible"])

        assert report["operation"] == "merge"
        assert report["operation_id"]
        assert report["status"] == "completed"
        assert report["attached"] == 2
        assert report["skipped"] == 0
        assert report["errors"] == []
        assert report["removed_sources"] == []
        target = await manager.list_folder_resources(ids["cible"])
        assert {r["resource_id"] for r in target} == {"skill-alpha", "skill-beta"}
        # Sources intactes (remove_sources non demandé).
        assert await manager.get_folder(ids["alpha"]) is not None
        assert await manager.get_folder(ids["beta"]) is not None
        # Les skills ne sont jamais dupliqués ni supprimés.
        assert await skills.get_skill("skill-alpha") is not None
        assert await skills.get_skill("skill-beta") is not None

    asyncio.run(scenario())


def test_merge_with_remove_sources_deletes_folders_never_resources():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["a", "b"])
        await manager.attach_resource(ids["a"], "skill", "skill-a")

        report = await manager.merge_folders([ids["a"]], ids["b"], remove_sources=True)

        assert report["status"] == "completed"
        assert report["removed_sources"] == [ids["a"]]
        assert await manager.get_folder(ids["a"]) is None
        assert await manager.get_folder(ids["b"]) is not None
        # La ressource survit à la suppression du dossier source.
        assert await skills.get_skill("skill-a") is not None
        target = await manager.list_folder_resources(ids["b"])
        assert [r["resource_id"] for r in target] == ["skill-a"]

    asyncio.run(scenario())


def test_merge_rejects_target_in_sources():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["a", "b"])
        with pytest.raises(ValueError, match="Target folder cannot"):
            await manager.merge_folders([ids["a"], ids["b"]], ids["a"])

    asyncio.run(scenario())


def test_merge_unknown_source_folder_raises():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["cible"])
        with pytest.raises(ValueError, match="not found"):
            await manager.merge_folders(["nope"], ids["cible"])

    asyncio.run(scenario())


def test_merge_reports_skipped_when_resource_already_in_target():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["src", "dst"])
        await manager.attach_resource(ids["src"], "skill", "skill-src")
        await manager.attach_resource(ids["dst"], "skill", "skill-src")  # déjà là

        report = await manager.merge_folders([ids["src"]], ids["dst"])

        assert report["attached"] == 0
        assert report["skipped"] == 1
        assert report["status"] == "completed"  # rien à faire ≠ échec

    asyncio.run(scenario())


def test_merge_partial_failure_is_reported_not_masked():
    async def scenario():
        manager, skills, store, _c = _manager()
        ids = await _seed(manager, skills, ["src", "dst"])
        # Membership fantôme : ressource disparue (fail-closed attendu).
        await store.save(
            _MEMBERSHIPS, "src:skill:ghost",
            {"id": "src:skill:ghost", "folder_id": ids["src"],
             "resource_type": "skill", "resource_id": "ghost"},
        )
        await manager.attach_resource(ids["src"], "skill", "skill-src")

        report = await manager.merge_folders([ids["src"]], ids["dst"])

        assert report["status"] == "partially_completed"
        assert report["attached"] == 1
        assert len(report["errors"]) == 1
        assert "ghost" in report["errors"][0]

    asyncio.run(scenario())
# ── Copy ─────────────────────────────────────────────────────────────────────


def test_copy_keeps_original_classification():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["a", "b"])
        await manager.attach_resource(ids["a"], "skill", "skill-a")

        report = await manager.copy_resources_to_folder(
            [{"resource_type": "skill", "resource_id": "skill-a"}], ids["b"]
        )

        assert report["operation"] == "copy"
        assert report["status"] == "completed"
        assert report["attached"] == 1
        # Multi-membership : la ressource vit dans les DEUX dossiers.
        folders_of = await manager.list_resource_folders("skill", "skill-a")
        assert {f["id"] for f in folders_of} == {ids["a"], ids["b"]}

    asyncio.run(scenario())


def test_copy_is_idempotent_and_reports_skipped():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["a", "b"])
        item = {"resource_type": "skill", "resource_id": "skill-a"}

        await manager.copy_resources_to_folder([item], ids["b"])
        report = await manager.copy_resources_to_folder([item], ids["b"])

        assert report["attached"] == 0
        assert report["skipped"] == 1

    asyncio.run(scenario())


# ── Move ─────────────────────────────────────────────────────────────────────


def test_move_makes_target_the_unique_folder():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["a", "b", "c"])
        await manager.attach_resource(ids["a"], "skill", "skill-a")
        await manager.attach_resource(ids["b"], "skill", "skill-a")

        report = await manager.move_resources_to_folder(
            [{"resource_type": "skill", "resource_id": "skill-a"}], ids["c"]
        )

        assert report["operation"] == "move"
        assert report["status"] == "completed"
        assert report["moved"] == 1
        folders_of = await manager.list_resource_folders("skill", "skill-a")
        assert {f["id"] for f in folders_of} == {ids["c"]}
        # La ressource n'est jamais supprimée.
        assert await skills.get_skill("skill-a") is not None

    asyncio.run(scenario())


def test_move_unknown_resource_is_reported_as_error():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["cible"])

        report = await manager.move_resources_to_folder(
            [{"resource_type": "skill", "resource_id": "ghost"},
             {"resource_type": "skill", "resource_id": "skill-cible"}],
            ids["cible"],
        )

        assert report["status"] == "partially_completed"
        assert report["moved"] == 1
        assert len(report["errors"]) == 1
        assert "ghost" in report["errors"][0]

    asyncio.run(scenario())


def test_move_all_unknown_reports_failed_status():
    async def scenario():
        manager, skills, _, _c = _manager()
        ids = await _seed(manager, skills, ["cible"])

        report = await manager.move_resources_to_folder(
            [{"resource_type": "skill", "resource_id": "ghost"}], ids["cible"]
        )

        assert report["status"] == "failed"
        assert report["moved"] == 0

    asyncio.run(scenario())

# ── Conversion dossier → collection Knowledge ────────────────────────────────


def test_folder_to_collection_creates_collection_and_attaches_knowledge():
    async def scenario():
        # Doubles légers : on teste folder_to_collection sans pipeline RAG lourd.
        fake_knowledge = _FakeKnowledgeManager(
            docs={"doc-veille-1": {"id": "doc-veille-1", "label": "doc"}}
        )
        fake_collections = _FakeCollectionsManager()
        manager, skills, store, collections = _manager(
            knowledge=fake_knowledge, collections=fake_collections
        )
        folder = await manager.create_folder("Veille IA")
        # Un document knowledge classé dans le dossier (relation réelle).
        await manager.attach_resource(folder["id"], "knowledge", "doc-veille-1")

        report = await manager.folder_to_collection(folder["id"], user_id="alice")

        assert report["operation"] == "to-collection"
        assert report["status"] == "completed"
        assert report["collection_id"]
        assert report["added_documents"] == ["doc-veille-1"]
        # La collection existe et porte le nom du dossier.
        collection = await collections.get_collection(report["collection_id"])
        assert collection is not None
        assert collection["name"] == "Veille IA"
        assert collection["user_id"] == "alice"
        # Le dossier est rattaché à la collection.
        linked = await manager.get_folder(folder["id"])
        assert linked["collection_id"] == report["collection_id"]
        # Les documents sont attachés à la collection (pipeline officiel).
        docs = await collections.list_documents(report["collection_id"])
        assert [d.get("id") for d in docs] == ["doc-veille-1"]

    asyncio.run(scenario())


def test_folder_to_collection_requires_registered_collections_manager():
    async def scenario():
        manager, skills, _, _c = _manager(with_knowledge=False)
        folder = await manager.create_folder("Sans collection")
        with pytest.raises(ValueError, match="not registered"):
            await manager.folder_to_collection(folder["id"])

    asyncio.run(scenario())


def test_folder_to_collection_unknown_folder_raises():
    async def scenario():
        # Double léger : collections présent → passe la guard "not registered",
        # mais le dossier est introuvable → erreur "not found".
        manager, _, _, _ = _manager(
            knowledge=_FakeKnowledgeManager(), collections=_FakeCollectionsManager()
        )
        with pytest.raises(ValueError, match="not found"):
            await manager.folder_to_collection("nope")

    asyncio.run(scenario())


# ── Restore / Corbeille ───────────────────────────────────────────────────────


def test_empty_trash_with_no_deleted_items():
    async def scenario():
        manager, _, _, _ = _manager()
        result = await manager.empty_trash()
        assert result == 0

    asyncio.run(scenario())


def test_create_archive_returns_pending_record():
    async def scenario():
        manager, skills, store, _c = _manager()
        folder = await manager.create_folder("Archive Test")
        # Membership simulé : create_archive compte les relations du store.
        await store.save("folder-memberships", "m1", {
            "id": "m1", "folder_id": folder["id"], "resource_type": "skill",
            "resource_id": "skill-test", "created_at": _utc_now(),
        })

        archive = await manager.create_archive(
            "backup",
            [folder["id"]],
            fmt="zip",
            compression_level=9,
        )

        assert archive["status"] == "pending"
        assert archive["format"] == "zip"
        assert archive["compression_level"] == 9
        assert archive["name"] == "backup"
        assert archive["file_count"] >= 1
        # L'archive est bien persistée dans le store.
        stored = await store.get("folder-archives", archive["id"])
        assert stored is not None
        assert stored["id"] == archive["id"]

    asyncio.run(scenario())


def test_create_archive_rejects_unsupported_format():
    async def scenario():
        manager, _, _, _ = _manager()
        with pytest.raises(ValueError, match="Unsupported archive format"):
            await manager.create_archive("bad", ["f1"], fmt="rar")

    asyncio.run(scenario())


# ── Restore Corbeille (soft-delete simulé) ───────────────────────────────────


def test_list_deleted_items_filters_by_user():
    async def scenario():
        manager, _, store, _ = _manager()

        # Simule des éléments soft-deletés directement dans le store
        await store.save("folder-deleted", "del-1", {
            "id": "del-1", "type": "folder", "name": "d1", "user_id": "alice",
            "deleted_at": "2025-01-01T00:00:00Z", "deleted_by": "alice",
        })
        await store.save("folder-deleted", "del-2", {
            "id": "del-2", "type": "folder", "name": "d2", "user_id": "bob",
            "deleted_at": "2025-01-02T00:00:00Z", "deleted_by": "bob",
        })

        all_items = await manager.list_deleted_items()
        assert len(all_items) == 2

        alice_items = await manager.list_deleted_items(user_id="alice")
        assert len(alice_items) == 1
        assert alice_items[0]["user_id"] == "alice"

    asyncio.run(scenario())


def test_restore_item_raises_on_unknown_id():
    async def scenario():
        manager, _, _, _ = _manager()
        with pytest.raises(ValueError, match="not found"):
            await manager.restore_item("unknown-deleted-id")

    asyncio.run(scenario())


def test_empty_trash_purges_all_items():
    async def scenario():
        manager, _, store, _ = _manager()

        await store.save("folder-deleted", "del-1", {
            "id": "del-1", "type": "folder", "name": "d1", "user_id": "alice",
            "deleted_at": "2025-01-01T00:00:00Z", "deleted_by": "alice",
        })
        await store.save("folder-deleted", "del-2", {
            "id": "del-2", "type": "resource", "name": "r1", "user_id": "alice",
            "deleted_at": "2025-01-02T00:00:00Z", "deleted_by": "alice",
        })

        count = await manager.empty_trash()
        assert count == 2

        remaining = await manager.list_deleted_items()
        assert len(remaining) == 0

    asyncio.run(scenario())
