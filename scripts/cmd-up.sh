#!/usr/bin/env bash
# ethan up — Démarrer les services ETHAN
# Usage: ./ethan up [service...]
#
# Attend que tous les healthchecks Docker soient "healthy"
# avant de déclarer le système opérationnel.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_docker

SERVICES="${*:-}"

section "Démarrage des services ETHAN"

# Log des informations de débogage
info "Répertoire ETHAN : ${ETHAN_ROOT}"
info "Fichier compose : ${COMPOSE_FILE}"
info "Services à démarrer : ${SERVICES:-<tous>}"

# Vérifier que le fichier docker-compose.yml existe
if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Fichier docker-compose.yml introuvable : ${COMPOSE_FILE}"
    exit 1
fi

success "Fichier docker-compose.yml trouvé"

# Exécuter docker compose up -d
if [ -n "$SERVICES" ]; then
    info "Exécution : docker compose -f \"${COMPOSE_FILE}\" up -d ${SERVICES}"
    if ! docker_compose up -d $SERVICES; then
        error "Échec de 'docker compose up -d ${SERVICES}'"
        info "Vérifier les logs Docker : docker compose logs"
        exit 1
    fi
    success "Commande 'docker compose up -d ${SERVICES}' exécutée avec succès"
else
    info "Exécution : docker compose -f \"${COMPOSE_FILE}\" up -d"
    if ! docker_compose up -d; then
        error "Échec de 'docker compose up -d'"
        info "Vérifier les logs Docker : docker compose logs"
        exit 1
    fi
    success "Commande 'docker compose up -d' exécutée avec succès"
fi

# Attendre que les healthchecks soient healthy
info "Attente des healthchecks (cela peut prendre 30-60s)..."
MAX_WAIT=90
WAITED=0
SLEEP_INTERVAL=3

while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    # Vérifier combien de services sont healthy
    HEALTHY=$(docker_compose ps --services --filter "health=healthy" 2>/dev/null | wc -l || echo "0")
    TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l || echo "0")
    RUNNING=$(docker_compose ps --services --filter "status=running" 2>/dev/null | wc -l || echo "0")

    if [ "$TOTAL" -gt 0 ] && [ "$HEALTHY" -eq "$TOTAL" ]; then
        success "Tous les healthchecks sont OK ($HEALTHY/$TOTAL)"
        break
    fi

    # Afficher la progression
    dim "  Progression : $HEALTHY/$TOTAL healthy, $RUNNING/$TOTAL running (${WAITED}s/${MAX_WAIT}s)"

    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        warn "Timeout atteint. Certains services peuvent ne pas être prêts."
        break
    fi

    sleep "$SLEEP_INTERVAL"
    WAITED=$((WAITED + SLEEP_INTERVAL))
done

# Vérification finale
RUNNING=$(docker_compose ps --services --filter "status=running" 2>/dev/null | wc -l || echo "0")
TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l || echo "0")
HEALTHY=$(docker_compose ps --services --filter "status=running" --filter "health=healthy" 2>/dev/null | wc -l || echo "0")

section "Résultat"

if [ "$RUNNING" -eq 0 ] || [ "$TOTAL" -eq 0 ]; then
    error "Aucun service n'est en cours d'exécution"
    info "Correction : docker compose up -d"
elif [ "$HEALTHY" -eq "$TOTAL" ]; then
    success "$HEALTHY/$TOTAL services opérationnels (healthy)"
    arrow "Frontend : http://localhost:3000"
    arrow "API      : http://localhost:8000"
    arrow "NATS     : http://localhost:8222"
elif [ "$RUNNING" -eq "$TOTAL" ]; then
    warn "$RUNNING/$TOTAL services démarrés, $HEALTHY/$TOTAL healthy"
    info "Certains services ne sont pas encore prêts. Attendre quelques secondes et vérifier : ./ethan status"
else
    error "$RUNNING/$TOTAL services en cours d'exécution, $HEALTHY/$TOTAL healthy"
    info "Correction : docker compose ps et docker compose logs <service>"
fi

metadata "$(timer_end)"
