"""Dependency — Déclaration des dépendances d'un module.

Les dépendances sont vérifiées au démarrage du module.
Si une dépendance required est absente, le module ne démarre pas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dependency:
    """Dépendance d'un module vers un service externe ou une autre capacité.

    Exemple :
        Dependency(
            name="redis",
            version=">=7.0",
            required=True,
            fallback=None,
        )
    """

    name: str
    """Nom de la dépendance (e.g., \"nats\", \"redis\", \"postgres\", \"memory.store\")."""

    version: str = ">=1.0.0"
    """Version requise au format semver (e.g., \">=7.0\", \"==2.1.0\")."""

    required: bool = True
    """Si True, le module ne peut pas fonctionner sans cette dépendance.

    Si False, le module fonctionne en mode dégradé.
    """

    fallback: str | None = None
    """Module de fallback si la dépendance est absente.

    Exemple : si \"redis\" est absent, utiliser \"memory.store\" comme fallback.
    Uniquement pertinent si required=False.
    """

    description: str = ""
    """Description lisible de la dépendance."""