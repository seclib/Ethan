"""Project Creator Skill — Compétence de création de projet."""

from __future__ import annotations

from core.skills.types import Skill, SkillStep
from core.skills.builtin.base import BaseBuiltinSkill


class ProjectCreatorSkill(BaseBuiltinSkill):
    """Skill de création de projet.
    
    Outils utilisés :
    - project_scaffolder : Créer la structure
    - dependency_installer : Installer les dépendances
    - git_initializer : Initialiser Git
    - config_generator : Générer la configuration
    """

    def _build_skill(self) -> Skill:
        return Skill(
            id="project_creator",
            name="Project Creator",
            description="Create a new project with best practices",
            version="1.0.0",
            category="development",
            tags=["project", "scaffold", "create", "setup"],
            steps=[
                SkillStep(
                    id="step1",
                    name="Scaffold project",
                    description="Create project structure",
                    tool_id="project_scaffolder",
                    parameters={"template": "python"},
                ),
                SkillStep(
                    id="step2",
                    name="Install dependencies",
                    description="Install project dependencies",
                    tool_id="dependency_installer",
                    parameters={"dev": True},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step3",
                    name="Initialize Git",
                    description="Initialize Git repository",
                    tool_id="git_initializer",
                    parameters={"initial_commit": True},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step4",
                    name="Generate config",
                    description="Generate configuration files",
                    tool_id="config_generator",
                    parameters={"format": "yaml"},
                    depends_on=["step1"],
                    optional=True,
                ),
            ],
            required_tools=["project_scaffolder", "dependency_installer", "git_initializer"],
            estimated_duration_ms=60000,
            risk_level="low",
            is_builtin=True,
        )