#!/usr/bin/env bash
# tests/test_boot.sh — vérifie le démarrage d'ETHAN (prérequis système)
set -euo pipefail

PASS=0
FAIL=0

echo "=== ETHAN Boot Tests ==="

# 1. Docker installé
if command -v docker >/dev/null 2>&1; then
    echo "  PASS docker installé"
    ((PASS++))
else
    echo "  FAIL docker non installé"
    ((FAIL++))
fi

# 2. Docker Compose v2
if docker compose version >/dev/null 2>&1; then
    echo "  PASS docker compose v2 disponible"
    ((PASS++))
else
    echo "  FAIL docker compose v2 indisponible"
    ((FAIL++))
fi

# 3. docker-compose.yml valide
if [ -f docker-compose.yml ]; then
    echo "  PASS docker-compose.yml présent"
    ((PASS++))
else
    echo "  FAIL docker-compose.yml manquant"
    ((FAIL++))
fi

# 4. Ports libres
PORTS="8000 8080 3001 4222 6379 5432"
for port in $PORTS; do
    if ss -tuln 2>/dev/null | grep -q ":${port} " || netstat -tuln 2>/dev/null | grep -q ":${port} "; then
        echo "  FAIL port ${port} occupé"
        ((FAIL++))
    else
        echo "  PASS port ${port} libre"
        ((PASS++))
    fi
done

# 5. docker-compose.yml syntaxiquement valide
if docker compose -f docker-compose.yml config >/dev/null 2>&1; then
    echo "  PASS docker-compose.yml valide"
    ((PASS++))
else
    echo "  FAIL docker-compose.yml invalide"
    ((FAIL++))
fi

echo ""
echo "Résultats: ${PASS} passés, ${FAIL} échoués"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0