"""Tests DAĒNĀ P2.7 — Découverte documentaire, classification et cycle de vie.

Ces tests s'exécutent sur des répertoires temporaires : les fichiers sources
réels du dépôt ne sont jamais modifiés, déplacés ni supprimés.

Périmètre couvert :
  1. Découverte des documents Markdown
  2. Découverte des documents RST
  3. Classification des documents
  4. Stabilité des UUIDv5
  5. Idempotence des redécouvertes
  6. Détection des modifications
  7. Détection des disparitions
  8. Restauration des documents réapparus
  9. Extraction du contenu
  10. Création et mise à jour des KnowledgeNodes
  11. Relations avec les Skills
  12. Préservation du catalogue des Skills
  13. Contrôle des autorisations (fail-closed)
  14. Gestion des erreurs partielles
  15. Non-régression des fonctionnalités existantes
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeType
from core.resources.discovery import (
    DEFAULT_SKILLS_ROOT,
    _compute_stable_id,
    classify_document,
    discover_documents,
    discover_skills,
    knowledge_root_list,
)
from core.resources.registry import (
    ResourceRegistry,
    _ExecutionContext,
    _AgentPrincipal,
    authorize_resource_access,
    check_access,
)
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
def km() -> KnowledgeManager:
    """KnowledgeManager isolé, adossé à un store mémoire."""
    return KnowledgeManager(store=CoreRecordStore())


@pytest.fixture
def registry(tmp_path: Path, km: KnowledgeManager) -> ResourceRegistry:
    """Registre isolé, adossé à une persistance JSON temporaire.

    Le ResourceRegistry cherche par défaut ``registry-meta.json`` à la racine
    ETHAN lorsqu'il n'est pas trouvé au chemin indiqué. On vide donc l'état
    chargé pour garantir que le test n'observe que ses propres ressources.
    """
    registry = ResourceRegistry(
        knowledge_manager=km,
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )
    registry._records.clear()
    registry._rebuild_indices()
    return registry


@pytest.fixture
def docs_root(tmp_path: Path) -> Path:
    """Racine documentaire temporaire avec un sous-répertoire user-guide."""
    root = tmp_path / "docs"
    (root / "user-guide").mkdir(parents=True)
    return root


def _write_doc(path: Path, title: str, body: str = "") -> Path:
    """Écrit un document Markdown minimal et renvoie son chemin."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"# {title}\n\n{body or 'Contenu de test suffisamment long pour être exploitable.'}\n"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 1. Découverte des documents Markdown
# ---------------------------------------------------------------------------


def test_discovers_markdown_documents(docs_root: Path) -> None:
    """Les fichiers .md des emplacements configurés sont découverts."""
    _write_doc(docs_root / "guide.md", "Guide de démarrage")
    _write_doc(docs_root / "user-guide" / "agents.md", "Agents")

    metas, nodes = discover_documents((docs_root,), create_knowledge_nodes=True)

    titles = sorted(meta["title"] for meta in metas)
    assert titles == ["Agents", "Guide de démarrage"]
    assert all(meta["resource_type"] in {rt.value for rt in ResourceType} for meta in metas)
    assert len(nodes) == len(metas)


def test_discovery_preserves_source_path(docs_root: Path) -> None:
    """Le chemin source d'origine est conservé tel quel, sans copie ni déplacement."""
    doc = _write_doc(docs_root / "guide.md", "Guide")

    metas, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert len(metas) == 1
    assert metas[0]["source_original"] == str(doc)
    assert doc.is_file()
    assert doc.read_text(encoding="utf-8").startswith("# Guide")


