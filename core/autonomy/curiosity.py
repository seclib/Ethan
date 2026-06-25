"""Curiosity Engine — Detects unknown areas and knowledge gaps."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.goals import GoalProposal, EXPLORATION_GOAL

logger = logging.getLogger(__name__)


class CuriosityEngine:
    """Generates exploration goals from knowledge gaps."""

    async def detect_gaps(self, context: Dict[str, Any]) -> List[GoalProposal]:
        """Identify areas with low coverage or unknowns."""
        proposals = []

        # Example: detect untested skills
        skills_tested = context.get("skills_tested", [])
        all_skills = context.get("all_skills", [])
        for skill in all_skills:
            if skill not in skills_tested:
                proposals.append(GoalProposal(
                    goal_type=EXPLORATION_GOAL,
                    title=f"Explore {skill}",
                    description=f"Test and learn {skill} capabilities",
                    target_domain=skill,
                    priority=0.6,
                    estimated_effort="medium",
                    expected_benefit=f"Expand coverage for {skill}",
                    source_signal="curiosity",
                    context={"skill": skill},
                ))

        # Example: detect missing tool coverage
        tools_used = context.get("tools_used", [])
        all_tools = context.get("all_tools", [])
        for tool in all_tools:
            if tool not in tools_used:
                proposals.append(GoalProposal(
                    goal_type=EXPLORATION_GOAL,
                    title=f"Test tool {tool}",
                    description=f"Evaluate tool {tool} effectiveness",
                    target_domain=tool,
                    priority=0.5,
                    estimated_effort="low",
                    expected_benefit=f"Tool coverage: {tool}",
                    source_signal="curiosity",
                    context={"tool": tool},
                ))

        logger.info(f"Curiosity detected {len(proposals)} gaps")
        return proposals