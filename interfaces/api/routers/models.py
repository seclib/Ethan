"""Router API — Catalogue agrégé des modèles LLM.

Routes :
    GET    /models                       → modèles découverts + fiches custom
    POST   /models                       → créer une fiche modèle custom
    GET    /models/{id}                  → détail d'une fiche
    PUT    /models/{id}                  → mettre à jour une fiche
    DELETE /models/{id}                  → supprimer une fiche
    POST   /models/{id}/toggle           → activer/désactiver
    GET    /models/search?q=...          → recherche

Le catalogue agrège :
- Les modèles **découverts** via ``ProviderManager.list_models()`` (providers
  activés interrogés en temps réel).
- Les fiches **personnalisées** du ``ModelStore`` Core (modèles non découverts
  automatiquement mais configurés manuellement).

Les providers eux-mêmes sont gérés par ``/providers`` (router ``providers.py``).
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.hardware.detector import get_system_hardware
from core.hardware.fit import check_model_compatibility
from core.llm.model_installer import install_or_use_model
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.models.discovery import discover_catalog_models, discover_models_async
from core.models.hub import get_model_hub
from fastapi import APIRouter, Depends, HTTPException, Query
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])

# Instances injectées au démarrage
_manager: ProviderManager | None = None
_store: ModelStore | None = None


def set_provider_manager(manager: ProviderManager) -> None:
    """Injecte le ProviderManager (appelé au startup)."""
    global _manager
    _manager = manager


def set_model_store(store: ModelStore) -> None:
    """Injecte le ModelStore (appelé au startup)."""
    global _store
    _store = store


def get_manager() -> ProviderManager:
    if _manager is None:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")
    return _manager


def get_store() -> ModelStore:
    if _store is None:
        raise HTTPException(status_code=503, detail="Model store not initialized")
    return _store


def _discovered_model_payload(model: Any) -> dict[str, Any]:
    """Serialize a discovered model without losing its provider routing name."""
    return {
        "id": model.id,
        "name": model.name,
        "model": model.model or model.id,
        "provider": model.provider,
        "context_length": model.context_length,
        "is_local": model.is_local,
        "is_private": model.is_private,
        "quality_score": model.quality_score,
        "capabilities": model.capabilities,
        "is_available": model.is_available,
        # Un modèle découvert n'a pas d'activation locale : son état suit le
        # provider. Champ présent pour un contrat homogène avec les fiches
        # custom (l'interface n'a pas à deviner la sémantique selon la source).
        "is_active": None,
        # Métadonnées réellement fournies par l'adapter (jamais inventées) :
        # la comparaison de la page Models ne les affiche que si le Core les
        # connaît (sinon null → ligne filtrée côté interface).
        "pricing": model.pricing,
        "avg_latency_ms": model.avg_latency_ms,
        "is_custom": False,
        "source": "discovered",
    }


def _custom_model_payload(card: dict[str, Any]) -> dict[str, Any]:
    """Serialize a custom card with a stable technical routing model.

    Frontière Provider / Modèle : ``provider`` est l'identifiant du SERVICE
    qui sert ce modèle (champ ``provider`` de la fiche).  Il ne doit jamais
    être remplacé par ``base_model_id`` (le modèle de base) — sinon le filtre
    par provider, le regroupement du sélecteur de chat et la résolution de
    provider échouent silencieusement.  Une fiche créée avant l'introduction
    de ce champ n'a pas de provider : la chaîne vide est renvoyée telle
    quelle, l'interface affiche alors « provider non déclaré » plutôt
    qu'un faux service.
    """
    return {
        "id": card["id"],
        "name": card.get("name", ""),
        "model": card.get("model") or card.get("base_model_id", ""),
        # Provider déclaré par la fiche (service réel) — "" si non renseigné.
        "provider": card.get("provider", ""),
        "context_length": card.get("params", {}).get("context_length", 4096),
        "is_local": card.get("meta", {}).get("is_local", False),
        "is_private": card.get("meta", {}).get("is_private", False),
        "quality_score": card.get("meta", {}).get("quality_score", 0.8),
        "capabilities": card.get("meta", {}).get("capabilities", []),
        # Métadonnées déclarées dans la fiche custom (meta) si et seulement si
        # l'administrateur les a renseignées — null sinon.
        "pricing": card.get("meta", {}).get("pricing"),
        "avg_latency_ms": card.get("meta", {}).get("avg_latency_ms"),
        # Une fiche custom n'est PAS découverte auprès d'un service : le Core ne
        # peut pas savoir si son provider est joignable. ``is_available``
        # reflète donc l'activation ADMINISTRATIVE de la fiche (``is_active``),
        # et non une joignabilité — les deux notions sont désormais exposées
        # séparément via ``is_active`` pour que l'interface ne les confonde pas.
        "is_available": card.get("is_active", True),
        "is_active": card.get("is_active", True),
        "is_custom": True,
        "source": "custom",
        # Modèle de base (≠ provider) : conservé pour l'affichage « basé sur ».
        "base_model_id": card.get("base_model_id", ""),
        "params": card.get("params", {}),
        "meta": card.get("meta", {}),
        "acl": card.get("acl", []),
        "created_at": card.get("created_at"),
        "updated_at": card.get("updated_at"),
    }


# ── GET /models ─────────────────────────────────────────────────────────


@router.get("")
async def list_models(
    provider_id: str | None = Query(default=None, description="Filtrer par provider"),
    include_custom: bool = Query(default=True, description="Inclure les fiches custom"),
):
    """Liste agrégée des modèles.

    Combine les modèles découverts via les providers Core et les fiches
    personnalisées du ModelStore.
    """
    manager = get_manager()
    results: list[dict[str, Any]] = []

    # 1. Modèles découverts via ProviderManager
    try:
        discovered = await manager.list_models(provider_id)
        for m in discovered:
            results.append(_discovered_model_payload(m))
    except Exception as exc:
        logger.warning("Failed to list discovered models: %s", exc)

    # 2. Fiches personnalisées
    if include_custom:
        store = get_store()
        try:
            custom = await store.list_models()
            for c in custom:
                # Le filtre provider s'applique aussi aux fiches custom :
                # sans cela, demander un provider inconnu renvoyait les fiches
                # d'un AUTRE service (le sélecteur de chat regroupait alors des
                # modèles non routables vers le provider demandé).
                if provider_id and c.get("provider", "") != provider_id:
                    continue
                results.append(_custom_model_payload(c))
        except Exception as exc:
            logger.warning("Failed to list custom models: %s", exc)

    return results


# ── GET /models/search ──────────────────────────────────────────────────


@router.get("/search")
async def search_models(q: str = Query(default="", description="Query string")):
    """Recherche dans le catalogue agrégé (discouvert + custom)."""
    manager = get_manager()
    results: list[dict[str, Any]] = []

    # Recherche dans les modèles découverts
    try:
        discovered = await manager.list_models()
        q_lower = q.lower()
        for m in discovered:
            if q_lower in m.id.lower() or q_lower in m.name.lower():
                results.append(_discovered_model_payload(m))
    except Exception as exc:
        logger.warning("Failed to search discovered models: %s", exc)

    # Recherche dans les fiches custom
    store = get_store()
    try:
        custom = await store.search_models(q)
        for c in custom:
            results.append(_custom_model_payload(c))
    except Exception as exc:
        logger.warning("Failed to search custom models: %s", exc)

    return results


# ── GET /models/hardware ────────────────────────────────────────────────


@router.get("/hardware")
async def get_hardware_info():
    """Retourne la carte des ressources matérielles du système hôte."""
    return get_system_hardware()


# ── GET /models/discover ────────────────────────────────────────────────


@router.get("/discover")
async def discover_models(
    q: str = Query(default="", description="Terme de recherche"),
    use_case: str | None = Query(default=None, description="Filtre par cas d'usage"),
    source: str = Query(default="all", description="Filtre par source (all, curated, huggingface, local)"),
):
    """Découvre les modèles du catalogue avec leur compatibilité matérielle."""
    return await discover_models_async(query=q, use_case=use_case, source=source)


# ── POST /models/detect-artifacts ─────────────────────────────────────────


@router.get(
    "/detect-artifacts/{model_id:path}",
)
async def detect_model_artifacts(model_id: str):
    """Détecte les artefacts disponibles et la méthode d'exécution pour un modèle."""
    hub = get_model_hub()
    return await hub.detect_artifact_formats(model_id=model_id)


