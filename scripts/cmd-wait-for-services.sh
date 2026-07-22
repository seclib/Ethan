#!/usr/bin/env bash
# ethan wait-for-services — Attendre que les services soient prêts (générique)
# Usage: ./ethan wait-for-services [--timeout SECONDS] [--interval SECONDS] SERVICE:CHECK
#
# Checks supportés:
#   http://...        - Vérifie endpoint HTTP (curl)
#   tcp:PORT          - Vérifie port TCP (nc)
#   docker:SERVICE      - Vérifie container Docker healthy
#
# Example:
#   ./ethan wait-for-services --timeout 120 docker:nats http://localhost:8000/health tcp:5432

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

# ── Default values ─────────────────────────────────────────────
TIMEOUT="${TIMEOUT:-60}"
INTERVAL="${INTERVAL:-2}"
SERVICES=()

# ── Parse arguments ─────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -*)
            warn "Unknown option: $1"
            shift
            ;;
        *)
            SERVICES+=("$1")
            shift
            ;;
    esac
done

if [[ ${#SERVICES[@]} -eq 0 ]]; then
    warn "No services specified, using defaults"
    SERVICES=(
        "docker:nats"
        "docker:postgres"
        "docker:redis"
        "http://localhost:8000/health:API"
        "docker:kernel"
    )
fi

section "Attente services (${TIMEOUT}s max)"

FAIL=0
ELAPSED=0

while [[ $ELAPSED -lt $TIMEOUT ]]; do
    ALL_READY=true
    
    for entry in "${SERVICES[@]}"; do
        CHECK="${entry%%:*}"
        VALUE="${entry##*:}"
        
        # Determine check type
        if [[ "$CHECK" == "http://*" ]] || [[ "$CHECK" == "https://*" ]]; then
            URL="$CHECK"
            NAME="$VALUE"
            if curl -sf "$URL" >/dev/null 2>&1; then
                success "HTTP $NAME ready"
            else
                ALL_READY=false
            fi
        elif [[ "$CHECK" == "tcp"* ]]; then
            PORT="${CHECK#tcp:}"
            if nc -z localhost "$PORT" 2>/dev/null; then
                success "TCP port $PORT ready"
            else
                ALL_READY=false
            fi
        elif [[ "$CHECK" == "docker"* ]]; then
            SVC="${VALUE}"
            HEALTHY=$(docker compose ps --services --filter "health=healthy" 2>/dev/null | grep -c "^${SVC}$" || true)
            if [[ "$HEALTHY" -eq 1 ]]; then
                success "Docker $SVC healthy"
            else
                ALL_READY=false
            fi
        fi
    done
    
    if $ALL_READY; then
        success "Tous les services sont prêts"
        exit 0
    fi
    
    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

error "Timeout: certains services ne sont pas prêts"
exit 1
