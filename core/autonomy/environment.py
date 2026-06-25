"""Environment Analyzer — Observes external signals and system state."""

from __future__ import annotations

import logging
from typing import Any, Dict

from sdk.goals import GoalProposal, MAINTENANCE_GOAL, OPTIMIZATION_GOAL

logger = logging.getLogger(__name__)


class EnvironmentAnalyzer:
    """Generates goals from environment and system signals."""

    async def analyze(self, context: Dict[str, Any]) -> list:
        """Analyze system state and propose actionable goals."""
        proposals = []

        # System load signals
        load = context.get("system_load", 0.0)
        if load > 0.8:
            proposals.append(GoalProposal(
                goal_type=OPTIMIZATION_GOAL,
                title="Reduce system load",
                description=f"Investigate and reduce high load ({load:.0%})",
                target_domain="system",
                priority=0.9,
                estimated_effort="medium",
                expected_benefit="Stability improvement",
                source_signal="environment",
                context={"load": load},
            ))

        # Tool failure signals
        recent_tool_failures = context.get("recent_tool_failures", 0)
        if recent_tool_failures >= 2:
            proposals.append(GoalProposal(
                goal_type=MAINTENANCE_GOAL,
                title="Investigate tool failures",
                description=f"investigate {recent_tool_failures} recent tool failures",
                target_domain="tools",
                priority=0.8,
                estimated_effort="medium",
                expected_benefit="Reduce tool error rate",
                source_signal="failure",
                context={"failures": recent_tool_failures},
            ))

        logger.info(f"Environment analyzer generated {len(proposals)} proposals")
        return proposals