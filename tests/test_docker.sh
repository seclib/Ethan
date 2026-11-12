#!/usr/bin/env bash
# tests/test_docker.sh — vérifie l'état Docker et les ressources
set -euo pipefail

PASS=0
FAIL=0

echo "=== ETHAN Docker Tests ==="

# 1. Docker daemon
if docker info >/dev/null 2>&1; then
    echo "  PASS docker daemon OK"
    ((PASS++))
else
    echo "  FAIL docker daemon KO"
    ((FAIL++))
fi

# 2. Aucun container éthérique en erreur
if docker compose -f docker-compose.yml ps --format "{{.Name}}\t{{.Status}}" 2>/dev/null | grep -qi "exited\|dead\|restarting"; then
    echo "  FAIL conteneurs en erreur"
    ((FAIL++))
else
    echo "  PASS pas de conteneurs en erreur"
    ((PASS++))
fi

# 3. Réseau ethan_default existe
if docker network list --format "{{.Name}}" | grep -q "ethan"; then
    echo "  PASS réseau ethan présent"
    ((PASS++))
else
    echo "  FAIL réseau ethan absent"
    ((FAIL++))
fi

echo ""
echo "Résultats: ${PASS} passés, ${FAIL} échoués"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0