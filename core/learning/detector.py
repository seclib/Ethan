"""Pattern Detector — Finds failure/success patterns in experiences."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sdk.learning import Experience, Pattern

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects recurring patterns in experience stream."""

    def __init__(self, threshold: int = 3):
        self.threshold = threshold  # min occurrences to call it a pattern

    async def detect(self, experiences: List[Dict[str, Any]]) -> List[Pattern]:
        """Run all detectors and return patterns."""
        patterns: List[Pattern] = []

        patterns.extend(await self._detect_failure_repeats(experiences))
        patterns.extend(await self._detect_success_streaks(experiences))
        patterns.extend(await self._detect_inefficiencies(experiences))

        for p in patterns:
            logger.info(f"Pattern detected: {p.pattern_type} skill={p.skill} freq={p.frequency}")

        return patterns

    async def _detect_failure_repeats(self, experiences: List[Dict[str, Any]]) -> List[Pattern]:
        """Find skills with repeated failures."""
        skill_stats: Dict[str, Dict[str, Any]] = {}

        for exp in experiences:
            if exp.get("outcome") != "failure":
                continue
            skill = exp.get("skill_invoked", "unknown")
            stats = skill_stats.setdefault(skill, {"fails": 0, "total": 0, "durations": []})
            stats["fails"] += 1
            stats["total"] += 1
            stats["durations"].append(exp.get("duration_ms", 0))

        patterns = []
        for skill, stats in skill_stats.items():
            if stats["fails"] >= self.threshold:
                patterns.append(Pattern(
                    pattern_type="failure_repeat",
                    skill=skill,
                    frequency=stats["fails"],
                    avg_duration_ms=sum(stats["durations"]) / len(stats["durations"]),
                    success_rate=0.0,
                    details={"fail_count": stats["fails"], "total": stats["total"]},
                ))
        return patterns

    async def _detect_success_streaks(self, experiences: List[Dict[str, Any]]) -> List[Pattern]:
        """Find skills with high success rate."""
        skill_stats: Dict[str, Dict[str, Any]] = {}

        for exp in experiences:
            skill = exp.get("skill_invoked", "unknown")
            stats = skill_stats.setdefault(skill, {"success": 0, "total": 0, "durations": []})
            stats["total"] += 1
            if exp.get("outcome") == "success":
                stats["success"] += 1
            stats["durations"].append(exp.get("duration_ms", 0))

        patterns = []
        for skill, stats in skill_stats.items():
            if stats["total"] >= self.threshold:
                rate = stats["success"] / stats["total"]
                if rate >= 0.8:
                    patterns.append(Pattern(
                        pattern_type="success_repeat",
                        skill=skill,
                        frequency=stats["success"],
                        avg_duration_ms=sum(stats["durations"]) / len(stats["durations"]),
                        success_rate=rate,
                        details={"success_count": stats["success"], "total": stats["total"]},
                    ))
        return patterns

    async def _detect_inefficiencies(self, experiences: List[Dict[str, Any]]) -> List[Pattern]:
        """Find unusually slow or retried executions."""
        skill_stats: Dict[str, Dict[str, Any]] = {}

        for exp in experiences:
            skill = exp.get("skill_invoked", "unknown")
            stats = skill_stats.setdefault(skill, {"durations": []})
            stats["durations"].append(exp.get("duration_ms", 0))

        patterns = []
        for skill, stats in skill_stats.items():
            if not stats["durations"]:
                continue
            avg = sum(stats["durations"]) / len(stats["durations"])
            if avg > 5000:  # > 5 seconds
                patterns.append(Pattern(
                    pattern_type="inefficiency",
                    skill=skill,
                    frequency=len(stats["durations"]),
                    avg_duration_ms=avg,
                    success_rate=0.0,
                    details={"avg_ms": avg, "count": len(stats["durations"])},
                ))
        return patterns