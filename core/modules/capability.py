"""Capability — Déclaration des capacités d'un module.

Une Capability est un contrat qui déclare :
- Ce que le module peut faire
- Quels événements il consomme et produit
- Quels états il lit et écrit
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Capability:
    """Capacité déclarée d'un module.

    Exemple :
        Capability(
            name="memory.store",
            version="1.0.0",
            description="Store data in memory",
            inputs=["memory.store.request"],
            outputs=["memory.store.complete"],
            state_reads=[],
            state_writes=["memory:entry:*"],
            shared=True,
        )
    """

    name: str
    """Nom unique de la capacité (e.g., \"memory.store\", \"llm.generate\")."""

    version: str
    """Version semver de cette capacité."""

    description: str = ""
    """Description lisible de la capacité."""

    inputs: list[str] = field(default_factory=list)
    """Types d'événements consommés (e.g., [\"memory.store.request\"])."""

    outputs: list[str] = field(default_factory=list)
    """Types d'événements produits (e.g., [\"memory.store.complete\"])."""

    state_reads: list[str] = field(default_factory=list)
    """Clés d'état lues (pattern Redis, e.g., [\"memory:entry:*\"])."""

    state_writes: list[str] = field(default_factory=list)
    """Clés d'état écrites (pattern Redis, e.g., [\"memory:session:*\"])."""

    shared: bool = False
    """True si cette capacité peut être partagée entre plusieurs modules.

    Si False, un seul module peut déclarer cette capacité.
    """

    dependencies: list[str] = field(default_factory=list)
    """Dépendances vers d'autres capacités (e.g., [\"filesystem.read\"])."""