"""DAĒNĀ P2.8.2 — Project Anchors : tests ciblés.

Environnement isolé : store Core en mémoire, projets et données semés dans
des domaines temporaires du store. Aucune donnée réelle n'est touchée.

Couverture :
  1. Création d'un ancrage
  2. Rattachement à un projet existant
  3. Rejet d'un identifiant projet invalide
  4. Informations globales
  5. Informations rattachées à un projet
  6. Partage multi-projets
  7. Recherche avec filtrage projet
  8. Isolation entre projets
  9. Préservation de la provenance
 10. Persistance et relecture
 11. Compatibilité des données historiques
 12. Comportement après redémarrage simulé
 13. Non-régression KnowledgeManager / Engineering Memory / P2.8.0 / P2.8.1
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeType
from core.projects.anchors import (
    ANCHOR_DOMAIN,
    AnchorScope,
    AnchorTargetType,
    ProjectAnchor,
    ProjectAnchorError,
    ProjectAnchorService,
    ProjectAnchorStoreUnavailable,
    TargetExistence,
    TargetResolution,
)
from core.state.record_store import CoreRecordStore, RecordStoreUnavailable


def _run(coro):
    """Exécute une coroutine dans une boucle événementielle dédiée."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _project(project_id: str, *, active: bool = True, name: str = "Projet") -> dict:
    """Construit un enregistrement projet minimal."""
    return {
        "id": project_id,
        "name": name,
        "description": "",
        "instructions": "",
        "user_id": "tester",
        "metadata": {},
        "is_active": active,
        "created_at": "2026-11-12T00:00:00Z",
        "updated_at": "2026-11-12T00:00:00Z",
    }


@pytest.fixture
def store() -> CoreRecordStore:
    """Store Core isolé, partagé par les objets d'un même test."""
    return CoreRecordStore()


def _knowledge(record_id: str, label: str) -> dict:
    """Construit un enregistrement KnowledgeNode minimal."""
    return {
        "id": record_id,
        "label": label,
        "node_type": "concept",
        "content": "c",
        "source": "s",
        "connections": [],
        "metadata": {},
        "created_at": "2026-11-12T00:00:00Z",
        "updated_at": "2026-11-12T00:00:00Z",
    }


@pytest.fixture
def seeded(store: CoreRecordStore) -> CoreRecordStore:
    """Store avec deux projets actifs, un inactif et une connaissance."""
    _run(store.save("projects", "p-alpha", _project("p-alpha", name="Alpha")))
    _run(store.save("projects", "p-beta", _project("p-beta", name="Beta")))
    _run(store.save("projects", "p-archive", _project("p-archive", active=False)))
    _run(store.save("knowledge", "kn-1", _knowledge("kn-1", "Nœud")))
    return store


@pytest.fixture
def service(store: CoreRecordStore) -> ProjectAnchorService:
    """Service d'ancrage adossé au store isolé."""
    return ProjectAnchorService(store)


# ---------------------------------------------------------------------------
# 1-2. Création et rattachement à un projet existant
# ---------------------------------------------------------------------------


def test_attach_creates_an_anchor(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Rattacher une donnée à un projet existant crée une ancre."""
    anchor = _run(
        service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="tester")
    )

    assert anchor.project_id == "p-alpha"
    assert anchor.target_type is AnchorTargetType.KNOWLEDGE_NODE
    assert anchor.target_id == "kn-1"
    assert anchor.anchor_id
    assert anchor.created_at
    assert anchor.is_active


def test_attach_is_idempotent(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Rattacher deux fois ne crée pas de seconde ancre."""
    first = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    second = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    assert first.anchor_id == second.anchor_id
    assert len(_run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))) == 1