def test_discovery_ignores_non_configured_locations(docs_root: Path, tmp_path: Path) -> None:
    """Aucun parcours global : seul l'emplacement configuré est exploré."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    _write_doc(outside / "orphan.md", "Hors périmètre")

    metas, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert metas == []


# ---------------------------------------------------------------------------
# 2. Découverte des documents RST
# ---------------------------------------------------------------------------


def test_discovers_rst_documents(docs_root: Path) -> None:
    """Les fichiers .rst sont pris en charge au même titre que les .md."""
    rst = docs_root / "reference.rst"
    rst.write_text(
        "Reference\n=========\n\nUne description suffisamment longue pour etre exploitee.\n",
        encoding="utf-8",
    )

    metas, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert len(metas) == 1
    assert metas[0]["source_original"] == str(rst)


# ---------------------------------------------------------------------------
# 3. Classification des documents
# ---------------------------------------------------------------------------


def test_classification_is_deterministic_and_justified() -> None:
    """La classification est déterministe et porte sa justification."""
    first = classify_document("ADR-001 — Choix technique", "decisions", "", [])
    second = classify_document("ADR-001 — Choix technique", "decisions", "", [])
    assert first == second
    assert first[0] == ResourceType.ADR
    assert first[1]


def test_classification_defaults_to_other_without_signal() -> None:
    """Sans signal explicite, le document est OTHER et non une catégorie arbitraire."""
    resource_type, reason = classify_document("Notes diverses", "notes", "", [])
    assert resource_type == ResourceType.OTHER
    assert "OTHER" in reason


def test_classification_uses_declared_category() -> None:
    """Une catégorie explicitement déclarée prime sur l'absence de mot-clé."""
    resource_type, _ = classify_document("Notes diverses", "notes", "", ["agent"])
    assert resource_type == ResourceType.AGENT


def test_discovery_records_classification_reason(docs_root: Path) -> None:
    """Chaque document découvert porte la justification de sa classification."""
    _write_doc(docs_root / "adr-001.md", "ADR-001 — Décision")

    metas, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert metas[0]["classification_reason"]
    assert metas[0]["metadata"]["classification_reason"] == metas[0]["classification_reason"]


# ---------------------------------------------------------------------------
# 4. Stabilité des UUIDv5
# ---------------------------------------------------------------------------


def test_stable_id_is_deterministic() -> None:
    """Le même triplet type/source/titre produit toujours le même identifiant."""
    first = _compute_stable_id(ResourceType.DOCUMENT, "/tmp/a.md", "Titre")
    second = _compute_stable_id(ResourceType.DOCUMENT, "/tmp/a.md", "Titre")
    assert first == second
    assert first != _compute_stable_id(ResourceType.DOCUMENT, "/tmp/b.md", "Titre")


def test_stable_id_survives_rediscovery(docs_root: Path) -> None:
    """Deux scans successifs produisent les mêmes identifiants."""
    _write_doc(docs_root / "guide.md", "Guide")

    first, _ = discover_documents((docs_root,), create_knowledge_nodes=False)
    second, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert [m["stable_id"] for m in first] == [m["stable_id"] for m in second]


# ---------------------------------------------------------------------------
# 5. Idempotence des redécouvertes
# ---------------------------------------------------------------------------


def test_rediscovery_creates_no_duplicate(registry: ResourceRegistry, docs_root: Path) -> None:
    """Une redécouverte n'ajoute aucun doublon au registre."""
    _write_doc(docs_root / "guide.md", "Guide")
    _write_doc(docs_root / "user-guide" / "agents.md", "Agents")

    first = _run(registry.discover_documents((docs_root,)))
    count_after_first = len(registry._records)
    second = _run(registry.discover_documents((docs_root,)))

    assert first["documents_discovered"] == second["documents_discovered"] == 2
    assert len(registry._records) == count_after_first == 2
    assert second["status_counts"]["stale"] == 0


def test_overlapping_roots_do_not_duplicate(docs_root: Path) -> None:
    """Des racines imbriquées ne produisent pas de double découverte."""
    _write_doc(docs_root / "user-guide" / "agents.md", "Agents")

    metas, _ = discover_documents((docs_root, docs_root / "user-guide"), create_knowledge_nodes=False)

    assert len(metas) == 1
    assert len({m["stable_id"] for m in metas}) == 1


