"""API Keys admin router — /v1/api-keys

Règle de sécurité (policy « secret once ») :
  - la clé en clair (ethan_...) est retournée UNIQUEMENT par POST (création)
    et par la route de rotation (POST /{key_id}/rotate) ;
  - stockage exclusif en SHA-256 (key_hash) côté Core — jamais de plaintext
    persisté, donc jamais renvoyable ;
  - GET liste des enregistrements SANS key_hash ni clé en clair ;
  - DELETE = révocation (soft-revoke, traçabilité conservée) ;
  - POST /{key_id}/rotate = rotation (révocation + recréation) ;
  - expiration optionnelle (`expires_at`, ISO-8601) ;
  - gate Permission.ADMIN sur toutes les routes ;
  - chaque action sensible (create / rotate / revoke) est loggée dans l'audit
    (catégorie SECURITY) — sans jamais y écrire le secret.

Aucune logique métier ici : délégation totale à core/auth/api_keys.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import Permission
from core.auth.api_keys import APIKeyManager
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])

_api_keys: APIKeyManager | None = None
_audit = None


def configure_api_keys(manager: APIKeyManager, audit_store=None) -> None:
    global _api_keys, _audit
    _api_keys = manager
    _audit = audit_store


def _require_manager() -> APIKeyManager:
    if _api_keys is None:
        raise HTTPException(503, "API key manager not initialized")
    return _api_keys


def _audit_log(action: str, key_id: str, user: str, **details) -> None:
    if _audit is None:
        return
    try:
        _audit.log(
            category="security",
            decision="allowed",
            action=f"api_key.{action}",
            actor=user or "system",
            source="api",
            details={**details, "resource": f"api-key:{key_id}"},
        )
    except Exception:
        pass  # L'audit ne doit jamais bloquer l'action métier.


def _public_view(record: dict) -> dict:
    """Vue publique : jamais de key_hash, jamais de clé en clair."""
    return {k: v for k, v in record.items() if k not in ("key_hash", "key", "secret")}


class CreateKeyRequest(BaseModel):
    name: str
    scopes: list[str] | None = None
    expires_at: str | None = None  # ISO-8601 ; expiration optionnelle.


@router.post("", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def create_api_key(
    body: CreateKeyRequest,
    user: str,
):
    """Crée une clé. Le plaintext n'apparaît QUE dans cette réponse."""
    if not user:
        raise HTTPException(422, "authenticated user required")
    if not body.name.strip():
        raise HTTPException(422, "name is required")
    manager = _require_manager()
    result = await manager.create_key(
        user_id=user,
        name=body.name.strip(),
        scopes=body.scopes or None,
        expires_at=body.expires_at or None,
    )
    key_id = result.get("id", "")
    _audit_log(
        "create", key_id, user,
        name=body.name.strip(),
        scopes=body.scopes,
        expires_at=body.expires_at,
    )
    # key_hash n'a aucune utilité côté client : réponse = vue publique + clé.
    return {**_public_view(result), "key": result["key"]}


@router.get("", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def list_api_keys():
    """Liste publique : SANS key_hash, SANS key en clair."""
    manager = _require_manager()
    keys = await manager.list_keys()
    return [_public_view(k) for k in keys]


@router.post("/{key_id}/rotate", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def rotate_api_key(
    key_id: str,
    user: str,
):
    """Rotation : révoque l'ancienne clé et en crée une nouvelle.

    Le nouveau plaintext n'apparaît QUE dans cette réponse.
    """
    if not user:
        raise HTTPException(422, "authenticated user required")
    manager = _require_manager()
    existing = [
        k for k in await manager.list_keys()
        if k.get("id") == key_id and k.get("active")
    ]
    if not existing:
        raise HTTPException(404, "API key not found or already revoked")
    result = await manager.rotate_key(key_id)
    if result is None:
        raise HTTPException(409, "rotation failed")
    new_id = result.get("id", "")
    _audit_log("rotate", new_id, user, name=result.get("name"))
    return {**_public_view(result), "key": result["key"]}


@router.delete("/{key_id}", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def revoke_api_key(
    key_id: str,
    user: str,
):
    """Révocation (soft-revoke Core : active=False + revoked_at)."""
    manager = _require_manager()
    existing = [k for k in await manager.list_keys() if k.get("id") == key_id]
    if not existing:
        raise HTTPException(404, "API key not found")
    await manager.revoke_key(key_id)
    record = next(
        (k for k in await manager.list_keys() if k.get("id") == key_id),
        existing[0],
    )
    _audit_log("revoke", key_id, user or "unknown")
    return _public_view(record)