def test_attach_persists_to_the_store(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """L'ancre est bien écrite dans le domaine dédié."""
    anchor = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    raw = _run(seeded.get(ANCHOR_DOMAIN, anchor.anchor_id))
    assert raw is not None
    assert raw["project_id"] == "p-alpha"
    assert raw["target_id"] == "kn-1"


# ---------------------------------------------------------------------------
# 3. Rejet d'un identifiant projet invalide
# ---------------------------------------------------------------------------


def test_unknown_project_is_rejected(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Un projet inexistant est refusé."""
    with pytest.raises(ProjectAnchorError, match="not found"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-inexistant"))


def test_empty_project_id_is_rejected(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Un identifiant de projet vide est refusé."""
    with pytest.raises(ProjectAnchorError, match="must not be empty"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "  "))


def test_inactive_project_is_rejected(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Un projet inactif ne peut pas recevoir de nouvel ancrage."""
    with pytest.raises(ProjectAnchorError, match="inactive"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-archive"))


def test_empty_target_id_is_rejected(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Un identifiant de donnée vide est refusé."""
    with pytest.raises(ProjectAnchorError, match="target_id"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "", "p-alpha"))


# ---------------------------------------------------------------------------
# 4-5. Portée globale et rattachée
# ---------------------------------------------------------------------------


def test_unanchored_data_is_global(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Une donnée sans ancre est de portée GLOBAL."""
    scope = _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))

    assert scope is AnchorScope.GLOBAL
    assert _run(service.projects_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) == []


def test_anchored_data_is_project_scoped(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Une donnée avec une seule ancre est de portée PROJECT."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    scope = _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))

    assert scope is AnchorScope.PROJECT
    assert _run(service.projects_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) == ["p-alpha"]


# ---------------------------------------------------------------------------
# 6. Partage multi-projets
# ---------------------------------------------------------------------------


def test_multi_project_sharing(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Une donnée peut être rattachée à plusieurs projets."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-beta"))

    scope = _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))

    assert scope is AnchorScope.MULTI_PROJECT
    assert set(_run(service.projects_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))) == {
        "p-alpha",
        "p-beta",
    }


def test_exclusive_target_refuses_second_project(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Une session appartient à un seul projet : un second rattachement est refusé."""
    _run(service.attach(AnchorTargetType.SESSION, "sess-1", "p-alpha"))

    with pytest.raises(ProjectAnchorError, match="exclusive"):
        _run(service.attach(AnchorTargetType.SESSION, "sess-1", "p-beta"))


# ---------------------------------------------------------------------------
# 7-8. Filtrage projet et isolation
# ---------------------------------------------------------------------------


def test_filter_by_project_keeps_global_and_own(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Le filtrage projet retourne le global et le sien, jamais celui d'autrui."""
    _run(seeded.save("knowledge", "kn-alpha", _knowledge("kn-alpha", "Alpha")))
    _run(seeded.save("knowledge", "kn-beta", _knowledge("kn-beta", "Beta")))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-alpha", "p-alpha"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-beta", "p-beta"))

    candidates = ["kn-1", "kn-alpha", "kn-beta"]
    visible = _run(service.filter_by_project(candidates, "p-alpha", AnchorTargetType.KNOWLEDGE_NODE))

    assert "kn-1" in visible       # global
    assert "kn-alpha" in visible    # le sien
    assert "kn-beta" not in visible  # celui d'un autre projet


def test_targets_for_project_lists_only_its_own(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """La liste des cibles d'un projet n'inclut pas les données d'un autre."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-beta"))

    alpha = _run(service.targets_for_project("p-alpha", AnchorTargetType.KNOWLEDGE_NODE))
    beta = _run(service.targets_for_project("p-beta", AnchorTargetType.KNOWLEDGE_NODE))

    assert alpha == ["kn-1"]
    assert beta == ["kn-1"]


def test_global_targets_exclude_anchored_data(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Les cibles globales sont celles qui n'ont aucune ancre active."""
    _run(seeded.save("knowledge", "kn-solo", _knowledge("kn-solo", "Solo")))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    globals_ = _run(service.global_targets(AnchorTargetType.KNOWLEDGE_NODE))

    assert "kn-solo" in globals_
    assert "kn-1" not in globals_


# ---------------------------------------------------------------------------
# 9. Préservation de la provenance
# ---------------------------------------------------------------------------


def test_anchor_preserves_provenance(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """L'ancre porte son auteur, sa date et ses métadonnées d'origine."""
    anchor = _run(
        service.attach(
            AnchorTargetType.MEMORY_RECORD,
            "EVT-2026-001",
            "p-alpha",
            actor="agent-architect",
            metadata={"origin": "session", "reason": "chantier DAENA"},
        )
    )

    assert anchor.actor == "agent-architect"
    assert anchor.created_at
    assert anchor.metadata["origin"] == "session"
    assert anchor.metadata["reason"] == "chantier DAENA"


def test_detach_preserves_history(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Détacher conserve l'historique du rattachement."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="tester"))

    assert _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha")) is True

    active = _run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))
    history = _run(
        service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", include_detached=True)
    )
    assert active == []
    assert len(history) == 1
    assert history[0].actor == "tester"
    assert history[0].detached_at


def test_detached_anchor_restores_scope(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Après détachement, la donnée redevient globale."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    assert _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) is AnchorScope.GLOBAL


def test_reattach_reactivates_the_same_anchor(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Rattacher à nouveau réactive l'ancre existante sans en créer de seconde."""
    first = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    again = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    assert again.anchor_id == first.anchor_id
    assert again.is_active
    assert len(_run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))) == 1


# ---------------------------------------------------------------------------
# 10-12. Persistance, relecture, redémarrage, historique
# ---------------------------------------------------------------------------


def test_anchor_survives_a_simulated_restart(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Les ancres sont durables : elles sont relues après reconstruction du service."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="tester"))

    rebuilt = ProjectAnchorService(seeded)
    anchors = _run(rebuilt.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))

    assert len(anchors) == 1
    assert anchors[0].project_id == "p-alpha"
    assert anchors[0].actor == "tester"


def test_historical_data_without_anchor_stays_global(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Les données historiques non rattachées restent globales et exploitables."""
    # Aucune ancre préexistante : c'est le cas des 100 KnowledgeNodes et des
    # 118 MemoryRecord déjà en base.
    assert _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) is AnchorScope.GLOBAL
    assert _run(service.projects_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) == []

    # Un rattachement ultérieur explicite reste possible.
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    assert _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) is AnchorScope.PROJECT


def test_anchor_domain_is_dedicated(service: ProjectAnchorService, seeded: CoreRecordStore) -> None:
    """Les ancres occupent leur propre domaine, sans toucher aux autres."""
    before = {domain: len(_run(seeded.list(domain))) for domain in ("knowledge", "projects")}

    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    after = {domain: len(_run(seeded.list(domain))) for domain in ("knowledge", "projects")}
    assert before == after
    assert len(_run(seeded.list(ANCHOR_DOMAIN))) == 1


def test_anchor_serialization_round_trip() -> None:
    """La sérialisation d'une ancre conserve tous les champs."""
    anchor = ProjectAnchor(
        anchor_id="a-1",
        target_type=AnchorTargetType.RESOURCE,
        target_id="r-1",
        project_id="p-alpha",
        created_at="2026-11-12T00:00:00Z",
        actor="tester",
        metadata={"k": "v"},
    )

    restored = ProjectAnchor.from_dict(anchor.to_dict())

    assert restored.anchor_id == anchor.anchor_id
    assert restored.target_type is AnchorTargetType.RESOURCE
    assert restored.metadata == {"k": "v"}
    assert restored.is_active


# ---------------------------------------------------------------------------
# 13. Non-régression
# ---------------------------------------------------------------------------


def test_knowledge_manager_non_regression(store: CoreRecordStore) -> None:
    """Le KnowledgeManager n'a pas été modifié par l'introduction des ancres."""
    km = KnowledgeManager(store=store)
    node = _run(km.create(label="Nœud", node_type=KnowledgeType.CONCEPT, content="c"))

    assert node.id in [n.id for n in _run(km.list())]
    assert _run(km.get(node.id)) is not None
    assert _run(km.delete(node.id)) is True


def test_engineering_memory_non_regression(tmp_path: Path) -> None:
    """L'Engineering Memory conserve son stockage documentaire."""
    from core.engineering_memory import EngineeringMemoryService, MemoryRecord, RecordType

    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = MemoryRecord(
        id="EVT-2026-002",
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
        notes="test P2.8.2",
    )
    stored = service.record(record)

    assert stored.repository_path is not None and stored.repository_path.is_file()
    assert service.get("EVT-2026-002") is not None


def test_p2_8_0_destinations_non_regression() -> None:
    """La correspondance des catégories de P2.8.0 reste valide."""
    from core.engineering_memory.models import RecordType as EMRecordType
    from core.engineering_memory.registry import EngineeringMemoryRegistry

    registry = EngineeringMemoryRegistry()

    assert registry.destination_for(EMRecordType.COMPONENT).relative_directory == (
        "Knowledge/Composants"
    )
    assert registry.destination_for(EMRecordType.TEST_RESULT).relative_directory == (
        "Knowledge/Tests-et-Preuves"
    )


def test_p2_8_1_persistence_non_regression(tmp_path: Path) -> None:
    """La persistance unifiée de P2.8.1 reste opérationnelle."""
    from core.resources.registry import ResourceRegistry
    from core.resources.repository import ResourceRepository

    store = CoreRecordStore()
    registry = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=store),
        store=store,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    _run(registry.persist())

    assert _run(ResourceRepository(store).count()) == 0
    assert Path(registry.export_path).is_file()


# ===========================================================================
# Consolidation P2.8.2 — défauts corrigés et garanties renforcées
# ===========================================================================


class _InterleavingStore(CoreRecordStore):
    """Store qui force l'entrelacement des opérations concurrentes.

    Deux points d'attente sont injectés :

    * `list_strict` — la lecture du contrôle d'exclusivité ;
    * `save_strict` — l'écriture qui suit le contrôle.

    L'attente placée **entre le contrôle et l'écriture** ouvre exactement la
    fenêtre qu'un contrôle suivi d'un `save()` laisse ouverte : les deux
    rattachements concurrents passent le contrôle avant que l'une des deux
    écritures ne soit visible. Sans section critique, les deux aboutissent.
    """

    def __init__(self, inner: CoreRecordStore) -> None:
        super().__init__()
        self._inner = inner

    async def list_strict(self, domain: str) -> list[dict[str, Any]]:
        await asyncio.sleep(0)
        return await self._inner.list_strict(domain)

    async def get_strict(self, domain: str, record_id: str) -> dict[str, Any] | None:
        return await self._inner.get_strict(domain, record_id)

    async def save_strict(self, domain: str, record_id: str, record: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        await self._inner.save_strict(domain, record_id, record)


class _BrokenStore(CoreRecordStore):
    """Store dont la lecture échoue, comme le ferait une panne d'infrastructure."""

    def __init__(self) -> None:
        super().__init__()
        self.reads = 0

    async def get_strict(self, domain: str, record_id: str) -> dict[str, Any] | None:
        self.reads += 1
        raise RecordStoreUnavailable("simulated read failure")

    async def list_strict(self, domain: str) -> list[dict[str, Any]]:
        raise RecordStoreUnavailable("simulated list failure")


# ---------------------------------------------------------------------------
# 1. Réactivation refusée si une autre ancre exclusive est active
# ---------------------------------------------------------------------------


def test_reattach_is_refused_when_another_exclusive_anchor_is_active(
    seeded: CoreRecordStore,
) -> None:
    """Une ancre détachée ne doit pas revenir active si un autre projet l'a prise."""
    service = ProjectAnchorService(seeded)
    _run(service.attach(AnchorTargetType.SESSION, "sess-1", "p-alpha"))
    _run(service.detach(AnchorTargetType.SESSION, "sess-1", "p-alpha"))
    # Un autre projet prend la cible pendant que l'ancre d'alpha est détachée.
    _run(service.attach(AnchorTargetType.SESSION, "sess-1", "p-beta"))

    with pytest.raises(ProjectAnchorError, match="exclusive"):
        _run(service.attach(AnchorTargetType.SESSION, "sess-1", "p-alpha"))

    active = _run(service.anchors_for(AnchorTargetType.SESSION, "sess-1"))
    assert [a.project_id for a in active] == ["p-beta"]
    # L'ancre d'alpha reste détachée : elle n'a pas été réactivée.
    alpha = _run(service.anchors_for(AnchorTargetType.SESSION, "sess-1", include_detached=True))
    alpha_anchor = [a for a in alpha if a.project_id == "p-alpha"][0]
    assert not alpha_anchor.is_active


# ---------------------------------------------------------------------------
# 2. Deux rattachements concurrents d'une même cible exclusive
# ---------------------------------------------------------------------------


def test_concurrent_attaches_of_an_exclusive_target_keep_one_owner(
    seeded: CoreRecordStore,
) -> None:
    """Deux rattachements concurrents : un seul projet peut posséder la cible."""
    store = _InterleavingStore(seeded)
    service = ProjectAnchorService(store)

    async def _both():
        return await asyncio.gather(
            service.attach(AnchorTargetType.SESSION, "sess-race", "p-alpha"),
            service.attach(AnchorTargetType.SESSION, "sess-race", "p-beta"),
            return_exceptions=True,
        )

    results = _run(_both())

    successes = [r for r in results if isinstance(r, ProjectAnchor)]
    failures = [r for r in results if isinstance(r, ProjectAnchorError)]
    assert len(successes) == 1, "un seul rattachement doit aboutir"
    assert len(failures) == 1, "l'autre doit être refusé pour exclusivité"
    assert "exclusive" in str(failures[0])

    active = _run(service.anchors_for(AnchorTargetType.SESSION, "sess-race"))
    assert len(active) == 1
    assert active[0].project_id == successes[0].project_id


# ---------------------------------------------------------------------------
# 3. Existence réelle d'une cible, par type, quand la source est disponible
# ---------------------------------------------------------------------------


def test_target_existence_is_verified_against_the_real_source(
    seeded: CoreRecordStore,
) -> None:
    """Chaque type dont la source est dans le store est vérifié réellement."""
    _run(seeded.save("resources", "res-1", {"stable_id": "res-1", "id": "res-1"}))
    _run(seeded.save("missions", "mis-1", {"id": "mis-1", "title": "Mission"}))
    service = ProjectAnchorService(seeded)

    for kind, target_id in (
        (AnchorTargetType.KNOWLEDGE_NODE, "kn-1"),
        (AnchorTargetType.RESOURCE, "res-1"),
        (AnchorTargetType.MISSION, "mis-1"),
    ):
        resolution = _run(service.resolve_target(kind, target_id))
        assert resolution.verified, f"{kind.value} : {resolution.reason}"
        anchor = _run(service.attach(kind, target_id, "p-alpha"))
        assert anchor.history[-1]["target_existence"] == "verified"


def test_unresolvable_source_is_not_claimed_as_verified(seeded: CoreRecordStore) -> None:
    """Une source inaccessible ne doit pas être présentée comme vérifiée."""
    service = ProjectAnchorService(seeded)

    resolution = _run(service.resolve_target(AnchorTargetType.MEMORY_RECORD, "EVT-1"))

    assert not resolution.verified
    assert resolution.existence is TargetExistence.UNRESOLVABLE
    anchor = _run(service.attach(AnchorTargetType.MEMORY_RECORD, "EVT-1", "p-alpha"))
    assert anchor.history[-1]["target_existence"] == "unresolvable"


def test_injected_resolver_is_used_for_memory_records(seeded: CoreRecordStore) -> None:
    """Un résolveur injecté est consulté : il fait autorité."""
    calls: list[str] = []

    async def _resolver(target_id: str) -> TargetResolution:
        calls.append(target_id)
        return TargetResolution.found("vault-test")

    service = ProjectAnchorService(
        seeded, target_resolvers={AnchorTargetType.MEMORY_RECORD: _resolver}
    )

    anchor = _run(service.attach(AnchorTargetType.MEMORY_RECORD, "EVT-42", "p-alpha"))

    assert calls == ["EVT-42"]
    assert anchor.history[-1]["target_existence"] == "verified"


# ---------------------------------------------------------------------------
# 4. Cible inexistante refusée
# ---------------------------------------------------------------------------


def test_missing_target_is_refused(seeded: CoreRecordStore) -> None:
    """Une cible absente de sa source est refusée."""
    service = ProjectAnchorService(seeded)

    with pytest.raises(ProjectAnchorError, match="not found"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-inexistant", "p-alpha"))

    assert _run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-inexistant")) == []


# ---------------------------------------------------------------------------
# 5. Inventaire indisponible distingué d'une liste réellement vide
# ---------------------------------------------------------------------------


def test_unavailable_inventory_is_distinguished_from_an_empty_one(
    seeded: CoreRecordStore,
) -> None:
    """Un inventaire indisponible n'est pas une liste vide."""
    service = ProjectAnchorService(seeded)

    # Type sans source dans le store : inventaire indisponible.
    memory = _run(service.global_inventory(AnchorTargetType.MEMORY_RECORD))
    assert memory["status"] == "unavailable"
    assert memory["targets"] == []
    assert memory["reason"]

    # Domaine non alimenté : la source n'est pas résoluble non plus.
    empty_source = _run(service.global_inventory(AnchorTargetType.RESOURCE))
    assert empty_source["status"] == "unavailable"

    # Domaine alimenté mais cible rattachée : la liste globale est réelle,
    # elle omet la cible rattachée et conserve les autres.
    _run(seeded.save("knowledge", "kn-solo", _knowledge("kn-solo", "Solo")))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-solo", "p-alpha"))
    populated = _run(service.global_inventory(AnchorTargetType.KNOWLEDGE_NODE))
    assert populated["status"] == "ok"
    assert "kn-solo" not in populated["targets"]
    assert "kn-1" in populated["targets"]

    # Et la liste n'est pas vide non plus quand une cible globale existe.
    _run(seeded.save("knowledge", "kn-libre", _knowledge("kn-libre", "Libre")))
    with_global = _run(service.global_inventory(AnchorTargetType.KNOWLEDGE_NODE))
    assert with_global["status"] == "ok"
    assert "kn-libre" in with_global["targets"]


def test_global_targets_refuses_to_masquer_an_unavailable_inventory(
    seeded: CoreRecordStore,
) -> None:
    """`global_targets` ne renvoie pas une liste vide quand la source manque."""
    service = ProjectAnchorService(seeded)

    with pytest.raises(ProjectAnchorError, match="unavailable"):
        _run(service.global_targets(AnchorTargetType.MEMORY_RECORD))


# ---------------------------------------------------------------------------
# 6. Erreur de lecture du store distinguée d'un projet inexistant
# ---------------------------------------------------------------------------


def test_store_read_failure_is_not_reported_as_a_missing_project() -> None:
    """Une panne de lecture est une panne technique, pas un projet absent."""
    store = _BrokenStore()
    service = ProjectAnchorService(store)

    with pytest.raises(ProjectAnchorStoreUnavailable):
        _run(service.validate_project("p-alpha"))

    with pytest.raises(ProjectAnchorStoreUnavailable):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    # Et un projet réellement absent reste une erreur métier.
    healthy = ProjectAnchorService(CoreRecordStore())
    with pytest.raises(ProjectAnchorError, match="not found"):
        _run(healthy.validate_project("p-alpha"))


# ---------------------------------------------------------------------------
# 7. Identifiants invalides dans detach()
# ---------------------------------------------------------------------------


def test_detach_validates_its_identifiers(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """`detach` applique la même validation que `attach`."""
    with pytest.raises(ProjectAnchorError, match="target_id"):
        _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "", "p-alpha"))

    with pytest.raises(ProjectAnchorError, match="project_id"):
        _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "   "))

    with pytest.raises(ProjectAnchorError, match="target_type"):
        _run(service.detach("inconnu", "kn-1", "p-alpha"))


def test_attach_validates_its_identifiers(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """`attach` refuse un type inconnu et normalise les identifiants."""
    with pytest.raises(ProjectAnchorError, match="target_type"):
        _run(service.attach("inconnu", "kn-1", "p-alpha"))

    with pytest.raises(ProjectAnchorError, match="target_id"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "   ", "p-alpha"))

    with pytest.raises(ProjectAnchorError, match="project_id"):
        _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", ""))


def test_identifiers_are_normalized_consistently(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Le bord d'un identifiant est normalisé de la même façon partout."""
    anchor = _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, " kn-1 ", " p-alpha "))

    assert anchor.target_id == "kn-1"
    assert anchor.project_id == "p-alpha"

    # Le détachement avec la même graphie retrouve l'ancre.
    assert _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, " kn-1 ", " p-alpha ")) is True


