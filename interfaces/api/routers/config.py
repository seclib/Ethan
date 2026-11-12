"""Router API — Configuration centralisée ETHAN.

Routes :
    GET    /config                    → configuration complète
    GET    /config/{domain}           → configuration d'un domaine
    PUT    /config/{domain}           → remplacer un domaine
    PATCH  /config/{domain}           → mettre à jour partiellement un domaine
    DELETE /config/{domain}/{key}     → supprimer une clé
    POST   /config/import             → importer une configuration
    GET    /config/export             → exporter la configuration
    GET    /config/validate           → valider la configuration
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.config import DOMAINS, ConfigurationService, config_to_json_schema
from core.config.store import ConfigPersistenceError
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


async def _write_domain(
    service: ConfigurationService, domain: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Exécute une écriture de configuration et mappe son échec en HTTP.

    Une écriture non persistée ne doit JAMAIS être présentée comme un succès :
    l'utilisateur verrait sa valeur disparaître au prochain redémarrage tout en
    croyant l'avoir enregistrée.  On renvoie donc 503 (le backend durable est
    indisponible) avec un message explicite, et l'état en mémoire est resté à sa
    valeur précédente.

    Returns:
        L'état du domaine réellement persisté (relu depuis le store).
    """
    try:
        return await service.set_domain(domain, data)
    except ConfigPersistenceError as e:
        logger.error("Configuration write failed for %s: %s", domain, e)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "persistence_failed",
                "domain": domain,
                "message": (
                    "Configuration was NOT saved. The durable store rejected the "
                    "write; the previous value is unchanged. Retry once storage "
                    "is available."
                ),
                "reason": str(e),
            },
        ) from e


# Écriture de la configuration = gate ``SETTINGS`` (et ``ADMIN`` pour
# l'import, qui remplace plusieurs domaines d'un coup).  Sans gate, n'importe
# quel rôle authentifié — y compris un rôle « lecture seule » — réécrivait la
# source de vérité d'ETHAN : modèle actif, routing RAG, comportement des
# agents.  La lecture reste ouverte aux rôles authentifiés (GET ... READ).

# Instance globale du ConfigurationService — injectée au démarrage
_service: ConfigurationService | None = None


def set_configuration_service(service: ConfigurationService) -> None:
    """Injecte le ConfigurationService dans le router (appelé au startup)."""
    global _service
    _service = service


def get_service() -> ConfigurationService:
    """Retourne le ConfigurationService global.

    Raises:
        HTTPException 503 si le service n'est pas initialisé.
    """
    if _service is None:
        raise HTTPException(status_code=503, detail="Configuration service not initialized")
    return _service


# ── GET /config ─────────────────────────────────────────────────────────────


@router.get("")
async def get_config():
    """Retourne la configuration complète (fusionnée)."""
    service = get_service()
    return service.get_all()


# ── GET /config/schema ──────────────────────────────────────────────────────


@router.get("/schema")
async def get_config_schema():
    """Retourne le JSON Schema complet de la configuration (auto-généré)."""
    return config_to_json_schema()


# ── GET /config/schema/{domain} ─────────────────────────────────────────────


@router.get("/schema/{domain}")
async def get_domain_schema(domain: str):
    """Retourne le JSON Schema d'un domaine de configuration.

    Raises:
        HTTPException 404 si le domaine est inconnu.
    """
    try:
        return config_to_json_schema(domain)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")


# ── GET /config/status ──────────────────────────────────────────────────────
# NB: déclaré AVANT /{domain}, sinon "status" serait avalé par le paramètre de
# route et renverrait 404 « Unknown domain ».


@router.get("/status")
async def get_config_status():
    """État réel de la persistance de la configuration.

    ``durable: false`` signifie que les écritures ne survivent pas à un
    redémarrage — l'interface doit alors prévenir l'utilisateur au lieu de
    laisser croire que l'enregistrement est effectif.
    """
    service = get_service()
    return await service.status()


# ── GET /config/export ──────────────────────────────────────────────────────
# Déclarés AVANT /{domain} : Starlette matche dans l'ordre de déclaration, donc
# après /{domain} ces routes étaient avalées par le paramètre (404 « Unknown
# domain 'export' ») au lieu d'être joignables.


@router.get("/export")
async def export_config():
    """Exporte la configuration complète."""
    service = get_service()
    return service.export()


