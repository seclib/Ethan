"""Tests — Event System (ADR-1007)"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from core.events import Event, EventBus, EventHandler, EventType


class TestEventHandler(EventHandler):
    """Test handler implementation."""
    
    def __init__(self):
        self.events_received = []
    
    async def handle(self, event: Event) -> None:
        self.events_received.append(event)


@pytest.fixture
def event_bus():
    return EventBus(record_history=True)


@pytest.fixture
def test_handler():
    return TestEventHandler()


@pytest.fixture
def sample_event():
    return Event(
        type=EventType.USER_INPUT_RECEIVED,
        source="cli",
        data={"input": "test query"},
        metadata={"user_id": "user_123"},
    )


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Test event creation with defaults."""
        event = Event()
        assert event.id is not None
        assert event.type == EventType.SYSTEM_STARTUP
        assert event.source == "system"
        assert isinstance(event.timestamp, datetime)
        assert event.data == {}
        assert event.metadata == {}

    def test_event_creation_with_values(self):
        """Test event creation with custom values."""
        event = Event(
            type=EventType.CAPABILITY_STARTED,
            source="test",
            data={"key": "value"},
            metadata={"trace": "123"},
        )
        assert event.type == EventType.CAPABILITY_STARTED
        assert event.source == "test"
        assert event.data == {"key": "value"}
        assert event.metadata == {"trace": "123"}

    def test_event_has_unique_id(self):
        """Test that each event has a unique ID."""
        event1 = Event()
        event2 = Event()
        assert event1.id != event2.id


class TestEventBus:
    """Tests for EventBus."""

    def test_create_event_bus(self, event_bus):
        """Test event bus creation."""
        assert event_bus._handlers == {}
        assert event_bus._history == []

    def test_create_event_bus_no_history(self):
        """Test event bus without history recording."""
        bus = EventBus(record_history=False)
        assert bus._history == []

    @pytest.mark.asyncio
    async def test_subscribe(self, event_bus, test_handler):
        """Test subscribing a handler."""
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, test_handler)
        
        assert EventType.USER_INPUT_RECEIVED in event_bus._handlers
        assert test_handler in event_bus._handlers[EventType.USER_INPUT_RECEIVED]

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus, test_handler):
        """Test unsubscribing a handler."""
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, test_handler)
        await event_bus.unsubscribe(EventType.USER_INPUT_RECEIVED, test_handler)
        
        assert test_handler not in event_bus._handlers[EventType.USER_INPUT_RECEIVED]

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self, event_bus, test_handler):
        """Test unsubscribing a handler that was never subscribed."""
        # Should not raise
        await event_bus.unsubscribe(EventType.USER_INPUT_RECEIVED, test_handler)

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, event_bus, sample_event):
        """Test publishing with no handlers."""
        # Should not raise
        await event_bus.publish(sample_event)
        assert len(event_bus._history) == 1

    @pytest.mark.asyncio
    async def test_publish_with_handler(self, event_bus, test_handler, sample_event):
        """Test publishing with a handler."""
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, test_handler)
        await event_bus.publish(sample_event)
        
        assert len(test_handler.events_received) == 1
        assert test_handler.events_received[0] == sample_event

    @pytest.mark.asyncio
    async def test_publish_to_multiple_handlers(self, event_bus, sample_event):
        """Test publishing to multiple handlers."""
        handler1 = TestEventHandler()
        handler2 = TestEventHandler()
        
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, handler1)
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, handler2)
        await event_bus.publish(sample_event)
        
        assert len(handler1.events_received) == 1
        assert len(handler2.events_received) == 1

    @pytest.mark.asyncio
    async def test_publish_records_history(self, event_bus, sample_event):
        """Test that publish records event in history."""
        await event_bus.publish(sample_event)
        
        assert len(event_bus._history) == 1
        assert event_bus._history[0] == sample_event

    @pytest.mark.asyncio
    async def test_publish_no_history_when_disabled(self, sample_event):
        """Test that history is not recorded when disabled."""
        bus = EventBus(record_history=False)
        await bus.publish(sample_event)
        
        assert len(bus._history) == 0

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_break_bus(self, event_bus, sample_event):
        """Test that handler exceptions don't break the bus."""
        
        class FailingHandler(EventHandler):
            async def handle(self, event: Event) -> None:
                raise Exception("Handler error")
        
        failing_handler = FailingHandler()
        good_handler = TestEventHandler()
        
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, failing_handler)
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, good_handler)
        
        # Should not raise despite failing handler
        await event_bus.publish(sample_event)
        
        # Good handler should still receive event
        assert len(good_handler.events_received) == 1

    def test_get_history_all(self, event_bus):
        """Test getting all event history."""
        event1 = Event(type=EventType.SYSTEM_STARTUP)
        event2 = Event(type=EventType.USER_INPUT_RECEIVED)
        
        event_bus._history = [event1, event2]
        
        history = event_bus.get_history()
        assert len(history) == 2
        assert history == [event1, event2]

    def test_get_history_by_type(self, event_bus):
        """Test getting event history filtered by type."""
        event1 = Event(type=EventType.SYSTEM_STARTUP)
        event2 = Event(type=EventType.USER_INPUT_RECEIVED)
        event3 = Event(type=EventType.USER_INPUT_RECEIVED)
        
        event_bus._history = [event1, event2, event3]
        
        history = event_bus.get_history(EventType.USER_INPUT_RECEIVED)
        assert len(history) == 2
        assert all(e.type == EventType.USER_INPUT_RECEIVED for e in history)

    def test_clear_history(self, event_bus):
        """Test clearing event history."""
        event_bus._history = [Event(), Event(), Event()]
        event_bus.clear_history()
        
        assert len(event_bus._history) == 0

    @pytest.mark.asyncio
    async def test_multiple_event_types(self, event_bus):
        """Test handling multiple event types."""
        handler_system = TestEventHandler()
        handler_user = TestEventHandler()
        
        await event_bus.subscribe(EventType.SYSTEM_STARTUP, handler_system)
        await event_bus.subscribe(EventType.USER_INPUT_RECEIVED, handler_user)
        
        system_event = Event(type=EventType.SYSTEM_STARTUP)
        user_event = Event(type=EventType.USER_INPUT_RECEIVED)
        
        await event_bus.publish(system_event)
        await event_bus.publish(user_event)
        
        assert len(handler_system.events_received) == 1
        assert handler_system.events_received[0] == system_event
        assert len(handler_user.events_received) == 1
        assert handler_user.events_received[0] == user_event


class TestEventTypes:
    """Tests for EventType enum."""

    def test_event_types_exist(self):
        """Test that all expected event types exist."""
        assert EventType.SYSTEM_STARTUP == "system.startup"
        assert EventType.CAPABILITY_STARTED == "capability.started"
        assert EventType.MEMORY_STORED == "memory.stored"
        assert EventType.USER_INPUT_RECEIVED == "user.input.received"

    def test_event_type_is_string(self):
        """Test that EventType is a string enum."""
        assert isinstance(EventType.SYSTEM_STARTUP, str)