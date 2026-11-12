"""Router API — Health checks."""
from __future__ import annotations
import os
from core.auth import Permission
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1", tags=["health"])
_health_checks = 0

def inc_health_checks() -> int:
    global _health_checks
    _health_checks += 1
    return _health_checks
def get_health_checks() -> int:
    return _health_checks

@router.get("/health", include_in_schema=False)
async def health():
    inc_health_checks()
    return {"status": "ok", "service": "ethan-api"}

@router.get("/health/rust", dependencies=[Depends(require_permission(Permission.READ))])
async def health_rust():
    inc_health_checks()
    base_url = os.getenv("ETHAN_RUST_HEALTH_URL", "http://127.0.0.1:18081")
    try:
        from interfaces.bridge.rust.health_adapter import RustHealthClient
        client = RustHealthClient(base_url=base_url, timeout=2.0)
        return {"available": True, "rust_health": client.get_health(), "rust_version": client.get_diagnostics_version()}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"rust health unavailable: {exc}")
