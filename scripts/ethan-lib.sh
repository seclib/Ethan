#!/usr/bin/env bash
# ETHAN — Bibliothèque commune
# Usage: source scripts/ethan-lib.sh

set -euo pipefail

# ── Couleurs (compatible CLI_DESIGN.md) ──────────────────────────
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_DIM="\033[2m"
C_BLUE="\033[38;5;39m"
C_CYAN="\033[38;5;44m"
C_GREEN="\033[38;5;42m"
C_YELLOW="\033[38;5;220m"
C_RED="\033[38;5;196m"
C_PURPLE="\033[38;5;135m"
C_WHITE="\033[38;5;255m"

# ── Icônes ──────────────────────────────────────────────────────
I_CHECK="✓"
I_CROSS="✗"
I_WARN="⚠"
I_INFO="ℹ"
I_ARROW="→"
I_SECTION="◆"
I_TIMER="⏱"
I_INPUT="▸"

# ── Chemins ──────────────────────────────────────────────────────
ETHAN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="${ETHAN_ROOT}/scripts"
COMPOSE_FILE="${ETHAN_ROOT}/docker-compose.yml"
COMPOSE_DEV="${ETHAN_ROOT}/docker-compose.dev.yml"
COMPOSE_PROD="${ETHAN_ROOT}/docker-compose.prod.yml"
LOG_DIR="${ETHAN_ROOT}/logs"
WEBUI_DIR="${ETHAN_ROOT}/interfaces/webui"
CLI_DIR="${ETHAN_ROOT}/interfaces/cli"
API_DIR="${ETHAN_ROOT}/interfaces/api"

mkdir -p "$LOG_DIR"

# ── Utilitaires ──────────────────────────────────────────────────

section()   { echo -e "\n${C_BLUE}${I_SECTION} $*${C_RESET}"; }
success()   { echo -e "  ${C_GREEN}${I_CHECK} $*${C_RESET}"; }
error()     { echo -e "  ${C_RED}${I_CROSS} $*${C_RESET}"; }
warn()      { echo -e "  ${C_YELLOW}${I_WARN} $*${C_RESET}"; }
info()      { echo -e "  ${C_CYAN}${I_INFO} $*${C_RESET}"; }
arrow()     { echo -e "  ${C_CYAN}${I_ARROW} $*${C_RESET}"; }
metadata()  { echo -e "  ${C_DIM}${I_TIMER} $*${C_RESET}"; }
dim()       { echo -e "  ${C_DIM}$*${C_RESET}"; }
bold()      { echo -e "${C_BOLD}$*${C_RESET}"; }

# ── Docker helpers ───────────────────────────────────────────────

# Support multi-compose-files : si COMPOSE_FILES est défini (tableau),
# l'utiliser. Sinon, utiliser COMPOSE_FILE seul.
docker_compose() {
    if [[ -n "${COMPOSE_FILES:-}" ]] && [[ "${#COMPOSE_FILES[@]}" -gt 0 ]]; then
        docker compose "${COMPOSE_FILES[@]}" "$@"
    else
        docker compose -f "$COMPOSE_FILE" "$@"
    fi
}

service_is_running() {
    local name="$1"
    docker ps --format '{{.Names}}' | grep -q "^${name}$"
}

require_docker() {
    if ! command -v docker &>/dev/null; then
        error "Docker n'est pas installé."
        info "Installe Docker : https://docs.docker.com/engine/install/"
        exit 1
    fi
    if ! docker info &>/dev/null; then
        error "Docker daemon n'est pas en cours d'exécution."
        exit 1
    fi
}

require_node() {
    if ! command -v node &>/dev/null; then
        error "Node.js n'est pas installé."
        exit 1
    fi
}

require_python() {
    if ! command -v python3 &>/dev/null; then
        error "Python 3 n'est pas installé."
        exit 1
    fi
}

check_dep() {
    if command -v "$1" &>/dev/null; then
        local ver="$("$1" --version 2>/dev/null | head -1 || true)"
        success "$1 — ${ver:-OK}"
    else
        error "$1 — manquant"
    fi
}

# ── Timing ───────────────────────────────────────────────────────

timer_start() {
    _timer_start=$(date +%s%N)
}

