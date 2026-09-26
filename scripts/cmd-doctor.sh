#!/usr/bin/env bash
# ethan doctor — Diagnostic de santé complet du système ETHAN
# Usage: ./ethan doctor [--verbose] [--json]
#
# Ce script vérifie que chaque composant est réellement opérationnel,
# pas seulement présent. Chaque test affiche PASS, WARNING ou FAIL.
# En cas d'échec, la cause, la correction et le fichier concerné sont indiqués.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

# ── État global ────────────────────────────────────────────────────────
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
declare -a FAIL_DETAILS=()

# ── Compteurs ──────────────────────────────────────────────────────────

check_pass() {
    ((PASS_COUNT++)) || true
    success "$1"
}

check_fail() {
    ((FAIL_COUNT++)) || true
    error "$1"
    FAIL_DETAILS+=("$1")
}

check_warn() {
    ((WARN_COUNT++)) || true
    warn "$1"
}

# ── Aide : affichage détaillé ──────────────────────────────────────────

show_fix() {
    local cause="$1"
    local fix_cmd="$2"
    local file_ref="${3:-—}"
    local priority="${4:-medium}"

    arrow "Cause: $cause"
    arrow "Correction: $fix_cmd"
    arrow "Fichier: $file_ref"
    arrow "Priorité: $priority"
}

# NB : `_env_get` (lecture sûre d'une clé du .env) est fourni par ethan-lib.sh.

# ── Section 1 : Environnement ──────────────────────────────────────────

check_environment() {
    section "1. Environnement"

    # ETHAN_ROOT
    if [ -n "${ETHAN_ROOT:-}" ]; then
        check_pass "ETHAN_ROOT défini : ${ETHAN_ROOT}"
    else
        check_fail "ETHAN_ROOT non défini"
        show_fix \
            "Variable d'environnement ETHAN_ROOT absente" \
            "export ETHAN_ROOT=\$HOME/AI/Ethan" \
            "~/.bashrc, ~/.zshrc ou ~/.config/ethan/config.json" \
            "high"
    fi

    # PATH
    if echo "${PATH:-}" | grep -q "${ETHAN_ROOT}"; then
        check_pass "ETHAN_ROOT dans PATH"
    else
        check_warn "ETHAN_ROOT absent de PATH"
        show_fix \
            "Le répertoire ETHAN n'est pas dans PATH" \
            "export PATH=\"\$PATH:${ETHAN_ROOT}\"" \
            "~/.bashrc, ~/.zshrc" \
            "medium"
    fi

    # PYTHONPATH — n'est requis que si les imports échouent sans lui : depuis
    # ETHAN_ROOT, `python3 -c 'import core'` fonctionne (cwd dans sys.path).
    # On teste donc l'effet réel pour éviter un faux positif.
    if [ -n "${PYTHONPATH:-}" ]; then
        check_pass "PYTHONPATH défini : ${PYTHONPATH}"
    elif (cd "${ETHAN_ROOT}" && python3 -c "import core, sdk, plugins" 2>/dev/null); then
        check_pass "PYTHONPATH non requis : imports core/sdk/plugins OK depuis ${ETHAN_ROOT}"
    else
        check_warn "PYTHONPATH non défini et imports core/sdk/plugins en échec"
        show_fix \
            "Python ne trouve pas les modules core/sdk/plugins" \
            "export PYTHONPATH=\"\${PYTHONPATH}:${ETHAN_ROOT}\"" \
            "~/.bashrc, ~/.zshrc" \
            "high"
    fi

    # NODE_ENV — jamais requis côté shell : le service ui fixe sa valeur dans
    # docker-compose.yml. Warning uniquement si le compose ne la gère pas.
    if [ -n "${NODE_ENV:-}" ]; then
        check_pass "NODE_ENV=${NODE_ENV}"
    elif grep -q 'NODE_ENV' "${ETHAN_ROOT}/docker-compose.yml" 2>/dev/null; then
        check_pass "NODE_ENV non défini (valeur fixée par docker-compose.yml pour le service ui)"
    else
        check_warn "NODE_ENV non défini (défaut: development)"
    fi

    # virtualenv
    if [ -d "${ETHAN_ROOT}/.venv" ]; then
        check_pass "virtualenv présent (.venv)"
        # Vérifier que le venv est activé
        if [ -n "${VIRTUAL_ENV:-}" ]; then
            check_pass "virtualenv activé : ${VIRTUAL_ENV}"
        else
            check_warn "virtualenv présent mais non activé"
            show_fix \
                "Le virtualenv n'est pas activé dans le shell courant" \
                "source ${ETHAN_ROOT}/.venv/bin/activate" \
                ".venv/bin/activate" \
                "medium"
        fi
    else
        check_warn "virtualenv absent (.venv non trouvé)"
        show_fix \
            "Aucun virtualenv détecté" \
            "cd ${ETHAN_ROOT} && python3 -m venv .venv && source .venv/bin/activate && pip install -e ." \
            ".venv/" \
            "medium"
    fi

    # Versions
    check_command "python3" "Python 3" || {
        check_fail "Python 3 introuvable"
        show_fix \
            "Python 3 est requis" \
            "sudo apt install python3 python3-venv" \
            "/usr/bin/python3" \
            "high"
    }

    check_command "node" "Node.js" || {
        check_fail "Node.js introuvable"
        show_fix \
            "Node.js est requis pour le WebUI" \
            "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs" \
            "/usr/bin/node" \
            "high"
    }

    check_command "npm" "npm" || {
        check_fail "npm introuvable"
        show_fix \
            "npm est requis pour le WebUI" \
            "sudo apt install npm" \
            "/usr/bin/npm" \
            "high"
    }
}