# ---------------------------------------------------------------------------
# 8-9. Historique des cycles et métadonnées initiales
# ---------------------------------------------------------------------------


def test_multiple_attach_detach_cycles_preserve_the_history(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Chaque cycle de rattachement est conservé."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="a1"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="d1"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="a2"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="d2"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="a3"))

    history = _run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))[0].history

    assert len(history) == 3
    assert [cycle["actor"] for cycle in history] == ["a1", "a2", "a3"]
    assert history[0]["detached_at"]
    assert history[0]["detached_by"] == "d1"
    assert history[1]["detached_at"]
    assert history[2]["detached_at"] is None


def test_initial_metadata_is_preserved_across_a_reattach(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """La réactivation n'efface pas silencieusement les métadonnées d'origine."""
    _run(
        service.attach(
            AnchorTargetType.KNOWLEDGE_NODE,
            "kn-1",
            "p-alpha",
            actor="a1",
            metadata={"origin": "session", "reason": "chantier DAENA"},
        )
    )
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(
        service.attach(
            AnchorTargetType.KNOWLEDGE_NODE,
            "kn-1",
            "p-alpha",
            actor="a2",
            metadata={"origin": "rattrapage"},
        )
    )

    anchor = _run(service.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))[0]

    # Le cycle d'origine reste lisible.
    assert anchor.history[0]["metadata"]["origin"] == "session"
    assert anchor.history[0]["metadata"]["reason"] == "chantier DAENA"
    # Le nouveau cycle porte ses propres métadonnées.
    assert anchor.history[1]["metadata"]["origin"] == "rattrapage"
    # Et l'état courant expose les métadonnées d'origine.
    assert anchor.metadata["origin"] == "session"


