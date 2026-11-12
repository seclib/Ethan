"""DAĒNĀ P2.8.0 — Correspondance entre les destinations configurées et le corpus réel.

Ces tests vérifient que `EngineeringMemoryRegistry` résout chaque catégorie
vers un emplacement **réellement présent** dans le corpus documentaire, et que
la résolution reste strictement en lecture seule.

Aucun test n'écrit dans le corpus réel : les écritures se font dans des
répertoires temporaires (`tmp_path`).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from core.engineering_memory import EngineeringMemoryService
from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordOrigin,
    RecordType,
    SourceOfFactLevel,
)
from core.engineering_memory.persistence import ObsidianPersistence
from core.engineering_memory.registry import EngineeringMemoryRegistry
from core.engineering_memory.validators import ValidationError

# --------------------------------------------------------------------------
# Racine du corpus documentaire réel (lecture seule dans tous les tests)
# --------------------------------------------------------------------------

DEFAULT_CORPUS_ROOT = Path("/home/fatsio/AI/Ethan/daena")


def _corpus_root() -> Path:
    """Racine du corpus, telle que configurée pour l'Engineering Memory."""
    raw = os.environ.get("ETHAN_ENGINEERING_MEMORY_ROOT")
    return Path(raw) if raw else DEFAULT_CORPUS_ROOT


CORPUS = _corpus_root()
corpus_available = pytest.mark.skipif(
    not CORPUS.is_dir(),
    reason=f"corpus documentaire absent : {CORPUS}",
)


REGISTRY = EngineeringMemoryRegistry()


# --------------------------------------------------------------------------
# 1. Correspondances réparées — chaque chemin corrigé pointe vers un répertoire
#    réellement présent dans le corpus.
# --------------------------------------------------------------------------

CORRECTED_DESTINATIONS = {
    RecordType.COMPONENT: "Knowledge/Composants",
    RecordType.VERIFICATION: "Knowledge/Tests-et-Preuves",
    RecordType.TEST_RESULT: "Knowledge/Tests-et-Preuves",
    RecordType.DEPENDENCY: "Knowledge",
}


@corpus_available
@pytest.mark.parametrize(
    ("record_type", "expected"),
    sorted((rt, path) for rt, path in CORRECTED_DESTINATIONS.items()),
)
def test_corrected_destinations_match_the_real_corpus(
    record_type: RecordType, expected: str
) -> None:
    """Les 4 mappings réparés pointent vers le répertoire réel du corpus."""
    destination = REGISTRY.destination_for(record_type)

    assert destination.relative_directory == expected
    assert (CORPUS / expected).is_dir(), (
        f"destination absente du corpus : {expected}"
    )


@corpus_available
def test_old_english_paths_are_absent_from_the_corpus() -> None:
    """Les chemins anglais corrigés n'ont jamais existé dans le corpus.

    C'est la justification du correctif : sans ce constat, la correction
    aurait été arbitraire.
    """
    for stale in ("Knowledge/Components", "Knowledge/Tests", "Knowledge/Dependencies"):
        assert not (CORPUS / stale).exists(), (
            f"{stale} existe : le mapping configuré n'était pas erroné"
        )


# --------------------------------------------------------------------------
# 2. Catégories dont le mapping était déjà correct — elles sont inchangées.
# --------------------------------------------------------------------------

UNCHANGED_DESTINATIONS = {
    RecordType.DECISION: "Knowledge/Decisions",
    RecordType.ENGINEERING_EVENT: "Archives/Events",
    RecordType.INCIDENT: "Knowledge/Incidents",
    RecordType.REPAIR: "Archives/Events",
    RecordType.TECHNICAL_DEBT: "Operational-Memory",
    RecordType.EVIDENCE: "_meta",
    RecordType.AGENT_REPORT: "Archives/Rapports-Agents",
}


@corpus_available
@pytest.mark.parametrize(
    ("record_type", "expected"),
    sorted((rt, path) for rt, path in UNCHANGED_DESTINATIONS.items()),
)
def test_unchanged_destinations_are_preserved(
    record_type: RecordType, expected: str
) -> None:
    """Les destinations déjà correctes sont inchangées et présentes dans le corpus."""
    destination = REGISTRY.destination_for(record_type)

    assert destination.relative_directory == expected
    assert (CORPUS / expected).is_dir()


