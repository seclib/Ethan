# Trust Boundaries Register — ETHAN

## Verified source entries

1. Public WebUI
   - User browser → WebUI.
   - Boundary: HTTP/HTTPS with cookies.
   - Not the security boundary for authorization.
2. API gateway
   - WebUI app → proxy → FastAPI.
   - Auth via JWT, API keys, optional service token.
   - Verified entries: `interfaces/api/auth.py`, `interfaces/api/routers/security.py`, `interfaces/api/routers/api_keys.py`.
3. PostgreSQL
   - Storage of users, config, records, goals, audit.
   - Trust zone: API / Core runtime service identity.
4. Redis cache
   - Cache and distributed state.
   - Trust zone: same as API/Core.
5. NATS messaging
   - Event bus and WebSocket bridge.
6. Docker host and socket
   - Odin controllers, compose services, external tools.
   - High risk if exposed to API.
7. External Web UI providers
   - Frontend dynamic proxy connected to backend and browser environment.
8. Ollama / model endpoints
   - External LLM runtime.
9. Odin / Frames
   - External independent Compose applications.
10. CLI
   - local bootstrap token and container service control.

## Warnings

- The WebUI must not be regarded as the authorization authority.
- WebSocket path is currently less protected than HTTP paths.
- Shared global record services are difficult to isolate per user.
