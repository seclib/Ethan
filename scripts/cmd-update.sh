#!/usr/bin/env bash
# ethan update — Mettre à jour ETHAN
# Usage: ./ethan update [--branch=main]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start

BRANCH="main"
for arg in "$@"; do
    case "$arg" in
        --branch=*) BRANCH="${arg#*=}" ;;
    esac
done

section "Mise à jour ETHAN"

# ── 1. Git pull ───────────────────────────────────────────────
if ! command -v git &>/dev/null; then
    error "Git n'est pas installé"
    exit 1
fi

info "Branche : ${BRANCH}"
git fetch origin "$BRANCH"
BEHIND=$(git rev-list --count "HEAD..origin/${BRANCH}" 2>/dev/null || echo 0)

if [ "$BEHIND" -eq 0 ]; then
    success "Déjà à jour (${BRANCH})"
else
    info "Mise à jour de ${BEHIND} commits..."
    git pull origin "$BRANCH"
    success "Code mis à jour"
fi

# ── 2. Re-installer les dépendances si package.json a changé ──
if git diff HEAD@{1} --name-only 2>/dev/null | grep -q "interfaces/webui/package.json"; then
    info "package.json modifié — réinstallation npm..."
    cd "$WEBUI_DIR" && npm install && cd "$ETHAN_ROOT"
    success "npm install terminé"
fi

# ── 3. Re-build Docker ─────────────────────────────────────────
if git diff HEAD@{1} --name-only 2>/dev/null | grep -q "docker-compose.yml\|Dockerfile"; then
    info "Dockerfiles modifiés — rebuild..."
    docker_compose build
    success "Images rebuild"
fi

# ── 4. Redémarrer si des services tournent ────────────────────
if docker_compose ps --services --filter "status=running" 2>/dev/null | grep -q .; then
    info "Redémarrage des services..."
    docker_compose up -d
    success "Services redémarrés"
    arrow "Fais ./ethan status pour vérifier"
fi

section "Mise à jour terminée"
metadata "$(timer_end)"