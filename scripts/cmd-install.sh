#!/usr/bin/env bash
# ethan install — Installer ETHAN (dépendances + config)
# Usage: ./ethan install

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start

section "Installation ETHAN"

# ── 1. Vérifier les dépendances systèmes ──────────────────────
info "Vérification des dépendances systèmes"
require_docker
require_node
require_python

# ── 2. Rendre le lanceur exécutable ───────────────────────────
if [ ! -x "${ETHAN_ROOT}/ethan" ]; then
    chmod +x "${ETHAN_ROOT}/ethan"
    success "Lanceur ./ethan rendu exécutable"
fi

# ── 3. Installer les dépendances frontend ─────────────────────
info "Installation des dépendances frontend"
if [ -f "${WEBUI_DIR}/package.json" ]; then
    cd "$WEBUI_DIR"
    npm install 2>&1 | tail -3
    success "npm install terminé"
    cd "$ETHAN_ROOT"
else
    error "package.json introuvable dans interfaces/webui"
fi

# ── 4. Installer les dépendances Python ───────────────────────
info "Installation des dépendances Python"
if [ -f "${ETHAN_ROOT}/pyproject.toml" ]; then
    # pip install en mode editable si on est dans un venv
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        pip install -e ".[server,dev]" 2>&1 | tail -2 || true
        success "pip install terminé"
    else
        info "Aucun venv actif — pip install ignoré"
        info "Active un environnement virtuel puis relance :"
        arrow "python3 -m venv .venv && source .venv/bin/activate"
    fi
else
    warn "pyproject.toml introuvable"
fi

# ── 5. Copier .env.example si nécessaire ──────────────────────
info "Configuration"
if [ ! -f "${ETHAN_ROOT}/.env" ] && [ -f "${ETHAN_ROOT}/.env.example" ]; then
    cp "${ETHAN_ROOT}/.env.example" "${ETHAN_ROOT}/.env"
    success ".env créé depuis .env.example"
    arrow "Édite .env pour configurer tes secrets"
elif [ -f "${ETHAN_ROOT}/.env" ]; then
    success ".env déjà présent"
else
    warn "Aucun fichier .env.example trouvé"
fi

# ── 6. Créer le dossier logs ──────────────────────────────────
mkdir -p "$LOG_DIR"
success "Dossier logs : ${LOG_DIR}"

# ── 7. Vérifier docker-compose ────────────────────────────────
if docker compose -f "$COMPOSE_FILE" config &>/dev/null; then
    success "docker-compose.yml valide"
fi

section "Installation terminée"
arrow "./ethan up     → Démarrer les services"
arrow "./ethan doctor → Diagnostiquer"
arrow "./ethan help   → Toutes les commandes"
metadata "$(timer_end)"