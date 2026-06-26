# ETHAN — Startup Workflow

**Version** : 1.0.0  
**Goal** : Zero-friction startup, user just runs `ethan`  
**Philosophy** : Automatic orchestration, transparent to user

---

## 1. Startup Philosophy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Startup Philosophy                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Zero Manual Steps                                                 │
│     User runs: ethan                                                  │
│     That's it. Everything else is automatic.                          │
│                                                                       │
│  2. Progressive Verification                                          │
│     Check each layer, fail fast with clear message                   │
│                                                                       │
│  3. Self-Healing                                                      │
│     If something is wrong, try to fix it automatically               │
│                                                                       │
│  4. Transparent                                                       │
│     Show what's happening, but don't overwhelm                       │
│                                                                       │
│  5. Fast                                                              │
│     Target: < 5s from command to ready                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### What User Sees

```
$ ethan

◆  Starting ETHAN...
  ✓ Docker available
  ✓ Runtime started
  ✓ Core online
  ✓ Databases ready
  ✓ Connected

◆  ethan  ◇  chat  ▸
```

### What User Never Sees

```
❌ docker-compose up -d
❌ Manual service management
❌ Configuration hunting
❌ Port conflicts
❌ Dependency ordering
```

---

## 2. Complete Startup Sequence

### 2.1 High-Level Flow

```
User runs: ethan
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: PREFLIGHT CHECKS (0-500ms)                                │
│  • Check if Docker is available                                      │
│  • Check if Runtime is running                                       │
│  • Check if socket exists                                            │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: RUNTIME STARTUP (0-2s)                                    │
│  • If Runtime stopped → start it                                     │
│  • Wait for Runtime ready                                            │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: SERVICE ORCHESTRATION (2-5s)                              │
│  • Runtime starts Docker Compose                                     │
│  • Wait for infrastructure (nats, redis, postgres)                   │
│  • Wait for Core healthy                                             │
│  • Wait for Plugins healthy                                          │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 4: CLI CONNECTION (5-6s)                                     │
│  • Connect to Runtime socket                                         │
│  • Load user configuration                                           │
│  • Resume last session (if configured)                               │
│  • Show welcome banner                                               │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 5: READY (6s+)                                               │
│  • Display prompt                                                    │
│  • Wait for user input                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Detailed Sequence

```
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Parse Arguments (10ms)                                     │
│  ├─ Command: ethan [chat|run|status|logs|config|help]              │
│  ├─ Flags: --resume, --model, --verbose, --debug                   │
│  └─ Load config from ~/.config/ethan/config.yaml                   │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Check Docker (100ms)                                       │
│  ├─ Try: docker info                                                │
│  ├─ If success: ✓ Docker available                                  │
│  └─ If fail: ✗ Docker not available → error + install hint         │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Check Runtime (50ms)                                       │
│  ├─ Try: connect to /var/run/ethan/runtime.sock                    │
│  ├─ If success: ✓ Runtime running → skip to Step 6                 │
│  └─ If fail: Runtime not running → continue to Step 4              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Start Runtime (1-2s)                                      │
│  ├─ Check if Runtime binary exists                                  │
│  │   └─ If not: install via pip/package manager                     │
│  ├─ Start Runtime process                                           │
│  │   └─ Command: ethan-runtime --config /etc/ethan/runtime.yaml    │
│  ├─ Wait for socket to appear (max 5s)                             │
│  └─ If timeout: ✗ Failed to start Runtime → error                  │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Verify Runtime Ready (500ms)                               │
│  ├─ Connect to socket                                               │
│  ├─ Send: {"command": "status"}                                     │
│  ├─ If response: ✓ Runtime ready                                    │
│  └─ If fail: ✗ Runtime not responding → error                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Check Services Status (1-2s)                              │
│  ├─ Send: {"command": "list"}                                       │
│  ├─ Parse service list                                              │
│  └─ Continue to Step 7                                              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: Start Infrastructure (if needed) (2-4s)                   │
│  ├─ Check: nats, redis, postgres running?                          │
│  │                                                                    │
│  │  If any stopped:                                                  │
│  │  ├─ Send: {"command": "start", "service": "nats"}               │
│  │  ├─ Send: {"command": "start", "service": "redis"}              │
│  │  ├─ Send: {"command": "start", "service": "postgres"}           │
│  │  └─ Wait for all healthy (health checks)                         │
│  │                                                                    │
│  └─ ✓ Infrastructure ready                                           │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: Start Core (if needed) (1-2s)                             │
│  ├─ Check: ethan-core running?                                      │
│  │                                                                    │
│  │  If stopped:                                                      │
│  │  ├─ Send: {"command": "start", "service": "ethan-core"}         │
│  │  ├─ Wait for health check (port 8000)                            │
│  │  └─ Verify: GET http://localhost:8000/health                     │
│  │                                                                    │
│  └─ ✓ Core online                                                    │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 9: Start Plugins (if needed) (1s)                            │
│  ├─ Check: ethan-plugins running?                                   │
│  │                                                                    │
│  │  If stopped:                                                      │
│  │  ├─ Send: {"command": "start", "service": "ethan-plugins"}      │
│  │  └─ Wait for health check                                        │
│  │                                                                    │
│  └─ ✓ Plugins online                                                 │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 10: Connect CLI (100ms)                                       │
│  ├─ Establish persistent connection to Runtime                      │
│  ├─ Load user configuration                                          │
│  ├─ Check for last session (if --resume or auto_resume)            │
│  └─ ✓ Connected                                                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 11: Show Welcome (50ms)                                       │
│  ├─ If new session: show welcome banner                             │
│  ├─ If resumed: show session info                                   │
│  └─ Display prompt: ◆ ethan ◇ chat ▸                               │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 12: Ready                                                      │
│  └─ Wait for user input                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation

