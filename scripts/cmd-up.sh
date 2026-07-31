#!/usr/bin/env bash
# ethan up — Démarrer les services ETHAN
# Usage: ./ethan up [service...] [--skip-preflight] [--skip-pull]
#
# FLUX COMPLET :
#   1. Préflight (ports, binaires, RAM, DNS, .env)
#   2. Pull séquentiel des images de base (si absentes du cache)
#   3. docker compose up -d
#   4. Boucle d'attente healthchecks (max 600s, aligné avec systemd)
#   5. Rapport final

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start

# ── Parse des arguments ─────────────────────────────────────────

SKIP_PREFLIGHT=false
SKIP_PULL=false
DEV_MODE=false
OBSERVABILITY=false
SERVICES=()

for arg in "$@"; do
    case "$arg" in
        --skip-preflight) SKIP_PREFLIGHT=true ;;
        --skip-pull)      SKIP_PULL=true ;;
        --dev)            DEV_MODE=true ;;
        --observability)  OBSERVABILITY=true ;;
        -*)               warn "Option inconnue : $arg (ignorée)" ;;
        *)                SERVICES+=("$arg") ;;
    esac
done

SERVICES_STR="${SERVICES[*]:-}"

# ── Sélection du fichier Compose ────────────────────────────────
COMPOSE_FILES=("-f" "${COMPOSE_FILE}")

if [[ "$DEV_MODE" == "true" ]]; then
    if [[ -f "${COMPOSE_DEV}" ]]; then
        COMPOSE_FILES+=("-f" "${COMPOSE_DEV}")
        info "Mode dev : ${COMPOSE_DEV} ajouté"
    else
        warn "Fichier dev introuvable : ${COMPOSE_DEV} — ignoré"
    fi
fi

if [[ "$OBSERVABILITY" == "true" ]]; then
    COMPOSE_OBS="${ETHAN_ROOT}/docker-compose.observability.yml"
    if [[ -f "$COMPOSE_OBS" ]]; then
        COMPOSE_FILES+=("-f" "$COMPOSE_OBS")
        info "Observabilité : $COMPOSE_OBS ajouté"
    else
        warn "Fichier observabilité introuvable : $COMPOSE_OBS — ignoré"
    fi
fi

section "Démarrage ETHAN"
info "Répertoire : ${ETHAN_ROOT}"
info "Compose    : ${COMPOSE_FILES[*]}"
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
        warn "Poursuite du boot malgré les erreurs"
    fi
fi

# Vérifier que le fichier docker-compose.yml existe
if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Fichier docker-compose.yml introuvable : ${COMPOSE_FILE}"
    warn "Poursuite du boot malgré les erreurs"
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

# ── Étape 3 : Lancement séquencé ───────────────────────────────

section "3/4 — Lancement des services"

