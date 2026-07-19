#!/bin/bash
# ETHAN — Stop Script
# Stops all services gracefully

set -e

echo "◆ ETHAN — Stopping System"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop in reverse order
echo "Stopping services..."

# Stop UI first
echo "  Stopping UI..."
docker compose stop ui

# Stop modules
echo "  Stopping cognitive modules..."
docker compose stop module-learning module-metacognition module-autonomy
docker compose stop module-executive module-planner module-memory module-reflective

# Stop application
echo "  Stopping application..."
docker compose stop api kernel

# Stop Runtime
echo "  Stopping Runtime..."
docker compose stop runtime

# Stop infrastructure
echo "  Stopping infrastructure..."
docker compose stop nats redis postgres

echo ""
echo -e "${GREEN}✓${NC} All services stopped"
echo ""

# Ask if user wants to remove containers
read -p "Remove containers? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing containers..."
    docker compose down
    echo -e "${GREEN}✓${NC} Containers removed"
    echo ""
    
    read -p "Remove volumes (WARNING: data loss)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing volumes..."
        docker compose down -v
        echo -e "${GREEN}✓${NC} Volumes removed"
        echo -e "${RED}⚠${NC} All data has been deleted"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ ETHAN stopped${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To start again: ./scripts/start_ethan.sh"
echo ""