#!/bin/bash
# ESIL status — system overview
. "$(dirname "$0")/core.sh"
_ethan_status | python3 -c "
import sys, json
s=json.load(sys.stdin)
print(f\"Mode:       {s.get('mode','?')}\")
print(f\"Goal:       {s.get('active_goal','none')}\")
print(f\"Tasks:      {s.get('running_tasks',0)}\")
" 2>/dev/null || _ethan_status