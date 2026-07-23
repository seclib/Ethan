"""Tests for cli/core/loading.py — spinner, step progress, thinker."""
from __future__ import annotations

import time
from unittest import mock

import pytest


class TestSpinner:
    """Spinner class tests."""

    def test_spinner_init_default(self) -> None:
        from cli.core.loading import Spinner
        spinner = Spinner()
        assert spinner.style == "dots"
        assert not spinner._running

    def test_spinner_init_custom_style(self) -> None:
        from cli.core.loading import Spinner
        spinner = Spinner("arrow")
        assert spinner.style == "arrow"

    def test_spinner_start_stop(self) -> None:
        from cli.core.loading import Spinner
        spinner = Spinner()
        spinner.start("Loading...")
        assert spinner._running
        spinner.stop()
        assert not spinner._running

    def test_spinner_cancel(self) -> None:
        from cli.core.loading import Spinner
        spinner = Spinner()
        spinner.start("Working...")
        spinner.cancel()
        assert not spinner._running

    def test_spinner_styles_available(self) -> None:
        from cli.core.loading import Spinner
        assert "dots" in Spinner.STYLES
        assert "arrow" in Spinner.STYLES
        assert "bounce" in Spinner.STYLES
        assert "line" in Spinner.STYLES
        assert "pulse" in Spinner.STYLES

    def test_spinner_thread_lifecycle(self) -> None:
        from cli.core.loading import Spinner
        spinner = Spinner()
        spinner.start("test")
        assert spinner._thread is not None
        assert spinner._thread.is_alive()
        spinner.stop()
        # Thread should be finished after stop
        assert not spinner._running


class TestStepProgress:
    """StepProgress class tests."""

    def test_step_progress_init(self) -> None:
        from cli.core.loading import StepProgress
        sp = StepProgress()
        assert sp._current == 0

    def test_step_progress_begin(self) -> None:
        from cli.core.loading import StepProgress
        sp = StepProgress()
        sp.begin("Deploying", total=3)
        assert sp._current == 0

    def test_step_progress_step(self) -> None:
        from cli.core.loading import StepProgress
        sp = StepProgress()
        sp.begin("Deploying", total=3)
        sp.step("Building...")
        assert sp._current == 0  # step only increments on spinner stop

    def test_step_progress_complete(self) -> None:
        from cli.core.loading import StepProgress
        sp = StepProgress()
        sp.begin("Deploying", total=1)
        sp.complete("Deployed successfully")

    def test_step_progress_fail(self) -> None:
        from cli.core.loading import StepProgress
        sp = StepProgress()
        sp.fail("Deployment failed")


class TestThinker:
    """Thinker class tests."""

    def test_thinker_init(self) -> None:
        from cli.core.loading import Thinker
        thinker = Thinker()
        assert thinker._phase == ""

    def test_thinker_begin_done(self) -> None:
        from cli.core.loading import Thinker
        thinker = Thinker()
        thinker.begin("Planning")
        assert thinker._phase == "Planning"
        thinker.done()

    def test_thinker_update(self) -> None:
        from cli.core.loading import Thinker
        thinker = Thinker()
        thinker.begin("Planning")
        thinker.update("Executing")
        assert thinker._phase == "Executing"
        thinker.done()

    def test_thinker_cancel(self) -> None:
        from cli.core.loading import Thinker
        thinker = Thinker()
        thinker.begin("Planning")
        thinker.cancel()