# --------------------------------------------------------------------------
# 3. destination_for() — cohérence sur l'ensemble des types
# --------------------------------------------------------------------------

@corpus_available
def test_every_destination_exists_in_the_corpus() -> None:
    """Aucune catégorie ne pointe vers un répertoire inexistant du corpus."""
    for record_type in RecordType:
        destination = REGISTRY.destination_for(record_type)
        assert (CORPUS / destination.relative_directory).is_dir(), (
            f"{record_type.value} -> {destination.relative_directory} absent"
        )


def test_destination_for_returns_the_declared_mapping() -> None:
    """`destination_for()` renvoie la destination déclarée pour le type."""
    destination = REGISTRY.destination_for(RecordType.COMPONENT)

    assert destination.record_type == RecordType.COMPONENT
    assert destination.schema_name == "Component"
    assert destination.naming == "CMP-YYYY-NNN-slug.md"


def test_destination_for_accepts_a_string_type() -> None:
    """Une catégorie passée en chaîne est acceptée (compatibilité d'API)."""
    from_string = REGISTRY.destination_for("component")
    from_enum = REGISTRY.destination_for(RecordType.COMPONENT)

    assert from_string == from_enum


def test_destination_for_rejects_an_unknown_type() -> None:
    """Une catégorie inconnue lève une erreur explicite.

    Selon le chemin emprunté, l'erreur vient de l'énumération
    (``RecordType(...)``) ou du registre ; les deux sont des ``ValueError``.
    """
    with pytest.raises(ValueError, match="RecordType|unknown record type"):
        REGISTRY.destination_for("not_a_record_type")


def test_relative_path_for_keeps_the_record_id_intact() -> None:
    """L'identifiant de l'enregistrement est préservé dans le chemin."""
    relative = REGISTRY.relative_path_for(
        RecordType.COMPONENT, "CMP-2026-042", "Memory Service"
    )

    assert relative.parts[0] == "Knowledge"
    assert relative.parts[1] == "Composants"
    assert relative.name.startswith("CMP-2026-042")


def test_relative_path_for_rejects_an_unsafe_record_id() -> None:
    """Un identifiant contenant un séparateur de chemin est refusé."""
    for unsafe in ("../escape", "a/b", "a\\b"):
        with pytest.raises(ValueError, match="not safe"):
            REGISTRY.relative_path_for(RecordType.COMPONENT, unsafe, "Titre")


# --------------------------------------------------------------------------
# 4. Chemins inexistants et cas d'erreur
# --------------------------------------------------------------------------

def test_destination_exists_is_false_for_an_absent_corpus(tmp_path: Path) -> None:
    """Sur une racine vide, aucune destination n'existe (aucune création)."""
    assert REGISTRY.destination_exists(tmp_path, RecordType.COMPONENT) is False


def test_resolve_destination_reports_a_missing_destination(tmp_path: Path) -> None:
    """La résolution signale une destination absente sans rien créer."""
    relative, exists = REGISTRY.resolve_destination(
        tmp_path, RecordType.COMPONENT, "CMP-2026-001", "Titre"
    )

    assert relative == Path("Knowledge/Composants/CMP-2026-001-titre.md")
    assert exists is False
    assert list(tmp_path.iterdir()) == []


def test_resolve_destination_reports_an_existing_destination(tmp_path: Path) -> None:
    """La résolution signale une destination existante."""
    (tmp_path / "Knowledge" / "Composants").mkdir(parents=True)

    relative, exists = REGISTRY.resolve_destination(
        tmp_path, RecordType.COMPONENT, "CMP-2026-001", "Titre"
    )

    assert exists is True
    assert relative.parent == Path("Knowledge/Composants")


def test_write_can_refuse_to_create_a_missing_destination(tmp_path: Path) -> None:
    """En mode strict, l'écriture refuse de créer un répertoire absent."""
    persistence = ObsidianPersistence(
        tmp_path / "Obsidian", require_existing_destination=True
    )
    record = _make_record(RecordType.COMPONENT, "CMP-2026-001")

    with pytest.raises(ValidationError, match="destination directory does not exist"):
        persistence.write(record)

    assert list((tmp_path / "Obsidian").rglob("*.md")) == []


