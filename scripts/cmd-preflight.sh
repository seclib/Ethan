#!/usr/bin/env bash
# ethan preflight — Vérifications système avant démarrage
# Usage: ./ethan preflight [--strict]
#
# Vérifie TOUS les prérequis pour un démarrage sain :
#   - Binaires système requis
#   - Versions Docker / Docker Compose
#   - Ports TCP libres (8000, 8080, 3000, 4222, 6379, 5432, 9090)
#   - RAM et espace disque disponibles
#   - DNS (Docker Hub)
#   - Fichier .env
#
# Exit codes :
#   0 — tout est OK
#   1 — au moins une erreur bloquante
#   2 — avertissements seulement (si --strict non passé → code 0)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

STRICT_MODE="${1:-}"
ERRORS=0
WARNINGS=0

_fail()  { error "$*"; (( ERRORS++ ))  || true; }
_warn()  { warn  "$*"; (( WARNINGS++ )) || true; }
_ok()    { success "$*"; }

# ── 1. Binaires système ─────────────────────────────────────────

section "1/7 — Binaires requis"

_check_bin() {
    local cmd="$1"
    local label="${2:-$cmd}"
    local min_version="${3:-}"

    if ! command -v "$cmd" &>/dev/null; then
        _fail "$label : introuvable (command not found)"
        return
    fi

    local ver
    ver="$("$cmd" --version 2>/dev/null | head -1 || true)"
    _ok "$label : ${ver:-OK}"

    if [[ -n "$min_version" && -n "$ver" ]]; then
        local actual
        actual="$(echo "$ver" | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)"
        if [[ -n "$actual" ]]; then
            local maj min
            maj="${actual%%.*}"
            min="${actual#*.}"
            local req_maj req_min
            req_maj="${min_version%%.*}"
            req_min="${min_version#*.}"
            if (( maj < req_maj )) || { (( maj == req_maj )) && (( min < req_min )); }; then
                _warn "$label version $actual < minimum requis $min_version"
            fi
        fi
    fi
}

_check_bin docker "Docker Engine" "24.0"
_check_bin curl   "curl"
_check_bin wget   "wget"

# Docker Compose peut être un plugin (docker compose) ou standalone (docker-compose)
if docker compose version &>/dev/null 2>&1; then
    compose_ver="$(docker compose version 2>/dev/null | head -1)"
    _ok "Docker Compose (plugin) : ${compose_ver:-OK}"
elif command -v docker-compose &>/dev/null; then
    compose_ver="$(docker-compose --version 2>/dev/null | head -1)"
    _ok "Docker Compose (standalone) : ${compose_ver:-OK}"
else
    _fail "Docker Compose : introuvable (ni plugin ni standalone)"
fi

# Python 3.10+ requis par cmd-status.sh et le CLI
if command -v python3 &>/dev/null; then
    py_ver="$(python3 --version 2>&1 | awk '{print $2}')"
    py_maj="${py_ver%%.*}"
    py_min="$(echo "$py_ver" | cut -d. -f2)"
    if (( py_maj >= 3 && py_min >= 10 )); then
        _ok "Python : $py_ver"
    else
        _warn "Python $py_ver < 3.10 requis (cmd-status.sh, CLI)"
    fi
else
    _warn "python3 : introuvable (cmd-status.sh peut échouer)"
fi

# Outils de connectivité utilisés par cmd-status.sh
for tool in nc redis-cli psql; do
    if command -v "$tool" &>/dev/null; then
        _ok "$tool : présent"
    else
        _warn "$tool : absent (cmd-status.sh aura des tests limités)"
    fi
done

# ── 2. Docker daemon ────────────────────────────────────────────

section "2/7 — Docker daemon"

if ! command -v docker &>/dev/null; then
    _fail "Docker non installé — impossible de continuer"
    # On ne quitte pas encore pour montrer tous les autres problèmes
elif ! docker info &>/dev/null 2>&1; then
    _fail "Docker daemon n'est pas en cours d'exécution"
    info  "Correction : sudo systemctl start docker"
