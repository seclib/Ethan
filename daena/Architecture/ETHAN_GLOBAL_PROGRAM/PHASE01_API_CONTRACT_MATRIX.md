# Phase 01 — API Contract Matrix (condensed)

- `/v1/plugins/*` backend router with `Permission.PLUGINS` (and `gateway_guard` on install).
- `/v1/providers/*` router: list/catalog/get/models/capabilities.
- `/v1/.../knowledge*`, `/v1/.../skills*`, `/v1/frame/status`, `/v1/plugins/odin*`, `/v1/.../quantar/*` routes mounted.
- Frontend `capabilities.ts` observed for calendar/notes and called `/v1/calendar`, `/v1/notes`, which signals a naming mismatch and possible contract gap.
- Plugin page documentation states it uses `/v1/plugins`.

## Unverified contracts
- Exact TS/Pydantic schema differences beyond above are not fully diffed in this phase due time.
