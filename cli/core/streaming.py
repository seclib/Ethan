"""ETHAN Streaming Output — smooth, flicker-free, cancellable.

Usage:
    from core.streaming import Streamer

    streamer = Streamer()
    streamer.start("Thinking...")
    for chunk in response:
        streamer.write(chunk)
    streamer.done()
"""

import sys
import time
import threading
from cli.core import colors as clr


class Streamer:
    """In-place streaming renderer with spinner, cancellation, and fallback."""

    def __init__(self):
        self.text = ""
        self._last_len = 0
        self._spinning = False
        self._spin_thread = None
        self._cancelled = False
        self._start_time = 0.0
        self._phase = 0
        self._lock = threading.Lock()

    def start(self, hint: str = "Thinking..."):
        """Begin stream. Shows initial line."""
        with self._lock:
            self._start_time = time.time()
            self._cancelled = False
            self._phase = 0
            self.text = ""
            self._last_len = 0
        self._start_spinner()
        self.write(hint)

    def write(self, chunk: str):
        """Append chunk and re-render."""
        if self._cancelled:
            return
        with self._lock:
            self.text += chunk
            display = self.text
        # Clear previous line
        sys.stdout.write("\r" + " " * self._last_len + "\r")
        # Write new text
        sys.stdout.write(display)
        self._last_len = len(display)
        sys.stdout.flush()

    def done(self):
        """Finalize stream."""
        self._stop_spinner()
        sys.stdout.write("\n")
        sys.stdout.flush()

    def cancel(self):
        """Cancel stream on user interrupt."""
        with self._lock:
            self._cancelled = True
        self._stop_spinner()
        # Clear and show cancelled state
        sys.stdout.write("\r" + " " * self._last_len + "\r")
        sys.stdout.flush()
        sys.stdout.write(f"{clr.PURPLE}{clr.I.DOT} ethan{C.RESET}  {clr.YELLOW}Cancelled{C.RESET}\n")
        sys.stdout.flush()
        self.text += " [cancelled]"

    def fallback(self, text: str):
        """If streaming fails, replace with static error."""
        self._stop_spinner()
        sys.stdout.write("\r" + " " * self._last_len + "\r")
        sys.stdout.flush()
        sys.stdout.write(f"{clr.RED}{clr.I.CROSS} Streaming failed{C.RESET}\n")
        sys.stdout.write(f"  {clr.DIM}{text}{clr.C.RESET}\n")
        sys.stdout.flush()
        sys.stdout.write(f"  {clr.CYAN}{clr.I.ARROW} Falling back to batch result{C.RESET}\n")
        sys.stdout.flush()

    def _start_spinner(self):
        if self._spin_thread is not None:
            return
        self._spinning = True
        self._spin_thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._spin_thread.start()

    def _stop_spinner(self):
        self._spinning = False
        self._spin_thread = None

    def _spin_loop(self):
        chars = clr.I.SPINNER
        while self._spinning:
            with self._lock:
                if self._cancelled:
                    break
                current = self.text
                last_len = self._last_len
            # Render spinner prefix
            sys.stdout.write("\r" + " " * last_len + "\r")
            sys.stdout.write(f"{clr.PURPLE}{chars[self._phase]} ethan{C.RESET}  ")
            self._phase = (self._phase + 1) % len(chars)
            sys.stdout.write(current)
            self._last_len = len(current)
            sys.stdout.flush()
            time.sleep(0.12)