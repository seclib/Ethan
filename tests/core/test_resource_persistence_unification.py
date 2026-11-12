"""DAĒNĀ P2.8.1 — Unification de la persistance : tests ciblés.

Ces tests s'exécutent sur un `CoreRecordStore` isolé (memoire) et des
répertoires temporaires. Aucune donnée réelle n'est modifiée.

Couverture :
  1. Persistance et relecture
  2. Création et mise à jour
  3. Identifiants stables
  4. Idempotence (absence de doublons)
  5. Provenance et métadonnées
  6. Relations entre enregistrements
  7. Gestion des erreurs
  8. Cohérence entre services
  9. Compatibilité des appels existants
 10. Durabilité après redémarrage simulé
 11. Non-régression KnowledgeManager / Engineering Memory / P2.8.0
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeType
from core.resources.registry import ResourceRegistry
from core.resources.repository import RESOURCE_DOMAIN, ResourceRepository
from core.resources.types import ResourceStatus, ResourceType
from core.state.record_store import CoreRecordStore


def _run(coro):
    """Exécute une coroutine dans une boucle événementielle dédiée."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture
def store() -> CoreRecordStore:
    """Store Core isolé, partagé par les objets d'un même test."""
    return CoreRecordStore()


@pytest.fixture
def km(store: CoreRecordStore) -> KnowledgeManager:
    """KnowledgeManager adossé au store isolé."""
    return KnowledgeManager(store=store)


@pytest.fixture
def registry(store: CoreRecordStore, km: KnowledgeManager, tmp_path: Path) -> ResourceRegistry:
    """Registre adossé au store isolé, avec export portable temporaire."""
    return ResourceRegistry(
        knowledge_manager=km,
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )


def _write_doc(path: Path, title: str, body: str = "Contenu de test suffisamment long.") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    return path


def _record(registry: ResourceRegistry, stable_id: str, title: str, source: str) -> None:
    """Insère une ressource minimale dans le registre."""
    from core.resources.registry import ResourceRecord

    registry._records[stable_id] = ResourceRecord(
        resource_type=ResourceType.DOCUMENT,
        title=title,
        stable_id=stable_id,
        knowledge_node=None,
        source_original=source,
        metadata={"domain": "test", "level": "C"},
        status=ResourceStatus.ACTIVE,
    )


# ---------------------------------------------------------------------------
# 1. Persistance et relecture
# ---------------------------------------------------------------------------


def test_repository_round_trip(store: CoreRecordStore, registry: ResourceRegistry) -> None:
    """Une ressource écrite puis relue est identique (round-trip complet)."""
    _record(registry, "doc-1", "Document un", "/tmp/doc-1.md")

    _run(registry.persist())

    repo = ResourceRepository(store)
    raw = _run(repo.get("doc-1"))

    assert raw is not None
    assert raw["stable_id"] == "doc-1"
    assert raw["title"] == "Document un"
    assert raw["source_original"] == "/tmp/doc-1.md"
    assert raw["resource_type"] == "document"
    assert raw["status"] == "active"


def test_registry_loads_from_repository(store: CoreRecordStore, tmp_path: Path) -> None:
    """Un registre reconstruit relit l'état depuis la source de vérité."""
    first = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    _record(first, "doc-1", "Document un", "/tmp/doc-1.md")
    _run(first.persist())

    # "Redémarrage" : nouveau registre, même store, aucun fichier d'amorçage.
    second = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "absent.json"),
    )
    loaded = _run(second.load_from_repository())

    assert loaded == 1
    assert "doc-1" in second._records
    assert second._records["doc-1"].title == "Document un"


def test_durability_after_simulated_restart(store: CoreRecordStore, tmp_path: Path) -> None:
    """L'état survit à la reconstruction complète du registre."""
    registry = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    _write_doc(tmp_path / "docs" / "guide.md", "Guide")
    _run(registry.discover_documents((tmp_path / "docs",)))
    _run(registry.persist())

    reloaded = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    count = _run(reloaded.load_from_repository())

    assert count >= 1
    assert len(reloaded._records) == len(registry._records)


# ---------------------------------------------------------------------------
# 2. Création et mise à jour
# ---------------------------------------------------------------------------


def test_update_is_reflected_in_the_store(store: CoreRecordStore, registry: ResourceRegistry) -> None:
    """Une mise à jour de métadonnées est visible dans la source de vérité."""
    _record(registry, "doc-1", "Titre initial", "/tmp/doc-1.md")
    _run(registry.persist())

    registry._records["doc-1"].title = "Titre mis à jour"
    registry._records["doc-1"].metadata["level"] = "A"
    _run(registry.persist())

    raw = _run(ResourceRepository(store).get("doc-1"))

    assert raw is not None
    assert raw["title"] == "Titre mis à jour"
    assert raw["metadata"]["level"] == "A"


