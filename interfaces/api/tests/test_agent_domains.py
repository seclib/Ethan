"""Tests réels de la validation agent → domain_ids (routers/v1.py).

Exécute le vrai DomainManager branché sur de vrais managers Core via
CoreRecordStore mémoire — aucun mock du domaine.  Vérifie que create/put
agents valident les domaines sélectionnés (domaine inconnu → 422) et que
la sélection est persistée telle quelle dans l'agent.
"""

from __future__ import annotations

import asyncio

import pytest
from core.domains import DomainManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore
from fastapi import HTTPException
from interfaces.api.routers import core_domains
from routers import v1


@pytest.fixture()
def domains():
    """Vrai DomainManager (providers Core réels) + wiring v1 pour les agents."""
    store = CoreRecordStore()
    collections = KnowledgeCollectionManager(
        store=store, rag=RAGPipeline(store=store)
    )
    manager = DomainManager(
        store=store,
        knowledge=KnowledgeManager(store=store),
        collections=collections,
    )
    core_domains.set_domain_manager(manager)
    v1.set_knowledge_collections(collections)
    v1.set_core_domain_services(v1.CoreDomainServices())
    yield manager
    core_domains.set_domain_manager(None)
    v1.set_knowledge_collections(None)


def test_agent_routes_validate_domain_ids(domains):
    """create/put agents : domain_ids validés (domaine inconnu → 422)."""
    osint = asyncio.run(domains.create_domain("OSINT"))
    code = asyncio.run(domains.create_domain("Code"))

    agent = asyncio.run(v1.create_agent({
        "name": "Recon Agent", "provider": "fake",
        "domain_ids": [osint["id"], code["id"]],
    }))
    assert agent["domain_ids"] == [osint["id"], code["id"]]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad", "domain_ids": ["ghost"],
        }))
    assert exc.value.status_code == 422

    updated = asyncio.run(v1.update_agent(agent["id"], {"domain_ids": [osint["id"]]}))
    assert updated["domain_ids"] == [osint["id"]]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.update_agent(agent["id"], {"domain_ids": ["ghost"]}))
    assert exc.value.status_code == 422


def test_agent_domain_selection_resolves_via_core(domains):
    """Les ressources d'un domain sont résolues par le Core, pas par l'agent."""
    collections_manager = v1.get_knowledge_collections()
    collection = asyncio.run(collections_manager.create_collection("Docs"))
    domain = asyncio.run(domains.create_domain("Research"))
    asyncio.run(domains.attach_resource(
        domain["id"], "collection", collection["id"]
    ))

    agent = asyncio.run(v1.create_agent({
        "name": "Scholar", "provider": "fake", "domain_ids": [domain["id"]],
    }))
    # L'agent ne stocke que la sélection explicite de domains…
    assert agent["domain_ids"] == [domain["id"]]
    # …et le Core résout les ressources à la demande (many-to-many).
    resolved = asyncio.run(domains.list_resources(domain["id"], "collection"))
    assert [r["resource_id"] for r in resolved] == [collection["id"]]
