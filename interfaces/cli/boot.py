#!/usr/bin/env python3
"""ETHAN CLI — Boot Manager for startup lifecycle."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from interfaces.cli.client import RuntimeClient, SOCKET_PATH


# ── Logging ───────────────────────────────────────────────────────────

class BootLogger:
    """Structured logging for boot phases."""
    
    def __init__(self):
        self.phases: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
    def begin_phase(self, name: str) -> None:
        """Mark phase start."""
        self._phase = {
            "name": name,
            "start": time.time(),
            "status": "running",
            "services": {},
        }
        print(f"\n◆ {name}")
        
    def end_phase(self, status: str, duration: Optional[float] = None) -> None:
        """Mark phase end."""
        self._phase["end"] = time.time()
        self._phase["duration"] = duration or (self._phase["end"] - self._phase["start"])
        self._phase["status"] = status
        
        icon = "✓" if status == "completed" else "⚠" if status == "degraded" else "✗"
        color = "\033[0;32m" if status == "completed" else "\033[0;33m" if status == "degraded" else "\033[0;31m"
        reset = "\033[0m"
        
        print(f"  {color}{icon} {status}{reset} ({self._phase['duration']:.1f}s)")
        self.phases.append(self._phase)
        
    def log_service(self, name: str, port: int, status: str) -> None:
        """Log a single service status."""
        self._phase.setdefault("services", {})[name] = status
        icon = "✓" if status == "healthy" else "⚠" if status == "degraded" else "✗"
        print(f"  {icon} {name} ({port})")
        
    def summary(self) -> Dict[str, Any]:
        """Return boot summary and log to file."""
        total = time.time() - self.start_time
        all_completed = all(p["status"] == "completed" for p in self.phases)
        
        print(f"\n  ⏱ Total: {total:.1f}s")
        
        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phases": self.phases,
            "total_duration_s": round(total, 1),
            "status": "success" if all_completed else "degraded",
        }
        
        # Log to file
        log_dir = os.path.expanduser("~/.ethan/logs")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "boot.json"), "a") as f:
            f.write(json.dumps(summary) + "\n")
        
        return summary


# ── Boot Manager ──────────────────────────────────────────────────────

class BootManager:
    """Manages the full ETHAN boot sequence."""
    
    def __init__(self):
        self.telemetry = BootLogger()
        self.client = RuntimeClient()
        
    def boot(self, services: Optional[List[str]] = None) -> bool:
        """Execute full boot sequence."""
        print("◆ ETHAN — Starting System")
        
        # Phase 0: Detect/Daemon Runtime
        self.telemetry.begin_phase("Runtime Detection")
        runtime_ok = self._detect_or_start_runtime()
        self.telemetry.end_phase("completed" if runtime_ok else "failed")
        
        if not runtime_ok:
            print("  → Run: ./scripts/start_ethan.sh")
            return False
        
        # Phase 1: Check Runtime Health
        self.telemetry.begin_phase("Runtime Health")
        healthy = self._check_runtime_health()
        self.telemetry.end_phase("healthy" if healthy else "degraded")
        
        if not healthy:
            print("  → Runtime health check failed")
            return False
        
        # Phase 2: Infrastructure
        self.telemetry.begin_phase("Infrastructure")
        infra_ok = self._start_infrastructure()
        self.telemetry.end_phase("completed" if infra_ok else "degraded")
        
        # Phase 3: Application
        self.telemetry.begin_phase("Application")
        app_ok = self._start_application()
        self.telemetry.end_phase("completed" if app_ok else "degraded")
        
        # Phase 4: Modules
        self.telemetry.begin_phase("Cognitive Modules")
        modules_ok = self._start_modules()
        self.telemetry.end_phase("completed" if modules_ok else "degraded")
        
        # Phase 5: Core Health Check
        self.telemetry.begin_phase("System Health")
        health_ok = self._check_system_health()
        self.telemetry.end_phase("healthy" if health_ok else "degraded")
        
        # Phase 6: UI
        self.telemetry.begin_phase("Web UI")
        ui_ok = self._start_ui()
        self.telemetry.end_phase("completed" if ui_ok else "degraded")
        
        # Summary
        summary = self.telemetry.summary()
        
        # Print status table
        self._print_status_table()
        
        return summary["status"] == "success"
    
    def _detect_or_start_runtime(self) -> bool:
        """Detect if Runtime is running, or start it."""
        if os.path.exists(SOCKET_PATH):
            try:
                c = RuntimeClient()
                c.send({"type": "ping", "session_id": "boot", "payload": {}})
                return True
            except (ConnectionRefusedError, OSError):
                os.remove(SOCKET_PATH)
        
        # Try to start Runtime from PATH
        for binary in ["ethan-runtime", "runtime/cmd/ethan-runtime/ethan-runtime"]:
            try:
                subprocess.Popen(
                    [binary, "--daemon"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(0.5)
                return True
            except FileNotFoundError:
                continue
        
        return False

    def _check_runtime_health(self) -> bool:
        """Check if Runtime is healthy."""
        for attempt in range(3):
            try:
                resp = self.client.send({
                    "type": "status.get",
                    "session_id": "boot",
                    "payload": {},
                })
                return resp.get("payload", {}).get("runtime", {}).get("state") == "RUNNING"
            except (ConnectionRefusedError, FileNotFoundError):
                time.sleep(1 + attempt)
                continue
        return False
    
    def _start_infrastructure(self) -> bool:
        """Start infrastructure services."""
        services = ["nats", "redis", "postgres"]
        try:
            resp = self.client.send({
                "type": "services.start",
                "session_id": "boot",
                "payload": {"services": services},
            })
            started = resp.get("payload", {}).get("services", [])
            for s in services:
                port = {"nats": 4222, "redis": 6379, "postgres": 5432}.get(s, 0)
                ok = s in started
                self.telemetry.log_service(s, port, "healthy" if ok else "failed")
            return len(started) == len(services)
        except Exception:
            return False
    
    def _start_application(self) -> bool:
        """Start application services."""
        services = ["api", "kernel"]
        try:
            resp = self.client.send({
                "type": "services.start",
                "session_id": "boot",
                "payload": {"services": services},
            })
            started = resp.get("payload", {}).get("services", [])
            for s in services:
                port = {"api": 8000, "kernel": 8080}.get(s, 0)
                ok = s in started
                self.telemetry.log_service(s, port, "healthy" if ok else "failed")
            return len(started) == len(services)
        except Exception:
            return False
    
    def _start_modules(self) -> bool:
        """Start cognitive modules."""
        services = [
            "module-executive", "module-planner", "module-memory", "module-reflective",
            "module-learning", "module-metacognition", "module-autonomy",
        ]
        try:
            resp = self.client.send({
                "type": "services.start",
                "session_id": "boot",
                "payload": {"services": services},
            })
            started = resp.get("payload", {}).get("services", [])
            self.telemetry.log_service(
                "modules", 0,
                f"{len(started)}/{len(services)} ready",
            )
            return len(started) >= len(services) - 1
        except Exception:
            return False
    
    def _check_system_health(self) -> bool:
        """Perform system health checks."""
        try:
            resp = self.client.send({
                "type": "services.status",
                "session_id": "boot",
                "payload": {},
            })
            services = resp.get("payload", {}).get("services", [])
            healthy_count = sum(1 for s in services if s.get("health") == "healthy")
            total = len(services)
            self.telemetry.log_service("health", 0, f"{healthy_count}/{total} healthy")
            return healthy_count >= total - 2
        except Exception:
            return False
    
    def _start_ui(self) -> bool:
        """Start Web UI."""
        try:
            resp = self.client.send({
                "type": "services.start",
                "session_id": "boot",
                "payload": {"services": ["ui"]},
            })
            started = resp.get("payload", {}).get("services", [])
            self.telemetry.log_service("ui", 8501, "healthy" if "ui" in started else "failed")
            return "ui" in started
        except Exception:
            return False
    
    def _print_status_table(self) -> None:
        """Print final service status table."""
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\033[0;32m✓ ETHAN is ready\033[0m")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\nAccess:")
        print("  CLI:  python3 -m interfaces.cli.main")
        print("  API:  http://localhost:8000")
        print("  UI:   http://localhost:8501")
        print()


def main() -> None:
    """CLI entry point for boot command."""
    manager = BootManager()
    success = manager.boot()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()