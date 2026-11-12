# Dependency Security Inventory — ETHAN

## Verified managers and artifacts

- Python: `pyproject.toml`, `uv.lock`
- WebUI npm: `interfaces/webui/package.json`, `interfaces/webui/package-lock.json`
- Docker compose and Dockerfiles under `deploy/` and `docker-compose*.yml`
- Python base requires external apt packages

## Observations

- Many Python deps for core/backend/security/API knowledge.
- Tests import openjarvis, perhaps external namespace/sample and not in first-party package.
- WebUI standalone output includes `.next` build artifacts locally.
- Lock file tracked.
- Frontend dependencies include Next.js 16 and xterm.
- Dependency drift is possible if `uv.lock`/npm lock not updated.
- `requirements` appears secondary; pip install from pyproject.
- Examples intentionally include unrelated package manifests.

## Gaps

- Automatic Dependabot absent.
- No package update workflow.
- No vulnerability scan beyond Trivy fuzzy fs.
- No SCA in unit pytest.
- Contributors may run with editable installs and local node_modules.
- generated `.next` and vendor caches must be ignored at public boundaries.

## Recommendations

- Add Dependabot for pip, npm and actions.
- Add SCA security scan in preflight/CI.
- Pin direct dependencies and use committed locks.
- Regular dependency ownership and abandonment review.
- Check each direct optional package.
- Add no-audio package assets if necessary.
- Ensure examples do not re-use unverified third-party source.
