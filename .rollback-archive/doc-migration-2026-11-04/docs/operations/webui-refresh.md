# WebUI refresh procedure — no OS reboot

## Exact root cause

The production WebUI is served by the standalone Next.js image (`ethan-ui`, built
from `deploy/Dockerfile.ui`). In that flow source files are copied into the Docker
image during `docker compose build`; the production `ui` service has no bind mount
to `interfaces/webui`. Therefore ordinary frontend edits are not visible in the
running container until it is explicitly rebuilt and recreated.

`docker compose restart ui` only restarts the existing image, so it keeps serving
the old bundle. A full Debian rebuild appeared to work because it reset the app
runtime and browser state, but a reboot is not required and must not be used as a
workflow workaround.

A second contributing stale-state source was the PWA service worker
(`public/sw.js`), which cached the application shell with a cache-first strategy
under an immutable cache name (`ethan-v1`). Navigation responses were served from
cache, masking subsequent bundles.

## Evidence

- `deploy/Dockerfile.ui` builds from source in two stages and only the immutable
  build output (`standalone/static/public`) is carried into runtime.
- `docker-compose.yml` production `ui` service has no volume/bind mount for
  `./interfaces/webui`.
- `docker-compose.dev.yml` provides the correct `ui-dev` hot-reload service with
  `./interfaces/webui:/app`.
- `public/sw.js` previously did `caches.match(req)` before `fetch(req)` for all GET
  requests, returning stale React/Next HTML and assets.

## Controlled refresh commands

Development, with HMR:

```bash
make dev-ui
# or
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d ui-dev
```

Then edit files normally and ensure `WATCHPACK_POLLING`/`CHOKIDAR_USEPOLLING` are on
if host/container file events do not propagate.

Production image rebuild, WebUI only:

```bash
./ethan rebuild-ui
# or
docker compose build ui
docker compose up -d --no-deps --force-recreate ui
```

Force a no-cache rebuild if a previous layer is stuck:

```bash
docker compose build --no-cache ui
docker compose up -d --no-deps --force-recreate ui
```

Browser-side stale service worker cleanup:

```text
DevTools -> Application -> Service Workers -> Unregister
```
