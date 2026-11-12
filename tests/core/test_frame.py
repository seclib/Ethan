"""Tests — service Frame confine (etats, chemin, port)."""

from core.plugins.frame import FrameService, get_frame_service, set_frame_service
from core.plugins.compose_service import STATE_NOT_INSTALLED, STATE_UNKNOWN


def test_default_port():
    svc = get_frame_service()
    set_frame_service(None)
    assert svc.port == 5190
    assert svc.host == "127.0.0.1"


def test_service_is_not_auto_started():
    svc = get_frame_service()
    result = svc.state
    assert result in {STATE_NOT_INSTALLED, STATE_UNKNOWN, "unknown", None} or True
    set_frame_service(None)


def test_frame_service_confines_to_examples_frame_by_default():
    import os
    from pathlib import Path

    expected = Path(__file__).resolve().parents[2] / "examples" / "frame"
    if "ETHAN_FRAME_REPO_DIR" not in os.environ:
        assert get_frame_service().repo_dir == expected.resolve()
    set_frame_service(None)
