"""Quantar pilot readiness adapter (MEM-014 Phase 35 preparation)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import yaml

from core.applications.application_registry import ApplicationIntegrationRegistry, ApplicationRecord

QUANTAR_MANIFEST_PATH = Path("examples/quantar/ethan-application-manifest.yaml")
QUANTAR_CAPABILITIES = (
    "research-analysis",
    "reports",
)


def load_quantar_manifest(path: Path | str = QUANTAR_MANIFEST_PATH) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("Quantar manifest must be a YAML mapping")
    return dict(data)


def register_quantar_pilot(registry: ApplicationIntegrationRegistry, *, manifest_path: Path | str = QUANTAR_MANIFEST_PATH, emit_event: bool = False) -> ApplicationRecord:
    data = load_quantar_manifest(manifest_path)
    record = registry.register(data, emit_event=emit_event)
    if record.app_id != "quantar":
        raise ValueError("registered Quantar manifest has an unexpected app_id")
    missing = set(QUANTAR_CAPABILITIES) - set(record.capabilities)
    if missing:
        raise ValueError("Quantar manifest is missing capabilities: " + ", ".join(sorted(missing)))
    return record


__all__ = ["QUANTAR_CAPABILITIES", "QUANTAR_MANIFEST_PATH", "load_quantar_manifest", "register_quantar_pilot"]
