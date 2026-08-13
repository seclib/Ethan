"""API Gateway — entry point for the Ethan Cognitive OS.

NOTE: This file relies on the 'ethan' package being installed in editable mode:
    pip install -e ".[server]"

If you encounter import errors, run the command above from the project root.
"""

from __future__ import annotations

import json
import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi.middleware import SlowAPIMiddleware

import nats

from core.telemetry.logger import setup_logging
from interfaces.api.routers.message import router as message_router, set_nats_client
from interfaces.api.routers.state import router as state_router
from interfaces.api.routers.internal import router as internal_router, init_modules
from interfaces.api.routers.v1 import (
    CoreDomainServices,
    router as v1_router,
    set_core_domain_services,
    set_provider_manager as set_v1_provider_manager,
)
from interfaces.api.routers.providers import router as providers_router, set_provider_manager
from interfaces.api.routers.config import router as config_router, set_configuration_service
from interfaces.api.routers.domains import router as domains_router, set_domain_managers
from interfaces.api.routers.capabilities import (
    CapabilityManagers,
    router as capabilities_router,
    set_capability_managers,
)
from interfaces.api.routers.v1 import set_webui_store
from core.config import ConfigurationService, ConfigStore
from core.state import CoreRecordStore
from core.state.webui_store import CoreWebUIStore
from interfaces.api.auth import auth_middleware, create_access_token, verify_token, verify_token_string, security
from interfaces.api.rate_limit import limiter, rate_limit_exceeded_handler
from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from core.agents import AgentManager
from core.knowledge import KnowledgeManager
from core.missions import MissionManager
from core.rag import RAGPipeline

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    HAS_PROMETHEUS = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PROMETHEUS = False

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from core.telemetry import init_telemetry
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False

    def generate_latest(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("prometheus_client is not installed")

    CONTENT_TYPE_LATEST = "text/plain; version=0.4"


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # --- Startup ---
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    logger.info(f"API Gateway connecting to NATS: {nats_url}")
    startup_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )

    for attempt in range(1, 11):
        try:
            remaining = startup_deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError("API dependency startup deadline exceeded")
            nc = await asyncio.wait_for(
                nats.connect(nats_url, name="api-gateway"), timeout=min(10, remaining)
            )
            set_nats_client(nc)
            logger.info("API Gateway connected to NATS")
            break
        except Exception as exc:
            if attempt == 10:
                logger.error("API Gateway could not connect to NATS after %s attempts", attempt)
                raise
            wait = min(attempt * 2, 10)
            wait = min(wait, max(0.0, startup_deadline - asyncio.get_running_loop().time()))
            logger.warning(
                "NATS connection failed (%s), retry %s/10 in %ss",
                exc,
                attempt,
                wait,
            )
            await asyncio.sleep(wait)

    init_modules(pg_conn=None)

    # --- LLM Provider Manager ---
    # Store (persistance) + Manager (logique) pour les providers LLM.
    # Redis/PG sont optionnels : en leur défaut, le ProviderStore bascule
    # automatiquement en mode mémoire.
    redis_client = None
    pg_pool = None
    provider_manager: ProviderManager | None = None
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan@postgres:5432/ethan")

    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(redis_url, decode_responses=True, protocol=2)
        await asyncio.wait_for(redis_client.ping(), timeout=5)
        logger.info("ProviderManager Redis cache connected")
    except Exception as exc:
        logger.warning("Redis unavailable for ProviderStore, using in-memory only: %s", exc)

    try:
        import asyncpg
        pg_pool = await asyncio.wait_for(
            asyncpg.create_pool(db_url, min_size=1, max_size=5), timeout=10
        )
        logger.info("ProviderManager PostgreSQL pool connected")
    except Exception as exc:
        logger.warning("PostgreSQL unavailable for ProviderStore, using in-memory only: %s", exc)

    # --- Core domain managers ---
    # The API owns only dependency composition.  The managers and their record
    # store live in core/ and remain usable by the CLI or another interface.
    domain_store = CoreRecordStore(pg_pool=pg_pool, redis_client=redis_client)
    core_domains = CoreDomainServices(
        agents=AgentManager(store=domain_store),
        missions=MissionManager(store=domain_store),
        knowledge=KnowledgeManager(store=domain_store),
        rag=RAGPipeline(store=domain_store),
    )
    set_core_domain_services(core_domains)
    app.state.core_domains = core_domains
    logger.info("Core domain managers ready")

    # --- Domain managers (chats, files, users, groups) ---
    from core.auth.groups import GroupManager
    from core.auth.users import UserManager
    from core.state.chats import ChatStore
    from core.state.files import FileStore

    set_domain_managers(
        chats=ChatStore(store=domain_store),
        files=FileStore(store=domain_store),
        users=UserManager(store=domain_store),
        groups=GroupManager(store=domain_store),
    )
    logger.info("Domain managers ready (chats, files, users, groups)")

    # --- WebUI-facing records store (goals, facts, skills, events, settings, providers, plugins) ---
    # Replaces the old process-local MemoryStore in routers/v1.py.  Persistence
    # lives in Core (CoreRecordStore) so the interface stays a thin HTTP gateway.
    webui_store = CoreWebUIStore(store=domain_store)
    set_webui_store(webui_store)
    app.state.webui_store = webui_store
    logger.info("CoreWebUIStore ready (persistent WebUI records)")

    # --- Capability managers (automations, calendar, tts, images, evaluations,
    #     analytics, channels, notes, tool servers, functions, prompts, scim) ---
    # All managers are Core-owned and share the same CoreRecordStore.  They are
    # injected here so the capabilities router stays a thin HTTP gateway.
    from core.scheduler.automations import AutomationManager
    from core.scheduler.calendar import CalendarManager
    from core.llm.tts import TTSEngine
    from core.llm.images import ImageGenerator
    from core.learning.evaluations import EvaluationManager
    from core.metrics.analytics import AnalyticsManager
    from core.state.channels import ChannelStore
    from core.state.notes import NoteStore
    from core.tools.servers import ToolServerManager
    from core.tools.functions import FunctionManager
    from core.config.prompts import PromptManager
    from core.auth.scim import SCIMManager

    capability_managers = CapabilityManagers(
        automations=AutomationManager(store=domain_store),
        calendar=CalendarManager(store=domain_store),
        tts=TTSEngine(store=domain_store),
        images=ImageGenerator(store=domain_store),
        evaluations=EvaluationManager(store=domain_store),
        analytics=AnalyticsManager(store=domain_store),
        channels=ChannelStore(store=domain_store),
        notes=NoteStore(store=domain_store),
        tool_servers=ToolServerManager(store=domain_store),
        functions=FunctionManager(store=domain_store),
        prompts=PromptManager(store=domain_store),
        scim=SCIMManager(store=domain_store),
    )
    set_capability_managers(capability_managers)
    app.state.capability_managers = capability_managers
    logger.info("Capability managers ready (12 Core capabilities exposed)")

    try:
        store = ProviderStore(redis_client=redis_client, pg_pool=pg_pool)
        provider_manager = ProviderManager(store=store)
        await provider_manager.initialize()
        set_provider_manager(provider_manager)
        set_v1_provider_manager(provider_manager)
        logger.info("ProviderManager ready (default=%s, providers=%d)",
                    provider_manager._default_provider,
                    len(provider_manager._registry.list_providers()))
    except Exception as exc:
        logger.exception("Failed to initialize ProviderManager: %s", exc)
        provider_manager = None

    # --- Configuration Service (source de vérité unique) ---
    try:
        config_store = ConfigStore(redis_client=redis_client, pg_pool=pg_pool)
        config_service = ConfigurationService(store=config_store)
        await config_service.load()
        set_configuration_service(config_service)
        app.state.config_service = config_service
        logger.info("ConfigurationService ready")
    except Exception as exc:
        logger.exception("Failed to initialize ConfigurationService: %s", exc)

    if HAS_TELEMETRY:
        try:
            init_telemetry("ethan-api")
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry tracing enabled for API Gateway")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")

    yield

    # --- Shutdown ---
    from interfaces.api.routers import message as _message_router
    nc = _message_router._nats
    if nc:
        try:
            await asyncio.wait_for(nc.drain(), timeout=10)
            logger.info("API Gateway NATS connection closed")
        except Exception as e:
            logger.error(f"Error during NATS shutdown: {e}")

    # Fermer le.ProviderManager (clients providers + store/redis)
    if provider_manager is not None:
        try:
            await provider_manager.close()
            logger.info("ProviderManager closed")
        except Exception as exc:
            logger.warning("Error closing ProviderManager: %s", exc)
    if pg_pool is not None:
        try:
            await asyncio.wait_for(pg_pool.close(), timeout=5)
        except Exception as exc:
            logger.warning("Error closing PostgreSQL pool: %s", exc)

