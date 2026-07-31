"""Logging Configuration — Configuration centralisée des logs.

Configure le logging pour :
- Format structuré (JSON)
- Niveaux configurables
- Rotation des fichiers
- Context (correlation_id, module)
"""

from __future__ import annotations

import logging

from core.telemetry.logger import JSONFormatter as StructuredFormatter
from core.telemetry.logger import TextFormatter as PlainFormatter
from core.telemetry.logger import setup_logging as _setup_logging


def setup_logging(
    level: str = "INFO",
    json_format: bool | None = None,
    log_file: str | None = None,
) -> None:
    """Configure le logging global.

    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        json_format: Utiliser le format JSON (ou laisser LOG_FORMAT décider)
        log_file: Chemin vers le fichier de log (optionnel)
    """
    _setup_logging(level, json_format=json_format, log_file=log_file)


def get_logger(name: str) -> logging.Logger:
    """Récupère un logger avec le nom donné."""
    return logging.getLogger(name)
