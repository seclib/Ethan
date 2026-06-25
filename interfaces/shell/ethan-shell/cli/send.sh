#!/bin/bash
# ESIL send — one-shot message
. "$(dirname "$0")/core.sh"
_ethan_history_record send "$*"
_ethan_api_raw "$@"