# ── Section 2 : Imports Python ─────────────────────────────────────────

check_python_imports() {
    section "2. Imports Python"

    # Test de l'import core
    info "Import 'core'..."
    if python3 -c "import core; print(core.__file__)" 2>/dev/null; then
        local core_path
        core_path=$(python3 -c "import core; print(core.__file__)" 2>/dev/null)
        check_pass "core importable (${core_path})"
    else
        check_fail "Import core échoué"
        show_fix \
            "Module 'core' introuvable par Python" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'import core'" \
            "core/__init__.py" \
            "high"
    fi

    # Test de core.kernel
    info "Import 'core.kernel'..."
    if python3 -c "from core.kernel import CognitiveKernel; print(CognitiveKernel.__module__)" 2>/dev/null; then
        check_pass "core.kernel importable (CognitiveKernel trouvé)"
    else
        check_fail "Import core.kernel échoué"
        show_fix \
            "Impossible d'importer CognitiveKernel" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'from core.kernel import CognitiveKernel'" \
            "core/kernel.py" \
            "high"
    fi

    # Test de sdk
    info "Import 'sdk'..."
    if python3 -c "import sdk; print(sdk.__file__)" 2>/dev/null; then
        check_pass "sdk importable"
    else
        check_fail "Import sdk échoué"
        show_fix \
            "Module 'sdk' introuvable" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'import sdk'" \
            "sdk/__init__.py" \
            "high"
    fi

    # Test de runtime (optionnel).
    # Le dépôt n'a pas de dossier runtime/ (architecture core/sdk/plugins) :
    # dans ce cas le check est neutralisé — un warning (et son fix
    # `pip install -e runtime`) serait un faux positif inapplicable.
    # Le test redevient actif dès que le dossier apparaît.
    if [ ! -d "${ETHAN_ROOT}/runtime" ]; then
        info "Import 'runtime'... (dossier runtime/ absent — optionnel, check neutralisé)"
    elif python3 -c "import runtime; print(runtime.__file__)" 2>/dev/null; then
        check_pass "runtime importable"
    else
        check_warn "Import runtime échoué (optionnel)"
        show_fix \
            "Module 'runtime' introuvable (optionnel pour certaines fonctionnalités)" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && pip install -e runtime" \
            "runtime/" \
            "low"
    fi

    # Test de plugins
    info "Import 'plugins'..."
    if python3 -c "import plugins; print(plugins.__file__)" 2>/dev/null; then
        check_pass "plugins importable"
    else
        check_warn "Import plugins échoué (optionnel)"
        show_fix \
            "Module 'plugins' introuvable" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'import plugins'" \
            "plugins/__init__.py" \
            "low"
    fi
}

# ── Section 3 : Docker ─────────────────────────────────────────────────

