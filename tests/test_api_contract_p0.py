"""Contrats de surface P0 de l'API ETHAN (G-06, ADR-3006).

Ces tests ne valident PAS la logique metier (couverte par les tests de
chaque domaine). Ils figent la **surface exposee a la WebUI** et les
invariants transverses, pour qu'aucune consolidation ni cleanup ne casse un
contrat silencieusement.

Precédent motivant (ADR-3006) : le merge des 41 commandes CLI plugin avait
casse des contrats sans que personne ne s'en apercoive. Memes risques ici :
92 routes P0 (Projects, Providers, Models, Knowledge/RAG, Folders, Chat,
Health, State) sont la surface reellement consommee par la WebUI **code
committé**. 3 routes n'existent que dans le WIP local
(GET+POST /v1/projects/active, GET /connections/providers) : elles
seront ajoutees au contrat le jour de leur commit.

Invariants couverts :
1. Existence des 92 routes P0 (regression de surface = echec) ;
2. RBAC : sans token, toute route P0 hors /health* renvoie 401 (audit du
   24/09/2026 : 87/92 en 401, 5 exemptions publiques) ;
3. Zero doublon (methode, chemin) sur l'application complete
   (les 5 doublons G-04/ADR-3008 ont ete supprimes le 24/09/2026) ;
4. /openapi.json documente chaque chemin P0 ;
5. Dette ADR-3006 : le nombre de routes P0 sans ``response_model`` (85 au
   24/09/2026) ne peut que baisser — garde-fou non bloquant.

Emplacement : `tests/` et non `interfaces/api/tests/` car
``testpaths = ["tests"]`` (pyproject.toml) : hors de `tests/`, le contrat
ne serait pas execute en CI.
"""

from __future__ import annotations

import os
import re
import secrets
from collections import Counter

import pytest
from fastapi.testclient import TestClient

# Fail-safe auto-suffisant : cle generee en memoire (jamais en dur dans le
# code — regle "no secrets"), pour que le test fonctionne meme si
# l'hote definit ETHAN_ENV=production.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

from interfaces.api.main import app  # noqa: E402

