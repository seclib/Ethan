#!/usr/bin/env bash
# tests/test_runtime.sh — vérifie le runtime ETHAN après démarrage
set -euo pipefail

PASS=0
FAIL=0

echo "=== ETHAN Runtime Tests ==="

# Vérifier que les services sont up
if ! docker compose -f docker-compose.yml ps --format "{{.Name}}" | grep -q "ethan"; then
    echo "  SKIP services non démarrés (ethan up requis)"
    exit 0
fi

# 1. API health endpoint
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "  PASS API health OK"
    ((PASS++))
else
    echo "  FAIL API health échoue"
    ((FAIL++))
fi

# 2. NATS healthz
if curl -sf http://localhost:4222/healthz >/dev/null 2>&1; then
    echo "  PASS NATS health OK"
    ((PASS++))
else
    echo "  FAIL NATS health échoue"
    ((FAIL++))
fi

# 3. Redis ping
if redis-cli -h localhost -p 6379 ping 2>/dev/null | grep -q "PONG"; then
    echo "  PASS Redis ping OK"
    ((PASS++))
else
    echo "  FAIL Redis inaccessible"
    ((FAIL++))
fi

# 4. PostgreSQL ready
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "  PASS PostgreSQL prêt"
    ((PASS++))
else
    echo "  FAIL PostgreSQL non prêt"
    ((FAIL++))
fi

echo ""
echo "Résultats: ${PASS} passés, ${FAIL} échoués"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0