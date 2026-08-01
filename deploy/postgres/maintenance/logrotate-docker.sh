#!/bin/bash
# Docker log rotation — prevent disk fill from container logs
# Run daily via cron
set -euo pipefail

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Rotating Docker container logs..."

# Truncate logs for running containers (json-file driver)
for container in $(docker ps --format '{{.Names}}' 2>/dev/null); do
    log_path=$(docker inspect --format='{{.LogPath}}' "$container" 2>/dev/null || true)
    if [[ -n "$log_path" && -f "$log_path" ]]; then
        size=$(stat -c%s "$log_path" 2>/dev/null || echo 0)
        if (( size > 10485760 )); then  # > 10MB
            echo "  → Truncating $container log (${size} bytes)"
            truncate -s 0 "$log_path"
        fi
    fi
done

# Prune old images and build cache
echo "  → Pruning unused images..."
docker image prune -f --filter "until=168h" 2>&1 || true

echo "  → Pruning build cache..."
docker builder prune -f --filter "until=168h" 2>&1 || true

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Log rotation complete."
