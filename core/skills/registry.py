"""Skill Registry — Catalogue des skills."""

from __future__ import annotations

import logging
from typing import Any

from core.skills.types import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Catalogue central des skills.
    
    Responsabilités :
    - Enregistrement des skills
    - Recherche et filtrage
    - Validation des dépendances
    """

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, skill: Skill) -> None:
        """Enregistre une skill.

        Args:
            skill: Skill à enregistrer
        """
        self._skills[skill.id] = skill

        # Catégorie
        if skill.category not in self._categories:
            self._categories[skill.category] = []
        self._categories[skill.category].append(skill.id)

        logger.debug(f"Skill registered: {skill.id} ({skill.name})")

    def unregister(self, skill_id: str) -> None:
        """Désenregistre une skill.

        Args:
            skill_id: ID de la skill
        """
        if skill_id in self._skills:
            skill = self._skills[skill_id]
            self._categories[skill.category].remove(skill_id)
            del self._skills[skill_id]
            logger.debug(f"Skill unregistered: {skill_id}")

    def get(self, skill_id: str) -> Skill | None:
        """Récupère une skill.

        Args:
            skill_id: ID de la skill

        Returns:
            Skill ou None
        """
        return self._skills.get(skill_id)

    def list_skills(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
        enabled_only: bool = True,
    ) -> list[Skill]:
        """Liste les skills.

        Args:
            category: Filtrer par catégorie
            tags: Filtrer par tags
            enabled_only: Uniquement les skills activés

        Returns:
            Liste de skills
        """
        skills = list(self._skills.values())

        # Filtrer par catégorie
        if category:
            skills = [s for s in skills if s.category == category]

        # Filtrer par tags
        if tags:
            skills = [s for s in skills if any(tag in s.tags for tag in tags)]

        # Filtrer par statut
        if enabled_only:
            skills = [s for s in skills if s.is_enabled]

        return skills

    def get_categories(self) -> list[str]:
        """Liste les catégories.

        Returns:
            Liste de catégories
        """
        return list(self._categories.keys())

    def get_by_tags(self, tags: list[str]) -> list[Skill]:
        """Recherche par tags.

        Args:
            tags: Tags à rechercher

        Returns:
            Liste de skills
        """
        return [
            s for s in self._skills.values()
            if any(tag in s.tags for tag in tags)
        ]

    def search(self, query: str) -> list[Skill]:
        """Recherche par nom/description.

        Args:
            query: Requête

        Returns:
            Liste de skills
        """
        query_lower = query.lower()
        return [
            s for s in self._skills.values()
            if query_lower in s.name.lower()
            or query_lower in s.description.lower()
        ]

    def validate_dependencies(self, skill_id: str) -> bool:
        """Valide les dépendances d'une skill.

        Args:
            skill_id: ID de la skill

        Returns:
            True si valide
        """
        skill = self._skills.get(skill_id)
        if not skill:
            return False

        # Vérifier les outils requis
        for tool_id in skill.required_tools:
            # TODO: Vérifier dans le ToolRegistry
            pass

        # Vérifier les capabilities
        for cap in skill.required_capabilities:
            # TODO: Vérifier dans le CapabilityRegistry
            pass

        return True

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "total_skills": len(self._skills),
            "categories": len(self._categories),
            "by_category": {
                cat: len(skills)
                for cat, skills in self._categories.items()
            },
        }