"""Gates RBAC du plan de contrôle — providers, config, provisioning, agents.

Complément de ``test_extensions_rbac_api.py`` (skills / plugins / MCP).  Ce
fichier verrouille les routes qui **contrôlent ETHAN lui-même** et qui, lors de
l'audit, étaient ouvertes à n'importe quel rôle authentifié — y compris un rôle
« lecture seule » :

- ``/providers``   : choisit l'endpoint qui reçoit **tout** le contexte des
  conversations et y stocke les clés API.  Non gate = exfiltration légale ;
- ``/config``      : source de vérité (modèle actif, routing RAG, agents) ;
- ``/v1/cookbook`` : installe des skills / prompts / automatisations — donc
  contournait les gates PLUGINS et EXECUTE de ces ressources ;
- ``/v1/agents``, ``/v1/automations`` : asymétrie constatée — la *création*
  exigeait une permission, la *modification* et la *suppression* aucune.

Règle appliquée : une permission n'existe que côté Core/API (jamais UI), et
deux routes d'une même ressource ne peuvent pas avoir des exigences
différentes sans raison écrite (voir ``test_*_coherence``).
"""

from __future__ import annotations

import inspect

import pytest
from core.auth import Permission, rbac
from routers import capabilities, component_lifecycle, config, cookbook, providers, security, v1

MUTATIONS = {"POST", "PUT", "PATCH", "DELETE"}


def _routes_of(router) -> list:
    inner = getattr(router, "router", router)
    return list(getattr(inner, "routes") or [])


def _permissions_of(route) -> set[Permission]:
    found: set[Permission] = set()
    for dep in getattr(route, "dependencies", []) or []:
        permission = getattr(getattr(dep, "dependency", None), "permission", None)
        if permission is not None:
            found.add(permission)
    for dep in getattr(getattr(route, "dependant", None), "dependencies", []) or []:
        permission = getattr(getattr(dep, "call", None), "permission", None)
        if permission is not None:
            found.add(permission)
    return found


def _required_permissions(router, method: str, path: str) -> set[Permission]:
    for route in _routes_of(router):
        if getattr(route, "path", None) != path:
            continue
        if method.upper() not in {m.upper() for m in getattr(route, "methods", set())}:
            continue
        return _permissions_of(route)
    raise AssertionError(f"Route introuvable : {method.upper()} {path}")


# ── Matrice « route → permission » ──────────────────────────────────────────

PROVIDER_ROUTES = [
    (providers, "POST", "/providers", Permission.PLUGINS),
    (providers, "PUT", "/providers/{provider_id}", Permission.PLUGINS),
    (providers, "DELETE", "/providers/{provider_id}", Permission.PLUGINS),
    (providers, "PUT", "/providers/{provider_id}/default", Permission.PLUGINS),
    (providers, "POST", "/providers/{provider_id}/test", Permission.PLUGINS),
]

CONFIG_ROUTES = [
    (config, "PUT", "/config/{domain}", Permission.SETTINGS),
    (config, "PATCH", "/config/{domain}", Permission.SETTINGS),
    (config, "DELETE", "/config/{domain}/{key}", Permission.SETTINGS),
    (config, "POST", "/config/import", Permission.ADMIN),
]

COOKBOOK_ROUTES = [
    (cookbook, "POST", "/v1/cookbook/install/{recipe_id}", Permission.PLUGINS),
    (cookbook, "DELETE", "/v1/cookbook/install/{recipe_id}", Permission.PLUGINS),
]

# Asymétrie corrigée : le gate de la création s'applique aussi aux suites.
RESOURCE_COHERENCE_ROUTES = [
    (v1, "PUT", "/v1/agents/{agent_id}", Permission.AGENTS),
    (v1, "DELETE", "/v1/agents/{agent_id}", Permission.AGENTS),
    (v1, "PUT", "/v1/settings", Permission.SETTINGS),
    (capabilities, "PUT", "/v1/automations/{automation_id}", Permission.EXECUTE),
    (capabilities, "DELETE", "/v1/automations/{automation_id}", Permission.EXECUTE),
    (capabilities, "POST", "/v1/automations/{automation_id}/trigger", Permission.EXECUTE),
]


@pytest.mark.parametrize(
    "router,method,path,expected",
    PROVIDER_ROUTES + CONFIG_ROUTES + COOKBOOK_ROUTES + RESOURCE_COHERENCE_ROUTES,
)
def test_control_plane_route_requires_permission(router, method, path, expected):
    required = _required_permissions(router, method, path)
    assert expected in required, f"{method} {path} doit exiger {expected.value} (reçu : {required})"


def _find(router, method: str, path: str):
    for route in _routes_of(router):
        if getattr(route, "path", None) != path:
            continue
        if method.upper() in {m.upper() for m in getattr(route, "methods", set())}:
            return route
    raise AssertionError(f"Route introuvable : {method.upper()} {path}")


def test_read_of_control_plane_stays_readable():
    """Durcir l'écriture ne doit pas casser la lecture (UI, diagnostics).

    Les GET des surfaces durcies restent accessibles à tout rôle authentifié
    (l'``auth_middleware`` exige déjà un JWT) : aucun gate d'autorisation
    supplémentaire n'a été ajouté sur la lecture.
    """
    for router, path in (
        (providers, "/providers"),
        (config, "/config"),
        (cookbook, "/v1/cookbook/recipes"),
    ):
        route = _find(router, "GET", path)
        assert _permissions_of(route) == set(), f"GET {path} ne doit pas être restreint"


