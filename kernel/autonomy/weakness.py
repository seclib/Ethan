"""Weakness Detector — Identifies low-performance domains from Self-Model."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.goals import GoalProposal, IMPROVEMENT_GOAL

logger = logging.getLogger(__name__)


class WeaknessDetector:
    """Generates improvement goals from self-model weaknesses."""

    async def detect(self, self_model: Dict[str, Any]) -> List[GoalProposal]:
        """Find skills below threshold and propose improvements."""
        proposals = []
        skills = self_model.get("skills", {})
        threshold = 0.4

        for skill, confidence in skills.items():
            if confidence < threshold:
                proposals.append(GoalProposal(
                    goal_type=IMPROVEMENT_GOAL,
                    title=f"Improve {skill}",
                    description=f"Boost {skill} from {confidence:.2f} to ≥{threshold}",
                    target_domain=skill,
                    priority=1.0 - confidence,
                    estimated_effort="high" if confidence < 0.2 else "medium",
                    expected_benefit=f"Reliability +{(threshold - confidence):.2f}",
                    source_signal="weakness",
                    context={"current_confidence": confidence, "target": threshold},
                ))

        logger.info(f"Weakness detector found {len(proposals)} low-performance domains")
        return proposals