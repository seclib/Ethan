"""Ressources ETHAN — Modèles de données pour le Resource Registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime

from core.knowledge.types import KnowledgeType, KnowledgeNode, KnowledgeConnection


class ResourceType(str, Enum):
    """Types de ressources reconnaissables par le Registry."""
    SKILL = "skill"
    AGENT = "agent"
    MCP_SERVER = "mcp_server"
    PLUGIN = "plugin"
    APPLICATION = "application"
    DOCUMENT = "document"
    ARCHITECTURE = "architecture"
    ADR = "adr"
    RUNBOOK = "runbook"
    SERVICE = "service"
    OTHER = "other"


@dataclass
class ResourceMeta:
    """Métadonnées standardisées pour toute ressource."""
    domain: str = ""
    level: str = ""  # Niveau A/B/C, ou tout autre classement
    version: str = ""
    author: str = ""
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)
    related_to: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "level": self.level,
            "version": self.version,
            "author": self.author,
            "confidence": self.confidence,
            "tags": self.tags,
            "related_to": self.related_to,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceMeta":
        return cls(
            domain=data.get("domain", ""),
            level=data.get("level", ""),
            version=data.get("version", ""),
            author=data.get("author", ""),
            confidence=data.get("confidence", 1.0),
            tags=data.get("tags", []),
            related_to=data.get("related_to", []),
        )


class ResourceStatus(str, Enum):
    """Statut opérationnel d'une ressource.

    Hérite de str pour être utilisable partout où une string est attendue,
    tout en bénéficiant des avantages d'un Enum (comparaison stricte, .
    valeurs uniques, itérabilité, etc.).
    """

    # Statuts prédéfinis
    ACTIVE = "active"
    STALE = "stale"
    DEPRECATED = "deprecated"
    DISAPPEARED = "disappeared"

    # Mapping des valeurs vers descriptions humaines
    _descriptions: dict[str, str] = {
        ACTIVE: "Ressource détectée et vérifiée récemment",
        STALE: "Ressource détectée mais plus vérifiée depuis longtemps",
        DEPRECATED: "Ressource marquée obsolète",
        DISAPPEARED: "Source originale introuvable",
    }

    def __str__(self) -> str:
        """Retourne la valeur string du statut."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Comparaison équivalence avec another ResourceStatus ou string."""
        if isinstance(other, ResourceStatus):
            return self.value == other.value
        return self.value == other

    @classmethod
    def from_value(cls, value: str) -> "ResourceStatus":
        """Crée un statut à partir d'une valeur string.

        Args:
            value: La string du statut (ex: "active", "stale").

        Returns:
            ResourceStatus correspondant.
        """
        if value in cls._descriptions:
            return cls(value)
        # Retourner ACTIVE comme valeur par défaut
        return cls.ACTIVE

    @classmethod
    def from_string(cls, value: str) -> "ResourceStatus":
        """Alias de from_value pour plus de clarté."""
        return cls.from_value(value)

    @property
    def description(self) -> str:
        """Retourne la description humaine du statut."""
        return self._descriptions.get(self.value, "Statut inconnu")

ResourceStatusChoices = [
    ResourceStatus.ACTIVE,
    ResourceStatus.STALE,
    ResourceStatus.DEPRECATED,
    ResourceStatus.DISAPPEARED,
]
