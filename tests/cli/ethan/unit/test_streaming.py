"""Tests for cli/core/streaming.py — streaming output."""
from __future__ import annotations

from unittest import mock

import pytest


class TestStreamer:
    """Streamer class tests."""

    def test_streamer_init(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        assert streamer.text == ""
        assert not streamer._cancelled

    def test_streamer_start(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start("Thinking...")
        assert "Thinking..." in streamer.text
        streamer.done()

    def test_streamer_write(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start()
        streamer.write("Hello")
        assert "Hello" in streamer.text
        streamer.done()

    def test_streamer_write_multiple(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start()
        streamer.write("Hello ")
        streamer.write("World")
        assert streamer.text == "Hello World"
        streamer.done()

    def test_streamer_done(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start("test")
        streamer.done()

    def test_streamer_cancel(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start("test")
        streamer.cancel()
        assert streamer._cancelled

    def test_streamer_write_after_cancel(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start()
        streamer.cancel()
        initial_text = streamer.text
        streamer.write("Should not appear")
        assert streamer.text == initial_text  # should not change

    def test_streamer_fallback(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start("test")
        streamer.fallback("Something went wrong")

    def test_streamer_start_time_recorded(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start()
        assert streamer._start_time > 0
        streamer.done()