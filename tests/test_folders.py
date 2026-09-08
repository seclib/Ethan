"""Tests Core — dossiers génériques multi-ressources (core/folders).

Couvre le cycle de vie complet : création libre (aucun dossier imposé),
rename, sous-dossiers, déplacement avec détection de cycles, suppression avec
re-parentage, classement multi-ressources par relations (aucune duplication
physique), ressources sans dossier, résolution via providers Core réels
(KnowledgeManager, KnowledgeCollectionManager) et persistance réelle
(CoreRecordStore partagé entre deux instances).
"""

from __future__ import annotations

import asyncio

import pytest
from core.agents import AgentManager
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


class _FakeSkillStore:
    """Double minimal du SkillStore (même protocole get_skill/list_skills)."""

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
    skills: _FakeSkillStore | None = None,
):
    """FolderManager branché sur des managers Core réels."""
    store = store or CoreRecordStore()
    skills = skills or _FakeSkillStore()
    manager = FolderManager(
        store=store,
        knowledge=KnowledgeManager(store=store),
        collections=KnowledgeCollectionManager(
            store=store, rag=RAGPipeline(store=store)
        ),
        skills=skills,
    )
    return manager, skills


# ── Cycle de vie des dossiers ────────────────────────────────────────────────


def test_no_folder_exists_before_user_creates_one():
    """Aucun dossier prédéfini : l'utilisateur part d'un espace vide."""

    async def scenario():
        manager, _ = _manager()
        assert await manager.list_folders() == []
        assert await manager.list_tree() == []
        # Nom vide rejeté : le nom est choisi librement mais jamais vide
        with pytest.raises(ValueError):
            await manager.create_folder("   ")

    asyncio.run(scenario())


def test_folder_crud_full_lifecycle():
    """Créer, renommer, décrire, réordonner, lire, supprimer."""

    async def scenario():
        manager, _ = _manager()
        folder = await manager.create_folder(
            "OSINT", description="Ressources OSINT", user_id="alice"
        )
        assert folder["name"] == "OSINT" and folder["parent_id"] is None

        # Rename (nom librement modifiable)
        renamed = await manager.rename_folder(folder["id"], "Recon")
        assert renamed["name"] == "Recon"
        assert (await manager.get_folder(folder["id"]))["name"] == "Recon"

        # Update partiel : description + ordre + icône
        updated = await manager.update_folder(
            folder["id"], description="Forensic & recon", order=2, icon="🔎"
        )
        assert updated["description"] == "Forensic & recon"
        assert updated["order"] == 2 and updated["icon"] == "🔎"
        # Rename vers un nom vide → rejet
        with pytest.raises(ValueError):
            await manager.update_folder(folder["id"], name="  ")

        # Delete
        assert await manager.delete_folder(folder["id"]) is not None
        assert await manager.get_folder(folder["id"]) is None
        assert await manager.delete_folder(folder["id"]) is None  # idempotent

    asyncio.run(scenario())


def test_subfolders_and_tree_ordering():
    """Sous-dossiers illimités, arbre ordonné (order puis name)."""

    async def scenario():
        manager, _ = _manager()
        root = await manager.create_folder("OSINT", user_id="alice")
        recon = await manager.create_folder(
            "Recon", parent_id=root["id"], user_id="alice"
        )
        forensic = await manager.create_folder(
            "Forensic", parent_id=root["id"], user_id="alice"
        )
        await manager.create_folder("Deep", parent_id=recon["id"], user_id="alice")

        tree = await manager.list_tree()
        assert len(tree) == 1 and tree[0]["name"] == "OSINT"
        children = tree[0]["children"]
        assert [c["name"] for c in children] == ["Forensic", "Recon"]  # alpha
        assert children[1]["children"][0]["name"] == "Deep"

        # Ordre explicite : Forensic passe après Recon
        await manager.update_folder(forensic["id"], order=10)
        tree = await manager.list_tree()
        assert [c["name"] for c in tree[0]["children"]] == ["Recon", "Forensic"]



