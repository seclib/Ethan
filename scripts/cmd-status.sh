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
    "ethan-ui:WebUI:3001"
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
                # Redis : PING (mot de passe lu dans .env ; sans redis-cli sur le
                # host → fallback via le conteneur, test réel).
                _redis_pass="${REDIS_PASSWORD:-$(_env_get REDIS_PASSWORD)}"
                if command -v redis-cli &>/dev/null; then
                    if [[ -n "$_redis_pass" ]]; then
                        _redis_ping="$(redis-cli -a "$_redis_pass" ping 2>/dev/null || true)"
                    else
                        _redis_ping="$(redis-cli ping 2>/dev/null || true)"
                    fi
                else
                    _redis_cmd=(docker exec ethan-redis redis-cli)
                    if [[ -n "$_redis_pass" ]]; then
                        _redis_cmd+=(-a "$_redis_pass")
                    fi
                    _redis_cmd+=(ping)
                    _redis_ping="$("${_redis_cmd[@]}" 2>/dev/null || true)"
                fi
                if grep -q "PONG" <<<"$_redis_ping"; then
                    success "$label : PING répond"
                else
                    error "$label : PING échoue"
                fi
            elif [ "$port" = "5432" ]; then
                # PostgreSQL : connexion (mot de passe lu dans .env, jamais affiché)
                if command -v psql &>/dev/null; then
                    _pg_password="${POSTGRES_PASSWORD:-$(_env_get POSTGRES_PASSWORD)}"
                    _pg_password="${_pg_password:-ethan_dev_pass}"
                    if PGPASSWORD="$_pg_password" psql -h localhost -U ethan -d ethan -c "SELECT 1" &>/dev/null; then
                        success "$label : connexion OK"
                    else
                        error "$label : impossible de se connecter"
                    fi
                else
                    warn "$label : psql non installé (test limité)"
                fi
            elif [ "$port" = "8000" ]; then
                # API Gateway : health endpoint (contrat public, sans JWT)
                if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
                    success "$label : /health répond"
                elif curl -sf "http://localhost:${port}/health/ready" >/dev/null 2>&1; then
                    success "$label : /health/ready répond"
                else
                    error "$label : injoignable"
                fi
            elif [ "$port" = "3001" ]; then
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
# `docker compose ps` ne supporte pas le filtre `health=healthy` (filtre
# inconnu → échec du pipeline sous `set -o pipefail`, ce qui tuait le script
# avant l'affichage du résumé). Lecture d'un état JSON par conteneur.
read -r TOTAL RUNNING HEALTHY < <(
    docker_compose ps --format json 2>/dev/null | python3 -c '
import json, sys
total = running = healthy = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        continue
    total += 1
    running += str(row.get("State", "")).lower() == "running"
    healthy += str(row.get("Health", "")).lower() == "healthy"
print(total, running, healthy)
' || echo "0 0 0"
)

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
    exit 1
fi

exit 0
