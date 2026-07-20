#!/usr/bin/env python3
"""ETHAN CLI — Terminal interface for ETHAN Cognitive Runtime.

Commands:
  ethan           Start REPL and auto-detect Runtime
  ethan up        Boot all services (full lifecycle)
  ethan down      Shutdown all services
  ethan status    Show system status
"""

import sys
import os
import argparse

from interfaces.cli.repl import repl_loop
from interfaces.cli.boot import BootManager, BootLogger
from interfaces.cli.client import RuntimeClient


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="ethan",
        description="ETHAN — Cognitive Runtime CLI",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="repl",
        choices=["repl"],
        help="Command to execute",
    )

    args = parser.parse_args()

    # Default: start REPL
    try:
        repl_loop()
    except KeyboardInterrupt:
        print("\n◆ Goodbye")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