def test_lifecycle_transition_persists(store: CoreRecordStore, registry: ResourceRegistry) -> None:
    """Une transition de cycle de vie est persistée."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _run(registry.persist())

    _run(registry.mark_disappeared("doc-1"))

    raw = _run(ResourceRepository(store).get("doc-1"))
    assert raw is not None
    assert raw["status"] == ResourceStatus.DISAPPEARED.value

    _run(registry.restore_resource("doc-1"))
    raw = _run(ResourceRepository(store).get("doc-1"))
    assert raw is not None
    assert raw["status"] == ResourceStatus.ACTIVE.value


# ---------------------------------------------------------------------------
# 3. Identifiants stables
# ---------------------------------------------------------------------------


def test_stable_id_is_preserved_across_reloads(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """Le `stable_id` ne change pas au fil des écritures et relectures."""
    _record(registry, "doc-stable", "Document stable", "/tmp/doc-stable.md")
    _run(registry.persist())

    reloaded = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path="/tmp/absent-does-not-exist.json",
    )
    _run(reloaded.load_from_repository())

    assert "doc-stable" in reloaded._records
    assert reloaded._records["doc-stable"].stable_id == "doc-stable"


def test_discovery_ids_are_deterministic(store: CoreRecordStore, tmp_path: Path) -> None:
    """Deux découvertes successives produisent les mêmes identifiants."""
    docs = tmp_path / "docs"
    _write_doc(docs / "guide.md", "Guide")

    ids = []
    for _ in range(2):
        registry = ResourceRegistry(
            knowledge_manager=KnowledgeManager(store=store),
            store=store,
            registry_meta_path=str(tmp_path / "registry-meta.json"),
        )
        _run(registry.discover_documents((docs,)))
        ids.append(sorted(registry._records))

    assert ids[0] == ids[1]
    assert len(ids[0]) == 1


# ---------------------------------------------------------------------------
# 4. Idempotence — absence de doublons
# ---------------------------------------------------------------------------


def test_repeated_writes_create_no_duplicate(store: CoreRecordStore, registry: ResourceRegistry) -> None:
    """Écrire plusieurs fois les mêmes ressources ne crée aucun doublon."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _record(registry, "doc-2", "Autre", "/tmp/doc-2.md")

    for _ in range(3):
        _run(registry.persist())

    repo = ResourceRepository(store)
    assert _run(repo.count()) == 2


def test_rediscovery_does_not_duplicate(
    store: CoreRecordStore, registry: ResourceRegistry, tmp_path: Path
) -> None:
    """La redécouverte ne duplique pas les ressources déjà enregistrées."""
    docs = tmp_path / "docs"
    _write_doc(docs / "a.md", "A")
    _write_doc(docs / "b.md", "B")

    _run(registry.discover_documents((docs,)))
    first = len(registry._records)
    _run(registry.discover_documents((docs,)))

    assert len(registry._records) == first == 2
    assert _run(ResourceRepository(store).count()) == 2


def test_sync_from_records_removes_only_stale_entries(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """La synchronisation retire les entrées disparues sans toucher aux autres domaines."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _record(registry, "doc-2", "Autre", "/tmp/doc-2.md")
    _run(registry.persist())

    # Un enregistrement d'un autre domaine ne doit pas être touché.
    _run(store.save("other-domain", "x", {"keep": True}))

    del registry._records["doc-2"]
    stats = _run(ResourceRepository(store).sync_from_records(registry._records.values()))

    assert stats["written"] == 1
    assert stats["removed"] == 1
    assert _run(ResourceRepository(store).count()) == 1
    assert _run(store.get("other-domain", "x")) is not None


# ---------------------------------------------------------------------------
# 5. Provenance et métadonnées
# ---------------------------------------------------------------------------


def test_provenance_and_metadata_survive_persistence(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """Provenance, domaine, niveau et raison de classement sont conservés."""
    from core.resources.registry import ResourceRecord

    registry._records["doc-1"] = ResourceRecord(
        resource_type=ResourceType.DOCUMENT,
        title="Document",
        stable_id="doc-1",
        knowledge_node=None,
        source_original="/origin/chemin/vers/doc.md",
        metadata={
            "domain": "docs",
            "level": "B",
            "knowledge_state": "extracted",
            "classification_reason": "domain 'docs'",
        },
        status=ResourceStatus.ACTIVE,
    )
    _run(registry.persist())

    raw = _run(ResourceRepository(store).get("doc-1"))

    assert raw is not None
    assert raw["source_original"] == "/origin/chemin/vers/doc.md"
    assert raw["metadata"]["domain"] == "docs"
    assert raw["metadata"]["level"] == "B"
    assert raw["metadata"]["knowledge_state"] == "extracted"
    assert raw["metadata"]["classification_reason"] == "domain 'docs'"


def test_round_trip_preserves_discovery_dates(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """La date de découverte n'est pas écrasée par une relecture."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    registry._records["doc-1"].discovered_at = registry._records["doc-1"].discovered_at.replace(
        year=2020, month=1, day=2
    )
    _run(registry.persist())

    reloaded = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path="/tmp/absent-2.json",
    )
    _run(reloaded.load_from_repository())

    assert reloaded._records["doc-1"].discovered_at.year == 2020