def test_write_creates_the_destination_by_default(tmp_path: Path) -> None:
    """Sans mode strict, le comportement historique est conservé."""
    persistence = ObsidianPersistence(tmp_path / "Obsidian")
    record = _make_record(RecordType.COMPONENT, "CMP-2026-001")

    path = persistence.write(record)

    assert path.is_file()
    assert path.parent == tmp_path / "Obsidian" / "Knowledge" / "Composants"


# --------------------------------------------------------------------------
# 5. Comportement en lecture seule
# --------------------------------------------------------------------------

@corpus_available
def test_destination_introspection_does_not_touch_the_corpus(tmp_path: Path) -> None:
    """Résoudre une destination ne crée aucun répertoire dans le corpus."""
    before_dirs = sorted(p.name for p in CORPUS.iterdir())
    before_events = len(list((CORPUS / "Archives" / "Events").glob("*.md")))

    for record_type in RecordType:
        REGISTRY.destination_exists(CORPUS, record_type)
        REGISTRY.resolve_destination(CORPUS, record_type, "X-2026-001", "Titre")
    REGISTRY.corpus_mapping()

    assert sorted(p.name for p in CORPUS.iterdir()) == before_dirs
    assert len(list((CORPUS / "Archives" / "Events").glob("*.md"))) == before_events


def test_corpus_mapping_exposes_every_type() -> None:
    """La correspondance canonique expose les 11 catégories."""
    mapping = REGISTRY.corpus_mapping()

    assert set(mapping) == {rt.value for rt in RecordType}
    assert mapping["component"]["relative_directory"] == "Knowledge/Composants"
    assert mapping["test_result"]["relative_directory"] == "Knowledge/Tests-et-Preuves"


def test_service_destination_status_is_read_only(tmp_path: Path) -> None:
    """Le service expose un statut de destination sans rien écrire."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")

    status = service.destination_status(RecordType.COMPONENT)

    assert status["relative_directory"] == "Knowledge/Composants"
    assert status["exists"] is False
    assert list(tmp_path.iterdir()) == []


def test_service_corpus_mapping_matches_the_registry(tmp_path: Path) -> None:
    """Le service et le registre exposent la même correspondance."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")

    assert service.corpus_mapping() == REGISTRY.corpus_mapping()


# --------------------------------------------------------------------------
# 6. Préservation des identifiants et des métadonnées
# --------------------------------------------------------------------------

def test_written_record_keeps_its_identity_and_metadata(tmp_path: Path) -> None:
    """Le changement de destination ne modifie ni l'identifiant ni les métadonnées."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = _make_record(RecordType.COMPONENT, "CMP-2026-777")

    stored = service.record(record)
    reloaded = service.get(record.id)

    assert stored.id == "CMP-2026-777"
    assert reloaded is not None
    assert reloaded.id == stored.id
    assert reloaded.title == stored.title
    assert reloaded.components == stored.components
    assert reloaded.source_of_fact == stored.source_of_fact
    assert reloaded.provenance_level == stored.provenance_level
    assert reloaded.evidence_refs == stored.evidence_refs
    assert reloaded.record_type == RecordType.COMPONENT


def test_existing_records_remain_readable_after_the_repair(tmp_path: Path) -> None:
    """Les enregistrements déjà écrits restent relisibles et inchangés."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = _make_record(RecordType.ENGINEERING_EVENT, "EVT-2026-001")
    service.record(record)

    reloaded = service.get(record.id)

    assert reloaded is not None
    assert reloaded.id == "EVT-2026-001"
    assert service.repository_path(record.id, record.record_type).is_file()


