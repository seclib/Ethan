# Campaign 02-A — GitHub Organization Discovery

Statut : PARTIALLY_COMPLETED

## Implementation
- `core/applications/github_organization_discovery.py`: public metadata adapter against the official GitHub REST API.
- `interfaces/api/routers/github_discovery.py`: read-only authenticated endpoint.
- `interfaces/webui/src/lib/api/github-discovery.ts` and `interfaces/webui/src/app/applications/page.tsx`: dynamic WebUI rendering.
- Tests:
  - `tests/core/test_github_org_discovery.py` : 2 passed
  - `tests/interfaces/test_github_discovery_api.py` : 3 passed

## Actual GitHub check
- `https://api.github.com/orgs/seclib/repos` returned `HTTP 404` in this environment.
- Therefore no live seclib repository metadata was ingested.
- The adapter is generic and verified with a mocked local server, not presented as live seclib discovery.

## Remaining work
- Live seclib organization availability and token requirements must be verified.
- Manifest discovery and registration from supported repositories require a defined manifest contract.
- `CatalogEntry` conversion from GitHub metadata only when a valid manifest is present.
- Dynamic WebUI application integration is limited to repository metadata and existing catalog entries.
