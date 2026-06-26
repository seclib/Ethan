"""Startup orchestrator — checks Runtime, starts if needed, connects CLI.

User runs 'ethan' and everything just works.
No manual Docker Compose commands. No configuration hunting.
"""

import time
import sys
from typing import Optional

from ethan.client import RuntimeClient, RuntimeError
from ethan.ui.colors import style


def startup_and_chat(
    runtime: RuntimeClient,
    config: dict,
    args,
) -> int:
    """Startup sequence: check Runtime → ensure services → start REPL."""
    print(f"{style.section('Starting ETHAN...')}")

    # ── Phase 1: Check Runtime ────────────────────────────────────
    try:
        if not runtime.is_available():
            print(f"  {style.info('Runtime not running, starting...')}")
            # In production, Runtime would auto-start via systemd
            # CLI can request Runtime to start via socket activation
    except RuntimeError:
        pass  # Expected if not running

    # ── Phase 2: Ensure services ──────────────────────────────────
    try:
        services = runtime.list_services()
    except RuntimeError:
        services = []

    core_running = any(s.get("name") == "ethan-core" and s.get("state") == "running"
                       for s in services)

    if not core_running:
        print(f"  {style.info('Starting services...')}")
        for svc in ["nats", "redis", "postgres", "ethan-core", "ethan-plugins"]:
            try:
                runtime.start_service(svc)
                print(f"  {style.success(f'{svc} started')}")
            except RuntimeError as e:
                print(f"  {style.error(f'{svc} failed: {e}')}")

    # Wait for core
    for _ in range(30):
        try:
            status = runtime.get_status()
            if status.get("core_healthy"):
                print(f"  {style.success('Core online')}")
                break
        except RuntimeError:
            pass
        time.sleep(0.5)
    else:
        print(f"  {style.error('Core failed to start')}")
        return 1

    # ── Phase 3: Connect and start REPL ───────────────────────────
    print(f"  {style.success('Connected')}\n")

    # Resume session if requested
    session_id = None
    if args.resume:
        try:
            resp = runtime.send({"command": "resume_last"})
            session_id = resp.get("session_id")
            sid = session_id[:8] if session_id else ""
            print(f"  {style.info(f'Session resumed: {sid}')}\n")
        except RuntimeError:
            pass

    # Start REPL
    from ethan.repl import REPL
    repl = REPL(runtime, config, session_id)
    repl.run()

    return 0