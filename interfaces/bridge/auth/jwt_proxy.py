"""Proxy JWT Open WebUI → ETHAN.

Transmet le token JWT ETHAN dans les requêtes vers l'API Gateway.
Open WebUI n'a pas sa propre gestion d'authentification pour le bridge :
elle délègue entièrement à ETHAN Core.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from interfaces.api.auth import verify_token_string

security = HTTPBearer(auto_error=False)


async def extract_ethan_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> str | None:
    """Extrait le token JWT ETHAN depuis la requête Open WebUI.

    Retourne None si aucun token n'est présent (accès anonyme autorisé
    selon la configuration ETHAN).
    """
    if credentials is not None:
        return credentials.credentials

    # Fallback : chercher dans les headers personnalisés Open WebUI
    token = request.headers.get("X-Ethan-Token")
    if token:
        return token

    return None


async def verify_ethan_token(token: str | None) -> dict[str, Any] | None:
    """Vérifie un token JWT ETHAN.

    Retourne les claims du token ou None si invalide/absent.
    """
    if token is None:
        return None

    try:
        payload = verify_token_string(token)
        return payload if payload else None
    except Exception:  # noqa: BLE001 — token invalide → accès refusé
        return None