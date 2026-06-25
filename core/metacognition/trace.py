"""Thought Trace Analyzer — Analyzes reasoning chains."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.metacognition import ThoughtTrace

logger = logging.getLogger(__name__)


class ThoughtTraceAnalyzer:
    """Analyzes reasoning chains for inefficiencies."""

    async def analyze(self, trace: ThoughtTrace) -> ThoughtTrace:
        """Analyze a thought trace and annotate."""
        steps = trace.steps
        loops_detected = 0
        inefficiencies: List[str] = []

        visited_actions = []
        for i, step in enumerate(steps):
            action = step.get("action", "")
            if action in visited_actions:
                loops_detected += 1
                inefficiencies.append(f"Loop detected at step {i}: {action}")
            visited_actions.append(action)

        total_ms = trace.total_duration_ms
        if total_ms > 10000:
            inefficiencies.append(f"Slow trace: {total_ms:.0f}ms total")

        if len(steps) > 20:
            inefficiencies.append(f"Too many steps: {len(steps)}")

        trace.loops_detected = loops_detected
        trace.inefficiencies = inefficiencies
        trace.completed = True

        logger.debug(f"Trace analyzed: {loops_detected} loops, {len(inefficiencies)} issues")
        return trace