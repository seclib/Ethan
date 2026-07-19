#!/usr/bin/env python3
"""Detect modules present in both core/ and legacy/ with the same name.

This helps plan the legacy -> core migration by listing which
submodules could be consolidated.

Usage:
    python scripts/audit_legacy_dupes.py
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _module_names(base: pathlib.Path) -> set[str]:
    """Return dotted module names under ``base`` (excluding __init__)."""
    names: set[str] = set()
    for path in base.rglob("*.py"):
        rel = path.relative_to(base)
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        names.add(".".join(parts))
    return names


def main() -> None:
    core = ROOT / "core"
    legacy = ROOT / "legacy"

    if not core.is_dir() or not legacy.is_dir():
        print("core/ or legacy/ missing")
        return

    core_mods = _module_names(core)
    legacy_mods = _module_names(legacy)

    dupes = sorted(core_mods & legacy_mods)

    print(f"core/    : {len(core_mods)} modules")
    print(f"legacy/  : {len(legacy_mods)} modules")
    print(f"overlap  : {len(dupes)} modules\n")

    if dupes:
        print("Modules present in BOTH (candidates for consolidation):")
        for d in dupes:
            print(f"  - {d}")
    else:
        print("No exact name overlaps found.")


if __name__ == "__main__":
    main()