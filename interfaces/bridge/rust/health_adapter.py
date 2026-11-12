"""Adaptateur minimal Python vers le service Rust ethan-health.

Responsabilité unique : transporter l'appel HTTP et normaliser les erreurs.
Aucune logique métier ni état interne partagé.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class RustHealthError(Exception):
    """Erreur transport/parsing du service Rust."""


class RustHealthTimeout(RustHealthError):
    """Délai d'attente dépassé."""


class RustHealthUnavailable(RustHealthError):
    """Service inaccessible ou réponse non valide."""


@dataclass(frozen=True)
class RustHealthClient:
    base_url: str
    timeout: float = 2.0

    def _url(self, path: str) -> str:
        return self.base_url.rstrip("/") + path

    def get_health(self) -> dict[str, Any]:
        return self._get("/health")

    def get_diagnostics_version(self) -> dict[str, Any]:
        return self._get("/v1/diagnostics/version")

    def _get(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(self._url(path), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                headers = getattr(response, "headers", None)
                if headers is None:
                    get_charset = None
                else:
                    get_charset = getattr(headers, "get_content_charset", None)
                charset = get_charset() if callable(get_charset) else "utf-8"
                charset = charset or "utf-8"
                raw = response.read().decode(charset)
        except TimeoutError as exc:
            raise RustHealthTimeout(f"timeout calling {path}: {exc}") from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise RustHealthUnavailable(f"unavailable calling {path}: {reason}") from exc
        except OSError as exc:
            raise RustHealthUnavailable(f"transport error calling {path}: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RustHealthUnavailable(f"invalid JSON from {path}: {exc}") from exc

        if not isinstance(payload, dict):
            raise RustHealthUnavailable(f"invalid payload from {path}: expected object")
        return payload
