"""Tests de l'Agent ABC."""

import asyncio
import pytest

from core.agents.base import Agent, AgentConfig, AgentStatus, AgentRegistry
from core.bus.memory_bus import InMemoryBus
from core.ethan_types.event import Event, EventType
from core.ethan_types.result import Result


class SimpleAgent(Agent):
    """Agent concret pour les tests."""

    async def _on_init(self):
        self.initialized = True

    async def _on_event(self, event):
        self.received_events.append(event)

    async def run(self, input_data=None):
        return Result.ok(data={"agent": self.name})

    async def _run_loop(self):
        # Override pour éviter la boucle infinie dans les tests
        pass


@pytest.fixture
def agent():
    a = SimpleAgent(
        config=AgentConfig(
            name="test-agent",
            subscription_patterns=["ethan.test.*"],
        ),
    )
    yield a
    asyncio.run(a.stop())


class TestAgent:
    def test_agent_creation(self):
        config = AgentConfig(name="my-agent")
        agent = SimpleAgent(config=config)
        assert agent.name == "my-agent"
        assert agent.status == AgentStatus.CREATED

    @pytest.mark.asyncio
    async def test_agent_init(self, agent):
        await agent.init()
        assert agent.status == AgentStatus.READY
        assert agent.initialized is True

    @pytest.mark.asyncio
    async def test_agent_start_stop(self, agent):
        await agent.start()
        assert agent.status == AgentStatus.RUNNING
        assert agent.is_running

        await agent.stop()
        assert agent.status == AgentStatus.STOPPED
        assert not agent.is_running

    @pytest.mark.asyncio
    async def test_agent_publish(self, agent):
        await agent.init()
        await agent.start()

        received = []

        async def handler(event):
            received.append(event)

        await agent.subscribe("ethan.agent.*", handler)
        await agent.publish(EventType.SYSTEM_BOOT, {"msg": "hello"})

        assert len(received) == 1
        assert received[0].source == "test-agent"

    @pytest.mark.asyncio
    async def test_agent_request_reply(self, agent):
        await agent.init()

        async def responder(event):
            reply = Event(
                type=EventType.SYSTEM_SHUTDOWN,
                source="responder",
                payload={"answer": 42},
            )
            reply.correlation_id = event.correlation_id
            await agent.bus.publish(f"ethan.response.{event.correlation_id}", reply)

        await agent.subscribe("ethan.request.answer", responder)

        response = await agent.request(
            "ethan.request.answer",
            payload={"question": "life"},
            timeout=5.0,
        )

        assert response is not None
        assert response.payload["answer"] == 42

    @pytest.mark.asyncio
    async def test_agent_run(self, agent):
        result = await agent.run()
        assert result.success is True
        assert result.data == {"agent": "test-agent"}

    def test_agent_metrics(self, agent):
        metrics = agent.get_metrics()
        assert metrics["name"] == "test-agent"
        assert metrics["status"] == AgentStatus.CREATED.value
        assert "uptime" in metrics
        assert "events_processed" in metrics


class TestAgentRegistry:
    def test_registry_creation(self):
        registry = AgentRegistry()
        assert registry.list() == []

    @pytest.mark.asyncio
    async def test_register_unregister(self):
        registry = AgentRegistry()
        config = AgentConfig(name="agent-1")
        agent = SimpleAgent(config=config)

        registry.register(agent)
        assert len(registry.list()) == 1
        assert registry.get("agent-1") is agent

        registry.unregister("agent-1")
        assert len(registry.list()) == 0
        assert registry.get("agent-1") is None

    @pytest.mark.asyncio
    async def test_list_by_status(self):
        registry = AgentRegistry()
        agent1 = SimpleAgent(config=AgentConfig(name="agent-1"))
        agent2 = SimpleAgent(config=AgentConfig(name="agent-2"))

        registry.register(agent1)
        registry.register(agent2)

        created = registry.list_by_status(AgentStatus.CREATED)
        assert len(created) == 2

    @pytest.mark.asyncio
    async def test_start_all_stop_all(self):
        registry = AgentRegistry()
        agents = [
            SimpleAgent(config=AgentConfig(name=f"agent-{i}"))
            for i in range(3)
        ]
        for a in agents:
            registry.register(a)

        await registry.start_all()
        for a in agents:
            assert a.status == AgentStatus.RUNNING

        await registry.stop_all()
        for a in agents:
            assert a.status == AgentStatus.STOPPED