app = FastAPI(
    title="Ethan Cognitive OS API",
    version="0.2.0",
    description="Event-driven cognitive operating system API Gateway",
    lifespan=lifespan,
)

# CORS — restrict origins in production via CORS_ORIGINS env var
_cors_origins = os.getenv("CORS_ORIGINS", "*")
_cors_origins_list = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (must be before auth middleware)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(429, rate_limit_exceeded_handler)

# Middleware d'authentification JWT (protège les routes sauf /health, /metrics, /docs)
app.middleware("http")(auth_middleware)

app.include_router(message_router)
app.include_router(state_router)
app.include_router(internal_router)
app.include_router(v1_router)
app.include_router(providers_router)
app.include_router(config_router)
app.include_router(domains_router)
app.include_router(capabilities_router)


# Old startup code removed as it's now in the lifespan context manager.


@app.post("/auth/login")
async def login(request: Request, response: Response):
    """Login endpoint — returns a JWT token and sets an HttpOnly cookie."""
    import json

    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username", "developer")
    password = body.get("password", "")
    
    role = "user"
    try:
        import asyncpg
        import asyncio
        import bcrypt
        
        db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
        
        # Connect to DB with timeout
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=2.0)
        try:
            row = await conn.fetchrow("SELECT password_hash, roles, is_active FROM users WHERE username = $1", username)
            if not row:
                # Prevent timing attacks
                bcrypt.checkpw(password.encode('utf-8'), b"$2b$12$IMasHHKJXSeiAxx6kYiGf.8zkx.ueVl6/oWo61VnT0mGCbv9.CQzK")
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            if not row["is_active"]:
                raise HTTPException(status_code=401, detail="User account is disabled")
                
            if not bcrypt.checkpw(password.encode('utf-8'), row["password_hash"].encode('utf-8')):
                raise HTTPException(status_code=401, detail="Invalid username or password")
                
            role = row["roles"][0] if row["roles"] else "user"
        finally:
            await conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB Auth unavailable: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
        
    token = create_access_token(data={"sub": username, "role": role})
    
    response.set_cookie(
        key="ethan_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        path="/",
        secure=os.getenv("NODE_ENV") == "production"
    )

    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "role": "user"},
    }


