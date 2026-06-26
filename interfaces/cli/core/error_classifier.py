"""Error classifier — categorize failures into known patterns."""
import re
from dataclasses import dataclass


@dataclass
class ErrorClassification:
    """Result of error classification."""
    code: str
    severity: str
    healable: bool
    category: str
    match: str | None = None


class ErrorClassifier:
    """Classify errors into known fixable categories."""

    TAXONOMY = {
        # Code | Patterns | Severity | Healable
        "IMPORT-ERR": {
            "patterns": [r"No module named '(\w+)'", r"ModuleNotFoundError"],
            "severity": "HIGH",
            "healable": False,
            "category": "dependency",
        },
        "REGISTRY-ERR": {
            "patterns": [r"Unknown command: '(\w+)'", r"Unknown subcommand"],
            "severity": "LOW",
            "healable": False,
            "category": "input",
        },
        "API-ERR": {
            "patterns": [r"API unreachable", r"Connection refused", r"URLError"],
            "severity": "HIGH",
            "healable": True,
            "category": "network",
        },
        "TIMEOUT-ERR": {
            "patterns": [r"timed out", r"Timeout:"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "network",
        },
        "CONFIG-ERR": {
            "patterns": [r"config", r"JSONDecodeError", r"Corrupt"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "config",
        },
        "PERM-ERR": {
            "patterns": [r"Permission denied", r"PermissionError"],
            "severity": "HIGH",
            "healable": False,
            "category": "permission",
        },
        "DAEMON-ERR": {
            "patterns": [r"daemon", r"PID", r"process"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "service",
        },
        "SYS-ERR": {
            "patterns": [r"Unexpected error", r"SYS-999"],
            "severity": "HIGH",
            "healable": False,
            "category": "unknown",
        },
    }

    def classify(self, exception, stdout) -> ErrorClassification:
        """Return classification with matched pattern."""
        text = str(exception) + "\n" + "\n".join(stdout)
        for code, meta in self.TAXONOMY.items():
            for pattern in meta["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return ErrorClassification(
                        code=code,
                        severity=meta["severity"],
                        healable=meta["healable"],
                        category=meta["category"],
                        match=match.group(1) if match.groups() else None,
                    )
        return ErrorClassification(
            code="UNKNOWN", severity="LOW", healable=False, category="unknown"
        )