### 3.1 Startup Orchestrator

```python
# ethan-cli/ethan/startup.py

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class StartupResult:
    success: bool
    runtime_ready: bool
    services: dict[str, str]
    session_id: Optional[str]
    duration_ms: int
    error: Optional[str] = None

class StartupOrchestrator:
    """Orchestrates the entire startup sequence."""
    
    def __init__(self, runtime_client: RuntimeClient, config: Config):
        self.runtime = runtime_client
        self.config = config
        self.start_time = time.time()
    
    async def startup(self, command: str = "chat", resume: bool = False) -> StartupResult:
        """Execute complete startup sequence."""
        
        # Phase 1: Preflight
        if not await self._check_docker():
            return self._error("Docker not available")
        
        if not await self._check_runtime():
            if not await self._start_runtime():
                return self._error("Failed to start Runtime")
        
        if not await self._verify_runtime():
            return self._error("Runtime not responding")
        
        # Phase 2: Service orchestration
        services = await self._check_services()
        
        if not await self._ensure_infrastructure():
            return self._error("Failed to start infrastructure")
        
        if not await self._ensure_core():
            return self._error("Failed to start Core")
        
        if not await self._ensure_plugins():
            return self._error("Failed to start Plugins")
        
        # Phase 3: CLI connection
        session_id = await self._connect_cli(resume)
        
        # Phase 4: Show welcome
        self._show_welcome(command, session_id)
        
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        return StartupResult(
            success=True,
            runtime_ready=True,
            services=services,
            session_id=session_id,
            duration_ms=duration_ms,
        )
    
    async def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False
    
    async def _check_runtime(self) -> bool:
        """Check if Runtime is already running."""
        try:
            self.runtime.send({"command": "ping"})
            return True
        except Exception:
            return False
    
    async def _start_runtime(self) -> bool:
        """Start Runtime process."""
        import subprocess
        
        try:
            # Start Runtime in background
            subprocess.Popen(
                ["ethan-runtime", "--config", "/etc/ethan/runtime.yaml"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            
            # Wait for socket to appear
            for _ in range(50):  # 5s max
                await asyncio.sleep(0.1)
                if await self._check_runtime():
                    return True
            
            return False
        except Exception:
            return False
    
    async def _verify_runtime(self) -> bool:
        """Verify Runtime is responding."""
        try:
            response = self.runtime.send({"command": "status"})
            return response.get("status") == "ok"
        except Exception:
            return False
    
    async def _check_services(self) -> dict[str, str]:
        """Check status of all services."""
        try:
            response = self.runtime.send({"command": "list"})
            services = {}
            for svc in response.get("services", []):
                services[svc["name"]] = svc["state"]
            return services
        except Exception:
            return {}
    
    async def _ensure_infrastructure(self) -> bool:
        """Ensure infrastructure services are running."""
        infra_services = ["nats", "redis", "postgres"]
        
        for service in infra_services:
            if not await self._ensure_service(service):
                return False
        
        return True
    
    async def _ensure_core(self) -> bool:
        """Ensure Core is running."""
        return await self._ensure_service("ethan-core")
    
    async def _ensure_plugins(self) -> bool:
        """Ensure Plugins are running."""
        return await self._ensure_service("ethan-plugins")
    
    async def _ensure_service(self, service_name: str) -> bool:
        """Ensure a specific service is running."""
        services = await self._check_services()
        
        if services.get(service_name) == "running":
            return True
        
        # Start service
        try:
            response = self.runtime.send({
                "command": "start",
                "service": service_name,
                "timeout": 30,
            })
            
            if response.get("status") == "ok":
                # Wait for healthy
                return await self._wait_for_healthy(service_name, timeout=30)
            
            return False
        except Exception:
            return False
    
    async def _wait_for_healthy(self, service: str, timeout: int = 30) -> bool:
        """Wait for service to become healthy."""
        start = time.time()
        
        while time.time() - start < timeout:
            services = await self._check_services()
            if services.get(service) == "running":
                return True
            await asyncio.sleep(1)
        
        return False
    
    async def _connect_cli(self, resume: bool = False) -> Optional[str]:
        """Connect CLI to Runtime."""
        # This establishes persistent connection
        # Implementation depends on Runtime API
        
        if resume:
            # Request last session from Runtime
            response = self.runtime.send({"command": "resume_last"})
            return response.get("session_id")
        
        return None
    
    def _show_welcome(self, command: str, session_id: Optional[str]):
        """Show welcome banner."""
        if command == "chat":
            if session_id:
                print(f"◆  ETHAN Chat  ◇  session {session_id[:8]}")
            else:
                print("◆  ETHAN Chat")
            
            print("  Ctrl+D or /exit to quit  •  /help for commands")
    
    def _error(self, message: str) -> StartupResult:
        """Create error result."""
        duration_ms = int((time.time() - self.start_time) * 1000)
        return StartupResult(
            success=False,
            runtime_ready=False,
            services={},
            session_id=None,
            duration_ms=duration_ms,
            error=message,
        )
```

