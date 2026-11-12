#!/bin/bash
# ESIL suggest — show frequent + recent commands
. "$(dirname "$0")/core.sh"
if command -v ethan-cli >/dev/null 2>&1; then
  ethan-cli suggest "$@"
else
  echo "ethan-cli not found — please install ethan-cli"
fi