@app.post("/auth/register")
async def register(request: Request):
    """Registration endpoint — public, returns a JWT token for the new user."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username") or body.get("email") or body.get("name")
    if not username:
        raise HTTPException(status_code=400, detail="Username or email is required")
    if not body.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")

    token = create_access_token(data={"sub": username, "role": "user"})
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
        "user": {"username": username, "email": body.get("email", ""), "role": "user"},
    }


@app.get("/auth/me")
async def auth_me(request: Request):
    """Return the current authenticated user from the JWT token.

    The auth middleware already validated the token and injected the user
    into request.state. We just return it.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = getattr(request.state, "token_payload", {})
    return {"user": {"username": user, "role": payload.get("role", "user")}}


@app.post("/auth/refresh")
async def auth_refresh(response: Response, credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    """Issue a new JWT token from a valid existing token."""
    # We must explicitly read the token since Depends(security) might miss the cookie if no Bearer header is present.
    token = request.cookies.get("ethan_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Authentification requise.")

    try:
        payload = await verify_token_string(token)
        username = payload.get("sub", "unknown")
        role = payload.get("role", "user")
        new_token = create_access_token(data={"sub": username, "role": role})
        
        response.set_cookie(
            key="ethan_token",
            value=new_token,
            httponly=True,
            samesite="lax",
            max_age=86400,
            path="/",
            secure=os.getenv("NODE_ENV") == "production"
        )
        
        return {
            "access_token": new_token,
            "token": new_token,
            "token_type": "bearer",
            "expires_in_hours": int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            "user": {"username": username, "role": role},
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/auth/logout")
async def auth_logout(response: Response):
    """Logout endpoint — clears the HttpOnly cookie."""
    response.delete_cookie(
        key="ethan_token",
        httponly=True,
        samesite="lax",
        path="/"
    )
    return {"status": "ok", "message": "Logged out successfully"}


@app.get("/health")
async def health():
    """Healthcheck endpoint used by Docker and scripts."""
    return await _health_readiness()


@app.get("/health/live")
async def health_live():
    """Liveness probe: the HTTP process is serving requests."""
    return {"status": "ok", "service": "api"}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe: the API can publish through its NATS connection."""
    return await _health_readiness()


async def _health_readiness() -> Response | dict:
    """Return a truthful readiness response for the API service."""
    from interfaces.api.routers import message as _message_router

    nc = _message_router._nats
    nats_ok = nc is not None and nc.is_connected
    payload = {
        "status": "ok" if nats_ok else "degraded",
        "service": "api",
        "nats_connected": nats_ok,
    }
    if not nats_ok:
        return Response(
            content=json.dumps(payload),
            status_code=503,
            media_type="application/json",
        )
    return payload


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check verifying connectivity to dependencies."""
    import asyncio
    import os
    import json

    results = {}

    from interfaces.api.routers import message as _message_router
    api_nats = _message_router._nats
    results["api_nats"] = (
        "connected" if api_nats is not None and api_nats.is_connected else "error: API NATS disconnected"
    )

    nc = None
    try:
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")
        nc = await asyncio.wait_for(nats.connect(nats_url), timeout=2)
        results["nats"] = "connected"
    except Exception as e:
        results["nats"] = f"error: {e}"
    finally:
        if nc is not None:
            try:
                await asyncio.wait_for(nc.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its NATS probe")

    r = None
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://default:ethan_dev_redis@redis:6379/0")
        r = aioredis.from_url(
            redis_url,
            decode_responses=True,
            protocol=2,
        )
        pong = await asyncio.wait_for(r.ping(), timeout=2)
        results["redis"] = "connected" if pong else "error"
    except Exception as e:
        results["redis"] = f"error: {e}"
    finally:
        if r is not None:
            try:
                await asyncio.wait_for(r.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its Redis probe")

    conn = None
    try:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@postgres:5432/ethan")
        conn = await asyncio.wait_for(asyncpg.connect(db_url, timeout=2), timeout=3)
        results["postgresql"] = "connected"
    except Exception as e:
        results["postgresql"] = f"error: {e}"
    finally:
        if conn is not None:
            try:
                await asyncio.wait_for(conn.close(), timeout=2)
            except Exception:
                logger.exception("Detailed healthcheck could not close its PostgreSQL probe")

    all_ok = all(v == "connected" for v in results.values())
    status_code = 200 if all_ok else 503

    return Response(
        content=json.dumps({"status": "ok" if all_ok else "degraded", "checks": results}),
        status_code=status_code,
        media_type="application/json"
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not HAS_PROMETHEUS:
        return {"error": "prometheus_client not installed"}
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Old shutdown code removed as it's now in the lifespan context manager.
