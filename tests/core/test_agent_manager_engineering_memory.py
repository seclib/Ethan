from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from core.agents.manager import AgentManager
from core.agents.types import AgentType


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_agent_manager_calls_memory_integration_on_create() -> None:
    integration = MagicMock()
    integration.record_agent_lifecycle.return_value = None
    manager = AgentManager(engineering_memory_integration=integration)

    agent = _run(manager.create("test-agent", agent_type=AgentType.USER))
    assert agent is not None
    integration.record_agent_lifecycle.assert_called_once()
    kwargs = integration.record_agent_lifecycle.call_args.kwargs
    assert kwargs["action"] == "created"
    assert kwargs["agent_id"] == agent.id
    assert kwargs["observed"] is True


def test_agent_manager_failure_does_not_block_operation() -> None:
    integration = MagicMock()
    integration.record_agent_lifecycle.side_effect = RuntimeError("boom")
    manager = AgentManager(engineering_memory_integration=integration)

    agent = _run(manager.create("test-agent-two", agent_type=AgentType.USER))
    assert agent is not None
