"""Modèles fondamentaux de l'Engineering Memory d'ETHAN."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class RecordType(StrEnum):
    """Types d'enregistrements réutilisés par la mémoire technique."""

    COMPONENT = "component"
    DECISION = "decision"
    ENGINEERING_EVENT = "engineering_event"
    INCIDENT = "incident"
    REPAIR = "repair"
    VERIFICATION = "verification"
    DEPENDENCY = "dependency"
    TEST_RESULT = "test_result"
    TECHNICAL_DEBT = "technical_debt"
    EVIDENCE = "evidence"
    AGENT_REPORT = "agent_report"


class RecordOrigin(StrEnum):
    """Origine logique d'une déclaration."""

    DECLARED = "declared"
    OBSERVED = "observed"


class SourceOfFactLevel(StrEnum):
    """Niveau de source associé à une information."""

    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED = "inferred"


class ConfidenceLevel(StrEnum):
    """Niveau de confiance documentaire."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=False, slots=True)
class MemoryRecord:
    """Enregistrement canonique de la mémoire technique.

    Un événement d'activité est représenté par un `ENGINEERING_EVENT`.
    Les autres types réutilisent la même enveloppe pour rester compatibles
    avec les documents YAML déjà définis.
    """

    id: str
    record_type: RecordType
    title: str
    status: str
    source_of_fact: str
    provenance_level: SourceOfFactLevel
    components: list[str]
    created_at: str
    updated_at: str
    evidence_refs: list[str]
    authors: list[str]
    origin: RecordOrigin
    confidence: ConfidenceLevel
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    correlation_id: str | None = None
    task_id: str | None = None
    schema_version: str = "1.0.0"
    repository_path: Path | None = None
    # P2.8.3 — charge utile structurée de l'enregistrement.
    #
    # Le modèle canonique (MEMORY_DATA_MODEL.md) ne prévoit qu'un champ
    # `notes` texte. La traçabilité des interventions exige une forme
    # *interrogeable* : sans elle, le contrôle de fin d'intervention ne
    # pourrait pas vérifier automatiquement les huit conditions sans parser
    # du Markdown. Le champ est donc **optionnel et rétro-compatible** : les
    # enregistrements existants n'ont pas de `metadata` et se relisent
    # identically. Aucun type d'enregistrement nouveau n'est créé.
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'enregistrement en dictionnaire YAML compatible."""
        result: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if key == "repository_path":
                continue
            if isinstance(value, str) and hasattr(value, "value"):
                value = str(value.value)
            if isinstance(value, str) and not hasattr(value, "value"):
                result[key] = value
            elif hasattr(value, "value"):
                result[key] = str(getattr(value, "value"))
            elif isinstance(value, bool):
                result[key] = value
            elif isinstance(value, int) or isinstance(value, float):
                result[key] = value
            elif isinstance(value, dict):
                # P2.8.3 — la charge utile structurée est conservée telle
                # quelle : la sérialiser en texte la rendrait illisible et
                # romprait la comparaison canonique d'idempotence.
                result[key] = value
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    result[key] = list(value)
                else:
                    result[key] = [str(item) for item in value]
            elif value is None:
                result[key] = None
            else:
                result[key] = str(value)
        return result

    def text_body(self) -> str:
        """Corps Markdown associé à l'enregistrement."""
        return f"# {self.title}\n\n{self.notes}\n"