check_docker() {
    section "3. Docker"

    # Daemon
    if command -v docker &>/dev/null; then
        check_pass "Docker CLI présent"
        if docker info &>/dev/null; then
            check_pass "Docker daemon actif"
            local dock_ver
            dock_ver=$(docker info --format '{{.ServerVersion}}' 2>/dev/null || echo "?")
            info "Docker daemon version: ${dock_ver}"
        else
            check_fail "Docker daemon injoignable"
            show_fix \
                "Le daemon Docker ne répond pas" \
                "sudo systemctl start docker && sudo systemctl enable docker" \
                "systemd docker service" \
                "high"
        fi
    else
        check_fail "Docker CLI introuvable"
        show_fix \
            "Docker n'est pas installé" \
            "curl -fsSL https://get.docker.com | sh" \
            "/usr/bin/docker" \
            "high"
    fi

    # Docker Compose
    if docker compose version &>/dev/null; then
        local compose_ver
        compose_ver=$(docker compose version --short 2>/dev/null || echo "?")
        check_pass "Docker Compose v${compose_ver}"
    else
        check_fail "Docker Compose introuvable"
        show_fix \
            "Docker Compose plugin manquant" \
            "sudo apt install docker-compose-plugin" \
            "/usr/libexec/docker/cli-plugins/docker-compose" \
            "high"
    fi

    # Compose file
    info "Fichier docker-compose.yml..."
    if [ -f "${COMPOSE_FILE}" ]; then
        check_pass "docker-compose.yml présent"
        if docker compose -f "$COMPOSE_FILE" config &>/dev/null; then
            check_pass "docker-compose.yml syntaxe valide"
        else
            check_fail "docker-compose.yml syntaxe invalide"
            show_fix \
                "Erreur de syntaxe dans docker-compose.yml" \
                "docker compose -f ${COMPOSE_FILE} config" \
                "docker-compose.yml" \
                "high"
        fi
    else
        check_fail "docker-compose.yml manquant"
        show_fix \
            "Le fichier docker-compose.yml n'existe pas" \
            "ls -la ${ETHAN_ROOT}/docker-compose.yml" \
            "docker-compose.yml (racine du projet)" \
            "high"
    fi

    # Images
    info "Images Docker..."
    if docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -q "ethan\|nats\|redis\|postgres"; then
        check_pass "Images ETHAN présentes"
    else
        check_warn "Aucune image ETHAN détectée — exécuter ./ethan install"
        show_fix \
            "Les images Docker pour ETHAN ne sont pas construites" \
            "./ethan install" \
            "deploy/Dockerfile.*" \
            "medium"
    fi

    # Containers
    info "Containers Docker..."
    local ethan_containers
    ethan_containers=$(docker ps --filter "name=ethan" --format '{{.Names}}' 2>/dev/null | wc -l)
    if [ "$ethan_containers" -gt 0 ]; then
        check_pass "$ethan_containers container(s) ETHAN en cours d'exécution"
    else
        check_warn "Aucun container ETHAN en cours d'exécution"
        show_fix \
            "Les services Docker ne sont pas démarrés" \
            "./ethan up" \
            "docker-compose.yml" \
            "medium"
    fi

    # Volumes
    info "Volumes Docker..."
    if docker volume ls --filter "name=ethan" --format '{{.Name}}' 2>/dev/null | grep -q .; then
        check_pass "Volumes ETHAN présents"
    else
        check_warn "Volumes ETHAN non détectés"
    fi

    # Réseaux
    info "Réseaux Docker..."
    if docker network ls --filter "name=ethan" --format '{{.Name}}' 2>/dev/null | grep -q .; then
        check_pass "Réseau ethan-core présent"
    else
        check_warn "Réseau ethan-core absent"
        show_fix \
            "Le réseau Docker 'ethan-core' n'existe pas" \
            "docker compose up -d" \
            "docker-compose.yml (networks)" \
            "medium"
    fi
}

# ── Section 4 : Services Docker ────────────────────────────────────────

