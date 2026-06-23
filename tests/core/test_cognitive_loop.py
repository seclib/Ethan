"""Tests — Cognitive Loop (ADR-1004)"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from core.context.intent import Intent, IntentRouter
from core.orchestration.cognitive_loop import (
    CognitiveLoop,
    CognitiveState,
    CognitiveResult,
)
from core.orchestration import Executor, Observer, Planner
from core.orchestration.registry import CapabilityRegistry


@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=CapabilityRegistry)
    registry.get.return_value = MagicMock()
    return registry


@pytest.fixture
def mock_intent_router():
    router = MagicMock(spec=IntentRouter)
    return router


@pytest.fixture
def cognitive_loop(mock_registry, mock_intent_router):
    return CognitiveLoop(
        registry=mock_registry,
        intent_router=mock_intent_router,
    )


@pytest.fixture
def sample_intent():
    return Intent(
        source="text",
        user_input="Test input",
        context={"key": "value"},
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_context():
    return MagicMock()


class TestCognitiveState:
    def test_initial_state(self):
        state = CognitiveState(session_id="test_session")
        assert state.session_id == "test_session"
        assert state.history == []
        assert state.memory == {}
        assert state.reflections == []
        assert isinstance(state.started_at, datetime)

    def test_state_with_data(self):
        state = CognitiveState(
            session_id="test",
            history=[{"test": "data"}],
            memory={"key": "value"},
            reflections=["reflection"],
        )
        assert len(state.history) == 1
        assert state.memory["key"] == "value"
        assert len(state.reflections) == 1


class TestCognitiveLoopPerception:
    @pytest.mark.asyncio
    async def test_perceive(self, cognitive_loop, mock_intent_router, sample_intent):
        mock_intent_router.parse.return_value = sample_intent
        
        intent = await cognitive_loop._perceive("text", "Hello")
        
        mock_intent_router.parse.assert_called_once_with("text", "Hello")
        assert intent == sample_intent
        assert intent.source == "text"


class TestCognitiveLoopReasoning:
    def test_reason(self, cognitive_loop, sample_intent):
        state = CognitiveState(session_id="test")
        
        reasoning = cognitive_loop._reason(sample_intent, state)
        
        assert reasoning["intent_type"] == "text"
        assert reasoning["has_context"] is True
        assert reasoning["history_length"] == 0

    def test_reason_with_history(self, cognitive_loop, sample_intent):
        state = CognitiveState(
            session_id="test",
            history=[{"success": True}],
        )
        
        reasoning = cognitive_loop._reason(sample_intent, state)
        
        assert reasoning["history_length"] == 1
        assert reasoning["last_success"] is True


class TestCognitiveLoopPlanning:
    def test_plan(self, cognitive_loop, sample_intent):
        with patch.object(cognitive_loop.planner, 'build') as mock_build:
            from core.orchestration.planner import Plan
            mock_plan = Plan(steps=[])
            mock_build.return_value = mock_plan
            
            plan = cognitive_loop._plan(sample_intent, {})
            
            mock_build.assert_called_once_with(sample_intent)
            assert plan == mock_plan


class TestCognitiveLoopExecution:
    @pytest.mark.asyncio
    async def test_execute(self, cognitive_loop, sample_context):
        from core.orchestration.planner import Plan, Step
        from core.capabilities import CapabilityStatus, CapabilityResult
        
        plan = Plan(steps=[
            Step(capability="test_cap", args={"arg1": "value1"})
        ])
        
        mock_cap = MagicMock()
        mock_cap.validate = AsyncMock(return_value=True)
        mock_cap.execute = AsyncMock(return_value=CapabilityResult(
            status=CapabilityStatus.SUCCESS,
            output="test output",
        ))
        cognitive_loop.registry.get.return_value = mock_cap
        
        observations = await cognitive_loop._execute(plan, sample_context)
        
        assert len(observations) == 1
        assert observations[0].success is True

    @pytest.mark.asyncio
    async def test_execute_failure(self, cognitive_loop, sample_context):
        from core.orchestration.planner import Plan, Step
        from core.capabilities import CapabilityStatus, CapabilityResult
        
        plan = Plan(steps=[
            Step(capability="missing_cap", args={})
        ])
        
        cognitive_loop.registry.get.return_value = None
        
        observations = await cognitive_loop._execute(plan, sample_context)
        
        assert len(observations) == 1
        assert observations[0].success is False


class TestCognitiveLoopMemory:
    def test_update_memory(self, cognitive_loop, sample_intent):
        state = CognitiveState(session_id="test")
        
        from core.orchestration.observer import Observation
        observations = [
            Observation(summary="Test obs", details={}, success=True)
        ]
        
        cognitive_loop._update_memory(sample_intent, observations, state)
        
        assert len(state.history) == 1
        assert "interaction_1" in state.memory
        assert state.memory["interaction_1"]["success"] is True

    def test_update_memory_with_failures(self, cognitive_loop, sample_intent):
        state = CognitiveState(session_id="test")
        
        from core.orchestration.observer import Observation
        observations = [
            Observation(summary="Failed", details={}, success=False)
        ]
        
        cognitive_loop._update_memory(sample_intent, observations, state)
        
        assert state.memory["interaction_1"]["success"] is False
        # Note: last_failure is set in _reflect, not _update_memory


class TestCognitiveLoopReflection:
    def test_reflect_success(self, cognitive_loop, sample_intent):
        state = CognitiveState(session_id="test")
        
        from core.orchestration.observer import Observation
        observations = [
            Observation(summary="Success", details={}, success=True)
        ]
        
        reflection = cognitive_loop._reflect(sample_intent, observations, state)
        
        assert "Successfully processed" in reflection
        assert len(state.reflections) == 1
        assert "last_failure" not in state.memory

    def test_reflect_failure(self, cognitive_loop, sample_intent):
        state = CognitiveState(session_id="test")
        
        from core.orchestration.observer import Observation
        observations = [
            Observation(summary="Failed op", details={}, success=False)
        ]
        
        reflection = cognitive_loop._reflect(sample_intent, observations, state)
        
        assert "Partial failure" in reflection
        assert "last_failure" in state.memory
        assert state.memory["last_failure"]["intent"] == "Test input"


class TestCognitiveLoopIntegration:
    @pytest.mark.asyncio
    async def test_run_full_cycle(self, cognitive_loop, mock_intent_router, sample_context):
        from core.orchestration.planner import Plan, Step
        from core.capabilities import CapabilityStatus, CapabilityResult
        from core.orchestration.observer import Observation
        
        # Setup mocks
        sample_intent = Intent(
            source="text",
            user_input="Test query",
            context={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_intent_router.parse.return_value = sample_intent
        
        with patch.object(cognitive_loop.planner, 'build') as mock_build:
            mock_build.return_value = Plan(steps=[])
            
            with patch.object(cognitive_loop.executor, 'run') as mock_exec:
                mock_exec.return_value = CapabilityResult(
                    status=CapabilityStatus.SUCCESS,
                    output="result",
                )
                
                result = await cognitive_loop.run(
                    source="text",
                    raw_input="Test query",
                    session_id="session_1",
                    context=sample_context,
                )
                
                assert isinstance(result, CognitiveResult)
                assert result.intent == sample_intent
                assert result.success is True
                assert result.duration_ms > 0
                assert isinstance(result.reflection, str)

    def test_get_state(self, cognitive_loop):
        state = cognitive_loop._get_state("session_1")
        assert state.session_id == "session_1"
        
        # Should return same state on second call
        state2 = cognitive_loop._get_state("session_1")
        assert state is state2

    def test_clear_state(self, cognitive_loop):
        cognitive_loop._get_state("session_to_clear")
        assert "session_to_clear" in cognitive_loop._states
        
        cognitive_loop.clear_state("session_to_clear")
        assert "session_to_clear" not in cognitive_loop._states