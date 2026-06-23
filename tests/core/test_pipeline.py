"""Tests — Capability Pipeline (ADR-1006)"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.capabilities import CapabilityContext, CapabilityResult, CapabilityStatus
from core.orchestration.executor import Executor
from core.orchestration.pipeline import (
    CapabilityPipeline,
    SequentialStep,
    ParallelStep,
    ConditionalStep,
    RetryStep,
)
from core.orchestration.registry import CapabilityRegistry


@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=CapabilityRegistry)
    return registry


@pytest.fixture
def mock_executor(mock_registry):
    executor = MagicMock(spec=Executor)
    executor.registry = mock_registry
    return executor


@pytest.fixture
def pipeline(mock_executor):
    return CapabilityPipeline(mock_executor)


@pytest.fixture
def sample_context():
    return CapabilityContext(
        user_id="user_123",
        session_id="session_456",
        trace_id="trace_789",
        permissions=["read", "write"],
    )


@pytest.fixture
def success_result():
    return CapabilityResult(
        status=CapabilityStatus.SUCCESS,
        output="success",
    )


@pytest.fixture
def failed_result():
    return CapabilityResult(
        status=CapabilityStatus.FAILED,
        error="failed",
    )


class TestCapabilityPipeline:
    """Tests for CapabilityPipeline."""

    def test_create_pipeline(self, mock_executor):
        """Test pipeline creation."""
        pipeline = CapabilityPipeline.create(mock_executor)
        assert pipeline.executor == mock_executor
        assert pipeline.steps == []

    def test_then_adds_sequential_step(self, pipeline):
        """Test adding sequential step."""
        pipeline.then("test_cap", arg1="value1")
        
        assert len(pipeline.steps) == 1
        assert isinstance(pipeline.steps[0], SequentialStep)
        assert pipeline.steps[0].capability == "test_cap"
        assert pipeline.steps[0].args == {"arg1": "value1"}

    def test_then_returns_self(self, pipeline):
        """Test that then() returns pipeline for chaining."""
        result = pipeline.then("cap1")
        assert result is pipeline

    def test_parallel_adds_parallel_step(self, pipeline):
        """Test adding parallel steps."""
        pipeline.parallel("cap1", "cap2", "cap3")
        
        assert len(pipeline.steps) == 1
        assert isinstance(pipeline.steps[0], ParallelStep)
        assert pipeline.steps[0].capabilities == ["cap1", "cap2", "cap3"]

    def test_branch_adds_conditional_step(self, pipeline):
        """Test adding conditional branch."""
        true_branch = CapabilityPipeline(pipeline.executor)
        false_branch = CapabilityPipeline(pipeline.executor)
        
        pipeline.branch("condition", true_branch, false_branch)
        
        assert len(pipeline.steps) == 1
        assert isinstance(pipeline.steps[0], ConditionalStep)
        assert pipeline.steps[0].condition == "condition"
        assert pipeline.steps[0].true_branch == true_branch
        assert pipeline.steps[0].false_branch == false_branch

    def test_branch_without_false_branch(self, pipeline):
        """Test conditional branch with only true branch."""
        true_branch = CapabilityPipeline(pipeline.executor)
        
        pipeline.branch("condition", true_branch)
        
        assert len(pipeline.steps) == 1
        assert isinstance(pipeline.steps[0], ConditionalStep)
        assert pipeline.steps[0].false_branch is not None

    def test_retry_wraps_last_step(self, pipeline):
        """Test retry wrapper."""
        pipeline.then("cap1")
        pipeline.retry(max_attempts=5)
        
        assert len(pipeline.steps) == 1
        assert isinstance(pipeline.steps[0], RetryStep)
        assert pipeline.steps[0].max_attempts == 5
        assert isinstance(pipeline.steps[0].step, SequentialStep)

    def test_retry_without_steps(self, pipeline):
        """Test retry with no steps."""
        pipeline.retry(max_attempts=3)
        assert len(pipeline.steps) == 0


class TestPipelineExecution:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_execute_sequential(self, pipeline, mock_executor, sample_context, success_result):
        """Test sequential execution."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        pipeline.then("cap1", arg1="val1")
        pipeline.then("cap2", arg2="val2")
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 2
        assert mock_executor.run.call_count == 2
        mock_executor.run.assert_any_call("cap1", sample_context, arg1="val1")
        mock_executor.run.assert_any_call("cap2", sample_context, arg2="val2")

    @pytest.mark.asyncio
    async def test_execute_parallel(self, pipeline, mock_executor, sample_context, success_result):
        """Test parallel execution."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        pipeline.parallel("cap1", "cap2", "cap3")
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 3
        assert mock_executor.run.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_conditional_true(self, pipeline, mock_executor, sample_context, success_result):
        """Test conditional execution - true branch."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        true_branch = CapabilityPipeline(mock_executor)
        true_branch.then("true_cap")
        false_branch = CapabilityPipeline(mock_executor)
        false_branch.then("false_cap")
        
        # Set condition in metadata to trigger true branch
        sample_context.metadata["condition"] = True
        
        pipeline.branch("condition", true_branch, false_branch)
        
        results = await pipeline.execute(sample_context)
        
        # Should execute true branch only
        assert len(results) == 1
        mock_executor.run.assert_called_once_with("true_cap", sample_context)

    @pytest.mark.asyncio
    async def test_execute_conditional_false(self, pipeline, mock_executor, sample_context, success_result):
        """Test conditional execution - false branch."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        true_branch = CapabilityPipeline(mock_executor)
        true_branch.then("true_cap")
        false_branch = CapabilityPipeline(mock_executor)
        false_branch.then("false_cap")
        
        # Condition not in metadata - should execute false branch
        pipeline.branch("condition", true_branch, false_branch)
        
        results = await pipeline.execute(sample_context)
        
        # Should execute false branch only
        assert len(results) == 1
        mock_executor.run.assert_called_once_with("false_cap", sample_context)

    @pytest.mark.asyncio
    async def test_execute_retry_success_first_attempt(
        self, pipeline, mock_executor, sample_context, success_result
    ):
        """Test retry - success on first attempt."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        pipeline.then("cap1").retry(max_attempts=3)
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 1
        assert mock_executor.run.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_retry_success_after_failures(
        self, pipeline, mock_executor, sample_context, success_result, failed_result
    ):
        """Test retry - success after failures."""
        # Fail twice, then succeed
        mock_executor.run = AsyncMock(
            side_effect=[failed_result, failed_result, success_result]
        )
        
        pipeline.then("cap1").retry(max_attempts=3)
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 1
        assert mock_executor.run.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_retry_exhausted(self, pipeline, mock_executor, sample_context, failed_result):
        """Test retry - all attempts fail."""
        mock_executor.run = AsyncMock(return_value=failed_result)
        
        pipeline.then("cap1").retry(max_attempts=2)
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 1
        assert mock_executor.run.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_mixed_steps(self, pipeline, mock_executor, sample_context, success_result):
        """Test mixed sequential and parallel steps."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        pipeline.then("cap1")
        pipeline.parallel("cap2", "cap3")
        pipeline.then("cap4")
        
        results = await pipeline.execute(sample_context)
        
        assert len(results) == 4  # 1 + 2 + 1
        assert mock_executor.run.call_count == 4


class TestPipelineIntegration:
    """Integration tests for pipelines."""

    @pytest.mark.asyncio
    async def test_complex_workflow(self, mock_executor, sample_context, success_result):
        """Test complex workflow with multiple step types."""
        mock_executor.run = AsyncMock(return_value=success_result)
        
        pipeline = CapabilityPipeline(mock_executor)
        
        # Build complex workflow
        pipeline.then("validate", data="test")
        pipeline.parallel("check_auth", "check_quota")
        
        # Conditional branch
        true_branch = CapabilityPipeline(mock_executor)
        true_branch.then("process_premium")
        false_branch = CapabilityPipeline(mock_executor)
        false_branch.then("process_standard")
        pipeline.branch("is_premium", true_branch, false_branch)
        
        pipeline.then("finalize")
        
        results = await pipeline.execute(sample_context)
        
        # Should execute: validate, check_auth, check_quota, process_standard (false), finalize
        assert len(results) == 5

    def test_pipeline_chaining(self, pipeline):
        """Test fluent API chaining."""
        result = (
            pipeline.then("cap1")
            .then("cap2")
            .parallel("cap3", "cap4")
            .then("cap5")
        )
        
        assert result is pipeline
        assert len(pipeline.steps) == 4