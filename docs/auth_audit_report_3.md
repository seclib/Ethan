# ETHAN Authentication Audit Report

> **Date**: 2026-08-02 | **Scope**: Full auth chain trace | **Status**: Root causes identified

---

## 1. Flow Trace

```
Browser (LoginForm)
  ↓ onSubmit(operatorId, password)
LoginPage.handleLogin()
  ↓ sets showOverlay=true, stores operatorId — ⚠️ DISCARDS password
LoadingOverlay (cosmetic animation ~4.5s)
  ↓ onComplete callback
LoginPage.handleAuthComplete()
  ↓ calls login("admin@ethan.ai", "password", pendingOperatorId) — 🔴 HARDCODED
AuthProvider.login(email, password, operatorId)
  ↓ fetch("/api/auth/login", { body: { username: "admin@ethan.ai", password: "password" } })
Next.js rewrite (next.config.js)
  ↓ /api/auth/login → http://localhost:8000/auth/login — ✅ CORRECT
FastAPI /auth/login (main.py L130)
  ↓ accepts any username, creates JWT, returns { access_token, token, user: { username, role } }
AuthProvider receives response
  ↓ stores token ✅, then calls setUser(data.user) — 🔴 SHAPE MISMATCH
```

---

## 2. Root Causes

### 🔴 ROOT CAUSE 1 — Login page discards user input and hardcodes credentials

**File**: [login/page.tsx](file:///home/fatsio/AI/Ethan/interfaces/webui/src/app/(auth)/login/page.tsx#L20-L40)

```typescript
// L20-26: handleLogin receives (operatorId, password) from the form
// but ONLY stores operatorId. The password is DISCARDED.
const handleLogin = useCallback(
  async (operatorId: string, password: string) => {
    setError(null);
    setPendingOperatorId(operatorId);  // ← stores operatorId
    setShowOverlay(true);             // ← password gone forever
  },
  []
);

// L29-40: handleAuthComplete ignores form values entirely
const handleAuthComplete = useCallback(() => {
  const fakeLogin = async () => {
    await login("admin@ethan.ai", "password", pendingOperatorId);
    //           ^^^^^^^^^^^^^^    ^^^^^^^^
    //           HARDCODED EMAIL   HARDCODED PASSWORD
  };
  fakeLogin();
}, [login, router, pendingOperatorId]);
```

**Impact**: No matter what the user types in the form, the system always sends `username: "admin@ethan.ai"` and `password: "password"` to the backend. The actual form inputs are discarded.

### 🔴 ROOT CAUSE 2 — User object shape mismatch

**File**: [auth-provider.tsx](file:///home/fatsio/AI/Ethan/interfaces/webui/src/core/providers/auth-provider.tsx#L89-L98)

The `User` TypeScript interface requires:
```typescript
// types/index.ts L203-210
interface User {
  id: string;         // ← backend NEVER returns this
  name: string;       // ← backend NEVER returns this
  email: string;      // ← backend returns "username" not "email"
  role: UserRole;
  permissions: Permission[];  // ← backend NEVER returns this
  created_at: string;         // ← backend NEVER returns this
}
```

The backend returns:
```json
{ "user": { "username": "admin@ethan.ai", "role": "user" } }
```

The auth-provider attempts a partial fix at L98:
```typescript
setUser(data.user?.username
  ? { ...data.user, email: data.user.username }
  : data.user);
```

But this still produces an object missing `id`, `name`, `permissions`, `created_at` — which will cause runtime failures in any component that accesses `user.name` or `user.id`.

### 🔴 ROOT CAUSE 3 — `/auth/me` response also mismatches

**File**: [main.py](file:///home/fatsio/AI/Ethan/interfaces/api/main.py#L175-L186)

```python
# GET /auth/me returns:
{"user": {"username": user, "role": payload.get("role", "user")}}
```

The auth-provider at L50-58:
```typescript
const response = await fetch("/api/auth/me", ...);
const data = await response.json();
setUser(data.user);  // ← data.user = { username: "admin", role: "user" }
                     // ← Missing: id, name, email, permissions, created_at
```

No `username → email` mapping is applied on the `/auth/me` path, unlike the login path.

---

## 3. What Works Correctly

| Component | Status | Notes |
|-----------|--------|-------|
| Next.js rewrite `/api/:path*` → `http://localhost:8000/:path*` | ✅ | Strips `/api` prefix correctly |
| Next.js middleware cookie check | ✅ | Checks `ethan_token` cookie, redirects to `/login` |
| `auth-provider.tsx` cookie + localStorage dual storage | ✅ | Both set on login, both cleared on logout |
| FastAPI `/auth/login` JWT issuance | ✅ | Returns valid JWT with `sub` and `role` claims |
| FastAPI `auth_middleware` public path bypass | ✅ | `/auth/login` and `/auth/register` are public |
| FastAPI `/auth/register` | ✅ | Works, frontend register page calls it correctly |
| FastAPI `/auth/logout` | ✅ | Returns `{"status": "ok"}`, client-side cleanup works |
| FastAPI `/auth/refresh` | ✅ | Issues new JWT from valid existing token |

---

## 4. Files Requiring Modification

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | `src/app/(auth)/login/page.tsx` | Hardcoded `"admin@ethan.ai"` / `"password"`, discards real user input | Pass actual `operatorId` + `password` to `login()` |
| 2 | `src/core/providers/auth-provider.tsx` | User object shape incomplete; `/auth/me` path doesn't map username→email | Normalize backend response into full `User` shape on both login and `/auth/me` |
| 3 | `src/app/(auth)/login/components/login-form.tsx` | Field labeled "Operator ID" but semantically is "username" | No code change required — it's a cosmetic label choice |

---

## 5. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Components accessing `user.id` crash on `undefined` | **High** | Generate a synthetic `id` from username |
| Components accessing `user.name` render blank | **Medium** | Default `name` from `username` |
| Components accessing `user.permissions` crash on `.length` | **High** | Default to empty array `[]` |
| Register flow breaks | **Low** | Register page doesn't use `AuthProvider.login()`, it's self-contained |
| Refresh token breaks | **Low** | Same proxy path, no changes to refresh logic |

---

## 6. Minimal Fix Plan

### Fix 1: `login/page.tsx` — Use real credentials
- Store both `operatorId` and `password` in state
- Pass them to `login()` instead of hardcoded values

### Fix 2: `auth-provider.tsx` — Normalize User object
- Create a `normalizeUser()` helper that maps backend response → `User` interface
- Apply it on both the `/auth/login` and `/auth/me` code paths
- Generate synthetic `id`, default `name`, default `permissions` and `created_at`

### Fix 3: No other files need changes
- `next.config.js` rewrite is correct
- `middleware.ts` cookie check is correct
- `api-client.ts` is not used by the login flow (auth-provider uses raw `fetch`)
- Backend FastAPI endpoints are correct and should not be modified
