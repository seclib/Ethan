#!/bin/bash
# ESIL Launcher — minimal TUI menu using bash builtins only

_ethan_launcher() {
  PS3="ETHAN > "
  while true; do
    clear
    cat <<'EOF'
 ETHAN Launcher
 ┌──────────────────────────────┐
 │ 1. Send message              │
 │ 2. Interactive chat           │
 │ 3. System status              │
 │ 4. Suggest commands           │
 │ 5. Exit                       │
 └──────────────────────────────┘
EOF
    read -p "Choice: " -r choice
    case "$choice" in
      1)
        read -p "Message: " -r msg
        [ -n "$msg" ] && ethan send "$msg" | head -n 5
        read -p "Enter to continue..." -r
        ;;
      2) ethan chat ;;
      3) ethan status; read -p "Enter to continue..." -r ;;
      4) ethan suggest; read -p "Enter to continue..." -r ;;
      5|q) break ;;
      *) echo "Invalid" ;;
    esac
  done
}

_ethan_launcher "$@"