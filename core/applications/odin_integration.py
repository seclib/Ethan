"""Odin pilot integration preparation (MEM-014 Phase 16)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import yaml

from core.applications.application_registry import ApplicationIntegrationRegistry, ApplicationRecord
from core.applications.models import ApplicationManifest


ODIN_MANIFEST_PATH = Path("examples/odin/ethan-application-manifest.yaml")
ODIN_CONTROL_CAPABILITIES = (
    "application.health.read",
    "application.lifecycle.read",
    "application.logs.read",
    "application.control.start",
    "application.control.stop",
    "application.control.restart",
)


def load_odin_manifest(path: Path | str = ODIN_MANIFEST_PATH) -> dict[str, Any]:
    resolved = Path(path)
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("Odin manifest must be a YAML mapping")
    return dict(data)


def register_odin_pilot(
    registry: ApplicationIntegrationRegistry,
    *,
    manifest_path: Path | str = ODIN_MANIFEST_PATH,
    emit_event: bool = False,
) -> ApplicationRecord:
    """Register Odin as a pilot application without launching it.

    This function only validates and records metadata. It does not execute
    Docker or any Odin lifecycle operation.
    """
    data = load_odin_manifest(manifest_path)
    record = registry.register(data, emit_event=emit_event)
    if record.app_id != "odin":
        raise ValueError("registered Odin manifest has an unexpected app_id")
    declared = set(record.capabilities)
    missing = set(ODIN_CONTROL_CAPABILITIES) - declared
    if missing:
        raise ValueError("Odin manifest is missing capabilities: " + ", ".join(sorted(missing)))
    return record


def odin_capability_matrix() -> list[dict[str, str]]:
    return [
        {"capability": capability, "execution": "not automatically available"}
        for capability in ODIN_CONTROL_CAPABILITIES
    ]


__all__ = [
    "ODIN_CONTROL_CAPABILITIES",
    "ODIN_MANIFEST_PATH",
    "load_odin_manifest",
    "odin_capability_matrix",
    "register_odin_pilot",
]
