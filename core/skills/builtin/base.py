"""Base Builtin Skill — Classe de base pour les skills intégrés."""

from __future__ import annotations

from core.skills.types import Skill


class BaseBuiltinSkill:
    """Classe de base pour les skills intégrés."""

    def _build_skill(self) -> Skill:
        """Construit la skill.

        Returns:
            Skill
        """
        raise NotImplementedError

    def get_skill(self) -> Skill:
        """Récupère la skill.

        Returns:
            Skill
        """
        return self._build_skill()