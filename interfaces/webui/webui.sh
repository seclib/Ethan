#!/usr/bin/env bash
# Launch ETHAN WebUI (Next.js)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-3001}"
HOST="${HOST:-127.0.0.1}"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required" >&2
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "Installing dependencies..."
  npm install
fi

echo "Starting ETHAN WebUI on http://$HOST:$PORT"
npm run dev -- --port "$PORT" --hostname "$HOST"