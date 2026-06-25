"""ModuleInterface — Interface standard pour tous les modules ETHAN.

Cette interface unifie la déclaration des modules :
- Capabilities
- Dépendances
- Permissions
- Cycle de vie
"""

from __future__ import annotations

from abc import abstractmethod

from core.modules.base import Module
from core.modules.capability import Capability
from core.modules.dependency import Dependency
from core.modules.permissions import Permissions


class ModuleInterface(Module):
    """Interface standard pour tous les modules.

    Étend Module avec la déclaration explicite des :
    - Capabilities : ce que le module peut faire
    - Dépendances : ce dont il a besoin
    - Permissions : ce qu'il est autorisé à faire
    """

    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """Retourne les capacités déclarées du module.

        Returns:
            Liste des capabilities (peut être vide pour les modules simples)
        """
        ...

    @abstractmethod
    def get_dependencies(self) -> list[Dependency]:
        """Retourne les dépendances déclarées du module.

        Returns:
            Liste des dépendances (peut être vide si aucune)
        """
        ...

    @abstractmethod
    def get_permissions(self) -> Permissions:
        """Retourne les permissions requises par le module.

        Returns:
            Permissions (peut être vide avec des listes vides)
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, object]:
        """Vérifie l'état de santé du module.

        Returns:
            Dict avec au minimum {"status": "healthy"|"degraded"|"unhealthy"}
        """
        ...