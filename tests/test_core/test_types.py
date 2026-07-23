"""Tests des dataclasses core/types/."""

import pytest
from datetime import datetime

from core.ethan_types.event import Event, EventType
from core.ethan_types.message import ChatMessage, ChatResponse, Message
from core.ethan_types.capability import Capability, Dependency
from core.ethan_types.goal import Goal, GoalState, GoalPriority
from core.ethan_types.plan import Plan, Task, TaskState, TaskDAG
from core.ethan_types.module import ModuleConfig, ModuleState, ModuleStateData
from core.ethan_types.result import Result, Error, Progress


class TestEvent:
    def test_event_creation(self):
        event = Event(
            type=EventType.SYSTEM_BOOT,
            source="test",
            payload={"key": "value"},
        )
        assert event.id is not None
        assert event.type == EventType.SYSTEM_BOOT
        assert event.source == "test"
        assert event.payload == {"key": "value"}
        assert isinstance(event.timestamp, datetime)

    def test_event_correlation_id(self):
        event = Event()
        assert event.correlation_id is None
        event.correlation_id = "corr-123"
        assert event.correlation_id == "corr-123"
        assert event.metadata["correlation_id"] == "corr-123"


class TestEventType:
    def test_all_event_types(self):
        assert EventType.SYSTEM_BOOT == "ethan.system.boot"
        assert EventType.INTERFACE_MESSAGE == "ethan.interface.message"
        assert EventType.EXECUTIVE_GOAL_CREATED == "ethan.executive.goal.created"
        assert EventType.PLANNER_PLAN_CREATED == "ethan.planner.plan.created"
        assert EventType.EXECUTOR_TASK_ASSIGNED == "ethan.executor.task.assigned"
        assert EventType.MEMORY_STORE == "ethan.memory.store"


class TestChatMessage:
    def test_chat_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.tool_calls is None

    def test_chat_message_with_tools(self):
        msg = ChatMessage(
            role="assistant",
            content="Result",
            tool_calls=[{"name": "tool1"}],
            tool_call_id="call-123",
        )
        assert msg.tool_calls == [{"name": "tool1"}]
        assert msg.tool_call_id == "call-123"


class TestChatResponse:
    def test_chat_response(self):
        resp = ChatResponse(
            content="Hi there",
            model="llama3",
            provider="ollama",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            latency_ms=150.5,
        )
        assert resp.content == "Hi there"
        assert resp.model == "llama3"
        assert resp.provider == "ollama"
        assert resp.usage["prompt_tokens"] == 10
        assert resp.latency_ms == 150.5


class TestCapability:
    def test_capability_creation(self):
        cap = Capability(
            name="docker.build",
            version="1.0.0",
            module="docker-module",
            description="Build Docker images",
            inputs=["docker.build.request"],
            outputs=["docker.build.complete"],
        )
        assert cap.name == "docker.build"
        assert cap.version == "1.0.0"
        assert cap.module == "docker-module"
        assert len(cap.inputs) == 1
        assert len(cap.outputs) == 1

    def test_capability_with_dependencies(self):
        dep = Dependency(name="filesystem.read", version="1.0.0", optional=True)
        cap = Capability(
            name="file.process",
            dependencies=[dep],
        )
        assert len(cap.dependencies) == 1
        assert cap.dependencies[0].name == "filesystem.read"
        assert cap.dependencies[0].optional is True


class TestGoal:
    def test_goal_creation(self):
        goal = Goal(
            title="Deploy API",
            description="Deploy to staging",
            state=GoalState.ACTIVE,
            priority=GoalPriority.HIGH,
        )
        assert goal.title == "Deploy API"
        assert goal.state == GoalState.ACTIVE
        assert goal.priority == GoalPriority.HIGH
        assert goal.id == ""  # Default

    def test_goal_states(self):
        assert GoalState.PENDING == "pending"
        assert GoalState.ACTIVE == "active"
        assert GoalState.COMPLETED == "completed"
        assert GoalState.FAILED == "failed"


class TestPlan:
    def test_plan_creation(self):
        task1 = Task(id="t1", capability="docker.build")
        task2 = Task(id="t2", capability="k8s.deploy", depends_on=["t1"])
        plan = Plan(
            id="plan-1",
            goal_id="goal-1",
            tasks=[task1, task2],
        )
        assert plan.id == "plan-1"
        assert len(plan.tasks) == 2
        assert plan.tasks[1].depends_on == ["t1"]

    def test_task_dag(self):
        dag = TaskDAG()
        task1 = Task(id="t1")
        task2 = Task(id="t2")
        dag.add_level([task1])
        dag.add_level([task2])
        assert len(dag.levels) == 2
        assert len(dag.levels[0]) == 1


class TestModuleConfig:
    def test_module_config(self):
        config = ModuleConfig(
            name="planner",
            module_path="core.agents.planner",
            auto_start=True,
            max_restarts=3,
        )
        assert config.name == "planner"
        assert config.module_path == "core.agents.planner"
        assert config.auto_start is True
        assert config.max_restarts == 3


class TestResult:
    def test_result_ok(self):
        result = Result.ok(data={"status": "done"}, duration_ms=100.0)
        assert result.success is True
        assert result.data == {"status": "done"}
        assert result.error is None
        assert result.duration_ms == 100.0

    def test_result_fail(self):
        result = Result.fail(
            code="TIMEOUT",
            message="Operation timed out",
            suggestion="Retry with longer timeout",
            duration_ms=5000.0,
        )
        assert result.success is False
        assert result.error is not None
        assert result.error.code == "TIMEOUT"
        assert result.error.message == "Operation timed out"
        assert result.error.suggestion == "Retry with longer timeout"
        assert result.duration_ms == 5000.0

    def test_result_default(self):
        result = Result()
        assert result.success is True
        assert result.data is None
        assert result.error is None