# ── POST /models/check-compatibility ────────────────────────────────────


@router.post("/check-compatibility")
async def check_compatibility(payload: dict[str, Any]):
    """Vérifie l'adéquation matérielle d'un modèle spécifié."""
    model_name = payload.get("model") or payload.get("model_id") or payload.get("name")
    if not model_name:
        raise HTTPException(status_code=400, detail="Missing 'model' or 'model_id' in payload")

    params_b = payload.get("params_b")
    quantization = payload.get("quantization")
    context_length = int(payload.get("context_length", 4096))

    result = check_model_compatibility(
        model_name=str(model_name),
        params_b=float(params_b) if params_b is not None else None,
        quantization=str(quantization) if quantization else None,
        context_length=context_length,
    )
    return result.to_dict()


# ── POST /models/install (et alias /models/pull) ─────────────────────────


def _install_error_status(result: dict[str, Any]) -> int:
    """Mappe le code d'erreur Core vers un statut HTTP exploitable.

    - incompatible_hardware → 422 (requête valide, matériel insuffisant)
    - ollama_pull_failed / download_failed (runtime indisponible) → 502
    - défaut → 400
    """
    code = str(result.get("error", ""))
    if code == "incompatible_hardware":
        return 422
    if code in ("ollama_pull_failed", "download_failed"):
        message = str(result.get("message", "")).lower()
        if any(
            hint in message
            for hint in ("connexion", "connection", "refused", "unreachable", "timeout", "timed out")
        ):
            return 502
        return 400
    return 400


