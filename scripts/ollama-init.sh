#!/bin/bash
# =============================================================================
# Ollama Init — Pull default model on container startup
# =============================================================================
# Ce script est exécuté au démarrage du conteneur Ollama.
# Il télécharge le modèle par défaut si non présent.
#
# Usage:
#   ./scripts/ollama-init.sh
#
# Configuration:
#   OLLAMA_MODEL : Modèle à télécharger (défaut: llama3.2)
#   OLLAMA_HOST  : Hôte Ollama (défaut: http://localhost:11434)
# =============================================================================

set -euo pipefail

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "=== Ollama Init ==="
echo "Model : ${OLLAMA_MODEL}"
echo "Host  : ${OLLAMA_HOST}"
echo ""

# Attendre qu'Ollama soit prêt
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama did not start in time"
        exit 1
    fi
    sleep 2
done

# Vérifier si le modèle est déjà présent
echo "Checking if model '${OLLAMA_MODEL}' is available..."
if curl -s "${OLLAMA_HOST}/api/tags" | grep -q "\"name\":\"${OLLAMA_MODEL}\""; then
    echo "Model '${OLLAMA_MODEL}' is already available"
else
    echo "Pulling model '${OLLAMA_MODEL}'..."
    curl -s -X POST "${OLLAMA_HOST}/api/pull" \
        -d "{\"name\": \"${OLLAMA_MODEL}\", \"stream\": false}"
    echo ""
    echo "Model '${OLLAMA_MODEL}' pulled successfully"
fi

# Afficher les modèles disponibles
echo ""
echo "=== Available Models ==="
curl -s "${OLLAMA_HOST}/api/tags" | python3 -m json.tool 2>/dev/null || curl -s "${OLLAMA_HOST}/api/tags"

echo ""
echo "=== Ollama Init Complete ==="