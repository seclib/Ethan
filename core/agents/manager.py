"""Core-owned definition, lifecycle and execution of ETHAN agents."""

from __future__ import annotations

from datetime import datetime
import inspect
import logging
from typing import Any, Awaitable, Callable
from uuid import uuid4

from core.agents.types import Agent, AgentExecution, AgentExecutionStatus, AgentStatus
from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

AgentExecutor = Callable[..., Awaitable[Any] | Any]


class AgentExecutionUnavailable(RuntimeError):
    """Raised when an execution was requested without a Core execution adapter."""


class AgentManager:
    """Own agent definitions, lifecycle transitions and execution history.

    The manager is intentionally interface-agnostic.  An executor is injected
    by the runtime composition root; it can bind a planner, a skill executor,
    or a specialized autonomous agent without making the API or WebUI owners
    of that behaviour.
    """

    _DOMAIN = "agents"
    _EXECUTIONS_DOMAIN = "agent-executions"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        *,
        executor: AgentExecutor | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._executor = executor

    async def create(
        self,
        name: str,
        description: str = "",
        capabilities: list[str] | None = None,
        model: str | None = None,
        provider: str | None = None,
        memory_scope: str = "default",
        skill_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Agent:
        """Create and persist an agent definition."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Agent name must not be empty")

        agent = Agent(
            id=str(uuid4()),
            name=normalized_name,
            description=description,
            capabilities=list(capabilities or []),
            model=model,
            provider=provider,
            memory_scope=memory_scope,
            skill_ids=list(skill_ids or []),
            metadata=dict(metadata or {}),
        )
        await self._persist(agent)
        await self._publish(EventType.AGENT_CREATED, "agent.created", {"agent": agent.to_dict()})
        return agent

    async def get(self, agent_id: str) -> Agent | None:
        """Retrieve one agent definition."""
        data = await self._store.get(self._DOMAIN, agent_id)
        return Agent.from_dict(data) if data else None

    async def list(self) -> list[Agent]:
        """List all agents, newest update first when persistence is enabled."""
        return [Agent.from_dict(data) for data in await self._store.list(self._DOMAIN)]

    async def update(self, agent_id: str, data: dict[str, Any]) -> Agent | None:
        """Apply a validated partial update to an agent definition."""
        agent = await self.get(agent_id)
        if agent is None:
            return None

        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                raise ValueError("Agent name must not be empty")
            agent.name = name
        if "description" in data:
            agent.description = str(data["description"])
        if "capabilities" in data:
            agent.capabilities = list(data["capabilities"])
        if "status" in data:
            agent.status = AgentStatus(data["status"])
        if "model" in data:
            agent.model = data["model"]
        if "provider" in data:
            agent.provider = data["provider"]
        if "memory_scope" in data:
            agent.memory_scope = str(data["memory_scope"])
        if "skill_ids" in data or "skills" in data:
            agent.skill_ids = list(data.get("skill_ids", data.get("skills", [])))
        if "metadata" in data:
            agent.metadata.update(dict(data["metadata"]))
        agent.updated_at = datetime.utcnow()

        await self._persist(agent)
        await self._publish(EventType.AGENT_UPDATED, "agent.updated", {"agent": agent.to_dict()})
        return agent

    async def delete(self, agent_id: str) -> bool:
        """Remove an agent definition and its persisted execution records."""
        existed = await self._store.delete(self._DOMAIN, agent_id)
        for execution in await self.list_executions(agent_id):
            await self._store.delete(self._EXECUTIONS_DOMAIN, execution.id)
        if existed:
            await self._publish(EventType.AGENT_DELETED, "agent.deleted", {"agent_id": agent_id})
        return existed

    async def set_status(self, agent_id: str, status: AgentStatus | str) -> Agent | None:
        """Set a lifecycle state using the same persistence and event path."""
        status_value = status.value if isinstance(status, AgentStatus) else status
        return await self.update(agent_id, {"status": status_value})

    async def start(self, agent_id: str) -> Agent | None:
        """Mark an agent available for work."""
        return await self.set_status(agent_id, AgentStatus.RUNNING)

    async def pause(self, agent_id: str) -> Agent | None:
        """Pause an agent without deleting its definition or memory scope."""
        return await self.set_status(agent_id, AgentStatus.PAUSED)

    async def stop(self, agent_id: str) -> Agent | None:
        """Stop an agent gracefully."""
        return await self.set_status(agent_id, AgentStatus.STOPPED)

    async def execute(
        self,
        agent_id: str,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        skill_id: str | None = None,
    ) -> AgentExecution:
        """Run work through the runtime-provided Core execution adapter.

        Agent execution is not simulated here: if the runtime has not provided
        an adapter, callers receive a clear error instead of a false success.
        The execution record still belongs to this manager and is available to
        every interface once an adapter exists.
        """
        agent = await self.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        if not task.strip():
            raise ValueError("Agent task must not be empty")
        if self._executor is None:
            raise AgentExecutionUnavailable("No Core agent executor is configured")
        if skill_id is not None and skill_id not in agent.skill_ids:
            raise ValueError(f"Skill {skill_id} is not assigned to agent {agent_id}")

        execution = AgentExecution(
            id=str(uuid4()),
            agent_id=agent_id,
            task=task,
            context=dict(context or {}),
            skill_id=skill_id,
        )
        await self._persist_execution(execution)
        await self.set_status(agent_id, AgentStatus.RUNNING)

        try:
            result = self._executor(
                agent=agent,
                task=task,
                context=execution.context,
                skill_id=skill_id,
            )
            execution.result = await result if inspect.isawaitable(result) else result
            execution.status = AgentExecutionStatus.COMPLETED
        except Exception as exc:
            execution.status = AgentExecutionStatus.FAILED
            execution.error = str(exc)
            await self.set_status(agent_id, AgentStatus.ERROR)
            logger.exception("Agent execution failed: %s", execution.id)
        else:
            await self.set_status(agent_id, AgentStatus.IDLE)
        finally:
            execution.completed_at = datetime.utcnow()
            await self._persist_execution(execution)

        return execution

    async def list_executions(self, agent_id: str | None = None) -> list[AgentExecution]:
        """Return execution history, optionally limited to one agent."""
        executions = [
            AgentExecution.from_dict(data)
            for data in await self._store.list(self._EXECUTIONS_DOMAIN)
        ]
        if agent_id is not None:
            executions = [execution for execution in executions if execution.agent_id == agent_id]
        return executions

    async def _persist(self, agent: Agent) -> None:
        await self._store.save(self._DOMAIN, agent.id, agent.to_dict())

    async def _persist_execution(self, execution: AgentExecution) -> None:
        await self._store.save(self._EXECUTIONS_DOMAIN, execution.id, execution.to_dict())

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="agent-manager", payload=payload))
