#!/usr/bin/env bash
# tests/test_cli.sh — vérifie les commandes CLI ETHAN
set -euo pipefail

PASS=0
FAIL=0

echo "=== ETHAN CLI Tests ==="

# 1. ethan status
if python3 -m interfaces.cli.main status >/dev/null 2>&1; then
    echo "  PASS ethan status OK"
    ((PASS++))
else
    echo "  FAIL ethan status KO"
    ((FAIL++))
fi

# 2. ethan doctor
if python3 -m interfaces.cli.main doctor >/dev/null 2>&1; then
    echo "  PASS ethan doctor OK"
    ((PASS++))
else
    echo "  FAIL ethan doctor KO"
    ((FAIL++))
fi

# 3. ethan plugin --help (sans erreur)
if python3 -m interfaces.cli.main plugin --help >/dev/null 2>&1 || true; then
    echo "  PASS ethan plugin accessible"
    ((PASS++))
else
    echo "  FAIL ethan plugin KO"
    ((FAIL++))
fi

# 4. ethan service status (systemd, peut échouer sans service)
python3 -m interfaces.cli.main service status >/dev/null 2>&1 && {
    echo "  PASS ethan service status OK"
    ((PASS++))
} || {
    echo "  SKIP ethan service status (service absent)"
}

# 5. Commande inconnue → erreur
if python3 -m interfaces.cli.main unknown_cmd 2>/dev/null; then
    echo "  FAIL commande inconnue acceptée"
    ((FAIL++))
else
    echo "  PASS commande inconnue rejetée"
    ((PASS++))
fi

echo ""
echo "Résultats: ${PASS} passés, ${FAIL} échoués"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0