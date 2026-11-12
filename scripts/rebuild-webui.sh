#!/usr/bin/env bash
# Rebuild and redeploy only the ETHAN WebUI container.
# This avoids restarting or rebuilding the whole ETHAN ecosystem.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${SCRIPT_DIR}/.."

echo "Rebuilding ETHAN WebUI image (source: interfaces/webui)..."
docker compose build ui

echo "Recreating WebUI container with the new image..."
docker compose up -d --no-deps --force-recreate ui

echo "Waiting for WebUI healthcheck..."
for i in {1..30}; do
    if wget -q --spider http://127.0.0.1:3001 2>/dev/null; then
        echo "✓ WebUI is ready: http://127.0.0.1:3001"
        break
    fi
    sleep 2
done
echo "If the browser still shows an old bundle, unregister sw.js once: DevTools → Application → Service Workers → Unregister."