### 3.2 Main Entry Point

```python
# ethan-cli/ethan/main.py

import asyncio
import sys
from ethan.startup import StartupOrchestrator
from ethan.client import RuntimeClient
from ethan.config import load_config
from ethan.repl import REPL
from ethan.commands import run, status, logs

def main():
    # Parse arguments
    args = parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Create runtime client
    runtime = RuntimeClient(config.runtime.socket)
    
    # Create startup orchestrator
    orchestrator = StartupOrchestrator(runtime, config)
    
    # Execute startup
    result = asyncio.run(orchestrator.startup(
        command=args.command,
        resume=args.resume,
    ))
    
    if not result.success:
        print_error(f"Startup failed: {result.error}")
        sys.exit(1)
    
    # Execute command
    if args.command == "chat":
        repl = REPL(runtime, config, result.session_id)
        repl.run()
    elif args.command == "run":
        run.once(args, runtime)
    elif args.command == "status":
        status.show(runtime)
    elif args.command == "logs":
        logs.show(args, runtime)
    else:
        # Default to chat
        repl = REPL(runtime, config, result.session_id)
        repl.run()

if __name__ == "__main__":
    main()
```

---

## 4. Error Handling

### 4.1 Error Categories

| Error | Cause | Recovery | User Action |
|-------|-------|----------|--------------|
| **DOCKER_NOT_FOUND** | Docker not installed | None | Install Docker |
| **DOCKER_NOT_RUNNING** | Docker daemon stopped | Start Docker | `sudo systemctl start docker` |
| **RUNTIME_START_FAILED** | Runtime binary missing/corrupt | Reinstall | `pip install --force-reinstall ethan` |
| **RUNTIME_NOT_RESPONDING** | Runtime crashed | Restart | `ethan restart` |
| **SERVICE_START_TIMEOUT** | Service failed to start | Check logs | `ethan logs --service <name>` |
| **CORE_NOT_HEALTHY** | Core crashed | Restart | `ethan restart` |
| **DATABASE_ERROR** | Postgres/Redis issue | Check config | Check connection strings |

