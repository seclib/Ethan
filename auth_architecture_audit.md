# ETHAN OS — Authentication Architecture Audit & Migration Plan

> **Date:** 2026-08-02
> **Context:** The current codebase suffers from authentication schizophrenia. There are two competing systems: a robust Web JWT implementation in `interfaces/api/auth.py` and a legacy in-memory "Jarvis OS" mock system in `core/auth/__init__.py`.
> **Objective:** Eliminate technical debt by strictly separating concerns: `interfaces` handles HTTP/JWT, `core` handles RBAC logic.

---

## 1. Current State & Technical Debt

### The Two Systems:
1. **`interfaces/api/auth.py` (Web User Auth)**
   - Uses JWT (JSON Web Tokens).
   - Validates tokens via FastAPI dependency (`auth_middleware`).
   - Populates `request.state.user` and role.
   - **Status:** Healthy, production-ready.

2. **`core/auth/__init__.py` (Kernel Legacy Auth)**
   - Copy-pasted from "Jarvis OS" (see header comments).
   - Maintains an in-memory `_users` dictionary.
   - Generates API keys and handles rate limiting manually.
   - **Status:** Legacy mock. Currently only used as a dangerous fallback in `main.py` if the PostgreSQL database is unreachable during login.

### The Problem:
- **Duplication:** Rate limiting is implemented twice (SlowAPI in `main.py` vs `check_rate_limit` in `core/auth`).
- **Security Risk:** If the DB drops, `main.py` falls back to an in-memory dictionary and grants access.
- **Coupling:** The Kernel (`core/`) should not know what a "User" or an "API Key" is. It should only care about "Roles" and "Permissions".

---

## 2. Target Architecture

We will adopt a strict Layered Security Model:

```mermaid
graph TD
    A[Web User / Client] -->|HTTP POST /login| B(API Gateway : auth.py)
    B -->|Query| C[(PostgreSQL Users)]
    B -->|Set-Cookie| A
    
    A -->|HTTP GET /api/...| D(API Gateway : middleware)
    D -->|Validate JWT| E{Valid?}
    E -- No --> F[401 Unauthorized]
    E -- Yes --> G[Extract Role from JWT]
    
    G --> H[API Route Handler]
    H -->|Has Permission?| I(Core RBAC : core/auth)
    I -->|check_permission(role, action)| J{Allowed?}
    J -- No --> K[403 Forbidden]
    J -- Yes --> L[Kernel Action Executed]
```

### Clarification of Responsibilities:
- **Web User:** Authenticates via username/password against the API Gateway.
- **JWT (interfaces/api/auth.py):** Encapsulates the user's identity and `role` securely.
- **API Gateway (interfaces/api/):** Handles all HTTP concerns, CORS, Rate Limiting (SlowAPI), and JWT validation.
- **Kernel RBAC (core/auth):** Stripped of all user/token concepts. Becomes a pure Policy Engine mapping `Roles` (e.g., "admin", "user") to `Permissions` (e.g., `READ`, `EXECUTE`).

---

## 3. Affected Files

| File | Action |
|------|--------|
| `interfaces/api/main.py` | Remove the `core.auth.system` fallback block in the `/auth/login` route. DB failure should result in 503/500, not an in-memory fallback. |
| `interfaces/api/auth.py` | Add a FastAPI dependency (e.g., `RequirePermission`) that calls the Kernel RBAC engine. |
| `core/auth/__init__.py` | **Major Refactor:** Delete `User`, `API Keys`, and `check_rate_limit` logic. Keep only `Permission` enum, `Role` mapping, and `has_permission(role, permission)` logic. |
| `interfaces/api/routers/*.py` | Inject the new RBAC dependency into protected endpoints. |

---

## 4. Migration Risks

1. **Loss of Emergency Login:** Removing the in-memory fallback in `main.py` means if PostgreSQL is down, no one can log in. *Mitigation: This is standard production behavior. Fix the DB, don't bypass it.*
2. **Endpoint Lockout:** Applying RBAC strictly to API routers might break frontend features if the WebUI uses a role that lacks the required `Permission`. *Mitigation: Default the "user" role to have broad permissions during phase 1.*
3. **API Key Breakage:** If any external service is currently using the `core.auth` API keys (none found in current audit), they will break. *Mitigation: API Keys should be managed in the DB and validated in `interfaces/api/auth.py`, not in memory.*

---

## 5. Execution Plan (Prioritized)

### Phase P0: Clean the API Gateway (Immediate)
- **Goal:** Stop bridging the two systems.
- **Task:** Edit `interfaces/api/main.py`. Remove the `except Exception as e:` fallback that creates an in-memory user via `auth_system.create_user(username)`. Fail gracefully with a `500 Internal Server Error` if DB auth fails.

### Phase P1: Strip the Kernel (Next)
- **Goal:** Remove legacy Jarvis OS code.
- **Task:** Edit `core/auth/__init__.py`. 
  - Delete `generate_api_key`, `validate_api_key`, `check_rate_limit`.
  - Remove the `_users` dictionary.
  - Rename `AuthSystem` to `RBACEngine` (or similar) that only holds `_roles`.

### Phase P2: Enforce RBAC at the Router Level (Future)
- **Goal:** Connect JWT roles to Kernel permissions.
- **Task:** Create a FastAPI dependency in `interfaces/api/auth.py` that reads the role from the JWT, calls `core.auth.RBACEngine.has_permission()`, and raises `403 Forbidden` if denied. Apply this to `interfaces/api/routers/`.