# ---------------------------------------------------------------------------
# 6. Relations entre enregistrements
# ---------------------------------------------------------------------------


def test_knowledge_node_link_is_persisted(
    store: CoreRecordStore, registry: ResourceRegistry, km: KnowledgeManager
) -> None:
    """Le lien ressource <-> KnowledgeNode est conservé après persistance."""
    node = _run(
        km.create(
            label="Nœud lié",
            node_type=KnowledgeType.DOCUMENT,
            content="contenu du nœud",
            source="/tmp/doc-1.md",
            node_id="node-1",
        )
    )
    from core.resources.registry import ResourceRecord

    registry._records["doc-1"] = ResourceRecord(
        resource_type=ResourceType.DOCUMENT,
        title="Document",
        stable_id="doc-1",
        knowledge_node=node,
        source_original="/tmp/doc-1.md",
        metadata={"domain": "docs"},
        status=ResourceStatus.ACTIVE,
    )
    _run(registry.persist())

    raw = _run(ResourceRepository(store).get("doc-1"))
    assert raw is not None
    assert raw["knowledge_node_id"] == "node-1"

    # Le nœud est relu depuis le store partagé (même store -> même base).
    reloaded = ResourceRegistry(
        knowledge_manager=km,
        store=store,
        registry_meta_path="/tmp/absent-3.json",
    )
    _run(reloaded.load_from_repository())
    assert reloaded._records["doc-1"].knowledge_node is not None
    assert reloaded._records["doc-1"].knowledge_node.id == "node-1"


def test_node_relations_survive_via_knowledge_manager(
    store: CoreRecordStore, km: KnowledgeManager
) -> None:
    """Les relations entre KnowledgeNodes restent dans le store partagé."""
    _run(km.create(label="A", node_type=KnowledgeType.CONCEPT, node_id="a"))
    _run(km.create(label="B", node_type=KnowledgeType.CONCEPT, node_id="b"))
    _run(km.connect("a", "b", relation_type="related_to"))

    node_a = _run(km.get("a"))
    assert node_a is not None
    assert len(node_a.connections) == 1
    assert node_a.connections[0].to_node_id == "b"


# ---------------------------------------------------------------------------
# 7. Gestion des erreurs
# ---------------------------------------------------------------------------


def test_unknown_record_read_returns_none(store: CoreRecordStore) -> None:
    """Lire un identifiant absent ne lève pas d'exception."""
    assert _run(ResourceRepository(store).get("absent")) is None


def test_malformed_record_is_skipped_on_load(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """Un enregistrement corrompu n'empêche pas le chargement des autres."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _run(registry.persist())

    # Injecte un enregistrement invalide.
    _run(store.save(RESOURCE_DOMAIN, "corrompu", {"aucun": "champ"}))

    reloaded = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path="/tmp/absent-4.json",
    )
    loaded = _run(reloaded.load_from_repository())

    assert loaded >= 1
    assert "doc-1" in reloaded._records
    assert "corrompu" not in reloaded._records


def test_store_failure_does_not_break_the_export(
    store: CoreRecordStore, registry: ResourceRegistry, tmp_path: Path, monkeypatch
) -> None:
    """Un échec du store n'empêche pas la production de l'export portable."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")

    async def boom(*args, **kwargs):
        raise RuntimeError("store indisponible")

    monkeypatch.setattr(registry._repository, "save_all", boom)
    _run(registry.persist())

    export = Path(registry.export_path)
    assert export.is_file()
    assert "doc-1" in export.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 8. Cohérence entre services
# ---------------------------------------------------------------------------