### 4.2 Error Display

```python
def show_startup_error(error: str, hint: str = ""):
    """Display startup error with recovery hint."""
    print(f"\n✗ Startup failed")
    print(f"  → {error}")
    if hint:
        print(f"  → {hint}")
    print()
```

**Example Output**:

```
✗ Startup failed
  → Docker not available
  → Install Docker: https://docs.docker.com/get-docker/
```

### 4.3 Retry Logic

```python
async def _start_runtime_with_retry(self, max_retries: int = 3) -> bool:
    """Start Runtime with retry logic."""
    for attempt in range(max_retries):
        if await self._start_runtime():
            return True
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return False
```

---

## 5. Performance Optimization

### 5.1 Parallel Checks

```python
async def _parallel_checks(self) -> tuple[bool, bool]:
    """Run checks in parallel."""
    docker_check = self._check_docker()
    runtime_check = self._check_runtime()
    
    docker_ok, runtime_ok = await asyncio.gather(
        docker_check,
        runtime_check,
    )
    
    return docker_ok, runtime_ok
```

### 5.2 Caching

```python
# Cache service status for 1s
_cache = {}
_cache_ttl = 1.0

async def _check_services_cached(self) -> dict[str, str]:
    """Check services with caching."""
    now = time.time()
    
    if "services" in _cache:
        cached_time, services = _cache["services"]
        if now - cached_time < _cache_ttl:
            return services
    
    services = await self._check_services()
    _cache["services"] = (now, services)
    return services
```

### 5.3 Fast Path

```python
async def startup(self) -> StartupResult:
    """Startup with fast path."""
    
    # Fast path: everything already running
    docker_ok = await self._check_docker()
    runtime_ok = await self._check_runtime()
    
    if docker_ok and runtime_ok:
        services = await self._check_services()
        
        # All services running?
        if all(s == "running" for s in services.values()):
            # Skip to connection
            session_id = await self._connect_cli()
            return self._success(services, session_id, "fast")
    
    # Slow path: start everything
    return await self._full_startup()
```

---

## 6. Configuration

### 6.1 Startup Config

```yaml
# ~/.config/ethan/config.yaml

startup:
  auto_start_runtime: true
  auto_start_services: true
  verify_docker: true
  verify_databases: true
  resume_last_session: true
  startup_timeout: 30  # seconds
  
  # Services to auto-start
  services:
    - nats
    - redis
    - postgres
    - ethan-core
    - ethan-plugins
  
  # Health check settings
  healthcheck:
    interval: 15s
    timeout: 10s
    retries: 3
```

### 6.2 Environment Variables

```bash
# Startup behavior
ETHAN_AUTO_START=true
ETHAN_STARTUP_TIMEOUT=30
ETHAN_RESUME_SESSION=true

# Runtime location
ETHAN_RUNTIME_PATH=/usr/local/bin/ethan-runtime
ETHAN_RUNTIME_CONFIG=/etc/ethan/runtime.yaml

# Socket path
ETHAN_SOCKET_PATH=/var/run/ethan/runtime.sock
```

---

## 7. User Experience

### 7.1 First Run

```
$ ethan

◆  First run detected
  ✓ Docker available
  ✓ Runtime installed
  ✓ Starting services...
  ✓ Core online
  ✓ Ready

◆  Welcome to ETHAN
  Your cognitive runtime is online.

  Quick start:
    ethan chat            Start AI conversation
    ethan run <task>      Execute a task
    ethan status          Show system state

  /help for commands

◆  ethan  ◇  chat  ▸
```

