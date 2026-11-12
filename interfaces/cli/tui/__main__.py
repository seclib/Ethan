"""Point d'entrée ``python3 -m interfaces.cli.tui``."""

from __future__ import annotations

if __name__ == "__main__":
    from interfaces.cli.tui.app import main

    raise SystemExit(main())
