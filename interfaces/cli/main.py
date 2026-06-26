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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interfaces.cli.repl import repl_loop
from interfaces.cli.boot import BootManager, BootLogger
from interfaces.cli.client import RuntimeClient


def cmd_up(args):
    """Boot all services (ethan up)."""
    manager = BootManager()
    success = manager.boot()
    if success:
        print("\nYou can now start chatting:")
        repl_loop()
    sys.exit(0 if success else 1)


def cmd_down(args):
    """Shutdown all services (ethan down)."""
    try:
        client = RuntimeClient()
        resp = client.send({
            "type": "services.stop",
            "session_id": "cmd",
            "payload": {
                "services": [
                    "ui", "module-autonomy", "module-metacognition",
                    "module-learning", "module-reflective", "module-memory",
                    "module-planner", "module-executive",
                    "api", "kernel", "runtime",
                    "postgres", "redis", "nats",
                ],
                "timeout": 30,
            },
        })
        print("◆ Services stopped")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Shutdown failed: {e}")
        sys.exit(1)


def cmd_status(args):
    """Show system status (ethan status)."""
    try:
        client = RuntimeClient()
        resp = client.send({
            "type": "status.get",
            "session_id": "cmd",
            "payload": {},
        })
        payload = resp.get("payload", {})
        runtime = payload.get("runtime", {})
        services = payload.get("services", [])

        print("\n◆ System Status")
        print(f"  Runtime: {runtime.get('state', 'unknown')}")
        print(f"  Uptime:  {runtime.get('uptime', 'N/A')}")
        print()
        print("  Services:")
        for svc in services:
            name = svc.get("name", "?")
            state = svc.get("state", "?")
            health = svc.get("health", "?")
            icon = "●" if health == "healthy" else "○"
            print(f"    {icon} {name}  [{state}]  ({health})")
        print()
    except Exception as e:
        print(f"✗ Status failed: {e}")
        sys.exit(1)


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
        choices=["repl", "up", "down", "status"],
        help="Command to execute",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Start Runtime in daemon mode",
    )

    args = parser.parse_args()

    if args.command == "up":
        cmd_up(args)
    elif args.command == "down":
        cmd_down(args)
    elif args.command == "status":
        cmd_status(args)
    else:
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