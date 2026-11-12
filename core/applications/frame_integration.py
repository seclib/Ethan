"""Frame pilot integration preparation (MEM-014 Phase 20)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import yaml

from core.applications.application_registry import ApplicationIntegrationRegistry, ApplicationRecord

FRAME_MANIFEST_PATH = Path("examples/frame/ethan-application-manifest.yaml")
FRAME_CONTROL_CAPABILITIES = (
    "application.health.read",
    "application.lifecycle.read",
    "application.logs.read",
    "application.control.start",
    "application.control.stop",
    "application.control.restart",
)


def load_frame_manifest(path: Path | str = FRAME_MANIFEST_PATH) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("Frame manifest must be a YAML mapping")
    return dict(data)


def register_frame_pilot(registry: ApplicationIntegrationRegistry, *, manifest_path: Path | str = FRAME_MANIFEST_PATH, emit_event: bool = False) -> ApplicationRecord:
    data = load_frame_manifest(manifest_path)
    record = registry.register(data, emit_event=emit_event)
    if record.app_id != "frame":
        raise ValueError("registered Frame manifest has an unexpected app_id")
    missing = set(FRAME_CONTROL_CAPABILITIES) - set(record.capabilities)
    if missing:
        raise ValueError("Frame manifest is missing capabilities: " + ", ".join(sorted(missing)))
    return record


__all__ = ["FRAME_CONTROL_CAPABILITIES", "FRAME_MANIFEST_PATH", "load_frame_manifest", "register_frame_pilot"]
