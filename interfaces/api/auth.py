"""Authentication module for ETHAN API Gateway.

Provides JWT-based authentication with Bearer token support.
Routes can be marked as public (health, metrics) or protected (everything else).
"""

from __future__ import annotations

import logging
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.auth import Permission, rbac
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────

from core.auth.principal import AgentPrincipal, PrincipalType, issue_trusted_principal
from core.auth.service_identities import ServiceIdentityManager, ServiceTokenValidator, ServiceRegistryUnavailable, get_or_create_service_secret
from core.security.jwt_bootstrap import get_or_create_jwt_secret

_SECRET_KEY = os.getenv("JWT_SECRET")
if not _SECRET_KEY or _SECRET_KEY == "change-me-in-prod-generate-a-random-secret-here":
    import sys

    # In production without an explicit or file secret, fail fast
    if (
        "pytest" not in sys.modules
        and os.getenv("ETHAN_ENV", "production").lower() not in ("development", "dev", "test", "staging")
        and not os.path.exists(".secrets/jwt.key")
    ):
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. "
            "Refusing to start in production without a secure JWT signing key. "
            "Generate one with: openssl rand -base64 64 "
            "and set JWT_SECRET in your .env file."
        )
    _SECRET_KEY = get_or_create_jwt_secret()

SECRET_KEY = _SECRET_KEY
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
    "/auth/forgot-password",
    "/auth/reset-password",
    "/v1/health",
    "/v1/version",
    # ── Diagnostics système ───────────────────────────────────────────────
    # NOT in PUBLIC_PATHS — require a valid JWT so require_permission(READ) can
    # populate request.state.token_payload. Previously listed as public here
    # caused a 403 for every authenticated user (empty payload → role=None → 403).
    # Open WebUI-compatible adapter endpoints (Phase 1 — auth is public).
    "/api/v1/auths/signin",
    "/api/v1/auths/signup",
    "/api/v1/auths/",
    "/api/v1/auths/signout",
    "/openai/config",
}

security = HTTPBearer(auto_error=False)

# ── API key manager (Core-owned) — injecté au startup via set_api_key_manager ──
_api_key_manager = None


def set_api_key_manager(manager) -> None:
    global _api_key_manager
    _api_key_manager = manager


def get_api_key_manager():
    return _api_key_manager


# ── Service identity registry (Core-owned) — injecté au startup ──────────
_service_identity_manager = None


def set_service_identity_manager(manager) -> None:
    global _service_identity_manager
    _service_identity_manager = manager


def get_service_identity_manager():
    return _service_identity_manager


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
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
    """Check if a path is public (no auth required).

    Prefix checks are anchored on a trailing slash so unrelated paths such as
    ``/healthz`` or ``/docs attacker-controlled`` cannot inherit public access.
    """
    return path in PUBLIC_PATHS or any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in ("/health", "/metrics", "/docs", "/openapi.json", "/redoc")
    )


def current_user_id(request: Request | None) -> str | None:
    """Username JWT (``sub``) peuplé par ``auth_middleware``.

    Retourne ``None`` si ``request`` est None (appels directs des tests
    unitaires) ou si aucun token n'a été décodé (routes publiques). Les
    routes doivent en faire la priorité sur tout ``user_id`` fourni par le
    client — un utilisateur authentifié ne peut pas usurper un autre compte
    en envoyant un ``user_id`` différent dans le body.
    """
    if request is None:
        return None
    return getattr(request.state, "user", None)


def authenticated_user_id(request: Request | None) -> str:
    """Identité authentifiée pour une route HTTP user-scoped.

    Un ``Request`` HTTP sans identité établie par le middleware est refusé.
    La valeur ``None`` est conservée comme chemin direct unitaire
    rétro-compatible, où les tests historiques appellent le handler sans
    middleware.
    """
    if request is None:
        return "anonymous"
    uid = current_user_id(request)
    if not uid:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise.",
        )
    return uid


def _request_role(request: Request | None) -> str | None:
    payload = getattr(getattr(request, "state", None), "token_payload", None)
    if isinstance(payload, dict):
        return str(payload.get("role") or "").strip() or None
    return None


