"""Debug trap — capture command execution for self-healing."""
import time
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


class DebugTrap:
    """Wraps command execution to capture failures."""

    def __init__(self, command_fn, argv):
        self.command_fn = command_fn
        self.argv = argv
        self.exit_code = None
        self.stdout = []
        self.stderr = []
        self.exception = None
        self.duration_ms = 0

    def execute(self):
        """Run command and capture all output."""
        t0 = time.time()
        stdout_buf = StringIO()
        stderr_buf = StringIO()

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                self.exit_code = self.command_fn(self.argv)
        except Exception as e:
            self.exception = e
            self.exit_code = 1
        self.duration_ms = int((time.time() - t0) * 1000)

        self.stdout = stdout_buf.getvalue().splitlines()
        self.stderr = stderr_buf.getvalue().splitlines()
        return self.exit_code

    def should_heal(self) -> bool:
        """Determine if this failure is healable."""
        return self.exit_code != 0 and self.exception is not None

    def get_context(self) -> dict:
        """Return execution context for patcher."""
        return {
            "argv": self.argv,
            "exit_code": self.exit_code,
            "exception": str(self.exception) if self.exception else None,
            "duration_ms": self.duration_ms,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }