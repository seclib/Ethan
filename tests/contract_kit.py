"""Kit partagé des tests de contrat API (ADR-3006 / G-06).

Les contrats de surface (`tests/test_api_contract_p0.py`,
`tests/test_api_contract_domains.py`) partagent les mêmes invariants et les
mêmes outils d'introspection de l'application réelle (`interfaces.api.main`).
Ce module évite leur duplication :

- `resolve_path` : neutralise les paramètres de chemin pour appeler une route ;
- `declared_routes` / `duplicate_pairs` / `routes_sans_response_model` :
  lecture de la surface réellement exposée par l'application.

Aucune logique métier ici : le kit ne fait que **lire** la surface exposée.
"""

from __future__ import annotations

import os
import re
import secrets
from collections import Counter

# Fail-safe auto-suffisant : clé générée en mémoire (jamais en dur dans le
# code — règle "no secrets"), pour que l'import de l'app fonctionne même si
# l'hôte définit ETHAN_ENV=production sans JWT_SECRET.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

from interfaces.api.main import app  # noqa: E402

ROUTE_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def resolve_path(path: str) -> str:
    """Remplace les paramètres de chemin par un jeton inoffensif."""
    return re.sub(r"\{[^}]+\}", "x", path)


def declared_routes() -> set[tuple[str, str]]:
    """Routes réellement déclarées sur l'application (méthode, chemin)."""
    declared: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            if method in ROUTE_METHODS:
                declared.add((method, route.path))
    return declared


def duplicate_pairs() -> dict[tuple[str, str], int]:
    """Paires (méthode, chemin) déclarées plusieurs fois sur l'application."""
    pairs: list[tuple[str, str]] = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            if method not in ("HEAD", "OPTIONS"):
                pairs.append((method, route.path))
    return {pair: n for pair, n in Counter(pairs).items() if n > 1}


def routes_sans_response_model(routes: set[tuple[str, str]]) -> int:
    """Combien des routes données sont déclarées sans ``response_model``.

    Dette ADR-3006 mesurée : sert de garde-fou non bloquant (le compte ne
    peut que baisser — une hausse signal une nouvelle route sans schéma).
    """
    count = 0
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        if getattr(route, "response_model", None):
            continue
        if any((method, route.path) in routes for method in methods if method in ROUTE_METHODS):
            count += 1
    return count
