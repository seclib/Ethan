"""Gates RBAC des extensions — MCP/tool servers, Skills, Plugins.

Principe (AGENTS.md + docs/security) : les extensions sont **non fiables par
défaut** ; toute permission est appliquée côté Core/API Gateway, jamais
uniquement dans l'interface.  Ce test verrouille la matrice
« route → permission » des surfaces d'extension : une route de mutation qui
perd son gate (retour à « simple utilisateur authentifié ») casse la CI.

Rappel : ``auth_middleware`` exige déjà un JWT valide sur toute route non
publique ; ces gates ajoutent l'**autorisation** (rôle → permission), ce qui
protège un ``viewer`` d'une escalade (par ex. transformer un serveur MCP en
commande locale, ou activer un plugin).
"""

from __future__ import annotations

import pytest
from core.auth import Permission, rbac
from routers import capabilities, v1


def _routes_of(router) -> list:
    """Routes FastAPI : accepte le module routeur (``.router``) ou l'APIRouter."""
    inner = getattr(router, "router", router)
    return list(getattr(inner, "routes") or [])


def _required_permissions(router, method: str, path: str) -> set[Permission]:
    """Permissions exigées par une route (lecture introspective des deps)."""
    for route in _routes_of(router):
        if getattr(route, "path", None) != path:
            continue
        if method.upper() not in {m.upper() for m in getattr(route, "methods", set())}:
            continue
        found: set[Permission] = set()
        for dep in getattr(route, "dependencies", []) or []:
            permission = getattr(getattr(dep, "dependency", None), "permission", None)
            if permission is not None:
                found.add(permission)
        dependant = getattr(route, "dependant", None)
        for dep in getattr(dependant, "dependencies", []) or []:
            permission = getattr(getattr(dep, "call", None), "permission", None)
            if permission is not None:
                found.add(permission)
        return found
    raise AssertionError(f"Route introuvable : {method.upper()} {path}")


# (router, méthode, chemin, permission attendue)
MCP_ROUTES = [
    (capabilities, "GET", "/v1/tools/servers", Permission.READ),
    (capabilities, "POST", "/v1/tools/servers", Permission.ADMIN),
    (capabilities, "GET", "/v1/tools/servers/{server_id}", Permission.READ),
    (capabilities, "PUT", "/v1/tools/servers/{server_id}", Permission.ADMIN),
    (capabilities, "PUT", "/v1/tools/servers/{server_id}/status", Permission.ADMIN),
    (capabilities, "POST", "/v1/tools/servers/{server_id}/sync", Permission.EXECUTE),
    (capabilities, "DELETE", "/v1/tools/servers/{server_id}", Permission.ADMIN),
    (capabilities, "GET", "/v1/tools/pipelines", Permission.READ),
    (capabilities, "GET", "/v1/tools/pipelines/{pipeline_id}", Permission.READ),
    (capabilities, "DELETE", "/v1/tools/pipelines/{pipeline_id}", Permission.WRITE),
]

SKILL_ROUTES = [
    (v1, "POST", "/v1/skills", Permission.PLUGINS),
    (v1, "PUT", "/v1/skills/{skill_id}", Permission.PLUGINS),
    (v1, "DELETE", "/v1/skills/{skill_id}", Permission.PLUGINS),
    (v1, "POST", "/v1/skills/{skill_id}/toggle", Permission.PLUGINS),
    (v1, "PUT", "/v1/skills/{skill_id}/valves", Permission.PLUGINS),
]

PLUGIN_ROUTES = [
    (v1, "POST", "/v1/plugins/install", Permission.PLUGINS),
    (v1, "POST", "/v1/plugins/{plugin_id}/install", Permission.PLUGINS),
    (v1, "POST", "/v1/plugins/{plugin_id}/enable", Permission.PLUGINS),
    (v1, "POST", "/v1/plugins/{plugin_id}/disable", Permission.PLUGINS),
    (v1, "PUT", "/v1/plugins/{plugin_id}/toggle", Permission.PLUGINS),
    (v1, "POST", "/v1/plugins/{plugin_id}/update", Permission.PLUGINS),
    (v1, "DELETE", "/v1/plugins/{plugin_id}", Permission.PLUGINS),
    (v1, "POST", "/v1/plugins/{plugin_id}/connect", Permission.PLUGINS),
    (v1, "DELETE", "/v1/plugins/{plugin_id}/connection", Permission.PLUGINS),
]


@pytest.mark.parametrize("router,method,path,expected", MCP_ROUTES + SKILL_ROUTES + PLUGIN_ROUTES)
def test_extension_route_requires_permission(router, method, path, expected):
    required = _required_permissions(router, method, path)
    assert expected in required, f"{method} {path} doit exiger {expected.value} (reçu : {required})"


def test_role_semantics_make_gates_meaningful():
    """Les gates choisis discriminent réellement les rôles (pas de faux gate)."""
    # viewer = lecture seule : ne peut ni administrer, ni exécuter, ni gérer les plugins.
    assert not rbac.has_permission("viewer", Permission.ADMIN)
    assert not rbac.has_permission("viewer", Permission.EXECUTE)
    assert not rbac.has_permission("viewer", Permission.PLUGINS)
    # standard = gère skills/plugins, mais pas les extensions privilégiées (MCP).
    assert rbac.has_permission("standard", Permission.PLUGINS)
    assert not rbac.has_permission("standard", Permission.ADMIN)
    # admin = tout.
    assert rbac.has_permission("admin", Permission.ADMIN)
    assert rbac.has_permission("admin", Permission.EXECUTE)
