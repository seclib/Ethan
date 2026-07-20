#!/usr/bin/env bash
# ethan up — Démarrer les services ETHAN
# Usage: ./ethan up [service...] [--skip-preflight] [--skip-pull]
#
# FLUX COMPLET :
#   1. Préflight (ports, binaires, RAM, DNS, .env)
#   2. Pull séquentiel des images de base (si absentes du cache)
#   3. docker compose up -d
#   4. Boucle d'attente healthchecks (max 90s)
#   5. Rapport final

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start

# ── Parse des arguments ─────────────────────────────────────────

SKIP_PREFLIGHT=false
SKIP_PULL=false
SERVICES=()

for arg in "$@"; do
    case "$arg" in
        --skip-preflight) SKIP_PREFLIGHT=true ;;
        --skip-pull)      SKIP_PULL=true ;;
        -*)               warn "Option inconnue : $arg (ignorée)" ;;
        *)                SERVICES+=("$arg") ;;
    esac
done

SERVICES_STR="${SERVICES[*]:-}"

section "Démarrage ETHAN"
info "Répertoire : ${ETHAN_ROOT}"
info "Compose    : ${COMPOSE_FILE}"
info "Services   : ${SERVICES_STR:-<tous>}"

# ── Vérification minimale (Docker) ──────────────────────────────

require_docker

# ── Étape 1 : Préflight ─────────────────────────────────────────

section "1/4 — Préflight"

if [[ "$SKIP_PREFLIGHT" == "true" ]]; then
    warn "Préflight ignoré (--skip-preflight)"
else
    if ! "${SCRIPT_DIR}/cmd-preflight.sh"; then
        error "Préflight échoué — corriger les erreurs avant de continuer"
        info  "Pour ignorer : ./ethan up --skip-preflight"
        exit 1
    fi
fi

# Vérifier que le fichier docker-compose.yml existe
if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Fichier docker-compose.yml introuvable : ${COMPOSE_FILE}"
    exit 1
fi

# ── Étape 2 : Pull des images de base ───────────────────────────

section "2/4 — Images Docker"

if [[ "$SKIP_PULL" == "true" ]]; then
    warn "Pull des images ignoré (--skip-pull)"
