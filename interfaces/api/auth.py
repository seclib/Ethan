"""Authentication module for ETHAN API Gateway.

Provides JWT-based authentication with Bearer token support.
Routes can be marked as public (health, metrics) or protected (everything else).
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from starlette.responses import JSONResponse

from core.auth import rbac, Permission

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-prod-generate-a-random-secret-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# Routes qui ne nécessitent pas d'authentification
PUBLIC_PATHS = {
    "/health",
    "/health/detailed",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/auth/register",
    "/v1/health",
    "/v1/version",
    # Open WebUI-compatible adapter endpoints (Phase 1 — auth is public).
    "/api/v1/auths/signin",
    "/api/v1/auths/signup",
    "/api/v1/auths/",
    "/api/v1/auths/signout",
    "/openai/config",
}

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token_string(token: str) -> dict:
    """Verify a JWT token string and return its payload.

    Raises HTTPException 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide ou expiré.",
        )

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> dict:
    """Legacy helper for verifying Authorization header credentials."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await verify_token_string(credentials.credentials)


def is_public_path(path: str) -> bool:
    """Check if a path is public (no auth required)."""
    return path in PUBLIC_PATHS or path.startswith(("/health", "/metrics", "/docs", "/openapi.json", "/redoc"))


async def auth_middleware(request: Request, call_next):
    """FastAPI middleware that enforces JWT authentication on protected routes.

    Usage in main.py:
        app.middleware("http")(auth_middleware)
    """
    path = request.url.path

    # Public paths: skip auth
    if is_public_path(path):
        return await call_next(request)

    # Protected paths: require valid cookie or Bearer token
    token = request.cookies.get("ethan_token")
    if not token:
        # Fallback to Authorization header if provided
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentification requise. Cookie ou Token manquant."},
        )

    try:
        payload = await verify_token_string(token)
        # Injecter les infos utilisateur dans request.state pour les routes
        request.state.user = payload.get("sub", "unknown")
        request.state.token_payload = payload
    except HTTPException as exc:
        # Une HTTPException levée directement depuis un middleware ASGI ne
        # passe pas par le gestionnaire FastAPI et devenait donc un 500.
        # Retourner explicitement la réponse d'authentification attendue.
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers or {},
        )

    return await call_next(request)


def require_permission(permission: Permission):
    """
    FastAPI dependency to enforce RBAC permissions.
    Expects auth_middleware to have populated request.state.token_payload.
    
    Usage:
        @router.get("/something", dependencies=[Depends(require_permission(Permission.READ))])
    """
    def permission_checker(request: Request):
        payload = getattr(request.state, "token_payload", {})
        role = payload.get("role")
        
        if not role or not rbac.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Permission requise : {permission.value}"
            )
        return True
        
    return permission_checker
