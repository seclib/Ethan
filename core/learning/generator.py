"""Rule Generator — Creates structured improvement proposals from patterns."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.learning import Pattern, RuleProposal

logger = logging.getLogger(__name__)


class RuleGenerator:
    """Generates rule proposals from detected patterns."""

    async def propose(self, pattern: Pattern) -> RuleProposal:
        """Generate a rule proposal from a pattern."""
        if pattern.pattern_type == "failure_repeat":
            return self._propose_failure_fix(pattern)
        elif pattern.pattern_type == "success_repeat":
            return self._propose_reinforce(pattern)
        elif pattern.pattern_type == "inefficiency":
            return self._propose_optimization(pattern)
        else:
            return self._propose_generic(pattern)

    def _propose_failure_fix(self, pattern: Pattern) -> RuleProposal:
        """Propose fix for repeated failures."""
        return RuleProposal(
            rule_type="reliability_improvement",
            condition=f"skill='{pattern.skill}' AND failure_count>={pattern.frequency}",
            suggestion=f"Increase retry limit for {pattern.skill} or add fallback handler",
            target_module=pattern.skill,
            confidence=min(0.5 + pattern.frequency * 0.1, 0.95),
            based_on_pattern_id=pattern.pattern_id,
        )

    def _propose_reinforce(self, pattern: Pattern) -> RuleProposal:
        """Propose reinforcing a successful pattern."""
        return RuleProposal(
            rule_type="capability_enhancement",
            condition=f"skill='{pattern.skill}' AND success_rate>={pattern.success_rate}",
            suggestion=f"Use {pattern.skill} as default for similar tasks (success rate {pattern.success_rate:.0%})",
            target_module=pattern.skill,
            confidence=pattern.success_rate,
            based_on_pattern_id=pattern.pattern_id,
        )

    def _propose_optimization(self, pattern: Pattern) -> RuleProposal:
        """Propose optimization for slow skills."""
        return RuleProposal(
            rule_type="performance_tuning",
            condition=f"skill='{pattern.skill}' AND avg_duration_ms>{pattern.avg_duration_ms}",
            suggestion=f"Optimize {pattern.skill} — avg {pattern.avg_duration_ms:.0f}ms (target < 2000ms)",
            target_module=pattern.skill,
            confidence=0.7,
            based_on_pattern_id=pattern.pattern_id,
        )

    def _propose_generic(self, pattern: Pattern) -> RuleProposal:
        """Generic proposal for unknown pattern types."""
        return RuleProposal(
            rule_type="generic",
            condition=f"pattern_type='{pattern.pattern_type}'",
            suggestion=f"Review {pattern.skill} — detected {pattern.pattern_type}",
            target_module=pattern.skill,
            confidence=0.5,
            based_on_pattern_id=pattern.pattern_id,
        )