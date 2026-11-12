"""Façade Python minimale vers le binaire Rust ethan-capability-contract.

Cette façade ne remplace pas le CapabilityManager. Elle envoie un snapshot
JSON et vérifie le contrat renvoyé par le noyau Rust.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _binary() -> str | None:
    candidates = [
        Path(__file__).resolve().parents[2] / "core" / "rust" / "ethan_capability_contract" / "target" / "debug" / "ethan-capability-contract",
        shutil.which("ethan-capability-contract"),
    ]
    for candidate in candidates:
        if candidate is not None and Path(candidate).is_file():
            return str(candidate)
    return None


def validate_contract(payload: str) -> dict[str, Any]:
    binary = _binary()
    if binary is None:
        return {"ok": False, "error": "binary_not_found"}
    proc = subprocess.run(
        [binary, "--validate-only"],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": "rust_binary_failed", "details": proc.stderr.strip()}
    try:
        return json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"ok": False, "error": "invalid_rust_output", "details": proc.stdout}


def detect_capabilities(payload: str):
    binary = _binary()
    if binary is None:
        return {"ok": False, "error": "binary_not_found"}
    proc = subprocess.run(
        [binary],
        input=payload,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": "rust_binary_failed", "details": proc.stderr.strip()}
    data = json.loads(proc.stdout)
    if isinstance(data, dict) and isinstance(data.get("detection"), list):
        return data
    return {"ok": False, "error": "invalid_detection_output", "details": proc.stdout}
