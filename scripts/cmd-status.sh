#!/usr/bin/env bash
# ethan status — État des services ETHAN
# Usage: ./ethan status [service...]
#
# Vérifie l'état réel des services :
# - Container démarré
# - Healthcheck Docker
# - Connectivité HTTP/port

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

require_docker

SERVICES="${*:-}"

section "État des services ETHAN"

if [ -n "$SERVICES" ]; then
    docker_compose ps --filter "name=$SERVICES"
else
    docker_compose ps
fi

echo

# Détailler chaque service
SERVICES_LIST=(
    "ethan-nats:NATS:4222"
    "ethan-redis:Redis:6379"
    "ethan-postgres:PostgreSQL:5432"
    "ethan-api:API Gateway:8000"
    "ethan-kernel:Core Kernel:8080"
    "ethan-modules:Cognitive Modules:—"
    "ethan-ui:WebUI:3000"
    "ethan-pg_backup:PostgreSQL Backup:—"
)

section "Healthchecks détaillés"

for svc_info in "${SERVICES_LIST[@]}"; do
    IFS=':' read -r container label port <<< "$svc_info"

    # Conteneur existe ? (docker ps OU docker_compose ps)
    if docker ps --format '{{.Names}}' | grep -q "^${container}$" || \
       docker_compose ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container}$"; then
        # Healthcheck
        health=$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "unknown")
        case "$health" in
            healthy) success "$label : healthy" ;;
            none) warn "$label : pas de healthcheck" ;;
            unhealthy) error "$label : unhealthy" ;;
            starting) warn "$label : starting..." ;;
            *) warn "$label : $health" ;;
        esac

        # Test de connectivité pour les services HTTP
        if [ "$port" != "—" ]; then
            if [ "$port" = "4222" ]; then
                # NATS : port TCP
                if nc -z localhost 4222 2>/dev/null || (echo > /dev/tcp/localhost/4222) 2>/dev/null; then
                    success "$label : port $port répond"
                else
                    error "$label : port $port fermé"
                fi
            elif [ "$port" = "6379" ]; then
                # Redis : PING
                if redis-cli ping 2>/dev/null | grep -q "PONG"; then
                    success "$label : PING répond"
                else
                    error "$label : PING échoue"
                fi
            elif [ "$port" = "5432" ]; then
                # PostgreSQL : connexion
                if command -v psql &>/dev/null; then
                    if PGPASSWORD="${POSTGRES_PASSWORD:-ethan_dev_pass}" psql -h localhost -U ethan -d ethan -c "SELECT 1" &>/dev/null; then
                        success "$label : connexion OK"
                    else
                        error "$label : impossible de se connecter"
                    fi
                else
                    warn "$label : psql non installé (test limité)"
                fi
            elif [ "$port" = "8000" ]; then
                # API Gateway : health endpoint
                if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
                    success "$label : /health répond"
                elif curl -sf "http://localhost:${port}/version" >/dev/null 2>&1; then
                    success "$label : /version répond"
                else
                    error "$label : injoignable"
                fi
            elif [ "$port" = "3000" ]; then
                # WebUI
                if wait_for_http "http://localhost:${port}/" 3; then
                    success "$label : répond"
                else
                    error "$label : injoignable"
                fi
            fi
        fi
    else
        error "$label : container absent ou arrêté"
    fi
done

echo
TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l)
RUNNING=$(docker_compose ps --services --filter "status=running" 2>/dev/null | wc -l)
HEALTHY=$(docker_compose ps --services --filter "status=running" --filter "health=healthy" 2>/dev/null | wc -l)

if [ "$TOTAL" -eq 0 ]; then
    warn "Aucun service défini — docker-compose.yml introuvable ou vide."
elif [ "$HEALTHY" -eq "$TOTAL" ]; then
    success "$HEALTHY/$TOTAL services opérationnels (healthy)"
elif [ "$RUNNING" -eq "$TOTAL" ]; then
    warn "$RUNNING/$TOTAL services démarrés, $HEALTHY/$TOTAL healthy"
    info "Attendre que les healthchecks passent, ou vérifier : ./ethan logs <service>"
else
    error "$RUNNING/$TOTAL services en cours d'exécution, $HEALTHY/$TOTAL healthy"
    info "Correction : docker compose ps et docker compose logs <service>"
fi
