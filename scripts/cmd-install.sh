#!/usr/bin/env bash
# ethan install — Installer ETHAN (dépendances + config + systemd)
# Usage: ./ethan install
#
# Ce script :
#   1. Vérifie les dépendances système
#   2. Installe les dépendances frontend et Python
#   3. Configure .env
#   4. Crée l'utilisateur systemd 'ethan'
#   5. Déploie les services systemd (ethan-core, ethan-watchdog)
#   6. Active le démarrage automatique au boot

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
    arrow "Édite .env pour configurer tes secrets (POSTGRES_PASSWORD, JWT_SECRET)"
elif [ -f "${ETHAN_ROOT}/.env" ]; then
    success ".env déjà présent"
else
    warn "Aucun fichier .env.example trouvé"
fi

# ── 6. Créer le dossier logs ──────────────────────────────────
mkdir -p "$LOG_DIR"
success "Dossier logs : ${LOG_DIR}"

# ── 7. Configuration système (root requis) ────────────────────
if [ "$(id -u)" = "0" ]; then

    # ── 7a. Créer l'utilisateur systemd ethan ─────────────────
    section "7a. Utilisateur systemd"
    if ! id ethan &>/dev/null; then
        useradd --system --shell /usr/sbin/nologin --home-dir /var/lib/ethan ethan 2>/dev/null || true
        success "Utilisateur systemd 'ethan' créé"
    else
        info "Utilisateur 'ethan' déjà présent"
    fi

    if ! getent group docker | grep -qw ethan; then
        usermod -aG docker ethan 2>/dev/null || true
        success "Utilisateur 'ethan' ajouté au groupe 'docker'"
    fi

    mkdir -p /var/lib/ethan /var/log/ethan
    chown -R ethan:docker /var/lib/ethan /var/log/ethan 2>/dev/null || true
    success "Chemins : /var/lib/ethan, /var/log/ethan"

    # ── 7b. Déployer les fichiers systemd ─────────────────────
    section "7b. Services systemd"

    SYSTEMD_SRC="${ETHAN_ROOT}/infrastructure/systemd"
    SYSTEMD_DST="/etc/systemd/system"

    if [ -d "$SYSTEMD_SRC" ]; then
        for unit in ethan-core.service ethan-watchdog.service ethan-watchdog.timer; do
            if [ -f "${SYSTEMD_SRC}/${unit}" ]; then
                cp "${SYSTEMD_SRC}/${unit}" "${SYSTEMD_DST}/${unit}"
                chmod 644 "${SYSTEMD_DST}/${unit}"
                success "  ✓ ${unit}"
            else
                warn "  ✗ ${unit} introuvable dans ${SYSTEMD_SRC}"
            fi
        done

        systemctl daemon-reload
        success "systemd daemon-reload"

        # Activer au démarrage
        systemctl enable ethan-core.service 2>/dev/null \
            && success "ethan-core.service activé (démarrage auto)" \
            || warn "Impossible d'activer ethan-core.service"

        systemctl enable ethan-watchdog.timer 2>/dev/null \
            && success "ethan-watchdog.timer activé (supervision conteneurs)" \
            || warn "Impossible d'activer ethan-watchdog.timer"

        echo
        info "Prochaine étape :"
        arrow "sudo systemctl start ethan-core    → Démarrer ETHAN"
        arrow "sudo systemctl status ethan-core   → Vérifier l'état"
        arrow "sudo journalctl -u ethan-core -f   → Logs en temps réel"
    else
        warn "Répertoire systemd introuvable : ${SYSTEMD_SRC}"
    fi
else
    warn "root requis pour la configuration systemd"
    echo
    arrow "sudo $0    → Relancer en root pour installer les services"
    arrow "sudo usermod -aG docker $USER"
    arrow "sudo mkdir -p /var/lib/ethan /var/log/ethan"
    arrow "sudo chown -R $USER:docker /var/lib/ethan /var/log/ethan"
fi

# ── 8. Vérifier docker-compose ────────────────────────────────
section "8. Validation"
if docker compose -f "$COMPOSE_FILE" config &>/dev/null; then
    success "docker-compose.yml valide"
else
    warn "docker-compose.yml invalide — vérifier la syntaxe"
fi

section "Installation terminée"
arrow "./ethan up       → Démarrer les services"
arrow "./ethan doctor   → Diagnostiquer"
arrow "./ethan help     → Toutes les commandes"
if [ "$(id -u)" = "0" ]; then
    arrow "systemctl start ethan-core  → Via systemd (démarrage auto au boot)"
fi
metadata "$(timer_end)"