def test_record_ids_and_provenance_survive_a_destination_change(tmp_path: Path) -> None:
    """Écrire puis relire un record conserve id, provenance et chemin de source."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = _make_record(RecordType.TEST_RESULT, "TST-2026-314", source="pytest run")

    service.record(record)
    reloaded = service.get("TST-2026-314")

    assert reloaded is not None
    assert reloaded.source_of_fact == "pytest run"
    assert reloaded.origin == RecordOrigin.DECLARED
    assert reloaded.confidence == ConfidenceLevel.MEDIUM


# --------------------------------------------------------------------------
# 7. Compatibilité avec les appels existants
# --------------------------------------------------------------------------

def test_statuses_and_naming_are_unchanged_by_the_repair() -> None:
    """La correction de chemin ne touche ni aux statuts ni au nommage."""
    assert REGISTRY.is_status_allowed(RecordType.COMPONENT, "PLANNED") is True
    assert REGISTRY.is_status_allowed(RecordType.COMPONENT, "REJECTED") is False
    assert REGISTRY.destination_for(RecordType.TEST_RESULT).naming == "TST-YYYY-NNN-slug.md"
    assert REGISTRY.destination_for(RecordType.VERIFICATION).naming == "VER-YYYY-NNN-slug.md"
    assert REGISTRY.destination_for(RecordType.DEPENDENCY).naming == "DEP-YYYY-NNN-slug.md"


def test_service_search_and_history_still_work(tmp_path: Path) -> None:
    """Les consommateurs existants (search, component_history) sont intacts."""
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    service.record(_make_record(RecordType.COMPONENT, "CMP-2026-001"))

    assert [r.id for r in service.search(component="CMP-registry")] == ["CMP-2026-001"]
    assert [r.id for r in service.component_history("CMP-registry")] == ["CMP-2026-001"]


def test_duplicate_detection_still_works(tmp_path: Path) -> None:
    """L'idempotence et le garde-fou de doublon sont préservés après la correction.

    La détection de doublon porte sur le *chemin* (identifiant + titre) : deux
    écritures de contenu identique sont idempotentes, et un contenu différent
    sur un chemin déjà occupé est refusé.
    """
    from core.engineering_memory.persistence import DuplicateRecordError

    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = _make_record(RecordType.COMPONENT, "CMP-2026-001")
    service.record(record)
    path = service.repository_path(record.id, record.record_type)

    # Même contenu : idempotent, un seul fichier.
    service.record(record)
    assert len(list(path.parent.glob("*.md"))) == 1

    # Contenu différent sur un chemin déjà occupé : refusé.
    conflicting = _make_record(
        RecordType.COMPONENT, "CMP-2026-001", title="Enregistrement de test"
    )
    conflicting.notes = "contenu divergent"
    path.write_text(
        "---\n"
        + yaml.safe_dump(conflicting.to_dict(), sort_keys=False, allow_unicode=True)
        + "---\n\ncorps divergent\n",
        encoding="utf-8",
    )
    with pytest.raises(DuplicateRecordError):
        service.record(record)


def test_registry_rejects_unknown_type_before_touching_the_filesystem(
    tmp_path: Path,
) -> None:
    """Une catégorie inconnue est refusée sans créer quoi que ce soit."""
    with pytest.raises(ValueError):
        REGISTRY.destination_for("inconnu")
    assert list(tmp_path.iterdir()) == []


# --------------------------------------------------------------------------
# Utilitaire
# --------------------------------------------------------------------------


def _make_record(
    record_type: RecordType,
    record_id: str,
    *,
    title: str = "Enregistrement de test",
    source: str = "test-source",
) -> MemoryRecord:
    """Construit un MemoryRecord minimal et valide.

    Le statut retenu est le premier statut autorisé par le registre pour le
    type donné : la correction de destination ne doit pas affecter la
    validation des statuts.
    """
    allowed = sorted(REGISTRY.destination_for(record_type).statuses)
    return MemoryRecord(
        id=record_id,
        record_type=record_type,
        title=title,
        status=allowed[0],
        source_of_fact=source,
        provenance_level=SourceOfFactLevel.OBSERVED,
        components=["CMP-registry"],
        created_at="2026-11-12T00:00:00+00:00",
        updated_at="2026-11-12T00:00:00+00:00",
        evidence_refs=[],
        authors=["pytest-agent"],
        origin=RecordOrigin.DECLARED,
        confidence=ConfidenceLevel.MEDIUM,
        notes="test P2.8.0",
    )