else
    docker_version="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo '?')"
    _ok "Docker daemon actif (server v${docker_version})"

    # Vérifier que l'utilisateur courant peut utiliser Docker sans sudo
    if docker ps &>/dev/null 2>&1; then
        _ok "Accès Docker sans sudo"
    else
        _warn "Docker nécessite sudo — ajouter l'utilisateur au groupe 'docker'"
        info  "Correction : sudo usermod -aG docker $USER && newgrp docker"
    fi
fi

# ── 3. Ports TCP disponibles ────────────────────────────────────

section "3/7 — Disponibilité des ports"

# CAS 1 / CAS 2 — Stack déjà provisionnée ?
#
# Ne pas déduire l'état du stack à partir du nom du conteneur : Compose
# ajoute un suffixe (`api-1`) et certains services n'en ont pas (`nats`).
# Les labels du projet Compose sont la source de vérité et couvrent aussi
# les conteneurs arrêtés après un démarrage incomplet.
_stack_container_ids="$(docker compose -f "${COMPOSE_FILE}" ps -aq 2>/dev/null || true)"
_stack_existing=false
if [[ -n "${_stack_container_ids//[[:space:]]/}" ]]; then
    _stack_existing=true
    info "Stack ETHAN déjà provisionnée : sauter la vérification des ports"
    _ok "Conteneurs ETHAN détectés par le projet Compose"
fi

if [[ "$_stack_existing" == "true" ]]; then
    # CAS 2 : vérifier la santé des conteneurs existants sans bloquer.
    _check_container_health() {
        local id="$1"
        local name="$2"
        local service="$3"
        local label="${service:-$name}"
        local state
        state=$(docker inspect --format='{{.State.Status}}' "$id" 2>/dev/null || echo "unknown")
        local health
        health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$id" 2>/dev/null || echo "unknown")
        if [[ "$state" == "running" && ( "$health" == "healthy" || "$health" == "none" ) ]]; then
            _ok "Conteneur $label ($name) : $state / $health"
            return 0
        fi
        _warn "Conteneur $label ($name) : $state / $health"
        return 1
    }

    health_ok=true
    while IFS= read -r cid; do
        [[ -z "$cid" ]] && continue
        cname=$(docker inspect --format='{{.Name}}' "$cid" 2>/dev/null | sed 's#^/##' || echo "$cid")
        cservice=$(docker inspect --format='{{index .Config.Labels "com.docker.compose.service"}}' "$cid" 2>/dev/null || true)
        _check_container_health "$cid" "$cname" "$cservice" || health_ok=false
    done <<< "$_stack_container_ids"
    if [[ "$health_ok" == "true" ]]; then
        _ok "Tous les conteneurs ETHAN existants sont opérationnels"
    else
        _warn "Certains conteneurs ETHAN nécessitent une attention — le démarrage reste autorisé"
    fi
else
    # CAS 1 : première install — vérifier les ports libres
    # Ports requis par les services ETHAN
    declare -A REQUIRED_PORTS=(
    [4222]="NATS (messaging)"
    [6222]="NATS (cluster)"
    [8222]="NATS (monitoring)"
    [5432]="PostgreSQL"
    [6379]="Redis"
    [8000]="API Gateway"
    [8080]="Kernel"
    [3000]="WebUI"
)

_port_in_use() {
    local port="$1"
    # Essayer ss, puis netstat, puis /proc/net
    if command -v ss &>/dev/null; then
        ss -tlnH "sport = :${port}" 2>/dev/null | grep -q ":${port}"
    elif command -v netstat &>/dev/null; then
        netstat -tlnp 2>/dev/null | grep -q ":${port} "
    else
        # Fallback via /proc/net/tcp (hex port)
        local hex_port
        hex_port="$(printf '%04X' "$port")"
        grep -qi ":${hex_port} " /proc/net/tcp 2>/dev/null || \
        grep -qi ":${hex_port} " /proc/net/tcp6 2>/dev/null
    fi
}