def test_move_folder_and_cycle_guards():
    """move_folder re-parente ; self-parent et descendants rejetés."""

    async def scenario():
        manager, _ = _manager()
        root = await manager.create_folder("OSINT")
        child = await manager.create_folder("Recon", parent_id=root["id"])
        leaf = await manager.create_folder("Deep", parent_id=child["id"])

        # Cycle : déplacer root sous son descendant
        with pytest.raises(ValueError, match="descendant"):
            await manager.move_folder(root["id"], leaf["id"])
        with pytest.raises(ValueError, match="own parent"):
            await manager.move_folder(root["id"], root["id"])
        # Parent inconnu
        with pytest.raises(ValueError, match="not found"):
            await manager.move_folder(child["id"], "ghost")

        # Move valide : child devient racine (Deep reste sous Recon)
        moved = await manager.move_folder(child["id"], None)
        assert moved["parent_id"] is None
        tree = await manager.list_tree()
        top = {n["name"] for n in tree}
        assert top == {"OSINT", "Recon"}
        recon_node = next(n for n in tree if n["name"] == "Recon")
        assert [c["name"] for c in recon_node["children"]] == ["Deep"]

    asyncio.run(scenario())


def test_delete_folder_reattaches_children_and_purges_memberships():
    """Suppression : enfants re-rattachés au grand-parent, classements purgés,
    ressources intouchées."""

    async def scenario():
        manager, skills = _manager()
        skill = {"id": "s1", "name": "nmap scan"}
        skills.add(skill)
        root = await manager.create_folder("OSINT")
        child = await manager.create_folder("Recon", parent_id=root["id"])
        await manager.attach_resource(child["id"], "skill", "s1")

        result = await manager.delete_folder(child["id"])
        assert result["reattached_children"] == []

        # La relation vers le dossier supprimé est purgée
        assert await manager.list_resource_folders("skill", "s1") == []
        # La ressource elle-même existe toujours (relation, pas possession)
        assert (await skills.get_skill("s1"))["id"] == "s1"

        # Re-parentage : parent supprimé → enfant remonté à la racine
        parent = await manager.create_folder("Code")
        await manager.create_folder("Python", parent_id=parent["id"])
        await manager.delete_folder(parent["id"])
        top = {n["name"] for n in await manager.list_tree()}
        assert "Python" in top and "Code" not in top

    asyncio.run(scenario())



# ── Classement des ressources (relations, multi-membership) ─────────────────


def test_resource_classification_multi_membership_and_move():
    """Une ressource peut être dans plusieurs dossiers, dans aucun, et être
    déplacée — sans duplication physique (relations uniquement)."""

    async def scenario():
        manager, skills = _manager()
        skills.add({"id": "s1", "name": "nmap"})
        skills.add({"id": "s2", "name": "wireshark"})
        osint = await manager.create_folder("OSINT")
        recon = await manager.create_folder("Recon")
        code = await manager.create_folder("Code")

        # Une ressource dans deux dossiers (multi-membership), attach idempotent
        await manager.attach_resource(osint["id"], "skill", "s1")
        await manager.attach_resource(recon["id"], "skill", "s1")
        await manager.attach_resource(recon["id"], "skill", "s1")
        folders = await manager.list_resource_folders("skill", "s1")
        assert {f["name"] for f in folders} == {"OSINT", "Recon"}

        # Résolution : le record réel est renvoyé, pas une copie
        content = await manager.list_folder_resources(recon["id"])
        assert content == [
            {"resource_type": "skill", "resource_id": "s1",
             "record": {"id": "s1", "name": "nmap"}}
        ]

        # move_resource remplace l'ensemble des dossiers
        target = await manager.move_resource("skill", "s1", [code["id"]])
        assert target == [code["id"]]
        assert {
            f["name"] for f in await manager.list_resource_folders("skill", "s1")
        } == {"Code"}
        # Multi via move
        await manager.move_resource("skill", "s1", [osint["id"], code["id"]])
        assert {
            f["name"] for f in await manager.list_resource_folders("skill", "s1")
        } == {"OSINT", "Code"}

        # Sans dossier : move_resource([]) remet la ressource hors classement
        await manager.move_resource("skill", "s1", [])
        assert await manager.list_resource_folders("skill", "s1") == []
        untagged = await manager.list_untagged("skill")
        assert {s["id"] for s in untagged} == {"s1", "s2"}

        # detach explicite ; un second detach retourne False (idempotent)
        await manager.attach_resource(osint["id"], "skill", "s2")
        assert await manager.detach_resource(osint["id"], "skill", "s2") is True
        assert await manager.detach_resource(osint["id"], "skill", "s2") is False

    asyncio.run(scenario())