else
    # Pull seulement les images absentes du cache (non bloquant sur erreur)
    BASE_IMAGES=(
        "nats:2.10-alpine"
        "redis:7-alpine"
        "postgres:16-alpine"
        "prom/prometheus:latest"
        "python:3.12-slim"
        "node:20-alpine"
    )

    PULL_NEEDED=()
    for image in "${BASE_IMAGES[@]}"; do
        if ! docker image inspect "$image" &>/dev/null 2>&1; then
            PULL_NEEDED+=("$image")
        fi
    done

    if (( ${#PULL_NEEDED[@]} == 0 )); then
        success "Toutes les images de base sont en cache"
    else
        info "${#PULL_NEEDED[@]} image(s) à télécharger (séquentiel)"
        pull_failed=0
        for image in "${PULL_NEEDED[@]}"; do
            info "  Pull : $image..."
            if docker pull "$image" 2>&1 | tail -2; then
                success "  ✓ $image"
            else
                warn "  ✗ $image : pull échoué — le build tentera quand même"
                (( pull_failed++ )) || true
            fi
        done

        if (( pull_failed > 0 )); then
            warn "${pull_failed} pull(s) échoué(s) — le démarrage peut échouer si les images sont absentes"
            info "Vérifier la connectivité : curl -sf https://registry-1.docker.io/v2/"
        fi
    fi
fi

# ── Étape 3 : docker compose up ─────────────────────────────────

section "3/4 — Lancement des services"

if (( ${#SERVICES[@]} > 0 )); then
    info "Démarrage des services : ${SERVICES_STR}"
    if ! docker_compose up -d "${SERVICES[@]}"; then
        error "Échec : docker compose up -d ${SERVICES_STR}"
        info  "Diagnostiquer : docker compose logs"
        exit 1
    fi
else
    info "Démarrage de tous les services"
    if ! docker_compose up -d; then
        error "Échec : docker compose up -d"
        info  "Diagnostiquer : docker compose logs"
        exit 1
    fi
fi

success "Commande docker compose up exécutée"

# ── Étape 4 : Attente des healthchecks ──────────────────────────

section "4/4 — Healthchecks"

info "Attente des healthchecks (max 90s)..."
MAX_WAIT=90
WAITED=0
SLEEP_INTERVAL=3
LAST_HEALTHY=-1
LAST_TOTAL=-1

while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    HEALTHY=$(docker_compose ps --services --filter "health=healthy" 2>/dev/null | wc -l || echo "0")
    TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l || echo "0")
    RUNNING=$(docker_compose ps --services --filter "status=running" 2>/dev/null | wc -l || echo "0")

    # Détecter les conteneurs crashés (exited)
    EXITED=$(docker_compose ps --services --filter "status=exited" 2>/dev/null | wc -l || echo "0")

    # Afficher la progression uniquement si changement
    if [[ "$HEALTHY" != "$LAST_HEALTHY" || "$TOTAL" != "$LAST_TOTAL" ]]; then
        if (( EXITED > 0 )); then
            warn "  ${WAITED}s — ${HEALTHY}/${TOTAL} healthy, ${RUNNING}/${TOTAL} running, ${EXITED} CRASHÉS"
            # Identifier quels services ont crashé
            crashed_svcs=$(docker_compose ps --services --filter "status=exited" 2>/dev/null | tr '\n' ' ' || true)
            error "  Services crashés : ${crashed_svcs}"
            info  "  Logs : docker compose logs ${crashed_svcs}"
        else
            dim "  ${WAITED}s — ${HEALTHY}/${TOTAL} healthy, ${RUNNING}/${TOTAL} running"
        fi
        LAST_HEALTHY="$HEALTHY"
        LAST_TOTAL="$TOTAL"
    fi

    if [ "$TOTAL" -gt 0 ] && [ "$HEALTHY" -eq "$TOTAL" ]; then
        success "Tous les healthchecks sont OK ($HEALTHY/$TOTAL)"
        break
    fi

    sleep "$SLEEP_INTERVAL"
    WAITED=$((WAITED + SLEEP_INTERVAL))
done

# ── Rapport final ────────────────────────────────────────────────

echo
RUNNING=$(docker_compose ps --services --filter "status=running" 2>/dev/null | wc -l || echo "0")
TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l || echo "0")
HEALTHY=$(docker_compose ps --services --filter "status=running" --filter "health=healthy" 2>/dev/null | wc -l || echo "0")
EXITED=$(docker_compose ps --services --filter "status=exited" 2>/dev/null | wc -l || echo "0")

section "Résultat"

if [ "$RUNNING" -eq 0 ] || [ "$TOTAL" -eq 0 ]; then
    error "Aucun service en cours d'exécution"
    info  "Diagnostiquer : docker compose ps && docker compose logs"
    metadata "$(timer_end)"
    exit 1
elif [ "$HEALTHY" -eq "$TOTAL" ]; then
    success "$HEALTHY/$TOTAL services opérationnels (healthy)"
    echo
    arrow "WebUI      : http://localhost:3000"
    arrow "API        : http://localhost:8000"
    arrow "Kernel     : http://localhost:8080"
    arrow "NATS mon.  : http://localhost:8222"
    arrow "Prometheus : http://localhost:9090"
    echo
    info  "Logs      : ./ethan logs [service]"
    info  "Status    : ./ethan status"
    info  "Arrêt     : ./ethan down"
elif (( EXITED > 0 )); then
    error "$RUNNING/$TOTAL démarrés, $HEALTHY/$TOTAL healthy, $EXITED CRASHÉS"
    info  "Identifier les crashs : docker compose ps"
    info  "Logs d'un service    : docker compose logs <service>"
else
    warn "$RUNNING/$TOTAL démarrés, $HEALTHY/$TOTAL healthy (timeout healthchecks)"
    info "Certains services peuvent être encore en cours d'initialisation"
    info "Vérifier : ./ethan status"
fi

metadata "$(timer_end)"