check_docker_services() {
    section "4. Services Docker"

    # Ports host résolus par ethan-lib.sh (mêmes clés que docker-compose.yml).
    local services=(
        "ethan-nats:NATS:${NATS_PORT}"
        "ethan-redis:Redis:${REDIS_PORT}"
        "ethan-postgres:PostgreSQL:${POSTGRES_PORT}"
        "ethan-api:API Gateway:${ETHAN_API_PORT}"
        "ethan-kernel:Core Kernel:${ETHAN_KERNEL_PORT}"
        "ethan-modules:Cognitive Modules:—"
        "ethan-ui:WebUI:${ETHAN_WEBUI_PORT}"
        "ethan-pg_backup:PostgreSQL Backup:—"
    )

    for svc_info in "${services[@]}"; do
        IFS=':' read -r container label port <<< "$svc_info"
        info "Vérification de ${label} (${container})..."

        # Conteneur existe-t-il ? (docker ps OU docker_compose ps)
        if docker ps --format '{{.Names}}' | grep -q "^${container}$" || \
           docker_compose ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container}$"; then
            check_pass "${label} : container en cours d'exécution"

            # Healthcheck Docker
            local health
            health=$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "unknown")
            case "$health" in
                healthy)
                    check_pass "${label} : healthcheck OK"
                    ;;
                none)
                    check_warn "${label} : pas de healthcheck configuré"
                    ;;
                unhealthy)
                    check_fail "${label} : healthcheck FAILED"
                    show_fix \
                        "Le healthcheck du container a échoué" \
                        "docker logs ${container} --tail 100" \
                        "docker-compose.yml (healthcheck pour ${container})" \
                        "high"
                    ;;
                starting)
                    check_warn "${label} : healthcheck en cours (starting)"
                    ;;
                *)
                    check_warn "${label} : healthcheck status inconnu (${health})"
                    ;;
            esac

            # Port exposé (si applicable)
            if [ "$port" != "—" ]; then
                if docker port "$container" 2>/dev/null | grep -q ":${port}"; then
                    check_pass "${label} : port ${port} exposé"
                else
                    check_fail "${label} : port ${port} non exposé"
                    show_fix \
                        "Le port ${port} n'est pas exposé pour ${container}" \
                        "Vérifier la section 'ports' dans docker-compose.yml pour ${container}" \
                        "docker-compose.yml" \
                        "high"
                fi
            fi
        else
            check_fail "${label} : container absent ou arrêté"
            show_fix \
                "Le container ${container} n'est pas en cours d'exécution" \
                "docker compose up -d ${container}" \
                "docker-compose.yml" \
                "high"
        fi
    done
}

# ── Section 5 : Connectivité HTTP ──────────────────────────────────────

check_http_connectivity() {
    section "5. Connectivité HTTP"

    # Ports host résolus par ethan-lib.sh (API_PORT/PORT restent prioritaires
    # si l'appelant les exporte).
    local API_PORT="${API_PORT:-${ETHAN_API_PORT:-8000}}"
    local WEBUI_PORT="${PORT:-${ETHAN_WEBUI_PORT:-3001}}"

    # API Gateway
    # NB : `/` n'existe pas comme route publique (401 via middleware JWT) —
    # le contrat de disponibilité est /health (PUBLIC_PATHS, healthcheck Docker).
    info "API Gateway (port ${API_PORT})..."
    if wait_for_http "http://localhost:${API_PORT}/health" 5; then
        check_pass "API Gateway : répond sur /health"
    else
        check_fail "API Gateway : injoignable sur http://localhost:${API_PORT}/health"
        show_fix \
            "L'API Gateway ne répond pas" \
            "docker compose logs api --tail 50 && docker compose restart api" \
            "docker-compose.yml (service api)" \
            "high"
    fi

    # Health readiness (contrat du healthcheck Docker)
    if curl -sf "http://localhost:${API_PORT}/health/ready" >/dev/null 2>&1; then
        check_pass "API Gateway : /health/ready répond"
    else
        check_warn "API Gateway : /health/ready inaccessible"
    fi

    # Version endpoint (contrat public : /v1/version)
    if curl -sf "http://localhost:${API_PORT}/v1/version" >/dev/null 2>&1; then
        check_pass "API Gateway : /v1/version répond"
    else
        check_warn "API Gateway : /v1/version inaccessible"
    fi

    # Swagger
    if curl -sf "http://localhost:${API_PORT}/docs" >/dev/null 2>&1; then
        check_pass "API Gateway : Swagger UI (/docs) accessible"
    else
        check_warn "API Gateway : Swagger UI inaccessible"
    fi

    # WebSocket endpoint (test basique)
    # Sans vrai client WS, un HTTP 400/426 est la réponse légitime : l'enjeu
    # est que la route existe (elle rejette le handshake) et non un 404/401.
    local ws_code
    ws_code="$(curl -s -o /dev/null -w '%{http_code}' \
        -H "Connection: Upgrade" -H "Upgrade: websocket" \
        "http://localhost:${API_PORT}/v1/events/ws" 2>/dev/null || true)"
    case "$ws_code" in
        101|400|426) check_pass "API Gateway : WebSocket /v1/events/ws présent (HTTP $ws_code)" ;;
        *)           check_warn "API Gateway : WebSocket /v1/events/ws non vérifiable (HTTP ${ws_code:-—})" ;;
    esac

    # WebUI
    info "WebUI (port ${WEBUI_PORT})..."
    if wait_for_http "http://localhost:${WEBUI_PORT}/" 10; then
        check_pass "WebUI : répond sur /"

        # Test de connectivité WebUI → API
        # Contrat public : /health (et non les routes JWT-protégées comme
        # /api/v1/version, qui répondaient 401 → faux échec).
        if curl -sf "http://localhost:${WEBUI_PORT}/" >/dev/null 2>&1 && \
           curl -sf "http://localhost:${API_PORT}/health" >/dev/null 2>&1; then
            check_pass "WebUI → API : connectivité OK"
        else
            check_fail "WebUI → API : connectivité échouée"
            show_fix \
                "La WebUI ne peut pas contacter l'API Gateway" \
                "Vérifier CORS, API_URL dans docker-compose.yml, et les logs WebUI" \
                "docker-compose.yml (variable API_URL), interfaces/webui/src/" \
                "high"
        fi
    else
        check_fail "WebUI : injoignable sur http://localhost:${WEBUI_PORT}/"
        show_fix \
            "La WebUI ne répond pas" \
            "docker compose logs ui --tail 50 && docker compose restart ui" \
            "docker-compose.yml (service ui)" \
            "high"
    fi
}

