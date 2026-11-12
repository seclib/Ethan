"""Log Pipeline — collecte, stockage et exposition des logs de Kernel.

La pipeline est :
    sources (stdlib, async, 3rd-party) → LogService → stockage (fichier/Redis) → exposition (API)

Le service unique de collecte et de filtrage, utilisé par le router logs et
par les dashboards WebUI/CLI.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class LogService:
    """Service de collecte et d'exposition des logs Kernel.

    Mémoire tampon circulaire (default 10 000 entrées) + filtres par
    niveau et module. Le stockage persistant est délégué au backend
    propre (fichier JSONL, Redis Streams ou PostgreSQL) si configuré.
    """

    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

    def __init__(self, capacity: int = 10_000) -> None:
        self._capacity = capacity
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self._backend: dict[str, Any] | None = None

    def set_backend(self, backend: dict[str, Any] | None) -> None:
        """Injecte un backend de persistance optionnel."""
        self._backend = backend

    def _emit(self, record: logging.LogRecord) -> dict[str, Any]:
        """Construit un dictionnaire de log standardisé."""
        levelname = record.levelname
        level_value = self.LEVELS.get(levelname, 50)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": levelname,
            "level_value": level_value,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
            "line": record.lineno,
            "thread": record.thread,
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self._format_exception(record.exc_info)
        if record.funcName:
            entry["function"] = record.funcName
        return entry

    def _format_exception(self, exc_info: tuple) -> str:
        import traceback

        return "\n".join(traceback.format_exception(*exc_info))

    def record(self, record: logging.LogRecord) -> dict[str, Any]:
        """Capture un log et l'ajoute à la mémoire tampon."""
        entry = self._emit(record)
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) > self._capacity:
                self._buffer.pop(0)
        logger.debug("LogPipeline: record %d, level=%s", len(self._buffer), entry["level"])
        return entry

    async def list(self, level: str | None = None, module: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Renvoie les logs récents filtrés."""
        with self._lock:
            entries = list(self._buffer)[-limit:]
        if level:
            entries = [e for e in entries if e.get("level") == level.upper()]
        if module:
            entries = [e for e in entries if e.get("module") == module]
        return entries

    async def count(self) -> dict[str, int]:
        """Retourne le nombre de logs par niveau."""
        counts: dict[str, int] = defaultdict(int)
        with self._lock:
            for e in self._buffer:
                counts[e.get("level", "UNKNOWN")] += 1
        return dict(counts)

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()



class LogServiceHandler(logging.Handler):
    """Handler de logging standard qui redirige vers LogService."""

    def __init__(self, log_service: 'LogService', level: int = logging.DEBUG) -> None:
        super().__init__(level=level)
        self._log_service = log_service

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._log_service._handle_stdlib(record)
        except Exception:
            self.handleError(record)


def install_log_bridge(log_service: 'LogService', name: str = 'ethan') -> logging.Handler:
    """Active l'ascenseur de logs stdlib -> LogService pour la racine."""
    handler = LogServiceHandler(log_service)
    root = logging.getLogger(name)
    root.addHandler(handler)
    root.setLevel(min(root.level, logging.DEBUG))
    return handler