@router.post("/install")
@router.post("/pull")
async def install_model(payload: dict[str, Any]):
    """Installe ou active un modèle dans ETHAN.

    Applique le principe : l'utilisateur choisit le modèle, ETHAN Core
    détermine la meilleure méthode d'exécution (Ollama, local, cloud).
    """
    model_id = payload.get("model") or payload.get("model_id") or payload.get("name")
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing 'model' or 'model_id' in payload")

    provider_hint = payload.get("provider")
    manager = get_manager()
    store = get_store()

    result = await install_or_use_model(
        model_id=str(model_id),
        provider_hint=str(provider_hint) if provider_hint else None,
        manager=manager,
        store=store,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=_install_error_status(result),
            detail=result.get("message", "Installation failed"),
        )

    return result


# ── GET /models/installed ───────────────────────────────────────────────


@router.get("/installed")
async def get_installed_models():
    """Liste tous les modèles installés et disponibles dans ETHAN."""
    hub = get_model_hub()
    return await hub.list_installed(manager=_manager, store=_store)


# ── GET /models/inspect/{model_id:path} ──────────────────────────────────


@router.get("/inspect/{model_id:path}")
async def inspect_model(model_id: str):
    """Inspecte un modèle et répond à : « Ce modèle peut-il fonctionner, et par quelle méthode ? »"""
    hub = get_model_hub()
    return await hub.inspect(model_id=model_id)


# ── GET /models/runtimes/health ─────────────────────────────────────────


@router.get("/runtimes/health")
async def get_runtimes_health():
    """Vérifie la santé des runtimes d'inférence configurés."""
    hub = get_model_hub()
    return await hub.check_runtime_health(manager=_manager)


# ── GET /models/downloads ───────────────────────────────────────────────


@router.get("/downloads")
async def list_downloads():
    """Liste tous les téléchargements de modèles (en cours et récents)."""
    hub = get_model_hub()
    return hub.list_downloads()


# ── GET /models/storage ─────────────────────────────────────────────────


@router.get("/storage")
async def get_storage_layout():
    """Retourne la disposition et les répertoires de stockage du Model Hub."""
    hub = get_model_hub()
    return hub.get_storage_layout().to_dict()


# ── GET /models/{id} ────────────────────────────────────────────────────


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Détail d'un modèle (fiche custom ou modèle découvert)."""
    # 1. Vérifier si c'est une fiche custom
    store = get_store()
    custom = await store.get_model(model_id)
    if custom is not None:
        return _custom_model_payload(custom)

    # 2. Vérifier si c'est un modèle découvert
    manager = get_manager()
    try:
        discovered = await manager.list_models()
        for m in discovered:
            if m.id == model_id:
                return _discovered_model_payload(m)
    except Exception as exc:
        logger.warning("Failed to look up discovered model %s: %s", model_id, exc)

    raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


# ── POST /models ────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=dict,
    status_code=201,
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def create_model(data: dict[str, Any]):
    """Crée une fiche modèle personnalisée."""
    store = get_store()
    try:
        return await store.create_model(data)
    except Exception as exc:
        logger.exception("Failed to create model: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to create model: {exc}")


# ── PUT /models/{id} ────────────────────────────────────────────────────


@router.put(
    "/{model_id}",
    response_model=dict,
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def update_model(model_id: str, data: dict[str, Any]):
    """Met à jour une fiche modèle personnalisée."""
    store = get_store()
    result = await store.update_model(model_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return result


# ── DELETE /models/{id} ─────────────────────────────────────────────────


@router.delete(
    "/{model_id}",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def delete_model(model_id: str):
    """Supprime une fiche modèle personnalisée."""
    store = get_store()
    existed = await store.delete_model(model_id)
    if not existed:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return {"status": "deleted", "model_id": model_id}


# ── POST /models/{id}/toggle ────────────────────────────────────────────


@router.post(
    "/{model_id}/toggle",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def toggle_model(model_id: str):
    """Active/désactive une fiche modèle personnalisée."""
    store = get_store()
    result = await store.toggle_model(model_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return result