port_errors=0
for port in $(echo "${!REQUIRED_PORTS[@]}" | tr ' ' '\n' | sort -n); do
    label="${REQUIRED_PORTS[$port]}"
    if _port_in_use "$port"; then
        # Identifier le processus qui utilise ce port
        proc=""
        if command -v ss &>/dev/null; then
            proc="$(ss -tlnp "sport = :${port}" 2>/dev/null | grep -oP 'pid=\K[^,]+' | head -1 || true)"
            if [[ -n "$proc" ]]; then
                proc=" (PID $proc)"
            fi
        fi
        _fail "Port $port ($label) : OCCUPÉ${proc}"
        (( port_errors++ )) || true
    else
        _ok "Port $port ($label) : libre"
    fi
done

if (( port_errors > 0 )); then
    info "Astuce : identifier les processus → sudo ss -tlnp | grep ':<port>'"
    info "Astuce : tuer un processus → sudo kill -9 <PID>"
fi
fi

# ── 4. Ressources système ───────────────────────────────────────

section "4/7 — Ressources système"

# RAM disponible (minimum 4 Go recommandé)
if command -v free &>/dev/null; then
    # free en kB → convertir en MB
    avail_mem_mb="$(free -m | awk '/^Mem:/{print $7}')"
    total_mem_mb="$(free -m | awk '/^Mem:/{print $2}')"
    avail_mem_gb="$(echo "scale=1; $avail_mem_mb / 1024" | bc 2>/dev/null || echo '?')"
    total_mem_gb="$(echo "scale=1; $total_mem_mb / 1024" | bc 2>/dev/null || echo '?')"

    if (( avail_mem_mb >= 4096 )); then
        _ok "RAM disponible : ${avail_mem_gb}GB / ${total_mem_gb}GB total"
    elif (( avail_mem_mb >= 2048 )); then
        _warn "RAM disponible : ${avail_mem_gb}GB (4GB recommandé — des services peuvent OOM)"
    else
        _fail "RAM disponible : ${avail_mem_gb}GB — insuffisant (4GB minimum requis)"
    fi
else
    _warn "free non disponible — impossible de vérifier la RAM"
fi

# Espace disque (minimum 10 Go sur la partition du projet)
if command -v df &>/dev/null; then
    avail_disk_mb="$(df -m "$ETHAN_ROOT" | awk 'NR==2{print $4}')"
    avail_disk_gb="$(echo "scale=1; $avail_disk_mb / 1024" | bc 2>/dev/null || echo '?')"

    if (( avail_disk_mb >= 10240 )); then
        _ok "Espace disque : ${avail_disk_gb}GB disponible"
    elif (( avail_disk_mb >= 5120 )); then
        _warn "Espace disque : ${avail_disk_gb}GB (10GB recommandé — images Docker volumineuses)"
    else
        _fail "Espace disque : ${avail_disk_gb}GB — insuffisant (10GB minimum pour les images)"
    fi
else
    _warn "df non disponible — impossible de vérifier l'espace disque"
fi

# ── 5. Connectivité réseau / DNS ────────────────────────────────

section "5/7 — Connectivité réseau (Docker Hub)"

_check_dns() {
    local host="$1"
    if command -v dig &>/dev/null; then
        dig +short "$host" &>/dev/null && return 0 || return 1
    elif command -v nslookup &>/dev/null; then
        nslookup "$host" &>/dev/null && return 0 || return 1
    else
        # Fallback: tentative de connexion TCP au port 443
        (echo >/dev/tcp/"$host"/443) &>/dev/null && return 0 || return 1
    fi
}

if _check_dns "registry-1.docker.io"; then
    _ok "DNS Docker Hub (registry-1.docker.io) : résolu"
else
    _fail "DNS Docker Hub inaccessible — les pulls d'images vont échouer"
    info  "Vérifie ta connexion réseau et /etc/resolv.conf"
fi

# Tester la connectivité HTTPS vers Docker Hub
if curl -sf --connect-timeout 5 --max-time 10 "https://registry-1.docker.io/v2/" -o /dev/null; then
    _ok "HTTPS Docker Hub : accessible"
elif curl -sf --connect-timeout 5 --max-time 10 "https://registry-1.docker.io/v2/" -o /dev/null 2>&1 | grep -q "401"; then
    # 401 = auth required = le serveur répond
    _ok "HTTPS Docker Hub : accessible (auth required — normal)"
