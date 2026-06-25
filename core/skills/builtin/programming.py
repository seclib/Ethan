"""Programming Skill — Compétence de programmation."""

from __future__ import annotations

from core.skills.types import Skill, SkillStep
from core.skills.builtin.base import BaseBuiltinSkill


class ProgrammingSkill(BaseBuiltinSkill):
    """Skill de programmation.
    
    Outils utilisés :
    - code_writer : Écrire du code
    - code_reviewer : Revoir du code
    - linter : Vérifier la syntaxe
    - test_runner : Exécuter les tests
    """

    def _build_skill(self) -> Skill:
        return Skill(
            id="programming",
            name="Programming",
            description="Write, review, and debug code in multiple languages",
            version="1.0.0",
            category="development",
            tags=["code", "programming", "development", "debug"],
            steps=[
                SkillStep(
                    id="step1",
                    name="Analyze requirements",
                    description="Understand what needs to be built",
                    tool_id="code_analyzer",
                    parameters={"mode": "analyze"},
                ),
                SkillStep(
                    id="step2",
                    name="Write code",
                    description="Generate the code",
                    tool_id="code_writer",
                    parameters={"language": "python"},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step3",
                    name="Review code",
                    description="Review generated code",
                    tool_id="code_reviewer",
                    parameters={"strict": True},
                    depends_on=["step2"],
                    optional=True,
                ),
                SkillStep(
                    id="step4",
                    name="Run tests",
                    description="Execute tests",
                    tool_id="test_runner",
                    parameters={"coverage": True},
                    depends_on=["step2"],
                ),
            ],
            required_tools=["code_writer", "code_reviewer", "test_runner"],
            estimated_duration_ms=120000,
            risk_level="low",
            is_builtin=True,
        )