def test_resource_validation_fail_closed():
    """Types inconnus et ressources inexistantes sont rejetés (pas de
    relation fantôme)."""

    async def scenario():
        manager, _ = _manager()
        folder = await manager.create_folder("OSINT")
        with pytest.raises(ValueError, match="Unknown resource type"):
            await manager.attach_resource(folder["id"], "ghost-type", "x1")
        with pytest.raises(ValueError, match="not found"):
            await manager.attach_resource(folder["id"], "skill", "missing-skill")
        with pytest.raises(ValueError, match="not found"):
            await manager.attach_resource(folder["id"], "collection", "ghost")
        # Dossier inexistant
        with pytest.raises(ValueError, match="not found"):
            await manager.attach_resource("ghost", "skill", "s1")

    asyncio.run(scenario())



def test_real_core_resources_resolution_and_stale_purge():
    """Providers réels : knowledge nodes et collections RAG résolus ; une
    ressource supprimée est purgée du classement."""

    async def scenario():
        store = CoreRecordStore()
        knowledge = KnowledgeManager(store=store)
        collections = KnowledgeCollectionManager(
            store=store, rag=RAGPipeline(store=store)
        )
        manager = FolderManager(
            store=store, knowledge=knowledge, collections=collections
        )

        node = await knowledge.create("Protocole OSINT", content="Méthodologie")
        collection = await collections.create_collection("Docs")

        folder = await manager.create_folder("OSINT")
        await manager.attach_resource(folder["id"], "knowledge", node.id)
        await manager.attach_resource(folder["id"], "collection", collection["id"])

        content = await manager.list_folder_resources(folder["id"])
        assert {item["resource_type"] for item in content} == {
            "knowledge", "collection"
        }
        records = {item["record"]["id"] for item in content}
        assert node.id in records and collection["id"] in records

        # La ressource classée disparaît → purge automatique du classement
        await knowledge.delete(node.id)
        content = await manager.list_folder_resources(folder["id"])
        assert {item["resource_type"] for item in content} == {"collection"}

        # Untagged : la collection classée n'apparaît plus dans la liste
        untagged = await manager.list_untagged("collection")
        assert all(c["id"] != collection["id"] for c in untagged)

    asyncio.run(scenario())


def test_real_persistence_across_manager_instances():
    """Persistance réelle : une seconde instance (même CoreRecordStore)
    retrouve dossiers et relations."""

    async def scenario():
        store = CoreRecordStore()
        skills = _FakeSkillStore()
        skills.add({"id": "s1", "name": "nmap"})
        manager1, _ = _manager(store, skills)
        folder = await manager1.create_folder("OSINT", user_id="alice")
        sub = await manager1.create_folder(
            "Recon", parent_id=folder["id"], user_id="alice"
        )
        await manager1.attach_resource(sub["id"], "skill", "s1")

        # Nouvelle instance : mêmes données persistées
        manager2, _ = _manager(store, skills)
        assert (await manager2.get_folder(folder["id"]))["name"] == "OSINT"
        tree = await manager2.list_tree(user_id="alice")
        assert tree[0]["children"][0]["name"] == "Recon"
        content = await manager2.list_folder_resources(sub["id"])
        assert content[0]["record"]["id"] == "s1"

        # Suppression persistée aussi
        await manager2.delete_folder(sub["id"])
        assert await manager1.get_folder(sub["id"]) is None

    asyncio.run(scenario())


def test_agent_folder_ids_persisted():
    """Préparation agents : folder_ids typé, persisté et éditable."""

    async def scenario():
        store = CoreRecordStore()
        manager, _ = _manager(store)
        agent_manager = AgentManager(store=store)
        folder = await manager.create_folder("OSINT")

        agent = await agent_manager.create("Recon Agent", folder_ids=[folder["id"]])
        assert agent.folder_ids == [folder["id"]]

        # Persistance
        loaded = await agent_manager.get(agent.id)
        assert loaded.folder_ids == [folder["id"]]

        # Update + sérialisation
        updated = await agent_manager.update(agent.id, {"folder_ids": []})
        assert updated.folder_ids == []
        assert "folder_ids" in agent.to_dict()

    asyncio.run(scenario())


