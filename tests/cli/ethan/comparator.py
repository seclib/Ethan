"""Comparator — compare CLI outputs against golden snapshots."""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ComparisonResult:
    """Result of snapshot comparison."""
    passed: bool
    diff: str
    missing: List[str]
    extra: List[str]


class Comparator:
    """Compare CLI outputs against golden snapshots."""

    def __init__(
        self,
        tolerance_lines: int = 0,
        ignore_patterns: Optional[List[str]] = None
    ):
        self.tolerance_lines = tolerance_lines
        self.ignore_patterns = ignore_patterns or []

    def compare(
        self,
        actual: str,
        expected: str,
        context: str = ""
    ) -> ComparisonResult:
        """Compare actual vs expected output.

        Args:
            actual: Current command output (normalized)
            expected: Golden snapshot content
            context: Command context for error messages

        Returns:
            ComparisonResult with pass/fail and details
        """
        actual_lines = actual.split("\n")
        expected_lines = expected.split("\n")

        # Apply ignore patterns
        actual_filtered = self._apply_ignore_patterns(actual_lines)
        expected_filtered = self._apply_ignore_patterns(expected_lines)

        # Allow line count tolerance
        if self.tolerance_lines > 0:
            if abs(len(actual_filtered) - len(expected_filtered)) <= self.tolerance_lines:
                actual_filtered = self._align_lines(actual_filtered, expected_filtered)

        # Compute diff
        missing, extra = self._compute_diff(actual_filtered, expected_filtered)

        passed = len(missing) == 0 and len(extra) == 0

        diff_text = ""
        if not passed:
            diff_text = self._format_diff(missing, extra, context)

        return ComparisonResult(
            passed=passed,
            diff=diff_text,
            missing=missing,
            extra=extra,
        )

    def _apply_ignore_patterns(self, lines: List[str]) -> List[str]:
        """Remove lines matching ignore patterns."""
        filtered = []
        for line in lines:
            skip = False
            for pattern in self.ignore_patterns:
                if re.search(pattern, line):
                    skip = True
                    break
            if not skip:
                filtered.append(line)
        return filtered

    def _compute_diff(
        self,
        actual: List[str],
        expected: List[str]
    ) -> tuple[List[str], List[str]]:
        """Simple line-by-line diff."""
        actual_set = set(actual)
        expected_set = set(expected)

        missing = [line for line in expected if line not in actual_set]
        extra = [line for line in actual if line not in expected_set]

        return missing, extra

    def _format_diff(
        self,
        missing: List[str],
        extra: List[str],
        context: str
    ) -> str:
        """Format diff for human reading."""
        lines = [f"Diff for: {context}", ""]

        if missing:
            lines.append("Missing lines (expected but not found):")
            for line in missing:
                lines.append(f"  - {line}")

        if extra:
            lines.append("Extra lines (found but not expected):")
            for line in extra:
                lines.append(f"  + {line}")

        return "\n".join(lines)

    def _align_lines(self, actual: List[str], expected: List[str]) -> List[str]:
        """Truncate longer list to match shorter one."""
        min_len = min(len(actual), len(expected))
        return actual[:min_len]