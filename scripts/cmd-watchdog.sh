#!/usr/bin/env bash
# ethan watchdog — Surveiller les conteneurs crashés (one-shot)
# Ce script est appelé par ethan-watchdog.service (déclenché par timer toutes les 30s)
# Vérifie l'état des conteneurs Docker et les redémarre si nécessaire
# NOTE: Plus de boucle infinie — le timer systemd gère le polling

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
MAX_RESTARTS=5

# Fichier pour compter les restarts (dans /tmp car stateless)
RESTART_COUNT_FILE="/tmp/ethan-watchdog-restarts"

# Compter les conteneurs exited
EXITED=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=exited" 2>/dev/null | wc -l || echo "0")

if [ "$EXITED" -gt 0 ]; then
    CRASHED_SVCS=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=exited" 2>/dev/null | tr '\n' ' ' || true)
    
    # Incrémenter le compteur de restarts
    CURRENT_RESTARTS=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo "0")
    NEW_RESTARTS=$((CURRENT_RESTARTS + EXITED))
    echo "$NEW_RESTARTS" > "$RESTART_COUNT_FILE"
    
    if [ "$NEW_RESTARTS" -gt "$MAX_RESTARTS" ]; then
        error "ALERT: Trop de restarts ($NEW_RESTARTS) - conteneurs crashés : $CRASHED_SVCS"
        error "Vérifiez les logs : docker compose logs ${CRASHED_SVCS}"
        # Reset du compteur après alerte
        echo "0" > "$RESTART_COUNT_FILE"
    else
        warn "Conteneurs exited détectés : $CRASHED_SVCS"
        # Essayer de redémarrer les conteneurs crashés
        for svc in $CRASHED_SVCS; do
            if docker compose -f "$COMPOSE_FILE" ps --services --filter "status=exited" 2>/dev/null | grep -q "^${svc}$"; then
                info "Redémarrage de $svc..."
                docker compose -f "$COMPOSE_FILE" up -d "$svc" 2>&1 || true
            fi
        done
    fi
fi
