"""Structured logging for the Cognitive Kernel.

Supports three modes:
- JSON (LOG_FORMAT=json): Machine-parseable, for log aggregation.
- TEXT (LOG_FORMAT=text, default): Human-readable, for `docker logs` and development.
- DUAL (LOG_FORMAT=dual): JSON on stdout and human-readable text on stderr.

Docker uses json-file driver by default, which captures raw stdout lines.
JSON-in-JSON is hard to read in `docker logs`, so TEXT is the default.
"""

import json
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Logging formatter that outputs JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "kernel"),
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        if hasattr(record, "goal_id"):
            log_entry["goal_id"] = record.goal_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """Human-readable colored formatter for terminal/docker logs."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        base = f"{ts} {color}{record.levelname:8s}{self.RESET} [{record.name}] {record.getMessage()}"
        if record.exc_info and record.exc_info[0]:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(
    level: str = "INFO",
    json_format: bool | None = None,
    log_file: str | None = None,
) -> None:
    """Configure the canonical ETHAN logger.

    ``LOG_FORMAT=json`` emits structured JSON, ``text`` emits a human-readable
    line, and ``dual`` emits JSON on stdout plus human-readable lines on
    stderr. ``json_format`` remains supported for older callers.
    """
    if json_format is None:
        log_format = os.getenv("LOG_FORMAT", "text").lower()
    else:
        log_format = "json" if json_format else "text"
    if log_format not in {"json", "text", "human", "dual"}:
        raise ValueError("LOG_FORMAT must be one of: json, text, human, dual")

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    if log_format in {"json", "dual"}:
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setFormatter(JSONFormatter())
        root.addHandler(json_handler)

    if log_format in {"text", "human", "dual"}:
        text_stream = sys.stderr if log_format == "dual" else sys.stdout
        text_handler = logging.StreamHandler(text_stream)
        text_handler.setFormatter(TextFormatter())
        root.addHandler(text_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setFormatter(
            JSONFormatter() if log_format in {"json", "dual"} else TextFormatter()
        )
        root.addHandler(file_handler)

    # Quiet noisy libs
    logging.getLogger("nats").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
