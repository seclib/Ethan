"""Core — Human Root of Trust — Audit log append-only.

Stocke l'intégrité des décisions HROT.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AuditLog:
    """Audit append-only pour les décisions HROT."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path
        self._entries: list[dict[str, Any]] = []

    def record(self, entry: dict[str, Any]) -> None:
        entry = dict(entry)
        entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
        self._entries.append(entry)
        if self._path is not None:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(f"{entry}\n")
            except OSError:
                pass
        logger.info("HROT audit record #%d: %s", len(self._entries) - 1, entry.get("action_id"))

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)