# ── Garde de cohérence : aucune mutation du plan de contrôle sans gate ──────

# Préfixes qui pilotent ETHAN (configuration, exécution, extensions).
PRIVILEGED_PREFIXES = (
    "/providers",
    "/config",
    "/v1/cookbook",
    "/v1/agents",
    "/v1/automations",
    "/v1/settings",
    "/v1/skills",
    "/v1/plugins",
    "/v1/tools",
    "/v1/models",
    "/v1/api-keys",
    # Cycle de vie des composants : install/configure/enable/disable/uninstall
    # pilotent l'hôte (dépendances, services).  Déjà gate côté router — le garde
    # empêche qu'un futur refactor les rouvre.
    "/v1/components",
)

# Mutations volontairement ouvertes à tout rôle authentifié — avec raison,
# sinon ce garde devient un bruit que la prochaine personne désactive.
GATE_EXCEPTIONS: dict[tuple[object, str], str] = {
    # Plan de données : consommer une capacité d'IA (vision / transcription).
    # Tout utilisateur authentifié peut déjà discuter ; le rôle « viewer »
    # inclut CHAT.  Ce n'est pas le plan de contrôle.
    (providers, "/providers/vision"): "inférence à la demande de l'utilisateur",
    (providers, "/providers/transcribe"): "inférence à la demande de l'utilisateur",
}


@pytest.mark.parametrize(
    "router_module",
    [providers, config, cookbook, capabilities, v1, component_lifecycle],
)
def test_no_privileged_mutation_without_gate(router_module):
    offenders = []
    for route in _routes_of(router_module):
        path = getattr(route, "path", "") or ""
        methods = {m.upper() for m in getattr(route, "methods", set())}
        if not methods & MUTATIONS:
            continue
        if not path.startswith(PRIVILEGED_PREFIXES):
            continue
        if _permissions_of(route):
            continue
        if (router_module, path) in GATE_EXCEPTIONS:
            continue
        offenders.append(f"{','.join(sorted(methods & MUTATIONS))} {path}")
    assert not offenders, (
        "Mutations du plan de contrôle sans require_permission (escalade de "
        f"privilège possible pour un rôle authentifié quel qu'il soit) : {offenders}"
    )


def test_documented_exceptions_are_actually_ungated():
    """Un contournement documenté qui n'existe plus doit être supprimé."""
    for (router_module, path), reason in GATE_EXCEPTIONS.items():
        route = _find(router_module, "POST", path)
        assert not _permissions_of(route), (
            f"{path} est désormais gatee ({reason}) : retire l'exception"
        )


def test_role_semantics_make_gates_meaningful():
    """Les permissions choisies discriminent réellement les rôles."""
    checked = (Permission.PLUGINS, Permission.SETTINGS, Permission.EXECUTE, Permission.AGENTS)
    for permission in checked:
        assert not rbac.has_permission("viewer", permission), (
            f"viewer ne doit pas porter {permission.value} : les gates seraient décoratifs"
        )
    assert rbac.has_permission("admin", Permission.ADMIN)
    assert rbac.has_permission("admin", Permission.PLUGINS)


# ── Garde inverse : ne pas sur-gater le plan de données ─────────────────────
# Durcir le contrôle ne doit pas casser l'usage nominal : un rôle « viewer »
# ou « user » doit continuer à produire du contenu et à s'auto-administrer.
DATA_PLANE_OPEN_ROUTES = [
    (providers, "POST", "/providers/vision"),
    (providers, "POST", "/providers/transcribe"),
    (security, "POST", "/auth/2fa/setup"),
    (security, "POST", "/auth/2fa/confirm"),
    (security, "POST", "/auth/2fa/disable"),
]


@pytest.mark.parametrize("router_module,method,path", DATA_PLANE_OPEN_ROUTES)
def test_data_plane_and_self_service_stay_open(router_module, method, path):
    """Ces routes servent l'utilisateur, pas la configuration d'ETHAN.

    Les gater imposerait une permission de plan de contrôle pour une action
    d'usage courant : le rôle « viewer » (READ + CHAT) ou « user » perdrait la
    vision, la transcription ou son propre 2FA.  Elles restent donc protégées
    par le seul ``auth_middleware`` (JWT valide).
    """
    route = _find(router_module, method, path)
    assert _permissions_of(route) == set(), (
        f"{method} {path} est du plan de données : ne pas exiger de permission"
    )


# ── Administration des comptes : gate de rôle en corps de route ─────────────
# ``security.py`` n'utilise pas ``require_permission`` mais ``_require_admin``
# (contrôle de rôle strict + garde-fous « dernier admin » / « pas soi-même »).
# On verrouille ce contrat par inspection de la source : le supprimer
# silencieusement casserait l'invariant sans qu'aucun test unitaire ne le voie.
USER_ADMIN_ROUTES = [
    ("POST", "/users"),
    ("PUT", "/users/{username}"),
    ("DELETE", "/users/{username}"),
    ("PUT", "/users/{username}/activate"),
]


@pytest.mark.parametrize("method,path", USER_ADMIN_ROUTES)
def test_user_admin_routes_keep_admin_check(method, path):
    route = _find(security, method, path)
    source = inspect.getsource(route.endpoint)
    assert "_require_admin(" in source or "_ensure_not_self(" in source, (
        f"{method} {path} doit conserver son contrôle admin explicite"
    )
