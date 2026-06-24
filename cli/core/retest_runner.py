"""Retest runner — re-run failed commands after fixes."""
import time
from dataclasses import dataclass


@dataclass
class RetestResult:
    """Result of retest attempt."""
    attempt: int
    exit_code: int
    success: bool
    timestamp: float


class RetestRunner:
    """Re-run command after auto-fix."""

    def __init__(self, original_argv, max_retries=1):
        self.original_argv = original_argv
        self.max_retries = max_retries
        self.attempts = 0
        self.history = []

    def should_retry(self, fix_recipe) -> bool:
        """Determine if retry is appropriate."""
        if not fix_recipe.retry:
            return False
        if self.attempts >= self.max_retries:
            return False
        return True

    def retry(self) -> RetestResult:
        """Re-run command. Returns result."""
        from cli.registry import dispatch

        delay = 0
        # Import here to avoid circular dependencies
        try:
            from cli.core.fix_map import FixRecipe
            if hasattr(self, '_current_recipe') and self._current_recipe:
                delay = self._current_recipe.retry_delay
        except Exception:
            pass

        if delay > 0:
            time.sleep(delay)

        self.attempts += 1
        try:
            exit_code = dispatch(self.original_argv)
        except SystemExit:
            exit_code = 0
        except Exception:
            exit_code = 1

        # Ensure int type (dispatch may return None)
        exit_code = int(exit_code) if exit_code is not None else 1

        result = RetestResult(
            attempt=self.attempts,
            exit_code=exit_code,
            success=(exit_code == 0),
            timestamp=time.time(),
        )
        self.history.append(result)
        return result

    def set_recipe(self, recipe):
        """Set current fix recipe for delay calculation."""
        self._current_recipe = recipe