else
    _warn "HTTPS Docker Hub : connexion lente ou timeout (les pulls peuvent être lents)"
fi

# ── 6. Fichier .env et variables critiques ──────────────────────

section "6/7 — Configuration (.env)"

ENV_FILE="${ETHAN_ROOT}/.env"
ENV_EXAMPLE="${ETHAN_ROOT}/.env.example"

if [ -f "$ENV_FILE" ]; then
    _ok ".env : présent"

    # Vérifier les variables clés
    _check_env_var() {
        local var="$1"
        local severity="${2:-warn}"  # warn ou error
        local val
        # shellcheck disable=SC1090
        val="$(grep -E "^${var}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"'"'" || true)"

        if [[ -z "$val" ]] || [[ "$val" == *"CHANGE_ME"* ]] || [[ "$val" == *"your_"* ]]; then
            if [[ "$severity" == "error" ]]; then
                _fail ".env : $var non défini ou placeholder"
            else
                _warn ".env : $var non défini (valeur par défaut utilisée)"
            fi
        else
            _ok ".env : $var défini"
        fi
    }

    _check_env_var "POSTGRES_PASSWORD" "warn"
    # Variables optionnelles mais importantes
    for var in OPENAI_API_KEY ANTHROPIC_API_KEY; do
        val="$(grep -E "^${var}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"'"'" || true)"
        if [[ -z "$val" ]]; then
            info ".env : $var vide (LLM cloud désactivé)"
        else
            _ok ".env : $var défini"
        fi
    done

else
    if [ -f "$ENV_EXAMPLE" ]; then
        _warn ".env absent — création depuis .env.example (valeurs par défaut)"
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        info "Édite ${ENV_FILE} pour configurer tes secrets"
    else
        _fail ".env absent et .env.example introuvable"
    fi
fi

# Vérifier que le fichier docker-compose.yml est valide
if docker compose -f "${COMPOSE_FILE}" config &>/dev/null 2>&1; then
    _ok "docker-compose.yml : syntaxe valide"
else
    _fail "docker-compose.yml : erreur de syntaxe"
    info  "Correction : docker compose -f ${COMPOSE_FILE} config"
fi

# ── 7. Docker images cache ──────────────────────────────────────

section "7/7 — Cache des images Docker"

declare -A BASE_IMAGES=(
    ["python:3.12-slim"]="Base Python (api, kernel, modules)"
    ["node:20-alpine"]="Base Node.js (ui)"
    ["nats:2.10-alpine"]="NATS"
    ["redis:7-alpine"]="Redis"
    ["postgres:16-alpine"]="PostgreSQL"
    ["prom/prometheus:latest"]="Prometheus"
)

cached=0
to_pull=0
for image in "${!BASE_IMAGES[@]}"; do
    label="${BASE_IMAGES[$image]}"
    if docker image inspect "$image" &>/dev/null 2>&1; then
        _ok "Image en cache : $image"
        (( cached++ )) || true
    else
        _warn "Image absente du cache : $image ($label) — sera téléchargée au démarrage"
        (( to_pull++ )) || true
    fi
done

if (( to_pull > 0 )); then
    info "→ ${to_pull} image(s) à télécharger — premier démarrage plus long"
    info "→ Pour pré-télécharger : ./ethan pull-images"
fi

# ── Résumé ──────────────────────────────────────────────────────

section "Résumé préflight"

if (( ERRORS == 0 && WARNINGS == 0 )); then
    success "Préflight OK — système prêt pour 'ethan up'"
    exit 0
elif (( ERRORS == 0 )); then
    warn "${WARNINGS} avertissement(s) — le démarrage devrait fonctionner mais vérifier ci-dessus"
    if [[ "$STRICT_MODE" == "--strict" ]]; then
        error "Mode strict activé — traiter les avertissements avant de continuer"
        exit 1
    fi
    exit 0
else
    error "${ERRORS} erreur(s) bloquante(s) + ${WARNINGS} avertissement(s)"
    info  "Corriger les erreurs ci-dessus avant de relancer 'ethan up'"
    exit 1
fi
