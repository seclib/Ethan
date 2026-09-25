"""Contrats de surface par domaine (ADR-3006 / G-06, ARCHITECTURE-CIBLE §7).

Ces tests ne valident PAS la logique métier (couverte par les tests de chaque
domaine). Ils figent la **surface exposée** des domaines non couverts par
`tests/test_api_contract_p0.py`, plus les invariants transverses :

1. Existence des routes de domaine (régression de surface = échec) ;
2. RBAC : sans token, toute route de domaine renvoie 401 (C-08) ;
3. /openapi.json documente chaque chemin de domaine ;
4. MCP : **aucun endpoint fictif** — MCP n'est pas implémenté, donc aucune
   route ne doit exister (si ce test casse, MCP a été implémenté : mettre à
   jour le contrat) ;
5. Snapshot versionné `docs/api/openapi.v1.json` (ADR-3006 §1) : aucune route
   du snapshot ne disparaît (compatibilité : ajout = OK, suppression = rupture) ;
6. Dette ADR-3006 : le nombre de routes de domaine sans `response_model`
   (90 au 25/09/2026) ne peut que baisser ;
7. Frontière stricte (§7.3.4) : aucune route ni schéma OpenAPI n'expose la
   structure interne du store (`core_domain_records`, `ethan_config`).

Base de vérité : routes **mesurées sur le code committé** (`22fad583`,
359 routes — inventaire complet). Le WIP local n'entre PAS dans le contrat.
Surfaces déclarées mais non committées à ce jour (aucun endpoint fictif) :
- Components (`/v1/components/*`, 17 routes) — WIP ;
- Connections (`/connections/*`, 9 routes) — WIP ;
- `/v1/projects/active`, `/connections/providers` — WIP.
Le jour de leur commit, corriger le contrat ET `docs/api/CONTRACTS-API.md`.

Outils partagés : `tests/contract_kit.py` + fixture `contract_client`
(`tests/conftest.py`) — mêmes invariants que le contrat P0, zéro duplication.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from tests.contract_kit import (
    declared_routes,
    resolve_path,
    routes_sans_response_model,
)

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_SNAPSHOT = ROOT / "docs" / "api" / "openapi.v1.json"

# Dette ADR-3006 mesurée au 25/09/2026 sur le code committé : 90/90 routes de
# domaine sans response_model. Ce plafond ne peut que baisser — une hausse
# signale une nouvelle route exposée sans schéma (ajouter un response_model
# ou justifier en RFC).
MAX_DOMAIN_SANS_RESPONSE_MODEL = 90

# Suppressions en attente de commit (WIP local, mesurées le 25/09/2026) :
# - /search, /search/types → déplacés vers /v1/search (+ /v1/search/types) ;
# - PUT + DELETE /users/{user_id} → dédupliqués (ownership `security.py`).
# Ces 4 routes existent dans le snapshot v1 (généré sur HEAD `22fad583`) et ne
# sont pas encore retirées du code *committé*. Au commit du WIP : régénérer
# `docs/api/openapi.v1.json` (commande dans docs/api/CONTRACTS-API.md) et
# vider cet ensemble.
WIP_PENDING_REMOVALS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/search"),
        ("GET", "/search/types"),
        ("PUT", "/users/{user_id}"),
        ("DELETE", "/users/{user_id}"),
    }
)

DOMAIN_ROUTES: dict[str, frozenset[tuple[str, str]]] = {
    # --- Agents / Missions / Goals (ARCHITECTURE-CIBLE §7.2) ---------------
    "agents": frozenset(
        {
            ("GET", "/v1/agents"),
            ("POST", "/v1/agents"),
            ("DELETE", "/v1/agents/{agent_id}"),
            ("GET", "/v1/agents/{agent_id}"),
            ("PUT", "/v1/agents/{agent_id}"),
            ("POST", "/v1/agents/{agent_id}/execute"),
            ("GET", "/v1/agents/{agent_id}/executions"),
            ("GET", "/v1/agents/{agent_id}/resources"),
        }
    ),
    "missions": frozenset(
        {
            ("GET", "/v1/missions"),
            ("POST", "/v1/missions"),
            ("DELETE", "/v1/missions/{mission_id}"),
            ("GET", "/v1/missions/{mission_id}"),
            ("PUT", "/v1/missions/{mission_id}"),
            ("POST", "/v1/missions/{mission_id}/steps/{step_id}/approve"),
            ("POST", "/v1/missions/{mission_id}/steps/{step_id}/verify"),
        }
    ),
    "goals": frozenset(
        {
            ("GET", "/v1/goals"),
            ("POST", "/v1/goals"),
            ("DELETE", "/v1/goals/{goal_id}"),
            ("GET", "/v1/goals/{goal_id}"),
            ("PUT", "/v1/goals/{goal_id}"),
        }
    ),
    # --- Conversations (ADR-3007 : famille /chats + streaming /v1/chat) ----
    "conversations": frozenset(
        {
            ("GET", "/chats"),
            ("POST", "/chats"),
            ("DELETE", "/chats/{chat_id}"),
            ("GET", "/chats/{chat_id}"),
            ("PUT", "/chats/{chat_id}"),
            ("GET", "/chats/{chat_id}/messages"),
            ("POST", "/chats/{chat_id}/messages"),
            ("POST", "/chats/{chat_id}/share"),
        }
    ),
    # --- Skills / Tools (§7.2 « Skills / Tools / MCP ») --------------------
    "skills": frozenset(
        {
            ("GET", "/v1/skills"),
            ("POST", "/v1/skills"),
            ("GET", "/v1/skills/export"),
            ("POST", "/v1/skills/import"),
            ("GET", "/v1/skills/lab/results"),
            ("POST", "/v1/skills/lab/test"),
            ("GET", "/v1/skills/search"),
            ("DELETE", "/v1/skills/{skill_id}"),
            ("GET", "/v1/skills/{skill_id}"),
            ("PUT", "/v1/skills/{skill_id}"),
            ("POST", "/v1/skills/{skill_id}/execute"),
            ("POST", "/v1/skills/{skill_id}/run"),
            ("POST", "/v1/skills/{skill_id}/toggle"),
            ("GET", "/v1/skills/{skill_id}/valves"),
            ("PUT", "/v1/skills/{skill_id}/valves"),
        }
    ),
    "tools": frozenset(
        {
            ("GET", "/v1/tools"),
            ("POST", "/v1/tools"),
            ("GET", "/v1/tools/pipelines"),
            ("POST", "/v1/tools/pipelines"),
            ("DELETE", "/v1/tools/pipelines/{pipeline_id}"),
            ("GET", "/v1/tools/pipelines/{pipeline_id}"),
            ("GET", "/v1/tools/servers"),
            ("POST", "/v1/tools/servers"),
            ("DELETE", "/v1/tools/servers/{server_id}"),
            ("GET", "/v1/tools/servers/{server_id}"),
            ("PUT", "/v1/tools/servers/{server_id}"),
            ("PUT", "/v1/tools/servers/{server_id}/status"),
            ("POST", "/v1/tools/servers/{server_id}/sync"),
            ("DELETE", "/v1/tools/{tool_id}"),
        }
    ),
    # --- Plugins -----------------------------------------------------------
    "plugins": frozenset(
        {
            ("GET", "/v1/plugins"),
            ("GET", "/v1/plugins/categories"),
            ("POST", "/v1/plugins/install"),
            ("DELETE", "/v1/plugins/{plugin_id}"),
            ("GET", "/v1/plugins/{plugin_id}"),
            ("GET", "/v1/plugins/{plugin_id}/capabilities"),
            ("POST", "/v1/plugins/{plugin_id}/connect"),
            ("DELETE", "/v1/plugins/{plugin_id}/connection"),
            ("POST", "/v1/plugins/{plugin_id}/disable"),
            ("POST", "/v1/plugins/{plugin_id}/enable"),
            ("POST", "/v1/plugins/{plugin_id}/install"),
            ("GET", "/v1/plugins/{plugin_id}/permissions"),
            ("PUT", "/v1/plugins/{plugin_id}/toggle"),
            ("POST", "/v1/plugins/{plugin_id}/update"),
        }
    ),
    # --- Integrations (sans préfixe /v1 — état réel du montage) ------------
    "integrations": frozenset(
        {
            ("GET", "/integrations"),
            ("POST", "/integrations"),
            ("DELETE", "/integrations/{integration_id}"),
            ("GET", "/integrations/{integration_id}"),
            ("PUT", "/integrations/{integration_id}"),
            ("POST", "/integrations/{integration_id}/connect"),
            ("POST", "/integrations/{integration_id}/disconnect"),
            ("POST", "/integrations/{integration_id}/test"),
        }
    ),
    # --- RAG (complète le domaine Knowledge du contrat P0) -----------------
    "rag": frozenset(
        {
            ("GET", "/v1/rag/config"),
            ("PUT", "/v1/rag/config"),
            ("POST", "/v1/rag/context"),
            ("GET", "/v1/rag/documents"),
            ("POST", "/v1/rag/documents"),
            ("POST", "/v1/rag/documents/from-file/{file_id}"),
            ("DELETE", "/v1/rag/documents/{document_id}"),
            ("GET", "/v1/rag/documents/{document_id}"),
            ("POST", "/v1/rag/retrieve"),
            ("GET", "/v1/rag/status"),
            ("GET", "/v1/rag/strategies"),
        }
    ),
}


def _all_domain_routes() -> set[tuple[str, str]]:
    return {route for routes in DOMAIN_ROUTES.values() for route in routes}


def test_surface_domaines_complete() -> None:
    """Chaque route de domaine déclarée existe encore sur l'application."""
    declared = declared_routes()
    missing = {
        domain: sorted(routes - declared)
        for domain, routes in DOMAIN_ROUTES.items()
        if routes - declared
    }
    assert not missing, f"routes de domaine disparues (régression de surface) : {missing}"


