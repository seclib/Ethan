"""Tests for ETHAN CLI streaming module — concurrency safety."""

import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))


def test_streamer_init():
    from cli.core.streaming import Streamer
    s = Streamer()
    assert s is not None
    assert s.text == ""
    assert s._cancelled is False


def test_streamer_write():
    from cli.core.streaming import Streamer
    s = Streamer()
    s.start("test")
    s.write(" chunk 1")
    assert "test" in s.text
    s.done()


def test_streamer_cancel():
    from cli.core.streaming import Streamer
    s = Streamer()
    s.start("processing")
    s.cancel()
    assert s._cancelled is True
    assert "[cancelled]" in s.text


def test_streamer_fallback():
    from cli.core.streaming import Streamer
    s = Streamer()
    s.start("thinking")
    s.fallback("connection lost")
    s.done()


def test_streamer_concurrent_writes():
    """Test thread safety: multiple writes from different threads."""
    from cli.core.streaming import Streamer
    s = Streamer()
    s.start("concurrent")

    def writer(n):
        for _ in range(10):
            s.write(f" {n}")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=1.0)

    assert len(s.text) > 10, f"Expected accumulated text, got '{s.text}'"
    s.done()


def test_streamer_lock_is_used():
    """Verify that Streamer uses a threading.Lock."""
    from cli.core.streaming import Streamer
    s = Streamer()
    assert s._lock is not None
    # threading.Lock() returns a lock object; check by type name
    assert type(s._lock).__name__ == "lock"


def test_streamer_multiple_start_stop():
    """Test that start/done can be called multiple times."""
    from cli.core.streaming import Streamer
    s = Streamer()
    for _ in range(3):
        s.start("cycle")
        time.sleep(0.01)
        s.done()
    assert s.text != ""


def test_streamer_stop_event():
    """Verify threading.Event is used for spinner stop."""
    from cli.core.streaming import Streamer
    s = Streamer()
    assert s._stop_event is not None
    assert isinstance(s._stop_event, threading.Event)