#!/bin/bash
# ETHAN Health Check — Vérification de l'état du système
# Usage: ./healthcheck.sh [--verbose]

set -euo pipefail

VERBOSE=false
if [[ "${1:-}" == "--verbose" ]]; then
    VERBOSE=true
fi

FAILURES=0

check_core() {
    if systemctl is-active --quiet ethan-core 2>/dev/null; then
        echo "✅ ethan-core: running"
    else
        echo "❌ ethan-core: stopped"
        FAILURES=$((FAILURES + 1))
    fi
}

check_grpc() {
    if nc -z localhost 50051 2>/dev/null; then
        echo "✅ gRPC port 50051: open"
    else
        echo "❌ gRPC port 50051: closed"
        FAILURES=$((FAILURES + 1))
    fi
}

check_nats() {
    if nc -z localhost 4222 2>/dev/null; then
        echo "✅ NATS port 4222: open"
    else
        echo "⚠️  NATS port 4222: closed (optional)"
    fi
}

check_redis() {
    if nc -z localhost 6379 2>/dev/null; then
        echo "✅ Redis port 6379: open"
    else
        echo "⚠️  Redis port 6379: closed (optional)"
    fi
}

check_postgres() {
    if nc -z localhost 5432 2>/dev/null; then
        echo "✅ PostgreSQL port 5432: open"
    else
        echo "⚠️  PostgreSQL port 5432: closed (optional)"
    fi
}

echo "═══════════════════════════════════"
echo "   ETHAN Health Check"
echo "═══════════════════════════════════"
echo ""

check_core
check_grpc

if [[ "$VERBOSE" == true ]]; then
    echo ""
    echo "--- Infrastructure ---"
    check_nats
    check_redis
    check_postgres
fi

echo ""

if [[ $FAILURES -eq 0 ]]; then
    echo "✅ ETHAN is healthy"
    exit 0
else
    echo "❌ ETHAN has $FAILURES failure(s)"
    exit 1
fi