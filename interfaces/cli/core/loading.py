"""ETHAN Loading States — spinner, step-based progress, thinking indicator, cancellation.

Thread-safe: all spinner/thinker operations use threading.Event for clean shutdown.
No zombie threads: _run() catches exceptions, stop() uses Event + timeout.

Usage:
    from core.loading import Spinner, StepProgress, Thinker

    spinner = Spinner("dots")
    spinner.start("Loading...")
    time.sleep(1)
    spinner.stop()

    steps = StepProgress()
    steps.begin("Deploying", total=3)
    steps.step("Building...")
    steps.step("Pushing...")
    steps.complete("Deployed")

    thinker = Thinker()
    thinker.begin("Planning")
    thinker.update("Executing")
    thinker.done()
"""

import sys
import time
import threading
from interfaces.cli.core import colors as clr


class Spinner:
    """Animated spinner with hint text.

    Uses threading.Event for clean stop. _run() is wrapped in try/except
    so that an unhandled exception never leaves a zombie thread.
    """

    STYLES = {
        "dots": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
        "arrow": "←↖↑↗→↘↓↙",
        "bounce": "⠁⠂⠄⠠⠐⠈",
        "line": "-\\|/",
        "pulse": "●○○●○",
        "thinking": "🤔🤔🤔",
    }

    def __init__(self, style: str = "dots"):
        self.style = style
        self.frames = self.STYLES.get(style, self.STYLES["dots"])
        self._running = False
        self._thread = None
        self._phase = 0
        self._text = ""
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def start(self, hint: str = ""):
        """Start spinner animation."""
        if self._thread is not None and self._thread.is_alive():
            return
        with self._lock:
            self._text = hint
            self._running = True
            self._phase = 0
            self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop spinner and clear the line."""
        with self._lock:
            self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
            if self._thread.is_alive():
                # Thread still alive after timeout — detach (daemon=True)
                self._thread = None
        else:
            self._thread = None
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def cancel(self):
        """Stop and show cancellation message."""
        self.stop()
        sys.stdout.write(f"{clr.C.RED}{clr.I.CROSS} Cancelled{clr.C.RESET}\n")
        sys.stdout.flush()

    def _run(self):
        """Spinner loop with exception safety."""
        try:
            while not self._stop_event.is_set():
                with self._lock:
                    if not self._running:
                        break
                    text = self._text
                frame = self.frames[self._phase % len(self.frames)]
                sys.stdout.write(f"\r{clr.C.PURPLE}{frame}{clr.C.RESET}  {text}")
                sys.stdout.flush()
                self._phase += 1
                time.sleep(0.08)
        except Exception:
            # Silently recover — spinner is non-critical
            pass


class StepProgress:
    """Step-based sequential progress."""

    def __init__(self):
        self._steps = []
        self._current = 0
        self._start_times = []

    def begin(self, title: str, total: int):
        self._steps = [title]
        self._total = total
        self._current = 0
        self._start_times = []
        print()
        print(clr.section(title))

    def step(self, hint: str):
        s = Spinner("dots")
        s.start(hint)
        t0 = time.time()
        self._start_times.append(t0)
        try:
            # Step runs synchronously here; caller does actual work.
            # For async use, run work, then s.stop().
            pass
        finally:
            s.stop()
            dt = time.time() - t0
            self._current += 1
            print(f"  {clr.C.GREEN}{clr.I.CHECK} {hint}{clr.C.RESET}  ({dt:.1f}s)")

    def complete(self, title: str):
        print()
        print(f"  {clr.C.GREEN}{clr.I.CHECK} {title}{clr.C.RESET}")

    def fail(self, hint: str):
        print()
        print(f"  {clr.C.RED}{clr.I.CROSS} {hint}{clr.C.RESET}")


class Thinker:
    """Thinking indicator for LLM/planning phases.

    Uses its own Spinner internally. update() safely recreates the spinner
    thread if it has finished.
    """

    def __init__(self):
        self._phase = ""
        self._spinner = Spinner("dots")
        self._start = 0.0

    def begin(self, phase: str):
        self._phase = phase
        self._start = time.time()
        self._spinner.start(f"■ {phase}...")

    def update(self, phase: str):
        """Update the thinking phase label."""
        self._phase = phase
        # Stop previous spinner rendering
        self._spinner.stop()
        sys.stdout.write(f"\r  {clr.C.GREEN}✓{clr.C.RESET} {self._phase}...")
        sys.stdout.flush()
        time.sleep(0.05)
        # Start new spinner for next phase
        self._spinner = Spinner("dots")  # Fresh spinner (new thread)
        self._spinner.start(f"■ {phase}...")

    def done(self):
        self._spinner.stop()
        dt = time.time() - self._start
        sys.stdout.write(f"\r  {clr.C.GREEN}{clr.I.CHECK} {self._phase}...{clr.C.RESET}  ({dt:.1f}s)\n")
        sys.stdout.flush()

    def cancel(self):
        self._spinner.cancel()