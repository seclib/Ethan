
"""Authenticated agent execution context propagation (Campaign 02-F2-R4)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from core.agents.manager import AgentManager
from core.auth.principal import AgentPrincipal, ExecutionContext, PrincipalType
from core.state.record_store import CoreRecordStore


def test_agent_execution_context_propagates() -> None:
    async def run():
        store = CoreRecordStore()
        manager = AgentManager(store=store)
        captured = {}

        async def executor(*, agent, task, context, skill_id, execution_context):
            captured["execution_context"] = execution_context
            return "done"

        await manager.set_executor(executor)
        agent = await manager.create(name="test-agent")
        principal = AgentPrincipal(
            principal_id="human:alice",
            principal_type=PrincipalType.HUMAN,
            subject_id="alice",
            permissions=("agents", "execute"),
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc).replace(year=2099),
        )
        execution_context = ExecutionContext(
            principal=principal,
            agent_id=agent.id,
            request_id="req-1",
            started_at=datetime.now(timezone.utc),
        )

        execution = await manager.execute(
            agent.id, "hello", execution_context=execution_context
        )

        assert execution.status.value == "completed"
        assert captured["execution_context"] is execution_context
        assert execution.execution_context == execution_context

        persisted = await store.get(manager._EXECUTIONS_DOMAIN, execution.id)
        persisted_context = persisted["execution_context"]
        if hasattr(persisted_context, "to_dict"):
            persisted_context = persisted_context.to_dict()
        assert persisted_context["principal"]["principal_id"] == "human:alice"

        restored = manager._execution_from_dict(persisted) if hasattr(manager, "_execution_from_dict") else None
        if restored is not None:
            assert restored.execution_context == execution_context

    asyncio.run(run())