### 7.2 Normal Startup

```
$ ethan

◆  Starting ETHAN...
  ✓ Runtime running
  ✓ Core online
  ✓ Databases ready
  ✓ Connected

◆  ethan  ◇  chat  ▸
```

### 7.3 Resume Session

```
$ ethan

◆  Starting ETHAN...
  ✓ Runtime running
  ✓ Core online
  ✓ Session resumed: a1b2c3d4

◆  ETHAN Chat  ◇  session a1b2c3d4

◆  ethan  ◇  chat  ▸
```

### 7.4 Slow Startup

```
$ ethan

◆  Starting ETHAN...
  ✓ Docker available
  ⠋ Starting Runtime...
  ✓ Runtime started
  ⠋ Starting services...
    ✓ nats (0.2s)
    ✓ redis (0.3s)
    ✓ postgres (1.2s)
    ✓ ethan-core (2.5s)
  ✓ All services ready

◆  ethan  ◇  chat  ▸
```

### 7.5 Error State

```
$ ethan

◆  Starting ETHAN...
  ✗ Docker not available
  → Install Docker: https://docs.docker.com/get-docker/
  → Or run: sudo systemctl start docker

  Startup failed after 2.3s
```

---

## 8. Advanced Features

### 8.1 Background Runtime

```python
# If Runtime not running, start it in background
# CLI doesn't wait for Runtime, just continues

async def _start_runtime_background(self):
    """Start Runtime in background, don't block."""
    subprocess.Popen(
        ["ethan-runtime"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    
    # Continue with other checks
    # Runtime will be ready by the time we need it
```

### 8.2 Service Dependencies

```python
# Runtime handles service dependencies
# CLI just asks Runtime to start everything

async def _start_all_services(self):
    """Start all services via Runtime."""
    response = self.runtime.send({
        "command": "start_all",
        "timeout": 60,
    })
    return response.get("status") == "ok"
```

### 8.3 Health Monitoring

```python
# After startup, monitor health in background
async def _monitor_health(self):
    """Monitor service health after startup."""
    while True:
        await asyncio.sleep(15)
        
        services = await self._check_services()
        for name, state in services.items():
            if state != "running":
                # Alert user
                print_warning(f"Service {name} is {state}")
```

---

## 9. Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STARTUP WORKFLOW SUMMARY                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  User Experience                                                     │
│  $ ethan                                                             │
│  ◆ Starting ETHAN...                                                 │
│    ✓ Docker available                                                │
│    ✓ Runtime started                                                 │
│    ✓ Core online                                                     │
│    ✓ Databases ready                                                 │
│    ✓ Connected                                                       │
│  ◆ ethan ◇ chat ▸                                                   │
│                                                                       │
│  Startup Phases                                                      │
│  1. Preflight (0-500ms)                                              │
│     • Check Docker                                                   │
│     • Check Runtime                                                  │
│                                                                       │
│  2. Runtime Startup (0-2s)                                          │
│     • Start Runtime if stopped                                       │
│     • Verify responding                                              │
│                                                                       │
│  3. Service Orchestration (2-5s)                                    │
│     • Start infrastructure (nats, redis, postgres)                   │
│     • Start Core                                                     │
│     • Start Plugins                                                  │
│                                                                       │
│  4. CLI Connection (5-6s)                                           │
│     • Connect to Runtime                                             │
│     • Load config                                                    │
│     • Resume session                                                 │
│                                                                       │
│  5. Ready (6s+)                                                     │
│     • Show welcome                                                   │
│     • Display prompt                                                 │
│                                                                       │
│  Key Features                                                        │
│  • Zero manual Docker Compose commands                               │
│  • Automatic service orchestration                                   │
│  • Progressive verification                                          │
│  • Fast path if everything already running                           │
│  • Clear error messages with recovery hints                          │
│                                                                       │
│  Performance                                                         │
│  • Target: < 5s from command to ready                               │
│  • Fast path: < 1s (everything already running)                     │
│  • Slow path: 3-6s (starting from cold)                             │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