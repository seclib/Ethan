"""ETHAN Loading States — spinner, step-based progress, thinking indicator, cancellation.

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
from cli.core import colors as clr


class Spinner:
    """Animated spinner with hint text."""

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

    def start(self, hint: str = ""):
        with self._lock:
            self._text = hint
            self._running = True
            self._phase = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
            self._thread = None
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def cancel(self):
        self.stop()
        sys.stdout.write(f"{clr.C.RED}{clr.I.CROSS} Cancelled{clr.C.RESET}\n")
        sys.stdout.flush()

    def _run(self):
        while True:
            with self._lock:
                if not self._running:
                    break
                text = self._text
            frame = self.frames[self._phase % len(self.frames)]
            sys.stdout.write(f"\r{clr.C.PURPLE}{frame}{clr.C.RESET}  {text}")
            sys.stdout.flush()
            self._phase += 1
            time.sleep(0.08)


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
    """Thinking indicator for LLM/planning phases."""

    def __init__(self):
        self._phase = ""
        self._spinner = Spinner("dots")
        self._start = 0.0

    def begin(self, phase: str):
        self._phase = phase
        self._start = time.time()
        self._spinner.start(f"■ {phase}...")

    def update(self, phase: str):
        self._phase = phase
        self._spinner.stop()
        sys.stdout.write(f"\r  {clr.C.GREEN}✓{clr.C.RESET} {self._phase}...")
        sys.stdout.flush()
        time.sleep(0.05)
        self._spinner._text = f"■ {phase}..."
        self._spinner._running = True
        if not self._spinner._thread:
            self._spinner._thread = threading.Thread(target=self._spinner._run, daemon=True)
            self._spinner._thread.start()

    def done(self):
        self._spinner.stop()
        dt = time.time() - self._start
        sys.stdout.write(f"\r  {clr.C.GREEN}{clr.I.CHECK} {self._phase}...{clr.C.RESET}  ({dt:.1f}s)\n")
        sys.stdout.flush()

    def cancel(self):
        self._spinner.cancel()