wait_for_health() {
    local target="$1"
    local timeout="$2"
    info "Attente de la santé de : $target (max ${timeout}s)..."
    local waited=0
    while [ "$waited" -lt "$timeout" ]; do
        local healthy=0
        local expected=0
        local unhealthy_services=""
        for svc in $target; do
            # Vérifier le statut du service via docker inspect (plus fiable)
            local container
            container=$(docker_compose ps --format "{{.Names}}" --filter "name=${svc}" 2>/dev/null | head -1 || true)
            if [[ -z "$container" ]]; then
                ((expected++)) || true
                continue
            fi
            local state
            state=$(docker inspect "$container" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    s = d[0].get('State', {})
    h = s.get('Health', {})
    status = s.get('Status', 'unknown')
    health = h.get('Status', 'none') if h else 'none'
    if status == 'running' and health == 'healthy':
        print('healthy')
    elif status == 'running' and health == 'none':
        print('running')
    elif status == 'running' and health == 'starting':
        print('starting')
    elif status == 'exited':
        rc = s.get('ExitCode', -1)
        print(f'exited({rc})')
    else:
        print(f'{status}/{health}')
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")
            case "$state" in
                healthy)
                    ((healthy++)) || true
                    ((expected++)) || true
                    ;;
                running|starting)
                    ((expected++)) || true
                    ;;
                exited*)
                    unhealthy_services="$unhealthy_services $svc($state)"
                    ((expected++)) || true
                    ;;
                *)
                    unhealthy_services="$unhealthy_services $svc($state)"
                    ((expected++)) || true
                    ;;
            esac
        done

        if [ "$healthy" -eq "$expected" ] && [ "$expected" -gt 0 ]; then
            success "Services prêts : $target"
            return 0
        fi

        # Afficher la progression toutes les 6s
        if (( waited % 6 == 0 )); then
            dim "  Progression : $healthy/$expected healthy (${waited}s/${timeout}s)"
            if [[ -n "$unhealthy_services" ]]; then
                for usvc in $unhealthy_services; do
                    warn "  $usvc pas encore healthy"
                done
            fi
        fi

        # Détecter les crashs (exited avec code != 0)
        local crashed
        crashed=$(docker_compose ps --services --filter "status=exited" 2>/dev/null | wc -l || echo "0")
        if (( crashed > 0 )); then
            local crashed_svcs
            crashed_svcs=$(docker_compose ps --services --filter "status=exited" 2>/dev/null | tr '\n' ' ' || true)
            error "CRASH détecté pendant l'attente : ${crashed_svcs}"
            info "Logs : docker compose logs ${crashed_svcs}"
            return 1
        fi

        sleep 3
        waited=$((waited + 3))
    done
    error "Timeout d'attente pour : $target (${healthy}/${expected} healthy)"
    # Afficher les logs des services non-healthy
    for svc in $target; do
        container_health_log "$svc"
    done
    return 1
}

if (( ${#SERVICES[@]} > 0 )); then
    info "Démarrage des services : ${SERVICES_STR}"
    if ! docker_compose up -d "${SERVICES[@]}"; then
        error "Échec : docker compose up -d ${SERVICES_STR}"
        warn "Poursuite du boot malgré les erreurs"
    fi
    wait_for_health "${SERVICES[*]}" 300
else
    # 3.1 Infrastructure
    info "Démarrage de l'infrastructure (nats, redis, postgres)..."
    if ! docker_compose up -d nats redis postgres; then
        warn "docker compose up a échoué pour certains services — poursuite du boot"
    fi
    wait_for_health "nats redis postgres" 120 || warn "Certains services d'infrastructure ne sont pas devenus healthy dans le délai — poursuite"

    # 3.2 Vérification forte de NATS (port TCP 4222)
    info "Vérification forte de NATS (port TCP 4222)..."
    nats_wait=0
    while ! nc -z localhost 4222 2>/dev/null; do
        if [ "$nats_wait" -gt 30 ]; then
            error "NATS injoignable sur le port 4222 après 30s"
            warn "Poursuite du boot malgré les erreurs"
        fi
        sleep 1
        nats_wait=$((nats_wait + 1))
    done
    success "NATS TCP 4222 est actif"

    # 3.3 Démarrage du Core
    info "Démarrage du Core (api, kernel)..."
    if ! docker_compose up -d api kernel; then
        error "Échec de démarrage du Core"
        warn "Poursuite du boot malgré les erreurs"
    fi
    wait_for_health "api kernel" 120 || warn "Poursuite du boot malgré les erreurs"

    # 3.4 Démarrage des Plugins (modules)
    info "Démarrage des Plugins (modules)..."
    if ! docker_compose up -d modules; then
        error "Échec de démarrage des modules"
        warn "Poursuite du boot malgré les erreurs"
    fi
    wait_for_health "modules" 120 || warn "Poursuite du boot malgré les erreurs"

    # 3.5 Démarrage des autres services (observabilité, ui)
    info "Démarrage des services additionnels (ui, prometheus)..."
    docker_compose up -d ui prometheus 2>/dev/null || true
fi

# ── Étape 4 : Validation globale ────────────────────────────────

section "4/4 — Validation"
success "Séquencement terminé avec succès"

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
    warn "Poursuite du boot malgré les erreurs"
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
