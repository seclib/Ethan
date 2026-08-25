"""Smoke test — SkillManager.execute end-to-end.

Vérifie que la chaîne complète fonctionne sans crash :
  SkillManager.execute
    -> SkillExecutor.execute
      -> ToolManager.select_and_execute
        -> ToolExecutor.execute

Utilise un builtin tool (web_search, auto-registered par ToolRegistry)
via una skill custom dont le nom de step correspond au nom de l'outil.
"""
import asyncio
import logging

logging.basicConfig(level=logging.WARNING)


async def main():
    from core.tools.manager import ToolManager
    from core.skills.manager import SkillManager
    from core.skills.types import Skill, SkillStep, SkillContext, SkillStatus

    # 1. ToolManager — registry enregistre automatiquement les builtins
    tool_manager = ToolManager()
    await tool_manager.initialize()
    builtin_tools = tool_manager.list_tools()
    print(f"[INFO] Builtin tools registered: {[t.name for t in builtin_tools]}")

    # 2. SkillManager avec un builtin skill (web_search)
    skill_manager = SkillManager(tool_manager=tool_manager)

    # Skill custom : step name = "web_search" pour matcher le builtin tool
    skill = Skill(
        id="smoke_test_skill",
        name="Smoke Test Skill",
        description="Verify end-to-end skill execution path",
        category="test",
        tags=["test", "smoke"],
        steps=[
            SkillStep(
                id="step1",
                name="web_search",
                description="Perform a web search",
                tool_id="web_search",
                parameters={"max_results": 3},
            ),
        ],
        required_tools=["web_search"],
        is_builtin=True,
    )
    skill_manager.register_skill(skill)

    # 3. Execute
    context = SkillContext(
        skill_id="smoke_test_skill",
        user_id="test_user",
        session_id="test_session",
        parameters={"query": "ETHAN AI system"},
    )

    result = await skill_manager.execute(context)

    # 4. Verify
    print(f"[RESULT] skill_id={result.skill_id}")
    print(f"[RESULT] status={result.status}")
    print(f"[RESULT] steps_completed={result.steps_completed}/{result.steps_total}")
    print(f"[RESULT] duration_ms={result.duration_ms:.1f}")
    print(f"[RESULT] output={result.output}")
    if result.error:
        print(f"[RESULT] error={result.error}")

    assert result.status == SkillStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    assert result.steps_completed == 1
    assert result.steps_total == 1
    print("\n[PASS] SkillManager.execute smoke test — all assertions passed!")


if __name__ == "__main__":
    asyncio.run(main())