def test_rbac_domaines_sans_token(contract_client: TestClient) -> None:
    """Sans token, toute route de domaine est refusée (401)."""
    protected = _all_domain_routes()
    assert len(protected) == 90, f"population inattendue : {len(protected)}"
    refused: dict[tuple[str, str], int] = {}
    for method, path in sorted(protected):
        response = contract_client.request(method, resolve_path(path))
        if response.status_code != 401:
            refused[(method, path)] = response.status_code
    assert not refused, (
        f"routes de domaine accessibles sans authentification (régression C-08) : {refused}"
    )


def test_openapi_couvre_les_chemins_domaines(contract_client: TestClient) -> None:
    """/openapi.json documente chaque chemin de domaine."""
    response = contract_client.get("/openapi.json")
    assert response.status_code == 200
    documented = set(response.json().get("paths", {}))
    missing = {path for _, path in _all_domain_routes()} - documented
    assert not missing, f"chemins de domaine absents de l'OpenAPI : {sorted(missing)}"


def test_mcp_non_implemente_aucun_endpoint_fictif() -> None:
    """Aucun endpoint MCP n'existe : le contrat ne déclare que le réel.

    MCP n'est pas implémenté (audit 25/09/2026 ; ARCHITECTURE-CIBLE §I.1).
    Si ce test échoue, MCP a été implémenté : ajouter ses routes à ce
    contrat ET au catalogue `docs/api/CONTRACTS-API.md`.
    """
    mcp_routes = sorted(
        (method, path) for method, path in declared_routes() if "mcp" in path.lower()
    )
    assert not mcp_routes, f"MCP semble implémenté — mettre à jour le contrat : {mcp_routes}"


