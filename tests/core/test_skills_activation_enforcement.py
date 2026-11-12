"""Activation des skills arbitrée par le Core (pas seulement par l'API).

Un viewer sans permission ``plugins`` ne peut pas activer une skill, mais
surtout : même si une skill est désactivée par un administrateur, aucun chemin
d'exécution (API, autonomie, planner) ne doit pouvoir la lancer.  Le contrôle
doit donc vivre dans ``SkillManager.execute`` (Core), pas uniquement dans la
route API — sinon la désactivation ne serait qu'une sécurité d'affichage.
"""

from __future__ import annotations

import asyncio

from core.skills.manager import SkillManager
from core.skills.types import Skill, SkillContext, SkillStatus
from core.tools.manager import ToolManager


def _skill(is_enabled: bool) -> Skill:
    return Skill(
        id="demo-skill",
        name="Demo",
        description="Skill sans étape (déterminisme du test)",
        steps=[],
        is_enabled=is_enabled,
    )


def test_disabled_skill_is_refused_by_core_manager():
    async def scenario():
        manager = SkillManager(tool_manager=ToolManager())
        manager.register_skill(_skill(is_enabled=False))

        result = await manager.execute(SkillContext(skill_id="demo-skill"))

        assert result.status == SkillStatus.FAILED
        assert "disabled" in (result.error or "").lower()

    asyncio.run(scenario())


def test_enabled_skill_executes():
    async def scenario():
        manager = SkillManager(tool_manager=ToolManager())
        manager.register_skill(_skill(is_enabled=True))

        result = await manager.execute(SkillContext(skill_id="demo-skill"))

        assert result.status == SkillStatus.COMPLETED

    asyncio.run(scenario())


def test_toggle_flag_is_the_only_discriminator():
    """Même skill, même contexte : seul ``is_enabled`` change le résultat."""

    async def scenario():
        manager = SkillManager(tool_manager=ToolManager())
        skill = _skill(is_enabled=False)
        manager.register_skill(skill)

        refused = await manager.execute(SkillContext(skill_id="demo-skill"))
        assert refused.status == SkillStatus.FAILED

        skill.is_enabled = True
        accepted = await manager.execute(SkillContext(skill_id="demo-skill"))
        assert accepted.status == SkillStatus.COMPLETED

    asyncio.run(scenario())