# ---------------------------------------------------------------------------
# 6. Détection des modifications
# ---------------------------------------------------------------------------


def test_modification_is_detected(registry: ResourceRegistry, docs_root: Path) -> None:
    """Un document modifié est signalé comme stale puis revalidé."""
    doc = _write_doc(docs_root / "guide.md", "Guide", "Première version du contenu.")
    _run(registry.discover_documents((docs_root,)))

    _write_doc(doc, "Guide révisé", "Deuxième version du contenu, nettement différente.")
    result = _run(registry.discover_documents((docs_root,)))

    assert result["status_counts"]["stale"] == 1
    record = next(iter(registry._records.values()))
    assert record.title == "Guide révisé"
    assert record.status == ResourceStatus.ACTIVE


# ---------------------------------------------------------------------------
# 7. Détection des disparitions
# ---------------------------------------------------------------------------


def test_disappearance_is_detected_without_deletion(
    registry: ResourceRegistry, docs_root: Path
) -> None:
    """Un document supprimé passe DISAPPEARED sans que ses métadonnées soient perdues."""
    doc = _write_doc(docs_root / "guide.md", "Guide")
    _run(registry.discover_documents((docs_root,)))
    stable_id = next(iter(registry._records.values())).stable_id

    doc.unlink()
    result = _run(registry.discover_documents((docs_root,)))

    assert result["status_counts"]["disappeared"] == 1
    record = registry._records[stable_id]
    assert record.status == ResourceStatus.DISAPPEARED
    # Les métadonnées et la provenance sont conservées.
    assert record.title == "Guide"
    assert record.source_original == str(doc)
    assert record.metadata


# ---------------------------------------------------------------------------
# 8. Restauration des documents réapparus
# ---------------------------------------------------------------------------


def test_restoration_when_document_reappears(
    registry: ResourceRegistry, docs_root: Path
) -> None:
    """Un document réapparu est restauré en ACTIVE."""
    doc = _write_doc(docs_root / "guide.md", "Guide")
    _run(registry.discover_documents((docs_root,)))
    stable_id = next(iter(registry._records.values())).stable_id

    doc.unlink()
    _run(registry.discover_documents((docs_root,)))
    assert registry._records[stable_id].status == ResourceStatus.DISAPPEARED

    _write_doc(doc, "Guide")
    _run(registry.discover_documents((docs_root,)))

    assert registry._records[stable_id].status == ResourceStatus.ACTIVE


# ---------------------------------------------------------------------------
# 9. Extraction du contenu
# ---------------------------------------------------------------------------


def test_content_is_extracted(docs_root: Path) -> None:
    """Le contenu d'un document exploitable est réellement extrait."""
    _write_doc(docs_root / "guide.md", "Guide", "Un contenu suffisamment volumineux.")

    metas, nodes = discover_documents((docs_root,), create_knowledge_nodes=True)

    assert metas[0]["knowledge_state"] == "extracted"
    assert metas[0]["extracted_content"]
    assert nodes[0].content


def test_empty_document_is_discovered_but_not_extracted(docs_root: Path) -> None:
    """Un document sans contenu exploitable reste DISCOVERED, il n'est pas indexé."""
    empty = docs_root / "vide.md"
    empty.write_text("# Vide\n", encoding="utf-8")

    metas, _ = discover_documents((docs_root,), create_knowledge_nodes=False)

    assert metas[0]["knowledge_state"] == "discovered"
    assert metas[0]["extracted_content"] == ""