def test_snapshot_v1_aucune_route_supprimee() -> None:
    """Toute route du snapshot versionné (ADR-3006 §1) existe encore.

    Compatibilité : un ajout de route est compatible (le snapshot est un
    sous-ensemble de la surface vive) ; une suppression casse ce test —
    elle exige une dépréciation explicite ou un bump de version.
    """
    assert OPENAPI_SNAPSHOT.exists(), f"snapshot introuvable : {OPENAPI_SNAPSHOT}"
    schema = json.loads(OPENAPI_SNAPSHOT.read_text(encoding="utf-8"))
    declared = declared_routes()
    removed: list[tuple[str, str]] = []
    for path, operations in schema.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method in operations and (method.upper(), path) not in declared:
                removed.append((method.upper(), path))
    unexpected = sorted(set(removed) - WIP_PENDING_REMOVALS)
    assert not unexpected, (
        f"routes du snapshot v1 disparues (rupture de contrat — ADR-3006) : {unexpected}"
    )


def test_dette_schemas_domaines_ne_regresse_pas() -> None:
    """Le nombre de routes de domaine sans response_model ne peut que baisser."""
    without_schema = routes_sans_response_model(_all_domain_routes())
    assert without_schema <= MAX_DOMAIN_SANS_RESPONSE_MODEL, (
        f"{without_schema} routes de domaine sans response_model > plafond "
        f"{MAX_DOMAIN_SANS_RESPONSE_MODEL} : nouvelle route exposée sans schéma "
        "(ADR-3006 — ajouter un response_model ou justifier en RFC)."
    )


def test_pas_de_fuite_du_store_interne(contract_client: TestClient) -> None:
    """Aucune route ni schéma OpenAPI n'expose la structure interne (§7.3.4)."""
    internal_markers = ("core_domain_records", "ethan_config")
    leaked_paths = sorted(
        path for _, path in declared_routes() if any(m in path for m in internal_markers)
    )
    schema_names = (
        contract_client.get("/openapi.json").json().get("components", {}).get("schemas", {})
    )
    leaked_schemas = sorted(
        name for name in schema_names if any(m in name.lower() for m in internal_markers)
    )
    assert not leaked_paths and not leaked_schemas, (
        f"fuite du store interne — chemins : {leaked_paths} ; schémas : {leaked_schemas}"
    )
