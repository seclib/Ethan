"""Tests du EventBus (InMemoryBus)."""

import asyncio
import pytest

from core.bus.memory_bus import InMemoryBus
from core.bus.interface import Subscription
from core.ethan_types.event import Event, EventType


@pytest.fixture
def bus():
    """Fixture : bus in-memory frais pour chaque test."""
    b = InMemoryBus()
    asyncio.run(b.connect("test://"))
    yield b
    asyncio.run(b.close())


class TestInMemoryBus:
    def test_connect(self, bus):
        assert bus.is_connected()

    def test_publish_subscribe(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        asyncio.run(bus.subscribe("ethan.test.*", handler))

        event = Event(type=EventType.SYSTEM_BOOT, source="test")
        asyncio.run(bus.publish("ethan.test.hello", event))

        assert len(received) == 1
        assert received[0].type == EventType.SYSTEM_BOOT
        assert received[0].source == "test"

    def test_publish_no_subscriber(self, bus):
        event = Event(type=EventType.SYSTEM_BOOT, source="test")
        asyncio.run(bus.publish("ethan.nonexistent.*", event))
        assert bus.subscriber_count == 0

    def test_multiple_subscribers(self, bus):
        received1 = []
        received2 = []

        async def handler1(event):
            received1.append(event)

        async def handler2(event):
            received2.append(event)

        asyncio.run(bus.subscribe("ethan.test.*", handler1))
        asyncio.run(bus.subscribe("ethan.test.*", handler2))

        event = Event(type=EventType.SYSTEM_BOOT, source="test")
        asyncio.run(bus.publish("ethan.test.hello", event))

        assert len(received1) == 1
        assert len(received2) == 1

    def test_wildcard_patterns(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        asyncio.run(bus.subscribe("ethan.module.*", handler))

        asyncio.run(bus.publish("ethan.module.planner", Event(type=EventType.PLANNER_PLAN_CREATED)))
        asyncio.run(bus.publish("ethan.module.executive", Event(type=EventType.EXECUTIVE_GOAL_CREATED)))
        asyncio.run(bus.publish("ethan.other.thing", Event(type=EventType.SYSTEM_BOOT)))

        assert len(received) == 2

    def test_unsubscribe(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        sub = asyncio.run(bus.subscribe("ethan.test.*", handler))
        asyncio.run(bus.publish("ethan.test.1", Event(type=EventType.SYSTEM_BOOT)))
        assert len(received) == 1

        asyncio.run(sub.unsubscribe())
        asyncio.run(bus.publish("ethan.test.2", Event(type=EventType.SYSTEM_BOOT)))
        assert len(received) == 1  # Toujours 1

    def test_request_reply(self, bus):
        async def responder(event):
            reply = Event(
                type=EventType.SYSTEM_SHUTDOWN,
                source="responder",
                payload={"response": "ok"},
            )
            reply.correlation_id = event.correlation_id
            await bus.publish(f"ethan.response.{event.correlation_id}", reply)

        asyncio.run(bus.subscribe("ethan.request.echo", responder))

        response = asyncio.run(
            bus.request(
                "ethan.request.echo",
                Event(type=EventType.SYSTEM_BOOT, source="test", payload={"msg": "hello"}),
                timeout=5.0,
            )
        )

        assert response is not None
        assert response.source == "responder"
        assert response.payload["response"] == "ok"

    def test_request_timeout(self, bus):
        response = asyncio.run(
            bus.request(
                "ethan.request.nobody",
                Event(type=EventType.SYSTEM_BOOT, source="test"),
                timeout=0.1,
            )
        )
        assert response is None

    def test_history(self, bus):
        asyncio.run(bus.publish("ethan.test.1", Event(type=EventType.SYSTEM_BOOT)))
        asyncio.run(bus.publish("ethan.test.2", Event(type=EventType.SYSTEM_SHUTDOWN)))

        history = bus.get_history()
        assert len(history) == 2

        boot_history = bus.get_history("ethan.test.1")
        assert len(boot_history) == 1

    def test_clear_history(self, bus):
        asyncio.run(bus.publish("ethan.test.1", Event(type=EventType.SYSTEM_BOOT)))
        bus.clear_history()
        assert len(bus.get_history()) == 0

    def test_handler_error_isolation(self, bus):
        """Un handler qui crash ne doit pas empêcher les autres."""
        received = []

        async def bad_handler(event):
            raise RuntimeError("fail")

        async def good_handler(event):
            received.append(event)

        asyncio.run(bus.subscribe("ethan.test.*", bad_handler))
        asyncio.run(bus.subscribe("ethan.test.*", good_handler))

        asyncio.run(bus.publish("ethan.test.hello", Event(type=EventType.SYSTEM_BOOT)))
        assert len(received) == 1  # good_handler a bien reçu l'event