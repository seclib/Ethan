"""Spinner for terminal loading states.

Rotating indicator for operations < 5s.
"""

import sys
import time
import threading
from typing import Optional

SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]
ASCII_FRAMES = ["-", "\\", "|", "/"]


class Spinner:
    """Terminal spinner animation."""

    def __init__(self, hint: str = "Thinking..."):
        self.hint = hint
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frames = SPINNER_FRAMES if sys.stdout.isatty() else ASCII_FRAMES

    def start(self) -> None:
        """Start the spinner."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self) -> None:
        """Spinner animation loop."""
        idx = 0
        while self._running:
            frame = self._frames[idx % len(self._frames)]
            sys.stdout.write(f"\r  {frame} {self.hint}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def stop(self) -> None:
        """Stop the spinner and clear line."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.3)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def update(self, hint: str) -> None:
        """Update the spinner hint text."""
        self.hint = hint