def test_knowledge_states_are_distinguished(registry: ResourceRegistry, docs_root: Path) -> None:
    """DISCOVERED, EXTRACTED et INDEXED sont trois états distincts."""
    _write_doc(docs_root / "guide.md", "Guide")
    _write_doc(docs_root / "vide.md", "Vide")
    (docs_root / "vide.md").write_text("# Vide\n", encoding="utf-8")

    result = _run(registry.discover_documents((docs_root,)))
    assert result["knowledge_states"]["extracted"] == 1
    assert result["knowledge_states"]["discovered"] == 1
    assert result["knowledge_states"]["indexed"] == 0

    from core.rag.pipeline import RAGPipeline

    rag = RAGPipeline(vector_backend="memory")
    indexing = _run(registry.index_documents(rag))

    assert indexing["indexed_count"] == 1
    assert indexing["failed_count"] == 0
    assert len(_run(rag.list_documents())) == 1


# ---------------------------------------------------------------------------
# 10. Création et mise à jour des KnowledgeNodes
# ---------------------------------------------------------------------------


def test_knowledge_nodes_are_created_and_attached(
    registry: ResourceRegistry, km: KnowledgeManager, docs_root: Path
) -> None:
    """Chaque document découvert reçoit un KnowledgeNode exploitable."""
    _write_doc(docs_root / "guide.md", "Guide")

    result = _run(registry.discover_documents((docs_root,)))

    assert result["knowledge_nodes_created"] == 1
    record = next(iter(registry._records.values()))
    assert record.knowledge_node is not None
    assert record.knowledge_node.node_type == KnowledgeType.DOCUMENT
    assert record.knowledge_node.source == record.source_original
    # L'identité du nœud est alignée sur celle de la ressource.
    assert record.knowledge_node.id == record.stable_id
    assert _run(km.get(record.stable_id)) is not None


def test_knowledge_node_content_is_refreshed_on_change(
    registry: ResourceRegistry, docs_root: Path
) -> None:
    """Le contenu du KnowledgeNode suit l'évolution du document."""
    doc = _write_doc(docs_root / "guide.md", "Guide", "Version initiale du document.")
    _run(registry.discover_documents((docs_root,)))
    record = next(iter(registry._records.values()))
    initial = record.knowledge_node.content

    _write_doc(doc, "Guide", "Version révisée avec un contenu nettement différent.")
    _run(registry.discover_documents((docs_root,)))

    assert registry._records[record.stable_id].knowledge_node.content != initial


def test_registry_persists_and_reloads(registry: ResourceRegistry, docs_root: Path, tmp_path: Path) -> None:
    """L'état du registre est rechargé depuis la persistance JSON."""
    _write_doc(docs_root / "guide.md", "Guide")
    _run(registry.discover_documents((docs_root,)))

    reloaded = ResourceRegistry(
        knowledge_manager=KnowledgeManager(store=CoreRecordStore()),
        registry_meta_path=str(tmp_path / "registry-meta.json"),
    )

    assert len(reloaded._records) == 1
    record = next(iter(reloaded._records.values()))
    assert record.title == "Guide"
    assert record.source_original == str(docs_root / "guide.md")
    assert record.status == ResourceStatus.ACTIVE


# ---------------------------------------------------------------------------
# 11. Relations avec les Skills
# ---------------------------------------------------------------------------


def test_relations_created_only_on_exact_match(
    registry: ResourceRegistry, docs_root: Path, tmp_path: Path
) -> None:
    """Une relation n'est créée que si les titres normalisés coïncident exactement."""
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "docker-patterns"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: docker-patterns\ndescription: Docker\n---\n\n# Docker Patterns\n\nContenu.\n",
        encoding="utf-8",
    )

    _write_doc(docs_root / "Docker Patterns.md", "Docker Patterns")
    _write_doc(docs_root / "autre.md", "Documentation sans rapport")

    # Le catalogue des Skills est enregistré par le registre lui-même.
    _run(registry.discover_skills(skills_root))
    _run(registry.discover_documents((docs_root,)))

    result = _run(registry.link_documents_to_skills())

    assert result["linked_count"] == 1
    link = result["links"][0]
    assert link["justification"] == "normalized titles are identical"
    assert link["document_id"] != link["skill_id"]


def test_no_relation_for_unrelated_document(
    registry: ResourceRegistry, docs_root: Path, tmp_path: Path
) -> None:
    """Aucune relation n'est inventée pour un document sans correspondance."""
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "docker-patterns"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: docker-patterns\ndescription: Docker\n---\n\n# Docker Patterns\n\nContenu.\n",
        encoding="utf-8",
    )

    _write_doc(docs_root / "guide.md", "Guide sans correspondance")

    _run(registry.discover_skills(skills_root))
    _run(registry.discover_documents((docs_root,)))

    result = _run(registry.link_documents_to_skills())

    assert result["linked_count"] == 0


# ---------------------------------------------------------------------------
# 12. Préservation du catalogue des Skills
# ---------------------------------------------------------------------------


def test_skill_catalogue_is_preserved() -> None:
    """Le catalogue des Skills OpenCode reste discoverable et inchangé."""
    skills, nodes = discover_skills(create_knowledge_nodes=True)

    assert len(skills) == 391
    assert len(nodes) == len(skills)
    assert all(skill["stable_id"] for skill in skills)
    assert all(skill["source_original"].startswith(str(DEFAULT_SKILLS_ROOT)) for skill in skills)


def test_skill_discovery_is_idempotent() -> None:
    """Deux scans du catalogue produisent les mêmes identifiants."""
    first, _ = discover_skills(create_knowledge_nodes=False)
    second, _ = discover_skills(create_knowledge_nodes=False)

    assert [s["stable_id"] for s in first] == [s["stable_id"] for s in second]
    assert len(first) == len(second)


def test_skill_registry_entries_survive_document_discovery(
    registry: ResourceRegistry, docs_root: Path
) -> None:
    """La découverte documentaire n'altère pas les entrées du catalogue des Skills."""
    skill_record = registry._records.get("")
    before = len(registry._records)

    _write_doc(docs_root / "guide.md", "Guide")
    _run(registry.discover_documents((docs_root,)))

    assert len(registry._records) == before + 1


# ---------------------------------------------------------------------------
# 13. Contrôle des autorisations (fail-closed)
# ---------------------------------------------------------------------------


def _principal(**overrides) -> _AgentPrincipal:
    """Construit un porteur HROT conforme au contrat du Resource Registry."""
    payload = {
        "principal_id": "principal-1",
        "principal_type": "AGENT",
        "subject_id": "agent-1",
        "actor_id": "agent-1",
        "permissions": ["resource:read"],
        "scopes": ["skill", "document", "resource"],
        "auth_proof": "proof",
    }
    payload.update(overrides)
    return _AgentPrincipal(**payload)


def test_access_is_denied_without_authorization() -> None:
    """Sans contexte d'exécution, l'accès est refusé (fail-closed)."""
    assert check_access(None, operation="read") is False
    allowed, reason = authorize_resource_access(None, operation="read")
    assert allowed is False
    assert "ACCESS_DENIED" in reason


def test_access_is_denied_without_auth_proof() -> None:
    """Un porteur sans auth_proof est refusé (fail-closed)."""
    principal = _principal(auth_proof=None)
    context = _ExecutionContext(principal=principal, agent_id="agent-1")

    assert check_access(context, operation="read") is False


def test_access_is_denied_for_non_agent_principal() -> None:
    """Un porteur qui n'est pas de type AGENT est refusé (fail-closed)."""
    principal = _principal(principal_type="SERVICE")
    context = _ExecutionContext(principal=principal, agent_id="agent-1")

    assert check_access(context, operation="read") is False


def test_access_is_denied_on_agent_id_mismatch() -> None:
    """Un agent_id non concordant est refusé (fail-closed)."""
    principal = _principal(actor_id="agent-other")
    context = _ExecutionContext(principal=principal, agent_id="agent-1")

    assert check_access(context, operation="read") is False