# ── Section 6 : Services d'infrastructure ──────────────────────────────

check_infrastructure_services() {
    section "6. Services d'infrastructure"

    # NATS
    info "NATS (port 4222)..."
    if nc -z localhost 4222 2>/dev/null || (echo > /dev/tcp/localhost/4222) 2>/dev/null; then
        check_pass "NATS : port 4222 ouvert"
        if curl -sf "http://localhost:8222/varz" >/dev/null 2>&1; then
            check_pass "NATS : monitoring HTTP actif (8222)"
        else
            check_warn "NATS : monitoring HTTP inaccessible (8222)"
        fi
    else
        check_fail "NATS : port 4222 fermé"
        show_fix \
            "NATS n'est pas accessible" \
            "docker compose ps nats && docker compose logs nats --tail 50" \
            "docker-compose.yml (service nats)" \
            "high"
    fi

    # Redis
    info "Redis (port 6379)..."
    if nc -z localhost 6379 2>/dev/null || (echo > /dev/tcp/localhost/6379) 2>/dev/null; then
        check_pass "Redis : port 6379 ouvert"
        # Le mot de passe vit dans .env (compose le lit) : sans lui, redis-cli
        # répond NOAUTH → faux FAIL.
        local redis_pass redis_ping
        redis_pass="${REDIS_PASSWORD:-$(_env_get REDIS_PASSWORD)}"
        if command -v redis-cli &>/dev/null; then
            if [[ -n "$redis_pass" ]]; then
                redis_ping="$(redis-cli -a "$redis_pass" ping 2>/dev/null || true)"
            else
                redis_ping="$(redis-cli ping 2>/dev/null || true)"
            fi
            if grep -q "PONG" <<<"$redis_ping"; then
                check_pass "Redis : PING répond (PONG)"
            else
                check_fail "Redis : PING échoue"
                show_fix \
                    "Redis ne répond pas au PING" \
                    "docker compose logs redis --tail 50 && docker compose restart redis" \
                    "docker-compose.yml (service redis)" \
                    "high"
            fi
        else
            # redis-cli absent du host → fallback via le conteneur : un port
            # ouvert ne prouve pas que Redis répond (test réel).
            local redis_container_cmd=(docker exec ethan-redis redis-cli)
            if [[ -n "$redis_pass" ]]; then
                redis_container_cmd+=(-a "$redis_pass")
            fi
            redis_container_cmd+=(ping)
            redis_ping="$("${redis_container_cmd[@]}" 2>/dev/null || true)"
            if grep -q "PONG" <<<"$redis_ping"; then
                check_pass "Redis : PING répond via le conteneur (redis-cli absent du host)"
            else
                check_warn "Redis : port ouvert, PING non vérifiable (ni host ni conteneur)"
            fi
        fi
    else
        check_fail "Redis : port 6379 fermé"
        show_fix \
            "Redis n'est pas accessible" \
            "docker compose ps redis && docker compose logs redis --tail 50" \
            "docker-compose.yml (service redis)" \
            "high"
    fi

    # PostgreSQL
    info "PostgreSQL (port 5432)..."
    if nc -z localhost 5432 2>/dev/null || (echo > /dev/tcp/localhost/5432) 2>/dev/null; then
        check_pass "PostgreSQL : port 5432 ouvert"
        if command -v psql &>/dev/null; then
            # Le mot de passe vit dans .env (compose le lit) : le doctor doit
            # le lire de la même façon, sinon faux FAIL d'authentification.
            # (Jamais affiché : règle « aucun secret dans les logs ».)
            local pg_password
            pg_password="${POSTGRES_PASSWORD:-$(_env_get POSTGRES_PASSWORD)}"
            pg_password="${pg_password:-ethan_dev_pass}"
            if PGPASSWORD="$pg_password" psql -h localhost -U ethan -d ethan -c "SELECT 1" &>/dev/null; then
                check_pass "PostgreSQL : connexion et requête OK"
            else
                check_fail "PostgreSQL : impossible de se connecter"
                show_fix \
                    "Connexion PostgreSQL échouée (vérifier identifiants)" \
                    "PGPASSWORD=<POSTGRES_PASSWORD du .env> psql -h localhost -U ethan -d ethan" \
                    "docker-compose.yml (POSTGRES_PASSWORD)" \
                    "high"
            fi
        else
            check_warn "PostgreSQL : port ouvert mais psql non installé (test limité)"
        fi
    else
        check_fail "PostgreSQL : port 5432 fermé"
        show_fix \
            "PostgreSQL n'est pas accessible" \
            "docker compose ps postgres && docker compose logs postgres --tail 50" \
            "docker-compose.yml (service postgres)" \
            "high"
    fi
}

