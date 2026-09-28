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
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
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
