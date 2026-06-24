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
    """In-place streaming renderer with spinner, cancellation, and fallback.

    Thread-safe: all stdout writes are serialized through a single lock.
    The spinner thread and write() calls never race on _last_len.
    """

    def __init__(self):
        self.text = ""
        self._last_len = 0
        self._spinning = False
        self._spin_thread = None
        self._stop_event = threading.Event()
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
            self._stop_event.clear()
        self._start_spinner()
        self.write(hint)

    def _render(self, text: str):
        """Thread-safe render: clear previous, write new, update length.

        Must be called with self._lock held.
        """
        sys.stdout.write("\r" + " " * self._last_len + "\r")
        sys.stdout.write(text)
        self._last_len = len(text)
        sys.stdout.flush()

    def write(self, chunk: str):
        """Append chunk and re-render."""
        if self._cancelled:
            return
        with self._lock:
            self.text += chunk
            self._render(self.text)

    def done(self):
        """Finalize stream."""
        self._stop_spinner()
        with self._lock:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def cancel(self):
        """Cancel stream on user interrupt."""
        self._stop_spinner()
        with self._lock:
            self._cancelled = True
            sys.stdout.write("\r" + " " * self._last_len + "\r")
            sys.stdout.flush()
            sys.stdout.write(f"{clr.C.PURPLE}{clr.I.DOT} ethan{clr.C.RESET}  {clr.C.YELLOW}Cancelled{clr.C.RESET}\n")
            sys.stdout.flush()
            self.text += " [cancelled]"

    def fallback(self, text: str):
        """If streaming fails, replace with static error."""
        self._stop_spinner()
        with self._lock:
            sys.stdout.write("\r" + " " * self._last_len + "\r")
            sys.stdout.flush()
            sys.stdout.write(f"{clr.C.RED}{clr.I.CROSS} Streaming failed{clr.C.RESET}\n")
            sys.stdout.write(f"  {clr.C.DIM}{text}{clr.C.RESET}\n")
            sys.stdout.flush()
            sys.stdout.write(f"  {clr.C.CYAN}{clr.I.ARROW} Falling back to batch result{clr.C.RESET}\n")
            sys.stdout.flush()

    def _start_spinner(self):
        if self._spin_thread is not None and self._spin_thread.is_alive():
            return
        self._spinning = True
        self._stop_event.clear()
        self._spin_thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._spin_thread.start()

    def _stop_spinner(self):
        self._spinning = False
        self._stop_event.set()
        self._spin_thread = None

    def _spin_loop(self):
        """Spinner animation loop with exception safety."""
        chars = clr.I.SPINNER
        try:
            while not self._stop_event.is_set() and self._spinning:
                with self._lock:
                    if self._cancelled:
                        break
                    current = self.text
                    last_len = self._last_len
                    phase = self._phase
                    self._phase = (self._phase + 1) % len(chars)
                # Render spinner prefix atomically
                line = f"{clr.C.PURPLE}{chars[phase]} ethan{clr.C.RESET}  {current}"
                with self._lock:
                    sys.stdout.write("\r" + " " * last_len + "\r")
                    sys.stdout.write(line)
                    self._last_len = len(line)
                    sys.stdout.flush()
                time.sleep(0.12)
        except Exception:
            # Silently recover — spinner is non-critical
            pass