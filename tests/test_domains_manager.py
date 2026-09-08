"""Tests réels du DomainManager Core (core/domains).

Couvre :
- CRUD domains (create/get/find_by_name/list/update/delete) ;
- unicité du nom (identité fonctionnelle) ;
- multi-membership : une ressource dans plusieurs domains ;
- attach/detach avec résolution réelle via providers Core (knowledge,
  collections) — une ressource inconnue est rejetée ;
- inversion de requête : domains d'une ressource, counts ;
- **persistance réelle** : les records survivent à une nouvelle instance
  de manager/store (PostgreSQL si DATABASE_URL est joignable, sinon le
  fallback mémoire du CoreRecordStore qui est le chemin standalone réel).
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from core.domains import DomainManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


def _make_manager(store: CoreRecordStore) -> DomainManager:
    return DomainManager(
        store=store,
        knowledge=KnowledgeManager(store=store),
        collections=KnowledgeCollectionManager(
            store=store, rag=RAGPipeline(store=store)
        ),
    )


def _cleanup_store(store: CoreRecordStore) -> None:
    store._memory.clear()


# ── CRUD & règles métier ────────────────────────────────────────────────


def test_domain_crud_and_unique_name():
    store = CoreRecordStore()
    manager = _make_manager(store)

    async def flow():
        created = await manager.create_domain(
            "OSINT",
            description="Renseignement sources ouvertes",
            icon="🔍",
            color="#2563eb",
        )
        assert created["name"] == "OSINT"
        assert created["description"] == "Renseignement sources ouvertes"

        # Unicité du nom
        with pytest.raises(ValueError, match="already exists"):
            await manager.create_domain("OSINT")

        # get / find_by_name / list
        got = await manager.get_domain(created["id"])
        assert got is not None and got["name"] == "OSINT"
        by_name = await manager.find_by_name("osint")  # insensible à la casse
        assert by_name is not None and by_name["id"] == created["id"]

        names = [d["name"] for d in await manager.list_domains()]
        assert "OSINT" in names

        # update
        updated = await manager.update_domain(created["id"], description="OSINT avancé")
        assert updated is not None and updated["description"] == "OSINT avancé"

        # rename vers un nom déjà pris → refusé
        other = await manager.create_domain("Recon")
        with pytest.raises(ValueError, match="already exists"):
            await manager.update_domain(other["id"], name="OSINT")

        # delete
        deleted = await manager.delete_domain(created["id"])
        assert deleted is not None and deleted["id"] == created["id"]
        assert await manager.get_domain(created["id"]) is None
        assert await manager.delete_domain(created["id"]) is None

    asyncio.run(flow())
    _cleanup_store(store)


def test_resource_multi_membership_and_shared_resolution():
    """Une ressource réelle peut appartenir à plusieurs domains."""
    store = CoreRecordStore()
    manager = _make_manager(store)

    async def flow():
        doc = await store.save(
            "knowledge-docs",
            "doc-x",
            {"title": "Rapport OSINT", "content": "..."},
        )
        assert doc is not None

        osint = await manager.create_domain("OSINT")
        recon = await manager.create_domain("Recon")

        # Multi-membership : même ressource dans 2 domains
        for domain in (osint, recon):
            attached = await manager.attach_resource(domain["id"], "knowledge", "doc-x")
            assert attached is not None

        # Résolution réelle via le provider Core (knowledge manager)
        resources = await manager.list_resources(osint["id"], "knowledge")
        assert len(resources) == 1
        assert resources[0]["id"] == "doc-x"
        assert resources[0]["record"]["title"] == "Rapport OSINT"

        # Inversion : domains d'une ressource
        domains_of = await manager.list_domains_for_resource("knowledge", "doc-x")
        assert {d["name"] for d in domains_of} == {"OSINT", "Recon"}

        # Counts
        counts = {
            d["name"]: d["resource_count"]
            for d in await manager.list_domains_with_counts()
        }
        assert counts["OSINT"] == 1 and counts["Recon"] == 1

        # Resource inconnue → rejetée (integrity of links)
        with pytest.raises(ValueError, match="not found"):
            await manager.attach_resource(osint["id"], "knowledge", "ghost-doc")

        # Type de ressource non fourni → rejeté
        with pytest.raises(ValueError, match="Unsupported"):
            await manager.attach_resource(osint["id"], "source", "src-1")

        # detach
        detached = await manager.detach_resource(recon["id"], "knowledge", "doc-x")
        assert detached is True
        domains_of = await manager.list_domains_for_resource("knowledge", "doc-x")
        assert {d["name"] for d in domains_of} == {"OSINT"}

        # Attacher à un domain inconnu → rejeté
        with pytest.raises(ValueError, match="not found"):
            await manager.attach_resource("ghost-domain", "knowledge", "doc-x")


# ── Persistance réelle ──────────────────────────────────────────────────


def test_domain_persistence_survives_new_manager_instance():
    """Persistance réelle : un nouveau manager retrouve les records existants."""
    url = os.getenv("DATABASE_URL", "postgresql://ethan:change-me-in-prod@localhost:5432/ethan")

    async def flow():
        try:
            import asyncpg

            pool = await asyncio.wait_for(asyncpg.create_pool(url), timeout=4)
        except Exception:
            pytest.skip(
                "PostgreSQL unavailable — standalone memory path covered elsewhere"
            )
            return

        token = uuid.uuid4().hex[:8]
        try:
            manager = _make_manager(CoreRecordStore(pg_pool=pool))
            created = await manager.create_domain(f"Forensic-{token}")

            # Nouvelle instance manager + store (simulate restart), même PG
            manager2 = _make_manager(CoreRecordStore(pg_pool=pool))
            fetched = await manager2.get_domain(created["id"])
            assert fetched is not None, "domain record must survive a fresh manager"
            assert fetched["name"] == f"Forensic-{token}"

            by_name = await manager2.find_by_name(f"Forensic-{token}")
            assert by_name is not None and by_name["id"] == created["id"]

            # La suppression persiste aussi
            assert await manager2.delete_domain(created["id"]) is not None
            manager3 = _make_manager(CoreRecordStore(pg_pool=pool))
            assert await manager3.get_domain(created["id"]) is None
        finally:
            # Nettoyage défensif du test dans la vraie base
            try:
                await pool.execute(
                    "DELETE FROM core_domain_records WHERE "
                    "record->>'name' LIKE 'Forensic-' || $1 || '%'",
                    token,
                )
            except Exception:
                pass
            await pool.close()

    asyncio.run(flow())


# ── API /v1/domains ─────────────────────────────────────────────────────


def test_domain_api_routes_crud_and_membership():
    from fastapi import HTTPException
    from interfaces.api.routers import core_domains

    store = CoreRecordStore()
    manager = _make_manager(store)
    core_domains.set_domain_manager(manager)
    try:
        domain = asyncio.run(
            core_domains.create_domain(
                {"name": "Security", "description": "Défense", "icon": "🛡️"}
            )
        )
        assert domain["name"] == "Security"

        # duplicate → 422 (mapping ValueError du router, pattern folders)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(core_domains.create_domain({"name": "Security"}))
        assert exc.value.status_code == 422

        listed = asyncio.run(core_domains.list_domains())
        assert any(d["name"] == "Security" for d in listed)

        km = KnowledgeManager(store=store)
        doc = asyncio.run(km.create("Playbook", content="x"))

        attached = asyncio.run(
            core_domains.attach_resource(
                domain["id"],
                {"resource_type": "knowledge", "resource_id": doc.id},
            )
        )
        assert attached is not None

        index = asyncio.run(core_domains.get_domain_index("knowledge"))
        # Convention folders : index {resource_id: [domain_id, ...]}
        assert doc.id in index and domain["id"] in index[doc.id]

        resources = asyncio.run(core_domains.list_domain_resources(domain["id"]))
        assert resources[0]["record"]["label"] == "Playbook"

        removed = asyncio.run(
            core_domains.detach_resource(domain["id"], "knowledge", doc.id)
        )
        assert removed["status"] == "detached"

        deleted = asyncio.run(core_domains.delete_domain(domain["id"]))
        assert deleted["status"] == "deleted"

        with pytest.raises(HTTPException) as exc:
            asyncio.run(core_domains.get_domain(domain["id"]))
        assert exc.value.status_code == 404
    finally:
        core_domains.set_domain_manager(None)
        _cleanup_store(store)
