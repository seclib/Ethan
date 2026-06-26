#!/bin/bash
# ETHAN Interfaces — Test and Launch Script

set -e

echo "◆ ETHAN Interfaces — Test Suite"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Python imports
echo "Testing Python CLI imports..."
cd /home/fatsio/AI/Ethan

if python3 -c "
import sys
sys.path.insert(0, '.')
from interfaces.cli.main import main
from interfaces.cli.repl import repl_loop
from interfaces.cli.client import RuntimeClient
from interfaces.cli.session import SessionManager, Session
from interfaces.cli.ui.prompt import get_prompt
from interfaces.cli.ui.renderer import render_user_message, render_error
from interfaces.cli.commands.parser import parse_command, COMMANDS
from interfaces.cli.commands.handler import cmd_exit, cmd_help, cmd_status
from interfaces.cli.config import config
print('✓ All CLI modules imported successfully')
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python CLI modules OK"
else
    echo -e "${RED}✗${NC} Python CLI modules FAILED"
    exit 1
fi

# Test 2: Go compilation
echo "Testing Go Runtime compilation..."
cd /home/fatsio/AI/Ethan/runtime

if go build ./... 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Go Runtime compiles OK"
else
    echo -e "${RED}✗${NC} Go Runtime compilation FAILED"
    exit 1
fi

# Test 3: Check files exist
echo "Checking file structure..."
cd /home/fatsio/AI/Ethan

FILES=(
    "interfaces/cli/main.py"
    "interfaces/cli/repl.py"
    "interfaces/cli/client.py"
    "interfaces/cli/session.py"
    "interfaces/cli/config.py"
    "interfaces/cli/commands/parser.py"
    "interfaces/cli/commands/handler.py"
    "interfaces/cli/ui/prompt.py"
    "interfaces/cli/ui/renderer.py"
    "runtime/internal/socket/server.go"
    "runtime/internal/api/server.go"
    "runtime/internal/socket/example_handler.go"
    "COMMUNICATION_PROTOCOL.md"
    "INTERFACES_README.md"
)

ALL_EXIST=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file MISSING"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = true ]; then
    echo -e "${GREEN}✓${NC} All files present"
else
    echo -e "${RED}✗${NC} Some files missing"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Start Runtime:  cd runtime && go run cmd/ethan-runtime/main.go"
echo "  2. Start CLI:      python3 -m interfaces.cli.main"
echo "  3. Read docs:      cat COMMUNICATION_PROTOCOL.md"
echo "                      cat INTERFACES_README.md"
echo ""