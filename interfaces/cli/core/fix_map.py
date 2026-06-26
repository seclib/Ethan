"""Fix map — known error-to-fix mappings."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FixRecipe:
    """Recipe for fixing a classified error."""
    suggestion: str
    auto_patch: Optional[str] = None
    retry: bool = False
    retry_delay: int = 0


class FixMap:
    """Database of known error → fix mappings."""

    FIXES = {
        "IMPORT-ERR": {
            "suggest": "Check if module is installed: pip install <module>",
            "auto_patch": None,
            "retry": False,
            "retry_delay": 0,
        },
        "REGISTRY-ERR": {
            "suggest": "Check command spelling: ethan --help",
            "auto_patch": None,
            "retry": False,
            "retry_delay": 0,
        },
        "API-ERR": {
            "suggest": "Start the daemon: ethan daemon start",
            "auto_patch": "daemon_start",
            "retry": True,
            "retry_delay": 2,
        },
        "TIMEOUT-ERR": {
            "suggest": "Increase timeout: ETHAN_API_TIMEOUT=30 ethan <cmd>",
            "auto_patch": "increase_timeout",
            "retry": True,
            "retry_delay": 1,
        },
        "CONFIG-ERR": {
            "suggest": "Reset config: ethan config reset",
            "auto_patch": "config_reset",
            "retry": True,
            "retry_delay": 0,
        },
        "PERM-ERR": {
            "suggest": "Check permissions or run with sudo",
            "auto_patch": None,
            "retry": False,
            "retry_delay": 0,
        },
        "DAEMON-ERR": {
            "suggest": "Restart daemon: ethan daemon stop && ethan daemon start",
            "auto_patch": "daemon_restart",
            "retry": True,
            "retry_delay": 2,
        },
        "SYS-ERR": {
            "suggest": "Try: ethan --help or report issue",
            "auto_patch": None,
            "retry": False,
            "retry_delay": 0,
        },
        "UNKNOWN": {
            "suggest": "Try: ethan --help for available commands",
            "auto_patch": None,
            "retry": False,
            "retry_delay": 0,
        },
    }

    def lookup(self, classification) -> FixRecipe:
        """Return fix recipe for error classification."""
        fix = self.FIXES.get(classification.code)
        if not fix:
            return FixRecipe(
                suggestion="Try: ethan --help",
                auto_patch=None,
                retry=False,
                retry_delay=0,
            )
        return FixRecipe(
            suggestion=fix.get("suggest", ""),
            auto_patch=fix.get("auto_patch"),
            retry=fix.get("retry", False),
            retry_delay=fix.get("retry_delay", 0),
        )