def _request_is_admin(request: Request | None) -> bool:
    # Prefer the immutable principal built from the authenticated account and
    # its RBAC roles.  The JWT role claim is only a fallback for direct or
    # legacy paths that do not carry request.state.principal.
    principal = getattr(getattr(request, "state", None), "principal", None)
    permissions = getattr(principal, "permissions", None)
    if isinstance(permissions, (tuple, list, set)):
        # The immutable principal is authoritative once authentication has
        # succeeded.  A stale or upgraded JWT claim cannot restore revoked
        # privileges.
        return Permission.ADMIN.value in {
            str(permission).strip().lower() for permission in permissions
        }

    role = _request_role(request)
    if not role:
        return False
    if role == "admin":
        return True
    try:
        return rbac.has_permission(role, Permission.ADMIN)
    except Exception:
        return False


def resolve_user_scope(
    request: Request | None, requested_user_id: str | None = None
) -> str:
    """Résout une portée utilisateur sans laisser le client choisir.

    En absence de Request (chemin unitaire historique), conserve le repli
    demandé / ``anonymous``. Sur une Request HTTP réelle, l'identité issue du
    middleware a priorité et un utilisateur non administrateur ne peut pas
    cibler un autre utilisateur.
    """
    if request is None:
        requested = None if requested_user_id is None else str(requested_user_id).strip()
        return requested or "anonymous"

    auth_uid = authenticated_user_id(request)
    requested = None if requested_user_id is None else str(requested_user_id).strip()
    if not requested or requested == auth_uid:
        return auth_uid
    if _request_is_admin(request):
        return requested
    from fastapi import HTTPException, status

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé à l'identité d'un autre utilisateur.",
    )


