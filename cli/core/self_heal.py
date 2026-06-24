"""Self-healing engine — automated fix patchers."""
import os
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatchResult:
    """Result of patch application."""
    success: bool
    message: str


class SelfHealer:
    """Execute safe automated fixes for known issues."""

    PATCHERS = {
        "daemon_start": "_start_daemon",
        "daemon_restart": "_restart_daemon",
        "config_reset": "_reset_config",
        "increase_timeout": "_increase_timeout",
    }

    def apply(self, patch_name: str, context: dict) -> PatchResult:
        """Apply named patch. Returns success/failure."""
        patcher_name = self.PATCHERS.get(patch_name)
        if not patcher_name:
            return PatchResult(success=False, message="No auto-patch available")

        patcher = getattr(self, patcher_name, None)
        if not patcher:
            return PatchResult(success=False, message="Patch implementation not found")

        try:
            message = patcher(context)
            return PatchResult(success=True, message=message)
        except Exception as e:
            return PatchResult(success=False, message=str(e))

    @staticmethod
    def _start_daemon(context: dict) -> str:
        """Auto-start daemon if not running."""
        try:
            from cli.core import daemon as daemon_core

            daemon_core.cmd_start([])
            time.sleep(1)
            return "Daemon started"
        except Exception as e:
            raise RuntimeError(f"Failed to start daemon: {e}")

    @staticmethod
    def _restart_daemon(context: dict) -> str:
        """Restart daemon."""
        try:
            from cli.core import daemon as daemon_core

            daemon_core.cmd_stop([])
            time.sleep(0.5)
            daemon_core.cmd_start([])
            return "Daemon restarted"
        except Exception as e:
            raise RuntimeError(f"Failed to restart daemon: {e}")

    @staticmethod
    def _reset_config(context: dict) -> str:
        """Reset config to defaults."""
        try:
            from cli.core import config as cfg

            cfg.reset()
            return "Config reset to defaults"
        except Exception as e:
            raise RuntimeError(f"Failed to reset config: {e}")

    @staticmethod
    def _increase_timeout(context: dict) -> str:
        """Temporarily increase timeout."""
        current = os.environ.get("ETHAN_API_TIMEOUT", "5")
        try:
            new_timeout = max(int(current) * 2, 30)
            os.environ["ETHAN_API_TIMEOUT"] = str(new_timeout)
            return f"Timeout increased to {new_timeout}s"
        except Exception as e:
            raise RuntimeError(f"Failed to increase timeout: {e}")