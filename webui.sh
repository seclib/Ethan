#!/usr/bin/env bash
# webui.sh — Lanceur du dashboard ETHAN Web UI
# Usage: ./webui.sh [--port 8501] [--api-url http://localhost:8000]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBUI_DIR="$SCRIPT_DIR/interfaces/webui"
VENV_DIR="$SCRIPT_DIR/.venv"
API_URL="${ETHAN_API_URL:-http://localhost:8000}"
PORT="${PORT:-8090}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERROR]${NC} $*"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        *)
            err "Option inconnue: $1"
            echo "Usage: $0 [--port 8501] [--api-url http://localhost:8000]"
            exit 1
            ;;
    esac
done

info "Lancement du dashboard ETHAN Web UI"
info "API URL: $API_URL"
info "Port: $PORT"

# Détecter le venv actif si présent
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    info "Venv actif détecté: $VIRTUAL_ENV"
    VENV_DIR="$VIRTUAL_ENV"
elif [[ -d "$VENV_DIR" ]]; then
    info "Venv du projet trouvé: $VENV_DIR"
else
    warn "Venv non trouvé, création avec pip..."
    python3 -m venv --with-pip "$VENV_DIR"
fi

# Fallback: si pip n'existe pas dans le venv, utiliser get-pip.py
if ! "$VENV_DIR/bin/python" -m pip --version 2>/dev/null; then
    warn "pip manquant dans le venv, installation via get-pip.py..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$VENV_DIR/bin/python" 2>/dev/null || {
        err "Impossible d'installer pip automatiquement"
        err "Installez-le manuellement dans le venv: $VENV_DIR/bin/python -m ensurepip --default-pip"
        exit 1
    }
fi

# Vérifier que streamlit est disponible
if ! "$VENV_DIR/bin/python" -c "import streamlit" 2>/dev/null; then
    warn "Installation des dépendances webui..."
    REQ_FILE="$WEBUI_DIR/requirements-webui.txt"
    if [[ -f "$REQ_FILE" ]]; then
        if ! "$VENV_DIR/bin/python" -m pip install -r "$REQ_FILE"; then
            err "Échec de l'installation des dépendances"
            err "Essayez manuellement: $VENV_DIR/bin/python -m pip install streamlit httpx fastapi uvicorn"
            exit 1
        fi
    else
        if ! "$VENV_DIR/bin/python" -m pip install streamlit httpx fastapi uvicorn; then
            err "Échec de l'installation de streamlit"
            err "Essayez manuellement: $VENV_DIR/bin/python -m pip install streamlit httpx fastapi uvicorn"
            exit 1
        fi
    fi
fi

# Vérifier que le répertoire webui existe
if [[ ! -d "$WEBUI_DIR" ]]; then
    err "Répertoire webui introuvable: $WEBUI_DIR"
    exit 1
fi

# Exporter la config API
export ETHAN_API_URL="$API_URL"
export API_URL="$API_URL"

info "Démarrage de Streamlit sur http://localhost:$PORT"
cd "$WEBUI_DIR"
exec "$VENV_DIR/bin/streamlit" run app.py --server.port "$PORT" --server.headless true