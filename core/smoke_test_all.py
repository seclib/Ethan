"""Comprehensive smoke test — Agents, Tools, MCP, Skills, Orchestration.

Tests real functional paths for each category per the architecture matrix.
"""
import asyncio
import sys
import os
import logging

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def test_skills():
    """Test Skills execution path: SkillManager -> SkillExecutor -> ToolManager."""
    section("SKILLS — SkillManager.execute -> ToolManager.select_and_execute")

    from core.skills.manager import SkillManager
    from core.skills.types import Skill, SkillStep, SkillContext, SkillStatus
    from core.tools.manager import ToolManager

    tool_manager = ToolManager()
    await tool_manager.initialize()
    print(f"[1] Builtin tools: {[t.name for t in tool_manager.list_tools()]}")

    skill_manager = SkillManager(tool_manager=tool_manager)

    skill = Skill(
        id="test_skill",
        name="Test Skill",
        description="Smoke test skill",
        category="test",
        tags=["test"],
        steps=[SkillStep(
            id="step1",
            name="web_search",
            description="Search the web",
            tool_id="web_search",
            parameters={"query": "ETHAN AI"},
        )],
        is_builtin=True,
    )
    skill_manager.register_skill(skill)
    print(f"[2] Registered skill: {skill.id}")

    context = SkillContext(skill_id="test_skill", user_id="tester", session_id="s1")
    result = await skill_manager.execute(context)

    print(f"[3] status={result.status}")
    print(f"    steps={result.steps_completed}/{result.steps_total}")
    print(f"    duration={result.duration_ms:.1f}ms")
    print(f"    output={result.output}")

    if result.status == SkillStatus.COMPLETED:
        print("[PASS] Skills path OK")
        return True
    else:
        print(f"[FAIL] Skills path: status={result.status}, error={result.error}")
        return False


async def test_tools():
    """Test Tools execution path: ToolManager -> ToolExecutor."""
    section("TOOLS — ToolManager.select_and_execute -> ToolExecutor.execute")

    from core.tools.manager import ToolManager
    from core.tools.types import ToolContext, ToolResult
    from core.tools.types import Tool

    tool_manager = ToolManager()
    await tool_manager.initialize()

    builtin = tool_manager.list_tools()
    print(f"[1] Builtin tools: {[t.name for t in builtin]}")

    # Test select_and_execute with a query matching 'web_search'
    context = ToolContext(
        query="web_search",
        source="test",
        user_id="tester",
        session_id="s1",
    )
    result = await tool_manager.select_and_execute(
        query="web search",
        params={"query": "hello"},
        context=context,
    )

    print(f"[2] ToolResult status={result.status}")
    print(f"    output={result.output}")
    print(f"    duration={result.duration_ms:.1f}ms")

    if result.status == "success":
        print("[PASS] Tools path OK")
        return True
    else:
        print(f"[FAIL] Tools path: status={result.status}, error={result.error}")
        return False


async def test_agents():
    """Test Agents path: AgentManager.create + execute (with executor injected)."""
    section("AGENTS — AgentManager.create -> AgentManager.execute")

    from core.agents.manager import AgentManager, AgentExecutionUnavailable
    from core.agents.types import AgentExecutionStatus

    # Test 1: Without executor → should raise AgentExecutionUnavailable (not a stub)
    manager = AgentManager(store=None)
    agent = await manager.create(name="TestAgent", description="Test agent")
    print(f"[1] Created agent: id={agent.id}, name={agent.name}")

    try:
        execution = await manager.execute(agent.id, task="test task")
        print(f"    [UNEXPECTED] Execution succeeded without executor")
        return False
    except AgentExecutionUnavailable as e:
        print(f"[2] Correctly raised AgentExecutionUnavailable when no executor: {e}")
        print(f"    [PASS] Agent execute raises clear error (not a fake success stub)")

    # Test 2: With executor → should execute and return COMPLETED
    async def fake_executor(agent=None, task=None, context=None, skill_id=None):
        return {"result": f"Agent {agent.name} completed task: {task}"}

    manager2 = AgentManager(store=None, executor=fake_executor)
    agent2 = await manager2.create(name="ExecutorAgent", description="With executor")
    print(f"[3] Created agent with executor: {agent2.id}")

    execution = await manager2.execute(agent2.id, task="do something")
    print(f"[4] Execution status={execution.status}")
    print(f"    result={execution.result}")

    if execution.status == AgentExecutionStatus.COMPLETED:
        print("[PASS] Agents path OK (with executor)")
        return True
    else:
        print(f"[FAIL] Agents path: status={execution.status}")
        return False


async def test_mcp():
    """Test MCP integration: ToolServerManager + MCPClient availability."""
    section("MCP — ToolServerManager + MCPClient")

    from core.tools.servers import ToolServerManager
    from core.tools.mcp_client import MCPClient, MCP_AVAILABLE

    print(f"[1] MCP_AVAILABLE: {MCP_AVAILABLE}")

    # ToolServerManager can be instantiated without a real MCP server
    # (store=None → in-memory, registry from ToolManager)
    from core.tools.manager import ToolManager
    tool_manager = ToolManager()
    await tool_manager.initialize()

    server_manager = ToolServerManager(store=None, registry=tool_manager.registry)
    print(f"[2] ToolServerManager created")

    servers = await server_manager.list()
    print(f"[3] Listed servers: {len(servers)}")

    # MCPClient can be instantiated (connection requires a real server)
    client = MCPClient()
    print(f"[4] MCPClient created: {client is not None}")

    print("[PASS] MCP integration path OK (classes importable & instantiable)")
    return True


async def test_orchestration():
    """Test Orchestration: Orchestrator.process with cognitive pipeline."""
    section("ORCHESTRATION — Orchestrator.process")

    from core.orchestrator.orchestrator import Orchestrator
    from core.orchestrator.context import OrchestratorContext
    from core.orchestrator.pipeline import CapabilityPipeline

    orchestrator = Orchestrator()
    print(f"[1] Orchestrator created: {orchestrator is not None}")
    print(f"    Modules registered: {orchestrator._modules}")
    print(f"    Pipelines registered: {orchestrator._pipelines}")

    # Register a module
    orchestrator.register_module("test_module", {"name": "test"})
    print(f"[2] After register_module: modules={list(orchestrator._modules.keys())}")

    # Orchestrator requires initialization before processing
    try:
        await orchestrator.process({"type": "test", "user_id": "tester"})
        print("[FAIL] Orchestrator.process succeeded without initialization")
        return False
    except RuntimeError as e:
        print(f"[3] Correctly raised RuntimeError when not initialized: {e}")

    # Initialize and process
    context = OrchestratorContext(request_id="test_req", user_id="tester", session_id="s1")
    await orchestrator.initialize(context)
    print(f"[4] Orchestrator initialized with modules: {orchestrator.get_stats()}")

    result = await orchestrator.process({"type": "chat", "user_id": "tester", "message": "hello"})
    print(f"[5] Process result: {result}")

    if result.get("status") == "success":
        print("[PASS] Orchestration path OK")
        return True
    else:
        print(f"[FAIL] Orchestration: result={result}")
        return False


async def main():
    results = {}
    results["skills"] = await test_skills()
    results["tools"] = await test_tools()
    results["agents"] = await test_agents()
    results["mcp"] = await test_mcp()
    results["orchestration"] = await test_orchestration()

    section("FINAL SUMMARY")
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:>15s}: {status}")

    all_passed = all(results.values())
    print(f"\n  Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
