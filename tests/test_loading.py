"""Tests for ETHAN CLI loading module — thread safety and spinner."""

import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))


def test_spinner_init():
    from cli.core.loading import Spinner
    s = Spinner("dots")
    assert s is not None
    assert s.style == "dots"


def test_spinner_start_stop():
    from cli.core.loading import Spinner
    s = Spinner("dots")
    s.start("testing")
    time.sleep(0.1)
    s.stop()
    assert s._running is False


def test_spinner_cancel():
    from cli.core.loading import Spinner
    s = Spinner("dots")
    s.start("testing")
    time.sleep(0.05)
    s.cancel()
    assert s._running is False


def test_spinner_stop_event():
    """Verify Spinner uses threading.Event."""
    from cli.core.loading import Spinner
    s = Spinner("dots")
    assert s._stop_event is not None
    assert isinstance(s._stop_event, threading.Event)


def test_spinner_multiple_stops():
    """Test that stop() can be called multiple times safely."""
    from cli.core.loading import Spinner
    s = Spinner("dots")
    s.start("test")
    s.stop()
    s.stop()  # second stop should not crash
    assert s._running is False


def test_spinner_restart():
    """Test that a spinner can be restarted after stop."""
    from cli.core.loading import Spinner
    s = Spinner("dots")
    s.start("first")
    time.sleep(0.05)
    s.stop()
    s.start("second")
    time.sleep(0.05)
    s.stop()
    assert s._running is False


def test_thinker_init():
    from cli.core.loading import Thinker
    t = Thinker()
    assert t is not None


def test_thinker_begin_update_done():
    from cli.core.loading import Thinker
    t = Thinker()
    t.begin("planning")
    time.sleep(0.05)
    t.update("executing")
    time.sleep(0.05)
    t.done()
    assert t._phase == "executing"


def test_thinker_cancel():
    from cli.core.loading import Thinker
    t = Thinker()
    t.begin("planning")
    time.sleep(0.05)
    t.cancel()
    assert t._spinner._running is False


def test_thinker_multiple_updates():
    """Test that update() can be called multiple times."""
    from cli.core.loading import Thinker
    t = Thinker()
    t.begin("phase1")
    for phase in ["phase2", "phase3", "phase4"]:
        time.sleep(0.02)
        t.update(phase)
    t.done()
    assert t._phase == "phase4"


def test_step_progress():
    from cli.core.loading import StepProgress
    sp = StepProgress()
    sp.begin("Deploying", total=3)
    sp.complete("Done")
    assert sp._current == 0


def test_spinner_exception_safety():
    """Verify that _run() doesn't crash on exceptions."""
    from cli.core.loading import Spinner
    s = Spinner("dots")
    s.start("test")
    # Force an exception by setting invalid frames
    s.frames = ""
    time.sleep(0.1)
    s.stop()
    assert s._running is False