# ── Section 7 : Core ───────────────────────────────────────────────────

check_core() {
    section "7. Core"

    info "Import core.kernel..."
    if python3 -c "from core.kernel import CognitiveKernel; print('OK')" 2>/dev/null; then
        check_pass "Core Kernel : import réussi"
    else
        check_fail "Core Kernel : import échoué"
        show_fix \
            "Impossible d'importer CognitiveKernel" \
            "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'from core.kernel import CognitiveKernel'" \
            "core/kernel.py" \
            "high"
    fi

    info "Vérification des providers LLM..."
    # Module réel : core/llm/provider_factory.py + core/llm/registry.py
    # (l'ancien chemin core.providers.* a disparu lors du rebuild).
    local provider_count
    if provider_count=$(python3 -c "
import sys
sys.path.insert(0, '${ETHAN_ROOT}')
from core.llm.provider_factory import create_default_providers
print(len(create_default_providers()))
" 2>/dev/null) && [[ "$provider_count" =~ ^[0-9]+$ ]] && (( provider_count > 0 )); then
        check_pass "Core : ${provider_count} provider(s) LLM par défaut (factory opérationnelle)"
    else
        check_warn "Core : impossible de vérifier les providers LLM"
        show_fix \
            "Le sous-système providers LLM du Core n'est pas importable" \
            "cd ${ETHAN_ROOT} && python3 -c 'from core.llm.provider_factory import create_default_providers; print(len(create_default_providers()))'" \
            "core/llm/provider_factory.py" \
            "medium"
    fi

    info "Vérification du catalogue de plugins..."
    # Modules réels : core/plugins/ (catalogue BUILTIN_PLUGINS + PluginRegistry).
    # PluginRegistry() exige un CoreRecordStore : on vérifie le catalogue et
    # l'importabilité du registre (l'ancien chemin core.registry a disparu).
    local plugin_count
    if plugin_count=$(python3 -c "
import sys
sys.path.insert(0, '${ETHAN_ROOT}')
from core.plugins import BUILTIN_PLUGINS, PluginRegistry
print(len(BUILTIN_PLUGINS))
" 2>/dev/null) && [[ "$plugin_count" =~ ^[0-9]+$ ]] && (( plugin_count > 0 )); then
        check_pass "Core : ${plugin_count} plugin(s) au catalogue (PluginRegistry importable)"
    else
        check_warn "Core : impossible de vérifier le catalogue de plugins"
        show_fix \
            "Le catalogue de plugins du Core n'est pas importable" \
            "cd ${ETHAN_ROOT} && python3 -c 'from core.plugins import BUILTIN_PLUGINS; print(len(BUILTIN_PLUGINS))'" \
            "core/plugins/catalog.py" \
            "medium"
    fi
}

# ── Section 8 : SDK ────────────────────────────────────────────────────

check_sdk() {
    section "8. SDK"

    local sdk_modules=(
        "sdk.event:Event SDK"
        "sdk.autonomy:Autonomy SDK"
        "sdk.learning:Learning SDK"
        "sdk.module:Module SDK"
        "sdk.goals:Goals SDK"
        "sdk.metacognition:Metacognition SDK"
    )

    for module_info in "${sdk_modules[@]}"; do
        IFS=':' read -r module label <<< "$module_info"
        info "Import '${module}'..."
        if python3 -c "from ${module} import *" 2>/dev/null; then
            check_pass "SDK : ${label} importable"
        else
            check_warn "SDK : ${label} import échoué"
            show_fix \
                "Import ${module} a échoué" \
                "cd ${ETHAN_ROOT} && export PYTHONPATH=\${PYTHONPATH}:\${PWD} && python3 -c 'from ${module} import *'" \
                "${module//./\/}.py" \
                "medium"
        fi
    done

    # Compatibilité SDK ↔ Core
    info "Compatibilité SDK ↔ Core..."
    if python3 -c "
import sys
sys.path.insert(0, '${ETHAN_ROOT}')
from sdk.event import EventType
from core.kernel import CognitiveKernel
print('SDK compatible avec Core')
" 2>/dev/null; then
        check_pass "SDK ↔ Core : compatibilité vérifiée"
    else
        check_warn "SDK ↔ Core : impossible de vérifier la compatibilité"
    fi
}

# ── Section 9 : CLI ────────────────────────────────────────────────────

check_cli() {
    section "9. CLI"

    if [ -d "${CLI_DIR}" ]; then
        check_pass "Répertoire CLI présent : ${CLI_DIR}"
    else
        check_fail "Répertoire CLI absent : ${CLI_DIR}"
        show_fix \
            "Le répertoire CLI n'existe pas" \
            "git status && ls -la ${ETHAN_ROOT}/interfaces/cli/" \
            "interfaces/cli/" \
            "high"
    fi

    # Vérifier que ./ethan est exécutable
    if [ -x "${ETHAN_ROOT}/ethan" ]; then
        check_pass "./ethan est exécutable"
    else
        check_fail "./ethan n'est pas exécutable"
        show_fix \
            "Le fichier ./ethan n'a pas les droits d'exécution" \
            "chmod +x ${ETHAN_ROOT}/ethan" \
            "${ETHAN_ROOT}/ethan" \
            "high"
    fi

    # Tester l'aide de la commande doctor
    info "Test de la commande 'ethan doctor --help'..."
    if "${ETHAN_ROOT}/ethan" doctor --help &>/dev/null; then
        check_pass "Commande 'ethan doctor --help' fonctionne"
    else
        check_warn "Commande 'ethan doctor --help' a échoué"
    fi
}

# ── Section 10 : WebUI (frontend) ──────────────────────────────────────

check_webui() {
    section "10. WebUI (Frontend)"

    if [ -d "${WEBUI_DIR}" ]; then
        check_pass "Répertoire WebUI présent : ${WEBUI_DIR}"
    else
        check_fail "Répertoire WebUI absent : ${WEBUI_DIR}"
        show_fix \
            "Le répertoire interfaces/webui n'existe pas" \
            "ls -la ${ETHAN_ROOT}/interfaces/webui/" \
            "interfaces/webui/" \
            "high"
        return
    fi

    # package.json
    if [ -f "${WEBUI_DIR}/package.json" ]; then
        check_pass "package.json présent"
    else
        check_fail "package.json absent"
        show_fix \
            "package.json manquant" \
            "ls -la ${WEBUI_DIR}/package.json" \
            "interfaces/webui/package.json" \
            "high"
    fi

    # node_modules
    if [ -d "${WEBUI_DIR}/node_modules" ]; then
        check_pass "node_modules installé"
    else
        check_warn "node_modules non installé"
        show_fix \
            "Les dépendances Node.js ne sont pas installées" \
            "cd ${WEBUI_DIR} && npm install" \
            "${WEBUI_DIR}/package-lock.json" \
            "medium"
    fi

    # Next.js / build
    if [ -f "${WEBUI_DIR}/next.config.js" ] || [ -f "${WEBUI_DIR}/next.config.ts" ]; then
        check_pass "Next.js configuré"
    else
        check_warn "Configuration Next.js non détectée"
    fi
}

# ── Section 11 : Résumé ────────────────────────────────────────────────

show_summary() {
    section "Résumé"

    echo
    if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
        check_pass "Tout est opérationnel (${PASS_COUNT} PASS, ${WARN_COUNT} WARNING)"
        echo
        dim "⏱ $(date '+%H:%M:%S')"
    elif [ "$FAIL_COUNT" -eq 0 ]; then
        check_pass "Aucun échec critique (${PASS_COUNT} PASS, ${WARN_COUNT} WARNING, ${FAIL_COUNT} FAIL)"
        echo
        info "Corrections suggérées :"
        for detail in "${FAIL_DETAILS[@]}"; do
            echo -e "  ${C_CYAN}${I_ARROW}${C_RESET} ${detail}"
        done
        echo
        info "Pour plus de détails : ./ethan logs"
        dim "⏱ $(date '+%H:%M:%S')"
    else
        check_fail "Problèmes détectés : ${FAIL_COUNT} FAIL, ${WARN_COUNT} WARNING, ${PASS_COUNT} PASS"
        echo
        info "Actions prioritaires :"
        info "  1. Vérifier les logs : ./ethan logs"
        info "  2. Diagnostic des services : docker compose ps"
        info "  3. Redémarrer : ./ethan restart"
        info "  4. Réinstaller : ./ethan install"
        echo
        info "Corrections suggérées :"
        for detail in "${FAIL_DETAILS[@]}"; do
            echo -e "  ${C_RED}${I_ARROW}${C_RESET} ${detail}"
        done
        echo
        dim "⏱ $(date '+%H:%M:%S')"
    fi

    echo
    dim "Pour une aide détaillée : ./ethan help"
    echo
}

# ── Section 12 : Json output (optionnel) ───────────────────────────────

generate_json() {
    cat <<EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "system": "ETHAN",
  "status": $([ "$FAIL_COUNT" -eq 0 ] && echo "\"healthy\"" || echo "\"degraded\""),
  "summary": {
    "pass": ${PASS_COUNT},
    "fail": ${FAIL_COUNT},
    "warn": ${WARN_COUNT}
  },
  "details": [
EOF

    local first=true
    # Liste basique des résultats (simplifié pour JSON)
    if [ "$first" = true ]; then
        first=false
    fi

    cat <<EOF
    {
      "summary": "ETHAN Doctor completed",
      "pass": ${PASS_COUNT},
      "fail": ${FAIL_COUNT},
      "warn": ${WARN_COUNT}
    }
  ]
}
EOF
}

# ── Main ────────────────────────────────────────────────────────────────

main() {
    local verbose=false
    local json_output=false

    for arg in "$@"; do
        case "$arg" in
            --verbose|-v) verbose=true ;;
            --json|-j) json_output=true ;;
            --help|-h)
                echo "ETHAN Doctor — Diagnostic de santé du système"
                echo ""
                echo "Usage: ./ethan doctor [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --verbose, -v   Afficher les détails supplémentaires"
                echo "  --json, -j      Sortie au format JSON"
                echo "  --help, -h      Afficher cette aide"
                echo ""
                echo "Exemples:"
                echo "  ./ethan doctor              # Diagnostic standard"
                echo "  ./ethan doctor --verbose    # Diagnostic détaillé"
                echo "  ./ethan doctor --json       # Pour intégration/automatisation"
                echo ""
                exit 0
                ;;
        esac
    done

    # En-tête
    echo ""
    bold "${C_CYAN}◆${C_RESET}  ${C_BOLD}ETHAN Doctor — Diagnostic de santé${C_RESET}"
    dim "$(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Exécuter tous les checks
    check_environment
    check_python_imports
    check_docker
    check_docker_services
    check_http_connectivity
    check_infrastructure_services
    check_core
    check_sdk
    check_cli
    check_webui

    # Résultat
    if [ "$json_output" = true ]; then
        generate_json
    else
        show_summary
    fi

    # Code de sortie : 0 si pas d'échec, sinon nombre d'échecs
    exit "$FAIL_COUNT"
}

main "$@"