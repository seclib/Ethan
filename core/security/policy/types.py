"""Policy Engine — Types et modèles de données.

Définit les briques de la hiérarchie des politiques (cf.
`docs/security/03-policy-hierarchy.md`) :
- huit niveaux de priorité (CORE → LLM) ;
- huit catégories d'actions sensibles ;
- les trois effets possibles (ALLOW / DENY / REQUIRE_CONFIRMATION) ;
- la requête à évaluer et la décision rendue.

Ce module est indépendant du LLM : aucune instruction de modèle ne peut
modifier une règle ni influencer une décision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Any


class PolicyLevel(IntEnum):
    """Niveau de priorité d'une règle (le plus petit est le plus fort).

    Reprend la hiérarchie opérationnelle à 8 niveaux de la Phase 03.
    """

    CORE = 1
    SECURITY = 2
    SYSTEM = 3
    PROJECT = 4
    AGENT = 5
    TASK = 6
    USER = 7
    LLM = 8


class PolicyEffect(StrEnum):
    """Effet produit par une règle sur l'action évaluée."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"


class PolicyResult(StrEnum):
    """Décision finale rendue par le moteur pour une requête."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_CONFIRMATION = "require_confirmation"


class ActionCategory(StrEnum):
    """Catégories d'actions sensibles évaluées par le moteur."""

    FILESYSTEM = "filesystem"
    PROCESS = "process"
    SHELL = "shell"
    DOCKER = "docker"
    NETWORK = "network"
    MCP = "mcp"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    EXTERNAL_TRANSMISSION = "external_transmission"


# ── Ordre de restrictivité des effets (A3 : à niveau égal, le plus restrictif gagne)
_RESTRICTIVITY_ORDER: dict[PolicyEffect, int] = {
    PolicyEffect.DENY: 0,
    PolicyEffect.REQUIRE_CONFIRMATION: 1,
    PolicyEffect.ALLOW: 2,
}


@dataclass(frozen=True)
class Policy:
    """Une règle de politique immuable.

    Attributes:
        id: Identifiant unique de la règle.
        level: Niveau de priorité (1..8).
        category: Catégorie d'action visée (ou "*" pour toutes).
        action: Action visée (glob, ex "read", "write", "*").
        resource: Ressource visée (glob, ex "/workspace/**", "*").
        effect: Effet à appliquer si la règle matche.
        reason: Raison explicite affichable / journalisable.
        enabled: Règle active ou non.
    """

    id: str
    level: PolicyLevel
    category: str
    action: str
    resource: str
    effect: PolicyEffect
    reason: str = ""
    enabled: bool = True

    def matches(self, category: str, action: str, resource: str) -> bool:
        """Vérifie si la règle matche une requête (glob simple + "*")."""
        return (
            self.enabled
            and _glob_match(self.category, category)
            and _glob_match(self.action, action)
            and _glob_match(self.resource, resource)
        )

    @property
    def restrictivity(self) -> int:
        """Ordre de restrictivité de l'effet (0 = le plus restrictif)."""
        return _RESTRICTIVITY_ORDER[self.effect]


@dataclass(frozen=True)
class PolicyRequest:
    """Requête d'évaluation d'une action sensible.

    Attributes:
        category: Catégorie d'action (filesystem, shell, docker, …).
        action: Action précise (read, write, delete, execute, …).
        resource: Ressource ciblée (chemin, commande, URL, clé mémoire, …).
        params: Paramètres supplémentaires (non utilisés pour l'autorisation).
        source: Origine déclarative de la demande (informationnelle — A6).
    """

    category: str
    action: str
    resource: str
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"


@dataclass(frozen=True)
class PolicyDecision:
    """Décision finale du moteur pour une requête.

    Attributes:
        result: ALLOW / DENY / REQUIRE_CONFIRMATION.
        reason: Raison explicite de la décision.
        policy_id: Identifiant de la règle ayant décidé (None si silence).
        level: Niveau de la règle ayant décidé (None si silence).
        matched: Règles qui matchent la requête (diagnostic).
        evaluated_at: Horodatage de l'évaluation.
    """

    result: PolicyResult
    reason: str
    policy_id: str | None = None
    level: PolicyLevel | None = None
    matched: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def allowed(self) -> bool:
        """True si la décision autorise l'exécution (ALLOW)."""
        return self.result is PolicyResult.ALLOW

    def to_dict(self) -> dict[str, Any]:
        """Sérialisation pour l'audit / les logs."""
        return {
            "result": self.result.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "level": self.level.value if self.level else None,
            "matched": list(self.matched),
            "evaluated_at": self.evaluated_at.isoformat(),
        }


class PolicyError(Exception):
    """Erreur générique du Policy Engine."""


class PolicyDeniedError(PolicyError):
    """Action refusée par une politique (levée par le garde à l'exécution)."""

    def __init__(self, decision: PolicyDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


class PolicyConfirmationRequiredError(PolicyError):
    """Action en attente de confirmation humaine (garde, fail-closed)."""

    def __init__(self, decision: PolicyDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


def _glob_match(pattern: str, value: str) -> bool:
    """Glob simple : ``*`` matche n'importe quelle séquence (et tout)."""
    if pattern == "*":
        return True
    if pattern == value:
        return True
    if pattern.endswith("**"):
        return value.startswith(pattern[:-2])
    if "*" in pattern:
        import fnmatch

        return fnmatch.fnmatchcase(value, pattern)
    return False
