#!/bin/bash
# ETHAN — Startup Script
# Starts all services in the correct order

set -e

echo "◆ ETHAN — Starting System"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Start infrastructure services
echo "Starting infrastructure services..."
docker compose up -d nats redis postgres

# Wait for infrastructure
echo "Waiting for infrastructure to be healthy..."
sleep 10

# Check health
if ! docker compose ps nats redis postgres | grep -q "healthy"; then
    echo -e "${YELLOW}⚠${NC} Some services not healthy yet, waiting more..."
    sleep 10
fi

echo -e "${GREEN}✓${NC} Infrastructure ready"
echo ""

# Start Runtime
echo "Starting Runtime controller..."
docker compose up -d runtime

# Wait for Runtime
echo "Waiting for Runtime..."
sleep 5

if ! docker compose ps runtime | grep -q "healthy"; then
    echo -e "${YELLOW}⚠${NC} Runtime not healthy yet, waiting more..."
    sleep 5
fi

echo -e "${GREEN}✓${NC} Runtime ready"
echo ""

# Start application services
echo "Starting application services..."
docker compose up -d api kernel

# Wait for application
echo "Waiting for application..."
sleep 10

echo -e "${GREEN}✓${NC} Application ready"
echo ""

# Start cognitive modules
echo "Starting cognitive modules..."
docker compose up -d module-executive module-planner module-memory module-reflective
docker compose up -d module-learning module-metacognition module-autonomy

echo -e "${GREEN}✓${NC} Modules ready"
echo ""

# Start UI
echo "Starting Web UI..."
docker compose up -d ui

echo -e "${GREEN}✓${NC} UI ready"
echo ""

# Optional: Start LLM
if [ "$1" == "--with-llm" ] || [ "$1" == "--llm" ]; then
    echo "Starting LLM provider (Ollama)..."
    docker compose --profile llm up -d ollama
    echo -e "${GREEN}✓${NC} LLM ready"
    echo ""
fi

# Final status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ ETHAN is ready${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Services:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Access points:"
echo "  CLI:  python3 -m interfaces.cli.main"
echo "  UI:   http://localhost:8501"
echo "  API:  http://localhost:8000"
echo ""
echo "Next steps:"
echo "  - Chat:     python3 -m interfaces.cli.main"
echo "  - Status:   docker compose ps"
echo "  - Logs:     docker compose logs -f"
echo "  - Stop:     ./scripts/stop_ethan.sh"
echo ""