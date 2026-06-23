"""Capability Pipeline — ADR-1006

Pattern de composition pour les capabilities:
- Pipelines séquentiels
- Exécution parallèle
- Branchements conditionnels
- Retry logic
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from core.capabilities import CapabilityContext, CapabilityResult, CapabilityStatus
from core.orchestration.executor import Executor


@dataclass
class PipelineStep(ABC):
    """Abstract pipeline step."""
    pass


@dataclass
class SequentialStep(PipelineStep):
    """Execute a single capability sequentially."""
    capability: str
    args: dict


@dataclass
class ParallelStep(PipelineStep):
    """Execute multiple capabilities in parallel."""
    capabilities: List[str]


@dataclass
class ConditionalStep(PipelineStep):
    """Execute one of two branches based on a condition."""
    condition: str  # Name of the condition check
    true_branch: CapabilityPipeline
    false_branch: CapabilityPipeline


@dataclass
class RetryStep(PipelineStep):
    """Retry a step on failure."""
    max_attempts: int
    step: PipelineStep


class CapabilityPipeline:
    """Compose capabilities into reusable workflows.
    
    Usage:
        pipeline = CapabilityPipeline(executor)
        pipeline.then("validate", data=...)
               .then("process", input=...)
               .parallel("notify_email", "notify_slack")
               .then("finalize")
        
        results = await pipeline.execute(context)
    """

    def __init__(self, executor: Executor):
        self.executor = executor
        self.steps: List[PipelineStep] = []

    def then(self, capability: str, **kwargs) -> CapabilityPipeline:
        """Add sequential step to pipeline."""
        self.steps.append(SequentialStep(capability=capability, args=kwargs))
        return self

    def parallel(self, *capabilities: str) -> CapabilityPipeline:
        """Add parallel steps to pipeline."""
        self.steps.append(ParallelStep(capabilities=list(capabilities)))
        return self

    def branch(
        self,
        condition: str,
        true_branch: CapabilityPipeline,
        false_branch: CapabilityPipeline | None = None,
    ) -> CapabilityPipeline:
        """Add conditional branching."""
        self.steps.append(
            ConditionalStep(
                condition=condition,
                true_branch=true_branch,
                false_branch=false_branch or CapabilityPipeline(self.executor),
            )
        )
        return self

    def retry(self, max_attempts: int = 3) -> CapabilityPipeline:
        """Add retry wrapper to last step."""
        if self.steps:
            last_step = self.steps.pop()
            self.steps.append(RetryStep(max_attempts=max_attempts, step=last_step))
        return self

    async def execute(self, context: CapabilityContext) -> List[CapabilityResult]:
        """Execute the pipeline."""
        results: List[CapabilityResult] = []

        for step in self.steps:
            if isinstance(step, SequentialStep):
                result = await self.executor.run(step.capability, context, **step.args)
                results.append(result)

            elif isinstance(step, ParallelStep):
                tasks = [
                    self.executor.run(cap, context) for cap in step.capabilities
                ]
                parallel_results = await asyncio.gather(*tasks)
                results.extend(parallel_results)

            elif isinstance(step, ConditionalStep):
                # Evaluate condition (simplified: check if condition string is in context metadata)
                should_execute_true = self._evaluate_condition(step.condition, context)
                
                if should_execute_true:
                    branch_results = await step.true_branch.execute(context)
                    results.extend(branch_results)
                else:
                    branch_results = await step.false_branch.execute(context)
                    results.extend(branch_results)

            elif isinstance(step, RetryStep):
                attempt = 0
                last_result = None
                success = False
                
                while attempt < step.max_attempts:
                    if isinstance(step.step, SequentialStep):
                        last_result = await self.executor.run(
                            step.step.capability, context, **step.step.args
                        )
                        success = last_result.status == CapabilityStatus.SUCCESS
                    elif isinstance(step.step, ParallelStep):
                        tasks = [
                            self.executor.run(cap, context)
                            for cap in step.step.capabilities
                        ]
                        last_result = await asyncio.gather(*tasks)
                        success = all(r.status == CapabilityStatus.SUCCESS for r in last_result)
                    
                    if success:
                        break
                    
                    attempt += 1
                
                if isinstance(last_result, list):
                    results.extend(last_result)
                elif last_result:
                    results.append(last_result)

        return results

    def _evaluate_condition(self, condition: str, context: CapabilityContext) -> bool:
        """Evaluate a condition string.
        
        Simplified implementation: checks if condition exists in context metadata.
        In production, this would use a proper expression evaluator.
        """
        return condition in context.metadata

    @staticmethod
    def create(executor: Executor) -> CapabilityPipeline:
        """Factory method to create a new pipeline."""
        return CapabilityPipeline(executor)