# Exemptions auth verifiees par audit : les seules routes P0 qui ne
# renvoient pas 401 sans token.
PUBLIC_P0_ROUTES: set[tuple[str, str]] = {
    ("GET", "/health"),
    ("GET", "/health/detailed"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/v1/health"),
}

# Dette ADR-3006 (au 24/09/2026) : 85 routes P0 sans response_model
# (82 mesures sur clone vierge ; plafond volontairement large pour
# reintegrer les 3 routes WIP sans recrire le test).
# Ce plafond ne peut que baisser (une hausse = nouvelle route sans schema).
MAX_SANS_RESPONSE_MODEL = 85

# Les 5 doublons G-04/ADR-3008 (mesurés sur clone vierge 92d0c396) ont été
# supprimés du code committé le 24/09/2026 : l'application ne doit plus
# comporter AUCUN doublon (methode, chemin). Toute nouvelle paire dupliquee
# fera echouer le test.
KNOWN_DOUBLONS: set[tuple[str, str]] = set()

P0_ROUTES: set[tuple[str, str]] = {
    # --- Chat / completion --------------------------------------------
    ("POST", "/api/v1/chat/completions"),
    ("POST", "/v1/chat/completions"),
    ("POST", "/v1/chat/completions/stream"),
    ("GET", "/v1/chat/history"),
    # --- Models (surface legacy /models + /api/v1/models) -------------
    ("GET", "/models"),
    ("POST", "/models"),
    ("GET", "/models/search"),
    ("GET", "/models/{model_id}"),
    ("PUT", "/models/{model_id}"),
    ("DELETE", "/models/{model_id}"),
    ("POST", "/models/{model_id}/toggle"),
    ("GET", "/api/v1/models/base"),
    ("GET", "/api/v1/models/list"),
    ("GET", "/api/v1/models/model"),
    ("GET", "/api/v1/models/tags"),
    # --- Providers ------------------------------------------------------
    ("GET", "/providers"),
    ("POST", "/providers"),
    ("GET", "/providers/{provider_id}"),
    ("PUT", "/providers/{provider_id}"),
    ("DELETE", "/providers/{provider_id}"),
    ("GET", "/providers/{provider_id}/capabilities"),
    ("PUT", "/providers/{provider_id}/default"),
    ("GET", "/providers/{provider_id}/models"),
    ("POST", "/providers/{provider_id}/test"),
    ("POST", "/providers/transcribe"),
    ("POST", "/providers/vision"),
    # --- Projects -------------------------------------------------------
    ("GET", "/v1/projects"),
    ("POST", "/v1/projects"),
    ("GET", "/v1/projects/default"),
    ("GET", "/v1/projects/{project_id}"),
    ("PATCH", "/v1/projects/{project_id}"),
    ("DELETE", "/v1/projects/{project_id}"),
    ("GET", "/v1/projects/{project_id}/context"),
    ("GET", "/v1/projects/{project_id}/documents"),
    ("POST", "/v1/projects/{project_id}/documents"),
    ("DELETE", "/v1/projects/{project_id}/documents/{doc_id}"),
    # --- Knowledge / RAG ------------------------------------------------
    ("GET", "/v1/knowledge"),
    ("POST", "/v1/knowledge"),
    ("GET", "/v1/knowledge/search"),
    ("GET", "/v1/knowledge/{knowledge_id}"),
    ("PUT", "/v1/knowledge/{knowledge_id}"),
    ("DELETE", "/v1/knowledge/{knowledge_id}"),
    ("POST", "/v1/knowledge/{knowledge_id}/connections"),
    ("POST", "/v1/knowledge/{knowledge_id}/rag"),
    ("GET", "/v1/knowledge/collections"),
    ("POST", "/v1/knowledge/collections"),
    ("POST", "/v1/knowledge/collections/retrieve-multi"),
    ("GET", "/v1/knowledge/collections/tree"),
    ("GET", "/v1/knowledge/collections/{collection_id}"),
    ("PUT", "/v1/knowledge/collections/{collection_id}"),
    ("DELETE", "/v1/knowledge/collections/{collection_id}"),
    ("GET", "/v1/knowledge/collections/{collection_id}/documents"),
    ("POST", "/v1/knowledge/collections/{collection_id}/documents"),
    (
        "DELETE",
        "/v1/knowledge/collections/{collection_id}/documents/{document_id}",
    ),
    ("POST", "/v1/knowledge/collections/{collection_id}/move"),
    ("POST", "/v1/knowledge/collections/{collection_id}/reindex"),
    ("POST", "/v1/knowledge/collections/{collection_id}/retrieve"),
    ("POST", "/v1/knowledge/import"),
    ("POST", "/v1/knowledge/import-batch"),
    ("GET", "/v1/knowledge/imports/{job_id}"),
    # --- Folders --------------------------------------------------------
    ("POST", "/v1/folders"),
    ("GET", "/v1/folders/index"),
    ("GET", "/v1/folders/tree"),
    ("GET", "/v1/folders/untagged"),
    ("POST", "/v1/folders/archive"),
    ("GET", "/v1/folders/archive/{archive_id}"),
    ("POST", "/v1/folders/merge"),
    ("POST", "/v1/folders/move-resource"),
    ("POST", "/v1/folders/move-resources"),
    ("POST", "/v1/folders/copy-resources"),
    ("GET", "/v1/folders/by-resource/{resource_type}/{resource_id}"),
    ("GET", "/v1/folders/deleted"),
    ("DELETE", "/v1/folders/deleted/empty"),
    ("POST", "/v1/folders/deleted/{deleted_id}/restore"),
    ("GET", "/v1/folders/{folder_id}"),
    ("PATCH", "/v1/folders/{folder_id}"),
    ("DELETE", "/v1/folders/{folder_id}"),
    ("POST", "/v1/folders/{folder_id}/move"),
    ("GET", "/v1/folders/{folder_id}/resources"),
    ("POST", "/v1/folders/{folder_id}/resources"),
    (
        "DELETE",
        "/v1/folders/{folder_id}/resources/{resource_type}/{resource_id}",
    ),
    ("POST", "/v1/folders/{folder_id}/to-collection"),
    # --- Health / State / OAuth / divers --------------------------------
    ("GET", "/health"),
    ("GET", "/health/detailed"),
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/v1/health"),
    ("GET", "/v1/state"),
    ("GET", "/v1/oauth/providers"),
    ("POST", "/v1/oauth/providers"),
    ("POST", "/v1/oauth/providers/{name}/disable"),
    ("GET", "/v1/dedup/health"),
}


def _resolve(path: str) -> str:
    """Remplace les parametres de chemin par un jeton inoffensif."""
    return re.sub(r"\{[^}]+\}", "x", path)


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Client de contrat : lifespan actif, etat global restaure apres coup.

    Le lifespan de main.py peuple deux singletons plugin
    (`core.plugins.registry._registry` + `interfaces.api.routers.v1
    ._plugin_registry`). `tests/test_plugins_api.py::test_routes_sans_
    registry_503` exige leur absence : on snapshot l'etat initial et on le
    restaure en teardown pour ne pas polluer le reste de la suite.
    """
    import core.plugins.registry as core_plugin_registry
    from interfaces.api.routers import v1

    saved_core_registry = core_plugin_registry._registry
    saved_v1_registry = v1._plugin_registry
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    core_plugin_registry.set_plugin_registry(saved_core_registry)
    v1.set_plugin_registry(saved_v1_registry)


def _declared_routes() -> set[tuple[str, str]]:
    declared: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            if method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                declared.add((method, route.path))
    return declared


def test_surface_p0_complete() -> None:
    """Chaque route P0 declaree existe encore sur l'application reelle."""
    missing = P0_ROUTES - _declared_routes()
    assert not missing, (
        f"{len(missing)} route(s) P0 disparue(s) de l'API — regression de "
        f"surface : {sorted(missing)}"
    )


def test_aucune_route_dupliquee() -> None:
    """Aucune paire (methode, chemin) en doublon (collision de routeurs)."""
    pairs: list[tuple[str, str]] = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            if method not in ("HEAD", "OPTIONS"):
                pairs.append((method, route.path))
    duplicates = {pair: n for pair, n in Counter(pairs).items() if n > 1}
    new_duplicates = set(duplicates) - KNOWN_DOUBLONS
    assert not new_duplicates, f"nouveaux doublons (methode, chemin) : {sorted(new_duplicates)}"


def test_rbac_p0_sans_token(client: TestClient) -> None:
    """Sans token, toute route P0 hors /health* est refusee (401)."""
    protected = P0_ROUTES - PUBLIC_P0_ROUTES
    assert len(protected) == 87, f"population inattendue : {len(protected)}"
    refused: dict[tuple[str, str], int] = {}
    for method, path in sorted(protected):
        response = client.request(method, _resolve(path))
        if response.status_code != 401:
            refused[(method, path)] = response.status_code
    assert not refused, f"routes P0 accessibles sans authentification (regression C-08) : {refused}"


def test_health_publique(client: TestClient) -> None:
    """Les endpoints de sante restent publics (liveness/readiness)."""
    for method, path in sorted(PUBLIC_P0_ROUTES):
        response = client.request(method, _resolve(path))
        if path == "/health/detailed":
            # 503 tant que les dependances (NATS/Redis/PG) sont absentes.
            assert response.status_code in (200, 503), f"{path} -> {response.status_code}"
        else:
            assert response.status_code == 200, f"{path} -> {response.status_code}"


def test_openapi_couvre_les_chemins_p0(client: TestClient) -> None:
    """/openapi.json reste public et documente chaque chemin P0."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    documented = set(response.json().get("paths", {}))
    missing = {path for _, path in P0_ROUTES} - documented
    assert not missing, f"chemins P0 absents de l'OpenAPI : {sorted(missing)}"


def test_dette_sans_schema_ne_regresse_pas() -> None:
    """Le nombre de routes P0 sans response_model ne peut que baisser."""
    without_schema = sum(
        1
        for route in app.routes
        if getattr(route, "methods", None)
        and any(
            (method, route.path) in P0_ROUTES
            for method in route.methods
            if method in ("GET", "POST", "PUT", "PATCH", "DELETE")
        )
        and not getattr(route, "response_model", None)
    )
    assert without_schema <= MAX_SANS_RESPONSE_MODEL, (
        f"{without_schema} routes P0 sans response_model > plafond "
        f"{MAX_SANS_RESPONSE_MODEL} : nouvelle route exposee sans schema "
        "(ADR-3006 — ajouter un response_model ou justifier en RFC)."
    )