def test_access_is_granted_with_valid_authorization() -> None:
    """Un porteur correctement autorisé obtient l'accès."""
    context = _ExecutionContext(principal=_principal(), agent_id="agent-1")

    assert check_access(context, operation="read") is True


def test_discovery_does_not_bypass_authorization() -> None:
    """La découverte documentaire n'ouvre aucun accès non autorisé."""
    context = _ExecutionContext(principal=_principal(), agent_id="agent-1")

    allowed, reason = authorize_resource_access(context, operation="write")
    assert allowed is False
    assert "ACCESS_DENIED" in reason


# ---------------------------------------------------------------------------
# 14. Gestion des erreurs partielles
# ---------------------------------------------------------------------------


def test_unreadable_document_does_not_stop_discovery(
    registry: ResourceRegistry, docs_root: Path, monkeypatch
) -> None:
    """Un document illisible n'interrompt pas la découverte des autres."""
    good = _write_doc(docs_root / "guide.md", "Guide")
    bad = _write_doc(docs_root / "casse.md", "Cassé")

    original_read = Path.read_text

    def failing_read(self: Path, *args, **kwargs):
        if self == bad:
            raise OSError("fichier illisible")
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read)

    result = _run(registry.discover_documents((docs_root,)))

    assert result["documents_discovered"] == 1
    assert good.is_file()


def test_missing_root_is_ignored(registry: ResourceRegistry, tmp_path: Path) -> None:
    """Un emplacement configuré absent n'interrompt pas la découverte."""
    result = _run(registry.discover_documents((tmp_path / "absent",)))

    assert result["documents_discovered"] == 0
    assert result["status_counts"]["disappeared"] == 0


# ---------------------------------------------------------------------------
# 15. Non-régression des fonctionnalités existantes
# ---------------------------------------------------------------------------


def test_knowledge_root_normalisation_deduplicates() -> None:
    """La normalisation des racines élimine les doublons et absolutise les chemins."""
    roots = knowledge_root_list((Path("/tmp/docs"), Path("/tmp/docs/"), Path("/tmp/docs")))
    assert len(roots) == 1
    assert roots[0].is_absolute()


def test_registry_search_still_works(registry: ResourceRegistry, docs_root: Path) -> None:
    """La recherche de ressources reste fonctionnelle après découverte documentaire."""
    _write_doc(docs_root / "guide.md", "Guide de démarrage")
    _run(registry.discover_documents((docs_root,)))

    results = registry.search_resources("démarrage")

    assert results
    assert any("démarrage" in record.title for record in results)


def test_registry_stats_and_indexes_consistent(
    registry: ResourceRegistry, docs_root: Path
) -> None:
    """Les index du registre restent cohérents avec les enregistrements."""
    _write_doc(docs_root / "guide.md", "Guide")
    _run(registry.discover_documents((docs_root,)))

    stats = registry.get_stats()
    assert stats["total_resources"] == len(registry._records)
    indexed = sum(len(records) for records in registry._index["by_type"].values())
    assert indexed == len(registry._records)


def test_knowledge_manager_create_accepts_explicit_id(km: KnowledgeManager) -> None:
    """KnowledgeManager.create accepte un identifiant imposé et reste idempotent."""
    first = _run(
        km.create(
            label="Nœud stable",
            node_type=KnowledgeType.DOCUMENT,
            content="contenu",
            source="/tmp/source.md",
            node_id="fixed-id",
        )
    )
    second = _run(
        km.create(
            label="Nœud stable",
            node_type=KnowledgeType.DOCUMENT,
            content="contenu",
            source="/tmp/source.md",
            node_id="fixed-id",
        )
    )

    assert first.id == "fixed-id"
    assert second.id == "fixed-id"
    assert _run(km.get("fixed-id")) is not None
