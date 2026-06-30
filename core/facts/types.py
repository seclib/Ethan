"""Types du module facts — faits atomiques, observations, relations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class FactStatus(StrEnum):
    """Statut d'un fait atomique."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    NEEDS_REVIEW = "needs_review"
    ARCHIVED = "archived"
    CONTRADICTED = "contradicted"


class FactCategory(StrEnum):
    """Catégories de faits."""

    PREFERENCE = "preference"
    PROJECT = "project"
    GOAL = "goal"
    IDENTITY = "identity"
    RELATIONSHIP = "relationship"
    KNOWLEDGE = "knowledge"
    SKILL = "skill"
    EVENT = "event"
    OBSERVATION = "observation"
    RULE = "rule"
    SYSTEM = "system"


class FactRelationType(StrEnum):
    """Types de relations entre faits."""

    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    CAUSES = "causes"


class ObservationType(StrEnum):
    """Types d'observation renforçant un fait."""

    CONFIRM = "confirm"
    CORRECT = "correct"
    REPEAT = "repeat"
    CONTRADICT = "contradict"
    AMEND = "amend"


@dataclass(frozen=True)
class Fact:
    """Fait atomique : une assertion élémentaire sur le monde.

    Un fait est un triplet (subject, predicate, object) dans une catégorie.
    Il est daté, sourcé, et peut être actif ou remplacé.
    Les faits ne sont jamais supprimés — seulement marqués comme superseded/archived.
    """

    id: str = field(default_factory=lambda: f"fct_{uuid4().hex[:12]}")
    subject: str = ""
    predicate: str = ""
    object: str = ""
    category: FactCategory = FactCategory.KNOWLEDGE
    status: FactStatus = FactStatus.ACTIVE
    confidence: float = 0.5
    importance: float = 0.5
    source: str = "system"
    source_event_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_seen_at: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_subject(self) -> str:
        return self.subject.strip().lower()

    @property
    def normalized_predicate(self) -> str:
        return self.predicate.strip().lower()

    @property
    def normalized_object(self) -> str:
        return self.object.strip().lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "category": self.category.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "importance": self.importance,
            "source": self.source,
            "source_event_id": self.source_event_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        return cls(
            id=data["id"],
            subject=data["subject"],
            predicate=data["predicate"],
            object=data["object"],
            category=FactCategory(data["category"]),
            status=FactStatus(data.get("status", "active")),
            confidence=data.get("confidence", 0.5),
            importance=data.get("importance", 0.5),
            source=data.get("source", "system"),
            source_event_id=data.get("source_event_id", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data.get("updated_at", data["created_at"])),
            last_seen_at=datetime.fromisoformat(data.get("last_seen_at", data["created_at"])),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class FactObservation:
    """Observation renforçant ou contredisant un fait."""

    id: str = field(default_factory=lambda: f"obs_{uuid4().hex[:10]}")
    fact_id: str = ""
    event_id: str = ""
    observation_type: ObservationType = ObservationType.CONFIRM
    confidence_delta: float = 0.0
    source: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fact_id": self.fact_id,
            "event_id": self.event_id,
            "observation_type": self.observation_type.value,
            "confidence_delta": self.confidence_delta,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class FactRelation:
    """Relation entre deux faits."""

    id: str = field(default_factory=lambda: f"rel_{uuid4().hex[:10]}")
    from_fact_id: str = ""
    to_fact_id: str = ""
    relation_type: FactRelationType = FactRelationType.RELATED_TO
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from_fact_id": self.from_fact_id,
            "to_fact_id": self.to_fact_id,
            "relation_type": self.relation_type.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class FactSearchResult:
    """Résultat de recherche FTS5 avec score BM25."""

    fact: Fact
    score: float = 0.0
    bm25: float = 0.0