def test_multi_folders_multi_resource_types_end_to_end():
    """Scénario complet multi-dossiers × multi-types : arborescence libre,
    classement croisé (knowledge, collections RAG, skills), filtrage par
    dossier, déplacement, multi-membership et ressources sans dossier."""

    async def scenario():
        store = CoreRecordStore()
        skills = _FakeSkillStore()
        skills.add({"id": "sk-nmap", "name": "Nmap scan"})
        skills.add({"id": "sk-burp", "name": "Burp proxy"})
        skills.add({"id": "sk-grep", "name": "Grep recipes"})
        knowledge = KnowledgeManager(store=store)
        collections = KnowledgeCollectionManager(
            store=store, rag=RAGPipeline(store=store)
        )
        manager = FolderManager(
            store=store, knowledge=knowledge, collections=collections, skills=skills
        )

        # 1. L'utilisateur construit librement son arborescence
        osint = await manager.create_folder("OSINT", user_id="alice")
        recon = await manager.create_folder("Recon", parent_id=osint["id"])
        code = await manager.create_folder("Code", user_id="alice")

        # 2. Ressources réelles des trois types
        node = await knowledge.create("Méthodologie OSINT", content="Étapes")
        col = await collections.create_collection("Rapports")

        # 3. Classement croisé multi-types dans un même dossier
        await manager.attach_resource(recon["id"], "knowledge", node.id)
        await manager.attach_resource(recon["id"], "collection", col["id"])
        await manager.attach_resource(recon["id"], "skill", "sk-nmap")

        content = await manager.list_folder_resources(recon["id"])
        assert {i["resource_type"] for i in content} == {
            "knowledge", "collection", "skill"
        }
        # Filtrage par type dans un dossier
        only_skills = await manager.list_folder_resources(recon["id"], "skill")
        assert [i["record"]["id"] for i in only_skills] == ["sk-nmap"]

        # 4. Multi-membership : la skill dans deux dossiers
        await manager.attach_resource(code["id"], "skill", "sk-nmap")
        assert {
            f["name"] for f in await manager.list_resource_folders("skill", "sk-nmap")
        } == {"Recon", "Code"}

        # 5. Déplacement : sk-burp va de Code vers OSINT
        await manager.attach_resource(code["id"], "skill", "sk-burp")
        await manager.move_resource("skill", "sk-burp", [osint["id"]])
        assert {
            f["name"] for f in await manager.list_resource_folders("skill", "sk-burp")
        } == {"OSINT"}

        # 6. Filtrage batch par dossier (index ressource → dossiers)
        index = await manager.folder_index("skill")
        assert set(index["sk-nmap"]) == {recon["id"], code["id"]}
        assert index["sk-burp"] == [osint["id"]]
        # sk-grep n'apparaît pas (sans dossier)
        assert "sk-grep" not in index
        full_index = await manager.folder_index()
        assert set(full_index) >= {"sk-nmap", "sk-burp", node.id, col["id"]}

        # 7. Ressources sans dossier : sk-grep uniquement (côté skills)
        untagged = await manager.list_untagged("skill")
        assert [s["id"] for s in untagged] == ["sk-grep"]

        # 8. Suppression d'un dossier : les ressources survivent
        await manager.delete_folder(recon["id"])
        assert await manager.get_folder(recon["id"]) is None
        # sk-nmap reste classé dans Code ; node/col redeviennent sans dossier
        assert {
            f["name"] for f in await manager.list_resource_folders("skill", "sk-nmap")
        } == {"Code"}
        remaining_nodes = await manager.list_untagged("knowledge")
        assert any(n["id"] == node.id for n in remaining_nodes)
        # L'arborescence reste cohérente
        top = {n["name"] for n in await manager.list_tree()}
        assert top == {"OSINT", "Code"}

    asyncio.run(scenario())
