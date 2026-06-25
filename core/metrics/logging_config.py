"""Logging Configuration — Configuration centralisée des logs.

Configure le logging pour :
- Format structuré (JSON)
- Niveaux configurables
- Rotation des fichiers
- Context (correlation_id, module)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Formateur de logs structuré (JSON)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajouter les champs extra
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Exception
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class PlainFormatter(logging.Formatter):
    """Formateur de logs simple (pour dev)."""

    def format(self, record: logging.LogRecord) -> str:
        return (
            f"{self.formatTime(record)} "
            f"[{record.levelname}] "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """Configure le logging global.

    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        json_format: Utiliser le format JSON
        log_file: Chemin vers le fichier de log (optionnel)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Supprimer les handlers existants
    root_logger.handlers.clear()

    # Formatter
    formatter = StructuredFormatter() if json_format else PlainFormatter()

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler fichier (optionnel)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Réduire le bruit des librairies tierces
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("nats").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Récupère un logger avec le nom donné."""
    return logging.getLogger(name)


# Import conditionnel pour RotatingFileHandler
try:
    from logging.handlers import RotatingFileHandler
except ImportError:
    pass