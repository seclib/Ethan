"""Helpers OAuth communs aux providers Connections (Core-owned)."""

from __future__ import annotations

import base64
import hashlib
import secrets as py_secrets
import time
from typing import Any

from core.integrations.connections.base import ConnectionError


def utc_now_iso() -> str:
    """Horodatage ISO-8601 UTC (même convention que ``core.integrations``)."""
    from datetime import datetime

    return datetime.utcnow().isoformat()


def epoch_in(seconds: int | None) -> float | None:
    """Convertit ``expires_in`` (s) en epoch absolu (``None`` si absent)."""
    return time.time() + seconds if seconds is not None else None


def basic_auth_header(client_id: str, client_secret: str) -> str:
    """Header HTTP Basic pour les providers qui l'exigent (Notion)."""
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode("ascii")


def decode_token_response(response: Any, service: str) -> dict[str, Any]:
    """Décode une réponse d'échange de token en dict JSON.

    Certains providers (GitHub sans ``Accept: application/json``) répondent
    en ``application/x-www-form-urlencoded`` : on décode les deux formats et
    on remonte une erreur explicite sinon (jamais de ``raise_for_status``
    silencieux avec perte du message du provider).
    """
    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        raise ConnectionError(f"{service} token exchange failed (HTTP {status})")
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    text = getattr(response, "text", "") or ""
    parsed: dict[str, Any] = {}
    for part in text.split("&"):
        if "=" in part:
            key, _, value = part.partition("=")
            parsed[key] = value
    if parsed:
        return parsed
    raise ConnectionError(f"{service} token exchange returned an unexpected payload")


def pkce_pair() -> tuple[str, str]:
    """Paire PKCE ``(code_verifier, code_challenge)`` (S256).

    Prête pour les providers qui l'exigent (Google/GitLab en mode strict).
    """
    verifier = py_secrets.token_urlsafe(64)[:128]
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .decode("ascii")
        .rstrip("=")
    )
    return verifier, challenge
