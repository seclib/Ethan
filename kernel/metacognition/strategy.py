"""Decision Strategy Selector — Chooses cognitive mode."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sdk.metacognition import (
    COGNITIVE_MODES,
    CognitiveMode,
    DecisionStrategy,
    DEEP_REASONING_MODE,
    DEBUG_MODE,
    EXPLORATION_MODE,
    FAST_EXECUTION_MODE,
    SAFE_MODE,
)
from sdk.learning import SelfModel

logger = logging.getLogger(__name__)


class DecisionStrategySelector:
    """Selects cognitive mode based on task, context, and self-model."""

    def __init__(self):
        self.current_mode = FAST_EXECUTION_MODE

    async def select(
        self,
        task_type: str,
        context: Dict[str, Any],
        self_model: Optional[SelfModel] = None,
    ) -> DecisionStrategy:
        """Choose strategy for a task."""
        # Gather signals
        confidence = self._get_skill_confidence(task_type, self_model)
        complexity = self._estimate_complexity(task_type, context)
        recent_failures = self._count_recent_failures(context)
        user_requested = context.get("mode_override")

        # Decision tree
        if user_requested and user_requested in COGNITIVE_MODES:
            mode = user_requested
            reasoning = f"User requested {mode}"
        elif recent_failures >= 3:
            mode = SAFE_MODE
            reasoning = f"Safe mode after {recent_failures} recent failures"
        elif confidence < 0.3:
            mode = EXPLORATION_MODE
            reasoning = f"Low confidence ({confidence:.2f}) → exploration"
        elif complexity >= 8:
            mode = DEEP_REASONING_MODE
            reasoning = f"High complexity ({complexity}) → deep reasoning"
        elif context.get("debug", False):
            mode = DEBUG_MODE
            reasoning = "Debug flag set"
        else:
            mode = FAST_EXECUTION_MODE
            reasoning = f"Fast path: confidence={confidence:.2f} complexity={complexity}"

        # Update current
        self.current_mode = mode

        depth = self._map_mode_to_depth(mode)

        strategy = DecisionStrategy(
            mode=mode,
            depth=depth,
            reasoning=reasoning,
            confidence=confidence,
            estimated_duration_ms=self._estimate_duration(mode, complexity),
        )

        logger.info(f"Strategy selected: {mode} (depth={depth}) reason={reasoning}")
        return strategy

    def _get_skill_confidence(self, skill: str, model: Optional[SelfModel]) -> float:
        if not model:
            return 0.5
        return model.skills.get(skill, 0.5)

    def _estimate_complexity(self, task_type: str, context: Dict[str, Any]) -> int:
        """Heuristic complexity 1-10."""
        base = {"analysis": 7, "research": 6, "communication": 4, "scheduling": 5, "general": 5}.get(task_type, 5)
        input_len = len(context.get("input", ""))
        if input_len > 500:
            base += 2
        elif input_len > 200:
            base += 1
        return min(base, 10)

    def _count_recent_failures(self, context: Dict[str, Any]) -> int:
        return len(context.get("recent_failures", []))

    def _map_mode_to_depth(self, mode: str) -> int:
        return {
            FAST_EXECUTION_MODE: 2,
            DEEP_REASONING_MODE: 5,
            EXPLORATION_MODE: 4,
            DEBUG_MODE: 5,
            SAFE_MODE: 3,
        }.get(mode, 3)

    def _estimate_duration(self, mode: str, complexity: int) -> float:
        base = {
            FAST_EXECUTION_MODE: 1000,
            DEEP_REASONING_MODE: 5000,
            EXPLORATION_MODE: 3000,
            DEBUG_MODE: 4000,
            SAFE_MODE: 2000,
        }.get(mode, 2000)
        return base + complexity * 200