def test_registry_and_repository_agree(
    store: CoreRecordStore, registry: ResourceRegistry
) -> None:
    """Le registre en mémoire et la source de vérité contiennent les mêmes entrées."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _run(registry.persist())

    repo = ResourceRepository(store)
    stored_ids = {r["stable_id"] for r in _run(repo.load_all())}

    assert stored_ids == set(registry._records)


def test_knowledge_nodes_created_by_discovery_are_durable(
    store: CoreRecordStore, tmp_path: Path
) -> None:
    """Les KnowledgeNodes produits par la découverte sont durables.

    Regression P2.8.1 : le registre construisait son KnowledgeManager sans
    store, donc les nœuds partaient en mémoire et disparaissaient au
    redémarrage, alors que les métadonnées affirmaient `indexed`.
    """
    docs = tmp_path / "docs"
    _write_doc(docs / "guide.md", "Guide", "Contenu suffisamment long pour être extrait.")

    registry = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    _run(registry.discover_documents((docs,)))

    node_ids = [
        r.knowledge_node.id
        for r in registry._records.values()
        if r.knowledge_node is not None
    ]
    assert node_ids, "la decouverte doit produire des KnowledgeNodes"

    # Les nœuds sont relus depuis le store partage : ils sont durables.
    km = KnowledgeManager(store=store)
    for node_id in node_ids:
        assert _run(km.get(node_id)) is not None, f"noeud {node_id} non durable"


# ---------------------------------------------------------------------------
# 9. Compatibilité des appels existants
# ---------------------------------------------------------------------------


def test_export_file_still_produced(
    registry: ResourceRegistry, tmp_path: Path
) -> None:
    """L'export portable registry-meta.json est toujours produit."""
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _run(registry.persist())

    export = Path(registry.export_path)
    assert export.is_file()
    import json

    data = json.loads(export.read_text(encoding="utf-8"))
    assert data["total_resources"] == 1
    assert data["records"][0]["stable_id"] == "doc-1"


def test_registry_without_store_still_works(tmp_path: Path) -> None:
    """Sans store, le registre conserve son comportement historique (fichier)."""
    registry = ResourceRegistry(
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    _record(registry, "doc-1", "Document", "/tmp/doc-1.md")
    _run(registry.persist())

    assert Path(registry.export_path).is_file()
    assert registry._repository is None


def test_search_and_list_still_work(registry: ResourceRegistry) -> None:
    """Les API de consultation du registre restent fonctionnelles."""
    _record(registry, "doc-1", "Guide de démarrage", "/tmp/doc-1.md")
    registry._rebuild_indices()
    _run(registry.persist())

    assert registry.list_by_type(ResourceType.DOCUMENT)
    assert registry.search_resources("démarrage")
    assert registry.get_resource("doc-1") is not None


# ---------------------------------------------------------------------------
# 10-11. Non-régression
# ---------------------------------------------------------------------------


def test_knowledge_manager_non_regression(store: CoreRecordStore) -> None:
    """Le KnowledgeManager n'a pas changé de comportement."""
    km = KnowledgeManager(store=store)

    node = _run(km.create(label="Nœud", node_type=KnowledgeType.CONCEPT, content="c"))
    assert node.id in [n.id for n in _run(km.list())]

    updated = _run(km.update(node.id, {"content": "c2"}))
    assert updated is not None and updated.content == "c2"

    assert _run(km.get(node.id)) is not None
    assert _run(km.delete(node.id)) is True
    assert _run(km.get(node.id)) is None


def test_engineering_memory_non_regression(tmp_path: Path) -> None:
    """L'Engineering Memory conserve son stockage documentaire."""
    from core.engineering_memory import EngineeringMemoryService, MemoryRecord, RecordType

    root = tmp_path / "Obsidian"
    service = EngineeringMemoryService(root=root)
    record = MemoryRecord(
        id="EVT-2026-001",
        record_type=RecordType.ENGINEERING_EVENT,
        title="Événement",
        status="RECORDED",
        source_of_fact="test",
        provenance_level="observed",
        components=["cmp-test"],
        created_at="2026-11-12T00:00:00+00:00",
        updated_at="2026-11-12T00:00:00+00:00",
        evidence_refs=[],
        authors=["pytest"],
        origin="declared",
        confidence="medium",
        notes="test P2.8.1",
    )
    stored = service.record(record)

    assert stored.repository_path is not None
    assert stored.repository_path.is_file()
    assert service.get("EVT-2026-001") is not None
    assert service.search(component="cmp-test")


def test_p2_8_0_non_regression(tmp_path: Path) -> None:
    """Les destinations de P2.8.0 restent valides."""
    from core.engineering_memory.registry import EngineeringMemoryRegistry
    from core.engineering_memory.models import RecordType

    registry = EngineeringMemoryRegistry()

    assert registry.destination_for(RecordType.COMPONENT).relative_directory == (
        "Knowledge/Composants"
    )
    assert registry.destination_for(RecordType.TEST_RESULT).relative_directory == (
        "Knowledge/Tests-et-Preuves"
    )
    assert registry.destination_for(RecordType.VERIFICATION).relative_directory == (
        "Knowledge/Tests-et-Preuves"
    )
    assert registry.destination_for(RecordType.ENGINEERING_EVENT).relative_directory == (
        "Archives/Events"
    )
