"""Authentification NATS — token partagé serveur ↔ clients (CTO P0-3).

Le serveur exige ``authorization { token: $NATS_TOKEN }``
(``infrastructure/nats/nats-server.conf``). Tout client doit donc fournir le
même token : cette fabrique centralise les options de connexion pour que
**aucun** point de connexion n'oublie l'authentification (Red Team — Attaque
« spoofing d'événements NATS »).

Le token vit uniquement dans l'environnement (``NATS_TOKEN``, non versionné)
— jamais dans le code, les logs ou les événements.
"""

from __future__ import annotations

import os

ENV_NATS_TOKEN = "NATS_TOKEN"

# Longueur minimale recommandée pour un token de bus (documentation).
MIN_TOKEN_LENGTH = 16


def nats_token() -> str | None:
    """Retourne le token NATS de l'environnement, ou ``None`` si absent."""
    token = os.getenv(ENV_NATS_TOKEN, "").strip()
    return token or None


def nats_connect_options() -> dict[str, str]:
    """Options ``nats.connect`` pour l'authentification.

    Retourne ``{"token": ...}`` si ``NATS_TOKEN`` est défini, sinon ``{}``
    (mode sans auth — serveur lui-même sans auth, ex. environnement isolé).
    """
    token = nats_token()
    return {"token": token} if token else {}
