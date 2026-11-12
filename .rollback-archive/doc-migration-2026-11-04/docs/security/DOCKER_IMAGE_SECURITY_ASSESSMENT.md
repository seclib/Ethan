# Docker Image Security Assessment — ETHAN

## Scope
Dockerfiles, compose services, images, network and volume declarations in `deploy/` and `docker-compose*.yml`.

## Verified
- API and kernel leverage shared `ethan/python-base image`.
- Compose contains explicit resource limits.
- Network services include `ethan-core` and `odin-control`.
- Ports universally bind to `127.0.0.1`.
- Redis password and NATS token required by Compose environment interpolation.
- Postgres stores password by env variable.
- Docker socket mounted only on `odin-controller`.
- Base image `python:3.12-slim` mutable tag.
- Dockerfiles add packages and run apt cleanup.
- API image includes Docker CLI and compose to support capability (documented).
- `ethan-api` restart policy modified in recent remediation to `"no"`.

## Risks
- Mutable base image/tag.
- No visible SHA digest pinning.
- Docker images potentially included generated artifacts.
- User-level runtime may vary by Dockerfile (root install).
- Smaller but notable no SBOM or attestation observed.
- Volumes stored local: `postgres_data`, `redis_data`, `nats_data`, etc.
- `deploy/postgres/init.sql` preloads default admin.
- Some examples bundle extra files not needed release.

## Recommendations
- digest pin all FROM images.
- use non-root where possible.
- separate build base and runtime images.
- generate SBOM.
- scan final images.
- protect build/secrets/generated artifacts.
- verify backup encryption and restore.
- isolate Odin/Frames and only lifecycle extra control.
- no public release of local DB volumes.
