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

from fastapi import APIRouter, HTTPException

from core.auth import Permission
from interfaces.api.auth import require_permission
from core.config import ConfigurationService, DOMAINS, config_to_json_schema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])

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


# ── GET /config/{domain} ────────────────────────────────────────────────────

@router.get("/{domain}")
async def get_domain(domain: str):
    """Retourne la configuration d'un domaine."""
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    return service.get_domain(domain)


# ── PUT /config/{domain} ────────────────────────────────────────────────────

@router.put("/{domain}")
async def set_domain(domain: str, data: dict[str, Any]):
    """Remplace complètement la configuration d'un domaine."""
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    await service.set_domain(domain, data)
    return service.get_domain(domain)


# ── PATCH /config/{domain} ──────────────────────────────────────────────────

@router.patch("/{domain}")
async def patch_domain(domain: str, data: dict[str, Any]):
    """Met à jour partiellement un domaine (fusion récursive)."""
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")

    current = service.get_domain(domain)
    merged = _deep_merge(current, data)
    await service.set_domain(domain, merged)
    return service.get_domain(domain)


# ── DELETE /config/{domain}/{key} ───────────────────────────────────────────

@router.delete("/{domain}/{key}")
async def delete_key(domain: str, key: str):
    """Supprime une clé de configuration dans un domaine."""
    service = get_service()
    if domain not in DOMAINS:
        raise HTTPException(status_code=404, detail=f"Unknown domain '{domain}'")
    full_key = f"{domain}.{key}"
    deleted = await service.delete(full_key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Key '{full_key}' not found")
    return {"status": "deleted", "key": full_key}


# ── POST /config/import ─────────────────────────────────────────────────────

@router.post("/import")
async def import_config(data: dict[str, Any]):
    """Importe une configuration (remplace les domaines fournis)."""
    service = get_service()
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Body must be a dict")
    result = await service.import_(data)
    if result["errors"]:
        raise HTTPException(status_code=422, detail=result)
    return result


# ── GET /config/export ──────────────────────────────────────────────────────

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