# ── GET /config/validate ────────────────────────────────────────────────────


@router.get("/validate")
async def validate_config(key: str | None = None):
    """Valide la configuration (optionnellement une clé)."""
    service = get_service()
    return service.validate(key)


# ── /config/preferences (route littérale, déclarée AVANT /{domain}) ─────────
#
# Starlette matche les routes DANS L'ORDRE : sans ces routes littérales,
# `/config/preferences` ne serait qu'un `/{domain}` générique — invisible pour
# un client (et pour le contrat WebUI/API), avec un gate de permission lu
# dans `request.path_params` au lieu d'être déclaré. Le domaine reste détenu
# par le Core ; l'API n'est qu'une passerelle.
#
# `preferences` = préférences de l'utilisateur connecté (modèle actif, agent,
# mode de chat) : permission `WRITE` et non `SETTINGS`.


@router.get("/preferences")
async def get_preferences():
    """Préférences de l'utilisateur connecté."""
    return get_service().get_domain("preferences")


@router.put("/preferences", dependencies=[Depends(require_permission(Permission.WRITE))])
async def set_preferences(data: dict[str, Any]):
    """Remplace les préférences — état réellement persisté, 503 sinon."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    return await _write_domain(get_service(), "preferences", data)


@router.patch("/preferences", dependencies=[Depends(require_permission(Permission.WRITE))])
async def patch_preferences(data: dict[str, Any]):
    """Fusion partielle des préférences — état réellement persisté, 503 sinon."""
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    service = get_service()
    merged = _deep_merge(service.get_domain("preferences"), data)
    return await _write_domain(service, "preferences", merged)


# ── GET /config/{domain} ────────────────────────────────────────────────────


@router.get("/{domain}")
async def get_domain(domain: str):
    """Retourne la configuration d'un domaine."""
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    return service.get_domain(domain)


# ── PUT /config/{domain} ────────────────────────────────────────────────────


@router.put(
    "/{domain}",
    dependencies=[Depends(require_permission(Permission.SETTINGS))],
)
async def set_domain(domain: str, data: dict[str, Any]):
    """Remplace complètement la configuration d'un domaine.

    Retourne l'état **réellement persisté** — jamais la requête brute.
    503 si le backend durable refuse l'écriture.
    """
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    return await _write_domain(service, domain, data)


# ── PATCH /config/{domain} ──────────────────────────────────────────────────


@router.patch(
    "/{domain}",
    dependencies=[Depends(require_permission(Permission.SETTINGS))],
)
async def patch_domain(domain: str, data: dict[str, Any]):
    """Met à jour partiellement un domaine (fusion récursive).

    Retourne l'état **réellement persisté**.  503 si l'écriture échoue.
    """
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")

    current = service.get_domain(domain)
    merged = _deep_merge(current, data)
    return await _write_domain(service, domain, merged)


# ── DELETE /config/{domain}/{key} ───────────────────────────────────────────


@router.delete(
    "/{domain}/{key}",
    dependencies=[Depends(require_permission(Permission.SETTINGS))],
)
async def delete_key(domain: str, key: str):
    """Supprime une clé de configuration dans un domaine.

    503 si la suppression n'a pas pu être persistée (elle n'est alors pas
    annoncée comme supprimée).
    """
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    full_key = f"{domain}.{key}"
    try:
        deleted = await service.delete(full_key)
    except ConfigPersistenceError as e:
        logger.error("Configuration delete failed for %s: %s", full_key, e)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "persistence_failed",
                "key": full_key,
                "message": "Key was NOT deleted; the durable store rejected the write.",
                "reason": str(e),
            },
        ) from e
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Key '{full_key}' not found")
    return {"status": "deleted", "key": full_key}


# ── POST /config/import ─────────────────────────────────────────────────────


@router.post(
    "/import",
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def import_config(data: dict[str, Any]):
    """Importe une configuration (remplace les domaines fournis).

    Gate ``ADMIN`` (et non ``SETTINGS``) : l'import remplace **plusieurs**
    domaines d'un seul coup — un import ciblé peut donc éteindre une
    compétence entière du système.  C'est une opération d'administration, pas
    un réglage.
    """
    service = get_service()
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    result = await service.import_(data)
    if result["errors"]:
        raise HTTPException(status_code=422, detail=result)
    return result


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Fusionne récursivement override dans base."""
    import copy

    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result