# ---------------------------------------------------------------------------
# 10-12. Filtrage, portée globale et isolation
# ---------------------------------------------------------------------------


def test_include_global_false_excludes_unanchored_data(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """`include_global=False` retire les données sans ancre."""
    _run(seeded.save("knowledge", "kn-own", _knowledge("kn-own", "Own")))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-own", "p-alpha"))

    candidates = ["kn-1", "kn-own"]
    with_global = _run(
        service.filter_by_project(candidates, "p-alpha", AnchorTargetType.KNOWLEDGE_NODE)
    )
    without_global = _run(
        service.filter_by_project(
            candidates, "p-alpha", AnchorTargetType.KNOWLEDGE_NODE, include_global=False
        )
    )

    assert "kn-1" in with_global
    assert "kn-1" not in without_global
    assert "kn-own" in without_global


def test_detached_target_becomes_global_again(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Une cible détachée redevient globale et réintègre l'inventaire global."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    assert _run(service.scope_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1")) is AnchorScope.GLOBAL
    visible = _run(
        service.filter_by_project(
            ["kn-1"], "p-beta", AnchorTargetType.KNOWLEDGE_NODE
        )
    )
    assert visible == ["kn-1"]
    globals_ = _run(service.global_targets(AnchorTargetType.KNOWLEDGE_NODE))
    assert "kn-1" in globals_


def test_exclusive_target_of_another_project_is_never_exposed(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Une cible exclusive d'un autre projet n'est jamais visible ailleurs."""
    _run(service.attach(AnchorTargetType.SESSION, "sess-x", "p-beta"))

    visible = _run(
        service.filter_by_project(["sess-x"], "p-alpha", AnchorTargetType.SESSION)
    )

    assert visible == []


def test_filtering_for_an_unknown_project_is_refused(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Filtrer pour un projet inconnu ou inactif est refusé."""
    with pytest.raises(ProjectAnchorError, match="not found"):
        _run(
            service.filter_by_project(
                ["kn-1"], "p-inexistant", AnchorTargetType.KNOWLEDGE_NODE
            )
        )

    with pytest.raises(ProjectAnchorError, match="inactive"):
        _run(
            service.filter_by_project(["kn-1"], "p-archive", AnchorTargetType.KNOWLEDGE_NODE)
        )


# ---------------------------------------------------------------------------
# 15. Persistance après reconstruction du service
# ---------------------------------------------------------------------------


def test_history_survives_a_service_reconstruction(seeded: CoreRecordStore) -> None:
    """L'historique des cycles est relu après reconstruction du service."""
    service = ProjectAnchorService(seeded)
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="a1"))
    _run(service.detach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="d1"))
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha", actor="a2"))

    rebuilt = ProjectAnchorService(seeded)
    anchor = _run(rebuilt.anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-1"))[0]

    assert len(anchor.history) == 2
    assert anchor.history[0]["detached_at"]
    assert anchor.history[1]["actor"] == "a2"
    assert anchor.is_active


def test_legacy_anchor_without_history_is_readable(seeded: CoreRecordStore) -> None:
    """Une ancre antérieure à l'historique des cycles reste lisible."""
    legacy = {
        "anchor_id": "legacy-1",
        "target_type": "knowledge_node",
        "target_id": "kn-legacy",
        "project_id": "p-alpha",
        "created_at": "2026-11-01T00:00:00Z",
        "actor": "legacy",
        "metadata": {"origin": "historique"},
        "detached_at": None,
    }
    _run(seeded.save(ANCHOR_DOMAIN, "legacy-1", legacy))

    anchor = _run(
        ProjectAnchorService(seeded).anchors_for(AnchorTargetType.KNOWLEDGE_NODE, "kn-legacy")
    )[0]

    assert anchor.actor == "legacy"
    assert anchor.metadata == {"origin": "historique"}
    assert len(anchor.history) == 1
    assert anchor.history[0]["attached_at"] == "2026-11-01T00:00:00Z"


# ---------------------------------------------------------------------------
# 16. Non-régression des sources
# ---------------------------------------------------------------------------


def test_source_models_are_not_modified_by_anchoring(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Les cinq modèles sources restent inchangés par un ancrage."""
    before = {
        domain: _run(seeded.list(domain))
        for domain in ("knowledge", "resources", "missions", "projects")
    }

    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    after = {
        domain: _run(seeded.list(domain))
        for domain in ("knowledge", "resources", "missions", "projects")
    }
    assert before == after


def test_anchors_stay_in_their_own_domain(
    service: ProjectAnchorService, seeded: CoreRecordStore
) -> None:
    """Les ancres n'occupent que leur domaine dédié."""
    _run(service.attach(AnchorTargetType.KNOWLEDGE_NODE, "kn-1", "p-alpha"))

    rows = _run(seeded.list(ANCHOR_DOMAIN))

    assert len(rows) == 1
    assert rows[0]["target_type"] == "knowledge_node"
    assert "history" in rows[0]