async def auth_middleware(request: Request, call_next):
    """FastAPI middleware that enforces JWT or API-key authentication on protected routes.

    Usage in main.py:
        app.middleware("http")(auth_middleware)
    """
    path = request.url.path

    # Public paths: skip auth
    if is_public_path(path):
        return await call_next(request)

    # Protected paths: require valid cookie, Bearer token, or API key
    token = request.cookies.get("ethan_token")
    if not token:
        # Fallback to Authorization header if provided
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    api_key = request.headers.get("X-API-Key")
    # A Bearer token that looks like an ETHAN API key is treated as one too.
    if token and token.startswith("ethan_"):
        api_key = token
        token = None

    if not token and not api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentification requise. Cookie ou Token manquant."},
        )

    # Service identity path: a JWT whose unverified type is "service".
    service_token_candidate = None
    if token and not api_key:
        try:
            from jose import jwt as _jose_jwt
            _unverified = _jose_jwt.get_unverified_claims(token)
        except Exception:
            _unverified = {}
        if str(_unverified.get("typ") or "").strip().lower() == "service" or str(_unverified.get("iss") or "").strip() == "ethan.service":
            service_token_candidate = token
            token = None
            api_key = None

    if service_token_candidate:
        manager = get_service_identity_manager()
        if manager is None:
            return JSONResponse(
                status_code=503,
                content={"detail": "Service identity manager not initialized."},
            )
        validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)
        try:
            result = await validator.validate(service_token_candidate)
        except ServiceRegistryUnavailable as exc:  # noqa: BLE001
            logger.warning("Service registry unavailable: %s", exc)
            return JSONResponse(status_code=503, content={"detail": "Service identity authority unavailable."})
        if result is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Service authentication required or invalid."},
            )
        record, payload = result
        scopes = sorted(set(payload.get("allowed_operations") or record.get("allowed_operations") or []))
        subject = str(record.get("service_id") or payload.get("service_id"))
        request.state.api_key_record = None
        request.state.service_identity_record = record
        request.state.user = f"service:{subject}"
        request.state.token_payload = {
            "sub": subject,
            "service_id": subject,
            "component": record.get("component"),
            "role": "service",
            "typ": "service",
            "scope": scopes,
            "scopes": scopes,
            "allowed_operations": scopes,
            "jti": payload.get("jti"),
            "rotation_id": payload.get("rotation_id"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
        }
        request.state.principal = await build_agent_principal(request)
        if request.state.principal is None:
            return JSONResponse(status_code=401, content={"detail": "Service authentication failed."})
        return await call_next(request)

    # API key path (server-to-server, e.g. GEV)
    if api_key and not token:
        manager = get_api_key_manager()
        if manager is None:
            return JSONResponse(
                status_code=503,
                content={"detail": "API key manager not initialized."},
            )
        try:
            key = await manager.validate_key(api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("API key validation failed: %s", exc)
            key = None
        if key is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Clé API invalide ou expirée."},
            )
        scopes = list(key.get("scopes") or [])
        subject = key.get("user_id")
        request.state.api_key_record = key
        request.state.user = subject
        request.state.principal = await build_agent_principal(request)
        if request.state.principal is None:
            return JSONResponse(status_code=401, content={"detail": "Authentification requise. Identité non validée."})
        request.state.token_payload = {
            "sub": subject,
            "role": "api-key",
            "scope": scopes,
            "scopes": scopes,
        }
        return await call_next(request)

    try:
        payload = await verify_token_string(token)
        # Injecter les infos utilisateur dans request.state pour les routes
        request.state.user = payload.get("sub", "unknown")
        request.state.token_payload = payload
        request.state.principal = await build_agent_principal(request)
        if request.state.principal is None:
            return JSONResponse(status_code=401, content={"detail": "Authentification requise. Identité non validée."})
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



def _permission_names(role: str) -> list[str]:
    """Return permission names granted by the centralized RBAC engine."""
    role_record = rbac.get_role(role)
    if role_record is None:
        return []
    return [permission.value for permission in getattr(role_record, "permissions", [])]


async def build_agent_principal(request: Request) -> AgentPrincipal | None:
    """Build a read-only AgentPrincipal from verified middleware state."""
    if request is None:
        return None

    existing_principal = getattr(request.state, "principal", None)
    if isinstance(existing_principal, AgentPrincipal) and existing_principal.principal_type is PrincipalType.SERVICE:
        return existing_principal

    token_payload = getattr(request.state, "token_payload", None) or {}
    service_record = getattr(request.state, "service_identity_record", None)
    if isinstance(service_record, dict) and isinstance(token_payload, dict) and token_payload.get("typ") == "service":
        subject = str(service_record.get("service_id") or token_payload.get("service_id") or "").strip()
        scopes = list(token_payload.get("allowed_operations") or token_payload.get("scopes") or service_record.get("allowed_operations") or [])
        if subject:
            expires = None
            try:
                expires = datetime.fromtimestamp(float(token_payload.get("exp")), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                expires = None
            return issue_trusted_principal(AgentPrincipal(
                principal_id=f"service:{subject}",
                principal_type=PrincipalType.SERVICE,
                subject_id=subject,
                actor_id=subject,
                initiator_id=subject,
                permissions=tuple(str(scope).strip() for scope in scopes if str(scope).strip() and str(scope).strip().lower() != "admin"),
                scopes=tuple(str(scope).strip() for scope in scopes if str(scope).strip() and str(scope).strip().lower() != "admin"),
                owner_id=subject,
                request_id=_request_id(request),
                expires_at=expires,
                auth_method="service_jwt",
            ))

    # Reconstruct a service principal from the presented token if available.
    _cookie_token = request.cookies.get("ethan_token")
    _auth_header = request.headers.get("Authorization", "")
    _service_token = _cookie_token
    if _auth_header.startswith("Bearer ") and not (_cookie_token and _cookie_token.startswith("ethan_")):
        _service_token = _auth_header.split(" ", 1)[1].strip()
    try:
        from jose import jwt as _jose_jwt
        _unverified = _jose_jwt.get_unverified_claims(_service_token or "")
    except Exception:
        _unverified = {}
    if _unverified.get("typ") == "service" or _unverified.get("iss") == "ethan.service":
        manager = get_service_identity_manager()
        if manager is not None:
            validator = ServiceTokenValidator(registry=manager, signing_secret=manager.secret)
            try:
                result = await validator.validate(_service_token)
            except ServiceRegistryUnavailable:
                result = None
            if result is not None:
                record, payload = result
                subject = str(record.get("service_id") or payload.get("service_id") or "").strip()
                scopes = list(payload.get("allowed_operations") or record.get("allowed_operations") or [])
                if subject:
                    expires = None
                    try:
                        expires = datetime.fromtimestamp(float(payload.get("exp")), tz=timezone.utc)
                    except (TypeError, ValueError, OverflowError):
                        expires = None
                    return issue_trusted_principal(AgentPrincipal(
                        principal_id=f"service:{subject}",
                        principal_type=PrincipalType.SERVICE,
                        subject_id=subject,
                        actor_id=subject,
                        initiator_id=subject,
                        permissions=tuple(str(scope).strip() for scope in scopes if str(scope).strip() and str(scope).strip().lower() != "admin"),
                        scopes=tuple(str(scope).strip() for scope in scopes if str(scope).strip() and str(scope).strip().lower() != "admin"),
                        owner_id=subject,
                        request_id=_request_id(request),
                        expires_at=expires,
                        auth_method="service_jwt",
                    ))
        return None

    # API-key identity previously validated by the middleware.
    cookie_token = request.cookies.get("ethan_token")
    auth_header = request.headers.get("Authorization", "")
    api_key = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") and auth_header.split(" ", 1)[1].strip().startswith("ethan_") else None
    if api_key is None and cookie_token and cookie_token.startswith("ethan_"):
        api_key = cookie_token

    api_key_record = getattr(request.state, "api_key_record", None)
    token_payload = getattr(request.state, "token_payload", None) or {}

    if api_key or (isinstance(token_payload, dict) and token_payload.get("role") == "api-key"):
        if api_key_record is None and api_key:
            manager = get_api_key_manager()
            if manager is not None:
                try:
                    api_key_record = await manager.validate_key(api_key)
                except Exception:
                    api_key_record = None
        if not isinstance(api_key_record, dict) or not api_key_record.get("active"):
            return None

        subject = str(api_key_record.get("user_id") or "").strip()
        if not subject:
            return None

        raw_scopes = [str(scope).strip() for scope in (api_key_record.get("scopes") or []) if str(scope).strip()]
        # Scopes are not RBAC permissions, and an API key is never allowed to
        # carry the administrative permission through a scope named "admin".
        safe_scopes = [scope for scope in raw_scopes if scope.lower() != "admin"]

        raw_expiry = api_key_record.get("expires_at")
        if raw_expiry:
            try:
                datetime.fromisoformat(str(raw_expiry).replace("Z", "+00:00"))
            except ValueError:
                return None
        expires_at = _parse_api_key_expiry(raw_expiry)

        active = api_key_record.get("active")
        if active is not True:
            return None

        return issue_trusted_principal(AgentPrincipal(
            principal_id=f"api-key:{subject}",
            principal_type=PrincipalType.API_KEY,
            subject_id=subject,
            actor_id=subject,
            initiator_id=subject,
            permissions=tuple(safe_scopes),
            scopes=tuple(safe_scopes),
            owner_id=subject,
            request_id=_request_id(request),
            expires_at=expires_at,
            auth_method="api_key",
        ))

    # Prefer the already-populated middleware state to avoid duplicate lookups.
    user = current_user_id(request)
    payload_role = None
    payload = getattr(request.state, "token_payload", None)
    if isinstance(payload, dict):
        user = user or str(payload.get("sub") or "").strip() or None
        payload_role = str(payload.get("role") or "").strip() or None

    if not user:
        return None

    user_record = None
    if fetch_user_record.__name__ != "fetch_user_record_placeholder":
        try:
            user_record = await fetch_user_record(user)
        except Exception:
            user_record = None

    # Fail closed: a protected HUMAN principal cannot be built from a JWT
    # role claim alone. The persistent account must exist and provide either
    # an explicit role or no fallback path to retained JWT privileges.
    if not isinstance(user_record, dict):
        return None
    if not user_record.get("is_active", False):
        return None
    roles = user_record.get("roles")
    if isinstance(roles, list) and roles:
        role = str(roles[0]).strip()
    else:
        return None

    if not role:
        return None

    params = _permission_names(role)

    expires = None
    exp = payload.get("exp") if isinstance(payload, dict) else None
    expires = _datetime_from_epoch(exp)

    if expires is not None and expires < datetime.now(timezone.utc):
        return None

    return issue_trusted_principal(AgentPrincipal(
        principal_id=user,
        principal_type=PrincipalType.HUMAN,
        subject_id=user,
        actor_id=user,
        initiator_id=user,
        permissions=tuple(params),
        scopes=tuple(params),
        owner_id=user,
        request_id=_request_id(request),
        expires_at=expires,
        auth_method="jwt",
    ))


def _request_id(request: Request) -> str:
    for header in ("X-Request-Id", "X-Request-ID"):
        candidate = request.headers.get(header)
        if candidate:
            try:
                request.state.request_id = str(candidate)
            except Exception:
                pass
            return str(candidate)
    candidate = str(uuid4())
    try:
        request.state.request_id = candidate
    except Exception:
        pass
    return candidate



def _datetime_from_epoch(value: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None



def _parse_api_key_expiry(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def require_service_operation(operation: str):
    """FastAPI dependency requiring a verified SERVICE principal with operation.

    This is independent of RBAC roles: a service only has the operations
    present in both the server registry and the validated token.
    """

    def checker(request: Request):
        principal = getattr(request.state, "principal", None)
        if (
            not isinstance(principal, AgentPrincipal)
            or principal.principal_type is not PrincipalType.SERVICE
            or operation not in (principal.permissions or ())
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service operation not authorized.",
            )
        return True

    checker.service_operation = operation
    return checker

# Aliases for central access.
current_principal = build_agent_principal
get_agent_principal = build_agent_principal
principal_from_request = build_agent_principal

def require_memory_scope(scope: str, *, permission: Permission | None = None):
    """FastAPI dependency requiring a memory scope (machine) or an RBAC permission.

    Les clients machine-à-machine (plugin OpenCode, CLI, service externe)
    ne portent pas un rôle RBAC : ils portent une **portée** (scope), portée
    par le principal HROT (`AgentPrincipal.permissions`). Cette dépendance
    accepte donc les deux formes d'autorisation :

    * une clé de service / un JWT de service dont la portée demandée est
      présente dans le principal vérifié ;
    * un rôle RBAC disposant de la permission demandée (session humaine).

    Elle s'appuie sur le même mécanisme que `require_service_operation` :
    c'est le **principal vérifié** qui fait foi, jamais une affirmation du
    client.

    Args:
        scope: Portée exigée (ex. `memory:traceability`).
        permission: Permission RBAC exigée en repli (par défaut `RECORD`).

    Returns:
        Dépendance FastAPI utilisable via `Depends(...)`.
    """
    fallback_permission = permission or Permission.RECORD

    async def scope_checker(request: Request):
        principal = getattr(request.state, "principal", None)
        if isinstance(principal, AgentPrincipal) and scope in (principal.permissions or ()):
            return True

        payload = getattr(request.state, "token_payload", {}) or {}
        raw_scopes = payload.get("scopes") or payload.get("scope") or []
        if isinstance(raw_scopes, str):
            raw_scopes = [raw_scopes]
        if scope in raw_scopes:
            return True

        role = payload.get("role")
        if role and rbac.has_permission(role, fallback_permission):
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accès refusé. Portée requise : {scope}",
        )

    # Attributs déclaratifs : le contrat d'introspection doit pouvoir relire
    # la portée et la permission exigées sans exécuter le gate.
    scope_checker.scope = scope
    scope_checker.permission = fallback_permission
    scope_checker.permissions = [fallback_permission]
    return scope_checker


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
                detail=f"Accès refusé. Permission requise : {permission.value}",
            )
        return True

    # Contrat d'introspection : FastAPI ne conserve que la closure, or les
    # tests de frontière RBAC (et toute matrice « permissions par route »
    # générée pour l'audit) doivent pouvoir relire la permission exigée sans
    # exécuter le gate. Attributs purement déclaratifs — aucun effet sur
    # l'exécution ni sur le comportement d'authentification.
    permission_checker.permission = permission
    permission_checker.permissions = [permission]

    return permission_checker


async def fetch_user_record(username: str) -> dict[str, object] | None:
    """Read one user's persisted authentication record.

    The Realtime WebSocket needs the same source of truth as login. The route
    itself cannot infer account status from the JWT: the token only carries a
    claim, so a re-enabled or disabled account would otherwise remain valid
    until token expiry.
    """
    if not username:
        return None
    try:
        import asyncio

        import asyncpg
    except ImportError:
        return None

    db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
    try:
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=2.0)
    except Exception:  # noqa: BLE001 - connection failure must deny access
        logger.warning("Could not fetch user record for WebSocket authentication.")
        return None
    try:
        row = await conn.fetchrow(
            "SELECT username, roles, is_active FROM users WHERE username = $1",
            username,
        )
        return dict(row) if row is not None else None
    except Exception:  # noqa: BLE001 - deny on unexpected storage error
        logger.warning("Unexpected error while fetching user record for WebSocket.")
        return None
    finally:
        await conn.close()


def normalized_ws_origins() -> tuple[str, ...]:
    """Return the configured browser origins allowed to open Realtime WS.

    A missing environment value keeps localhost-only defaults. Missing Origin
    headers (non-browser clients) are authorized separately at call site; the
    default is never a wildcard.
    """
    raw = os.getenv("ETHAN_ALLOWED_WS_ORIGINS", "").strip()
    if raw:
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    return ("http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1")
