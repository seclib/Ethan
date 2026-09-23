#!/usr/bin/env bash
# ethan wait-for-services — Attendre que les services ETHAN soient prêts
# Usage: ./ethan wait-for-services [--timeout SECONDS] [--interval SECONDS] CHECK...
#
# Checks supportés :
#   docker:SERVICE            conteneur Compose healthy (ou running sans healthcheck)
#   tcp:PORT                  port TCP ouvert sur 127.0.0.1
#   http://URL | https://URL  endpoint HTTP joignable (curl -sf)
#
# Sans argument : attente de la stack standard
#   (nats, postgres, redis, kernel, modules + API /health/ready).
#
# Exemples :
#   ./ethan wait-for-services --timeout 120 docker:nats tcp:5432
#   ./ethan wait-for-services http://localhost:8000/health/ready
#
# Exit codes :
#   0 — tous les services sont prêts
#   1 — timeout : au moins un service n'est pas prêt
#   2 — aucun check valide fourni

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

usage() {
    cat <<'EOF'
Usage: ./ethan wait-for-services [--timeout SECONDS] [--interval SECONDS] CHECK...

Checks supportés :
  docker:SERVICE            conteneur Compose healthy (ou running sans healthcheck)
  tcp:PORT                  port TCP ouvert sur 127.0.0.1
  http://URL | https://URL  endpoint HTTP joignable (curl -sf)

Sans argument : attente de la stack standard
  (nats, postgres, redis, kernel, modules + API /health/ready)

Exemples :
  ./ethan wait-for-services --timeout 120 docker:nats tcp:5432
  ./ethan wait-for-services http://localhost:8000/health/ready
EOF
}

# ── Valeurs par défaut ───────────────────────────────────────────
TIMEOUT="${TIMEOUT:-60}"
INTERVAL="${INTERVAL:-2}"
SERVICES=()

# ── Parse des arguments ──────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --timeout)  TIMEOUT="$2"; shift 2 ;;
        --interval) INTERVAL="$2"; shift 2 ;;
        --help|-h)  usage; exit 0 ;;
        --)         shift; break ;;
        -*)         warn "Option inconnue : $1 (ignorée)"; shift ;;
        *)          SERVICES+=("$1"); shift ;;
    esac
done

if [[ ${#SERVICES[@]} -eq 0 ]]; then
    info "Aucun check spécifié — attente de la stack standard"
    SERVICES=(
        "docker:nats"
        "docker:postgres"
        "docker:redis"
        "docker:kernel"
        "docker:modules"
        "http://localhost:8000/health/ready"
    )
fi

# ── Parsing d'un check "TYPE:VALEUR" ─────────────────────────────
# Positionne CHECK_TYPE / CHECK_VALUE. Retourne 1 si non reconnu.
parse_check() {
    local entry="$1"
    case "$entry" in
        http://*|https://*) CHECK_TYPE="http";   CHECK_VALUE="$entry" ;;
        tcp:*)              CHECK_TYPE="tcp";    CHECK_VALUE="${entry#tcp:}" ;;
        docker:*)           CHECK_TYPE="docker"; CHECK_VALUE="${entry#docker:}" ;;
        *)                  CHECK_TYPE="";       CHECK_VALUE="$entry"; return 1 ;;
    esac
}

# ── Évaluateurs ──────────────────────────────────────────────────

_check_http() {
    curl -sf --max-time 5 "$1" >/dev/null 2>&1
}

_check_tcp() {
    local port="$1"
    if command -v nc &>/dev/null; then
        nc -z 127.0.0.1 "$port" 2>/dev/null
    else
        # Fallback bash natif si `nc` est absent (préflight : simple avertissement).
        (exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null
    fi
}

# Vérifie l'état d'un conteneur Compose via son JSON (`--format json`).
# `docker compose ps --filter health=...` n'existe pas (filtre inconnu) :
# on lit directement les champs `State` et `Health` du conteneur.
# Sans healthcheck déclaré (`Health` absent), un conteneur `running` est prêt.
_check_docker() {
    local svc="$1" raw json state health
    raw="$(docker_compose ps "$svc" --format json 2>/dev/null || true)"
    json="${raw%%$'\n'*}"
    [[ -n "$json" ]] || return 1
    state="$(sed -n 's/.*"State":"\([^"]*\)".*/\1/p' <<<"$json")"
    health="$(sed -n 's/.*"Health":"\([^"]*\)".*/\1/p' <<<"$json")"
    [[ "$state" == "running" ]] || return 1
    [[ -z "$health" || "$health" == "healthy" ]]
}

# ── Préparation des checks ───────────────────────────────────────
CHECK_TYPES=()
CHECK_VALUES=()
CHECK_LABELS=()

for entry in "${SERVICES[@]}"; do
    if parse_check "$entry"; then
        CHECK_TYPES+=("$CHECK_TYPE")
        CHECK_VALUES+=("$CHECK_VALUE")
        CHECK_LABELS+=("$entry")
    else
        warn "Check non reconnu, ignoré : $entry (attendu docker:SERVICE, tcp:PORT ou http://URL)"
    fi
done

if (( ${#CHECK_LABELS[@]} == 0 )); then
    error "Aucun check valide — rien à attendre"
    usage
    exit 2
fi

section "Attente des services (timeout ${TIMEOUT}s, interval ${INTERVAL}s)"

# ── Boucle d'attente ─────────────────────────────────────────────
declare -A READY=()
declare -A ANNOUNCED=()
ELAPSED=0

while (( ELAPSED < TIMEOUT )); do
    ALL_READY=true

    for i in "${!CHECK_LABELS[@]}"; do
        label="${CHECK_LABELS[$i]}"
        [[ -n "${READY[$label]:-}" ]] && continue

        ok=false
        case "${CHECK_TYPES[$i]}" in
            http)   if _check_http "${CHECK_VALUES[$i]}";   then ok=true; fi ;;
            tcp)    if _check_tcp "${CHECK_VALUES[$i]}";    then ok=true; fi ;;
            docker) if _check_docker "${CHECK_VALUES[$i]}"; then ok=true; fi ;;
        esac

        if [[ "$ok" == "true" ]]; then
            READY[$label]=1
            success "$label ready"
        else
            ALL_READY=false
            if [[ -z "${ANNOUNCED[$label]:-}" ]]; then
                ANNOUNCED[$label]=1
                info "En attente : $label"
            fi
        fi
    done

    if $ALL_READY; then
        success "Tous les services sont prêts (${ELAPSED}s)"
        exit 0
    fi

    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

# ── Timeout : lister les checks non satisfaits ───────────────────
MISSING=()
for label in "${CHECK_LABELS[@]}"; do
    [[ -n "${READY[$label]:-}" ]] && continue
    MISSING+=("$label")
done

error "Timeout (${TIMEOUT}s) — ${#MISSING[@]} service(s) non prêt(s) :"
for label in "${MISSING[@]}"; do
    info "  - $label"
done
info "Diagnostiquer : ./ethan status && docker compose logs <service>"
exit 1
