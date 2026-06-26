"""CapabilityRegistry — Gestion centralisée des capacités des modules.

Registry capable de :
- Enregistrer des capacités avec validation
- Résoudre des capacités par nom/version
- Détecter les conflits d'écriture
- Vérifier les dépendances entre capacités
"""

from __future__ import annotations

import logging
from typing import Any

from core.modules.capability import Capability

logger = logging.getLogger(__name__)


class CapabilityConflictError(Exception):
    """Une capacité en conflit avec une existante a été détectée."""
    pass


class CapabilityDependencyError(Exception):
    """Une dépendance entre capacités est manquante."""
    pass


class CapabilityRegistry:
    """Registry des capacités des modules.

    Thread-safe. Centralise la découverte et la validation des capacités.
    """

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._module_capabilities: dict[str, list[str]] = {}
        """Map module_name -> [capability_names]"""

    # ──────────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────────

    def register(self, module_name: str, capability: Capability) -> None:
        """Enregistre une capacité pour un module.

        Args:
            module_name: Nom du module propriétaire
            capability: Capacité à enregistrer

        Raises:
            CapabilityConflictError: Si la capacité est déjà enregistrée
                et n'est pas marquée comme shared.
        """
        existing = self._capabilities.get(capability.name)

        if existing is not None and not capability.shared:
            raise CapabilityConflictError(
                f"Capability '{capability.name}' already registered "
                f"(not shared). Module '{module_name}' cannot override."
            )

        self._capabilities[capability.name] = capability

        if module_name not in self._module_capabilities:
            self._module_capabilities[module_name] = []
        self._module_capabilities[module_name].append(capability.name)

        logger.debug(
            "Capability registered: %s v%s by %s",
            capability.name, capability.version, module_name,
        )

    def unregister(self, capability_name: str) -> bool:
        """Supprime une capacité du registry.

        Args:
            capability_name: Nom de la capacité à supprimer

        Returns:
            True si la capacité a été trouvée et supprimée
        """
        if capability_name in self._capabilities:
            del self._capabilities[capability_name]
            # Nettoyer la map module -> capabilities
            for module_name, caps in list(self._module_capabilities.items()):
                if capability_name in caps:
                    caps.remove(capability_name)
                    if not caps:
                        del self._module_capabilities[module_name]
            return True
        return False

    def unregister_module(self, module_name: str) -> None:
        """Supprime toutes les capacités d'un module.

        Args:
            module_name: Nom du module à désenregistrer
        """
        capability_names = self._module_capabilities.pop(module_name, [])
        for cap_name in capability_names:
            self._capabilities.pop(cap_name, None)
        logger.debug("Module unregistered: %s (%d capabilities)", module_name, len(capability_names))

    # ──────────────────────────────────────────────
    # Resolution
    # ──────────────────────────────────────────────

    def get(self, name: str) -> Capability | None:
        """Récupère une capacité par son nom.

        Args:
            name: Nom de la capacité

        Returns:
            La capacité, ou None si non trouvée
        """
        return self._capabilities.get(name)

    def get_by_module(self, module_name: str) -> list[Capability]:
        """Récupère toutes les capacités d'un module.

        Args:
            module_name: Nom du module

        Returns:
            Liste des capacités du module
        """
        cap_names = self._module_capabilities.get(module_name, [])
        return [
            self._capabilities[name]
            for name in cap_names
            if name in self._capabilities
        ]

    def resolve(self, name: str, version: str | None = None) -> list[Capability]:
        """Résout une capacité par nom et version optionnelle.

        Args:
            name: Nom de la capacité
            version: Version semver optionnelle

        Returns:
            Liste des capacités correspondantes
        """
        capability = self._capabilities.get(name)
        if capability is None:
            return []

        if version is not None and capability.version != version:
            return []

        return [capability]

    # ──────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────

    def validate_dependencies(self, capability: Capability) -> list[str]:
        """Vérifie que les dépendances d'une capacité sont satisfaites.

        Args:
            capability: Capacité à valider

        Returns:
            Liste des dépendances manquantes (vide si OK)
        """
        missing = []
        for dep_name in capability.dependencies:
            if dep_name not in self._capabilities:
                missing.append(dep_name)
        return missing

    def check_write_conflicts(self) -> list[tuple[str, str, str]]:
        """Détecte les conflits d'écriture entre modules.

        Returns:
            Liste de (key_pattern, module1, module2) pour chaque conflit
        """
        write_patterns: dict[str, str] = {}
        conflicts: list[tuple[str, str, str]] = []

        for module_name, cap_names in self._module_capabilities.items():
            for cap_name in cap_names:
                capability = self._capabilities.get(cap_name)
                if capability is None or capability.shared:
                    continue
                for pattern in capability.state_writes:
                    if pattern in write_patterns:
                        other_module = write_patterns[pattern]
                        conflicts.append((pattern, other_module, module_name))
                    else:
                        write_patterns[pattern] = module_name

        return conflicts

    # ──────────────────────────────────────────────
    # Query
    # ──────────────────────────────────────────────

    def list_all(self) -> list[Capability]:
        """Liste toutes les capacités enregistrées.

        Returns:
            Liste de toutes les capacités
        """
        return list(self._capabilities.values())

    def list_names(self) -> list[str]:
        """Liste les noms de toutes les capacités.

        Returns:
            Liste des noms
        """
        return list(self._capabilities.keys())

    def list_modules(self) -> list[str]:
        """Liste tous les modules enregistrés.

        Returns:
            Liste des noms de modules
        """
        return list(self._module_capabilities.keys())

    def count(self) -> int:
        """Nombre de capacités enregistrées.

        Returns:
            Nombre de capacités
        """
        return len(self._capabilities)

    def __contains__(self, name: str) -> bool:
        return name in self._capabilities

    def __len__(self) -> int:
        return len(self._capabilities)