timer_end() {
    local end=$(date +%s%N)
    local elapsed_ms=$(( (end - _timer_start) / 1000000 ))
    if [ "$elapsed_ms" -ge 60000 ]; then
        echo "$((elapsed_ms / 60000))m $(( (elapsed_ms % 60000) / 1000 ))s"
    elif [ "$elapsed_ms" -ge 1000 ]; then
        echo "$((elapsed_ms / 1000)).$(( (elapsed_ms % 1000) / 100 ))s"
    else
        echo "${elapsed_ms}ms"
    fi
}

# ── Healthchecks ────────────────────────────────────────────────

wait_for_http() {
    local url="$1"
    local timeout="${2:-30}"
    local start
    start=$(date +%s)

    while true; do
        if curl -sf "$url" >/dev/null 2>&1; then
            return 0
        fi
        local now
        now=$(date +%s)
        if (( now - start >= timeout )); then
            return 1
        fi
        sleep 1
    done
}

# Diagnostic : logs le message d'erreur du healthcheck d'un conteneur
container_health_log() {
    local service="$1"
    local container
    container=$(docker_compose ps --format "{{.Names}}" --filter "name=${service}" 2>/dev/null | head -1 || true)
    [[ -z "$container" ]] && return
    docker inspect "$container" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    state = d[0].get('State', {})
    health = state.get('Health', {})
    status = health.get('Status', 'none')
    if status == 'unhealthy' and health.get('Log'):
        last = health['Log'][-1]
        output = last.get('Output', '')[:200]
        print(f'unhealthy: {output}')
    else:
        print(status)
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown"
}

# Vérification rapide qu'un service Docker tourne sans crash immédiat
service_is_stable() {
    local service="$1"
    local container
    container=$(docker_compose ps --format "{{.Names}}" --filter "name=${service}" 2>/dev/null | head -1 || true)
    [[ -z "$container" ]] && return 1
    local status
    status=$(docker inspect "$container" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    s = d[0].get('State', {})
    if s.get('Status') == 'running':
        print('running')
    elif s.get('Status') == 'exited':
        rc = s.get('ExitCode', -1)
        print(f'exited({rc})')
    else:
        print(s.get('Status', 'unknown'))
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")
    [[ "$status" == "running" ]]
}

check_url() {
    local name="$1"
    local url="$2"
    if curl -sf "$url" >/dev/null 2>&1; then
        success "$name : $url"
        return 0
    else
        error "$name injoignable : $url"
        return 1
    fi
}

ensure_container_running() {
    local name="$1"
    local label="${2:-$1}"
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        success "$label est en cours d'exécution"
        return 0
    else
        warn "$label n'est pas en cours d'exécution"
        return 1
    fi
}

ensure_compose_service() {
    local service="$1"
    local label="${2:-$1}"
    local total
    total=$(docker_compose ps --services 2>/dev/null | wc -l)
    if [ "$total" -eq 0 ]; then
        warn "Aucun service docker-compose détecté"
        return 1
    fi
    if docker_compose ps --services --filter "status=running" | grep -q "^${service}$"; then
        success "$label est en cours d'exécution"
        return 0
    else
        warn "$label n'est pas en cours d'exécution — tentative de démarrage..."
        docker_compose up -d "$service" || true
        sleep 2
        if docker_compose ps --services --filter "status=running" | grep -q "^${service}$"; then
            success "$label démarré"
            return 0
        else
            error "$label toujours indisponible"
            return 1
        fi
    fi
}

# ── Diagnostic helpers ────────────────────────────────────────

check_command() {
    local cmd="$1"
    local label="${2:-$1}"
    if command -v "$cmd" &>/dev/null; then
        local ver
        ver=$("$cmd" --version 2>/dev/null | head -1 || echo "OK")
        success "$label : $ver"
        return 0
    else
        error "$label introuvable"
        return 1
    fi
}

check_python_import() {
    local mod="$1"
    local label="${2:-$1}"
    if python3 -c "import $mod" 2>/dev/null; then
        success "import $label"
        return 0
    else
        error "import $label échoué"
        return 1
    fi
}

check_http_endpoint() {
    local name="$1"
    local url="$2"
    local timeout="${3:-5}"
    if wait_for_http "$url" "$timeout"; then
        success "$name : $url"
        return 0
    else
        error "$name injoignable : $url"
        return 1
    fi
}
