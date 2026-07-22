"""Authentication module for ETHAN API Gateway.

Provides JWT-based authentication with Bearer token support.
Routes can be marked as public (health, metrics) or protected (everything else).
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

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
}

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> dict:
    """Verify a JWT token and return its payload.

    Raises HTTPException 401 if token is invalid or missing.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise. Utilisez un Bearer token JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )


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

    # Protected paths: require valid Bearer token
    credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
    try:
        payload = await verify_token(credentials)
        # Injecter les infos utilisateur dans request.state pour les routes
        request.state.user = payload.get("sub", "unknown")
        request.state.token_payload = payload
    except HTTPException:
        raise

    return await call_next(request)