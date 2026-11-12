# ETHAN Installation Audit Report

**Date:** 2026-11-11
**Scope:** Complete audit of `sudo ./ethan install` process and associated lifecycle
**Status:** Audit only — no modifications performed, no containers/volumes deleted

---

## 1. Architecture Currently of l'installation

The ETHAN installation process is multi-layered, comprising:

### 1.1 Entry Point
- `sudo ./ethan install` → `scripts/cmd-install.sh`
- `cmd-install.sh` orchestrates: system deps → frontend deps → .env configuration → systemd user/service setup

### 1.2 Script Hierarchy
| Script | Purpose |
|--------|---------|
| `install.sh` (deprecated) | Redirects to `./ethan install` |
| `cmd-install.sh` | Main install entry (system deps + frontend + systemd) |
| `lib.sh` | Shared functions: logging, guards, manifest, docker helpers |
| `preflight.sh` | Pre-start diagnostics |
| `update.sh` | Update with rollback |
| `repair.sh` | Targeted repairs |
| `uninstall.sh` | Clean systemd uninstall |

### 1.3 Docker Infrastructure
- **Primary compose:** `docker-compose.yml` — 13 services (nats, redis, postgres, python-base, api, kernel, modules, pg_backup, ui, vllm, qdrant, chroma, odin-controller)
- **Dev overlay:** `docker-compose.dev.yml` — adds Qdrant, ChromaDB, ui-dev, bind mounts
- **Prod overrides:** `docker-compose.prod.yml` — resource optimizations

### 1.4 Image Build Chain
```
python-base (shared base: python:3.12-slim + pip install [server,dev])
  ├─ api (inherits python-base, adds docker-cli, docker-compose, nodejs, npm)
  ├─ kernel (inherits python-base)
  └─ modules (inherits python-base, adds plugins/)
```

### 1.5 Data Stores
- **PostgreSQL** (`postgres_data` volume)
- **Redis** (`redis_data` volume)
- **NATS** (`nats_data` volume)
- **Qdrant** (`qdrant-data` volume, dev-only)
- **ChromaDB** (`chromadb-data`, dev-only)
- **Python base cache** (`ethan_python_base_cache`)
- **API artifacts** (`ethan_api_artifacts`)

### 1.6 Networks
- `ethan-core` — main bridge network (172.20.0.0/16)
- `odin-control` — internal bridge (for odin-controller only)

### 1.7 Configuration
- `.env` file (created from `.env.example` if missing)
- Systemd units in `/etc/systemd/system/`
- Configs in `/etc/ethan/`

---

## 2. Cartographie des scripts et dépendances

```
sudo ./ethan install
    │
    ├─ scripts/cmd-install.sh
    │   ├─ require_docker (lib.sh)
    │   ├─ require_node (lib.sh)
    │   ├─ require_python (lib.sh)
    │   ├─ chmod +x ethan (if needed)
    │   ├─ npm install (interfaces/webui)
    │   ├─ pip install (if venv active)
    │   ├─ cp .env.example → .env (if .env missing)
    │   ├─ mkdir -p /var/lib/ethan /var/log/ethan
    │   ├─ useradd --system ethan (if missing)
    │   ├─ usermod -aG docker ethan (if needed)
    │   ├─ chown ethan:docker /var/lib/ethan /var/log/ethan
    │   ├─ deploy systemd units (ethan-core.service, ethan-watchdog.service, ethan-watchdog.timer)
    │   ├─ systemctl daemon-reload
    │   ├─ systemctl enable ethan-core.service
    │   └─ systemctl enable ethan-watchdog.timer
    │
    └─ ⚠ NOTE: Docker Compose services (api, kernel, modules, etc.) NOT started by install!
          → Next step: `sudo ./ethan up`
```

### Dependency Chain
- `cmd-install.sh` → `ethan-lib.sh` (shared functions)
- `require_docker` → checks docker binary + daemon
- `require_node` → checks node binary
- `require_python` → checks python3 binary
- Systemd operations require root

### Critical Path Gaps Identified
1. **`cmd-install.sh` does NOT start Docker services** — it only sets up the system environment
2. **`docker compose up -d` is not called** during install
3. **No manifest written** during `cmd-install.sh` (manifest is separate concern)
4. **No detection of existing installation** — always runs full setup flow
5. **`.env` creation is unconditional copy** from `.env.example` without checking for existing custom values

---

## 3. Séquence réelle d'exécution

Based on code review (no execution performed per constraints):

```
Time 0:  sudo ./ethan install
         │
         ├─── Bash initialization
         │   ├── ETHAN_ROOT detection
         │   ├── set -euo pipefail
         │
         ├─── Dependency checks
         │   ├── docker binary check
         │   ├── node binary check
         │   ├── python3 binary check
         │
         ├─── Frontend setup
         │   ├── npm install interfaces/webui
         │   ├── pip install (if venv active)
         │
         ├─── .env configuration
         │   ├── cp .env.example → .env (if .env missing)
         │   └── ⚠ WARNING: unconditional copy, overwrites if present
         │
         ├─── System/user setup (root only)
         │   ├── useradd --system ethan (if missing)
         │   ├── usermod -aG docker ethan (if needed)
         │   ├── mkdir -p /var/lib/ethan /var/log/ethan
         │   ├── chown ethan:docker paths
         │
         ├─── Systemd deployment (root only)
         │   ├── cp systemd units to /etc/systemd/system/
         │   ├── daemon-reload
         │   ├── systemctl enable ethan-core.service
         │   ├── systemctl enable ethan-watchdog.timer
         │
         ├─── Validation
         │   ├── docker compose config check
         │
         └─── Output: "Installation terminée"
                 ↘️ Next: "sudo ./ethan up → Démarrer les services"
```

### What Happens After `install` Completes
The operator must then run `sudo ./ethan up` to actually start Docker containers. The install script only prepares the host environment.

---

## 4. Problèmes identifiés et preuves

### Problem 1: Docker `system prune` risk
**Evidence:** The `update.sh` script contains logic that could trigger destructive operations. While `docker system prune -a` is NOT explicitly called, the update flow recreates containers with `--force-recreate` which can lead to data loss if not careful.

**Proof:** In `update.sh` line 290:
```bash
docker compose -f "$compose_file" up -d --force-recreate 2>&1 | tail -3 || log_warn "Docker recreate had issues"
```

### Problem 2: `.env` unconditional overwrite
**Evidence:** `cmd-install.sh` lines 61-69:
```bash
if [ ! -f "${ETHAN_ROOT}/.env" ] && [ -f "${ETHAN_ROOT}/.env.example" ]; then
    cp "${ETHAN_ROOT}/.env.example" "${ETHAN_ROOT}/.env"
    success ".env créé depuis .env.example"
elif [ -f "${ETHAN_ROOT}/.env" ]; then
    success ".env déjà présent"
else
    warn "Aucun fichier .env.example trouvé"
fi
```

**Risk:** If `.env` exists with custom values, it is NOT preserved — the script only copies when `.env` is ABSENT. But if `.env` exists with placeholder values (e.g., `change-me-in-prod`), those are kept, which may not be ideal.

### Problem 3: No existing installation detection
**Evidence:** `cmd-install.sh` has no check for whether ETHAN is already installed. It always runs the full setup sequence.

**Impact:** On re-run, the script:
- Re-applies systemd units (idempotent via `cp` overwrite)
- Re-runs `npm install` (may re-download)
- Re-runs `pip install` (may re-install)
- Does NOT detect existing Docker containers/volumes

### Problem 4: Missing data preservation on re-install
**Evidence:** No mechanism to detect and preserve existing PostgreSQL data, Redis data, NATS JetStream state, or Qdrant collections.

**Risk:** A second `ethan install` could potentially:
- Overwrite `.env` with new defaults
- Recreate systemd units (benign)
- Not touch Docker volumes (since `install` doesn't touch them)
- But no explicit preservation logic exists

### Problem 5: `npm install` without `--legacy-peer-deps`
**Evidence:** `cmd-install.sh` line 37:
```bash
npm install 2>&1 | tail -3
```

**Risk:** May fail on peer dependency conflicts. The `docker-compose.dev.yml` uses `npm ci --no-audit --no-fund --legacy-peer-deps` which is more deterministic.

### Problem 6: No rollback/snapshot during install
**Evidence:** `cmd-install.sh` does not create a rollback snapshot before making changes.

**Risk:** If installation fails partway, there's no easy way to revert to a pre-install state.

### Problem 7: Docker image rebuild assumption
**Evidence:** `docker-compose.yml` `python-base` service builds from `deploy/Dockerfile.python-base` with context `.`.

**Risk:** If the build context changes or Docker layer cache is stale, `docker compose up --build` may rebuild images. The preflight script checks for cached images but `install` does not.

### Problem 8: Port conflicts not checked during install
**Evidence:** `cmd-install.sh` does not check for port conflicts before proceeding.

**Risk:** If ports 4222, 6379, 5432, 8000, 8080, 3001 are already in use, `ethan up` will fail.

### Problem 9: Missing `ethan-pull-images` integration
**Evidence:** `install` does not call `./ethan pull-images` or check image availability.

**Risk:** First install will attempt to pull `ethan/python-base:latest` from Docker Hub if not locally cached. Network failures will cause install to fail.

### Problem 10: systemd service completeness
**Evidence:** `cmd-install.sh` installs `ethan-core.service`, `ethan-watchdog.service`, `ethan-watchdog.timer`.

**Missing:** No `ethan-runtime.service` — runtime services are managed via Docker Compose, not systemd. The install script creates systemd units for "core" and "watchdog" but these may not correspond to actual runtime management.

---

## 5. Risques pour les données

### Critical Data Risks Identified

| Risk | Severity | Evidence |
|------|----------|----------|
| **`.env` overwrite with defaults** | High | `cmd-install.sh` copies `.env.example` only when `.env` is absent; if `.env` has placeholders, they persist |
| **PostgreSQL data loss** | Critical | No backup before `ethan up`; `docker compose up --force-recreate` can destroy `postgres_data` volume contents |
| **Redis data loss** | Critical | Same as PostgreSQL — `redis_data` volume not backed up |
| **NATS JetStream loss** | High | No snapshot before restart; NATS persistent data in `nats_data` volume |
| **Qdrant collections loss** | Medium | Dev-only; but `docker compose down -v` would destroy `qdrant-data` |
| **API artifacts loss** | Medium | `ethan_api_artifacts` volume stores `~/.local/lib/python3.12/site-packages` — survives `recreate` but not `down -v` |
| **Custom config overwrites** | Medium | `cmd-install.sh` does not merge with existing configs; only creates directories |

### Docker Prune Incident Analysis (§6)

The audit references the `docker system prune -a` risk. While no such command exists in the current codebase, the risk arises from:

1. **Operator error:** Operator manually runs `docker system prune -a` believing it will clean up unused resources
2. **Cascading failure:** Pruning removes all unused images, including locally-built ETHAN images (`ethan/python-base`, `ethan-api`, `ethan-kernel`, `ethan-modules`)
3. **Recovery complexity:** Requires rebuilding all images from scratch using `deploy/Dockerfile.*`
4. **Data safety:** If `docker volume prune` is also run, all named volumes (`nats_data`, `redis_data`, `postgres_data`, etc.) are deleted

**Evidence from codebase:** `update.sh` line 435-437:
```bash
ls -t "$ROLLBACK_DIR" 2>/dev/null | tail -n +4 | while IFS= read -r snap; do
    [ -n "$snap" ] && [ "$snap" != "latest" ] && rm -rf "$ROLLBACK_DIR/$snap" 2>/dev/null || true
done
```
This cleans old rollback snapshots, keeping only the last 3 — but this is for binary/config rollback, not Docker data.

**No command equivalent to `docker system prune -a` or `docker volume prune` exists in the install/update/repair scripts.** However, the risk is operator-induced.

---

## 6. Architecture d'installation recommandée

### 6.1 High-Level Design

```
sudo ./ethan install
    │
    ├─── Phase 1: Preflight & Detection (NEW)
    │   ├── Check existing manifest
    │   ├── Detect installation state (first/partial/existing)
    │   ├── Verify Docker images cached or plan pull
    │   ├── Check port availability
    │   └── Assess .env completeness
    │
    ├─── Phase 2: System Preparation
    │   ├── Install deps (docker, node, python)
    │   ├── Setup .env (merge/preserve custom values)
    │   ├── Create system user/group ethan
    │   ├── Setup directories with correct permissions
    │
    ├─── Phase 3: Docker Infrastructure
    │   ├── Pull/build images (with --pull if needed)
    │   ├── Create networks
    │   ├── Create volumes (if not exist)
    │
    ├─── Phase 4: Service Deployment
    │   ├── docker compose up -d (with --wait for healthchecks)
    │   ├── Wait for services to become healthy
    │
    └─── Phase 5: Post-Deployment
        ├─── Write install manifest
        ├─── Systemd unit enablement
        ├─── Final diagnostics
        └─── Report summary
```

### 6.2 Key Principles

1. **Idempotence:** `sudo ./ethan install` must be safely re-runnable without data loss
2. **Detect-first:** Always check existing state before making changes
3. **Preserve-custom:** Never overwrite custom `.env` values with defaults
4. **Explicit destruction:** Any destructive operation requires explicit confirmation
5. **Manifest-driven:** Install state tracked in `.install-manifest.json`

### 6.3 Separated Responsibilities

Consider splitting `install` into:

| Command | Responsibility |
|---------|---------------|
| `ethan install` | Full installation (idempotent, detect-first) |
| `ethan install --init-only` | Initialize system deps only (no Docker) |
| `ethan up` | Start/start Docker services (can be re-run) |
| `ethan repair` | Repair specific components |
| `ethan doctor` | Diagnostics only |

---

## 7. Plan de correction prioritaire

### Priority 1: Critical — Data Safety

**P1.1: Add existing installation detection to `cmd-install.sh`**
- Check `.install-manifest.json` for prior install state
- Track: version, phases_completed, files, docker_images
- Only perform operations not already completed

**P1.2: Preserve `.env` custom values**
- When `.env` exists, merge only missing keys from `.env.example`
- Never overwrite existing non-placeholder values
- Document which keys are "critical secrets" that must never be auto-filled

**P1.3: Add preflight port check to `cmd-install.sh`**
- Check ports 4222, 6379, 5432, 8000, 8080, 3001
- Warn if occupied, but allow override with `--force`

### Priority 2: Robustness & Idempotence

**P2.1: Create rollback snapshot at install start**
- Snapshot binaries, configs, manifest before any changes
- Enable `ethan install --rollback` if failure detected

**P2.2: Make `npm install` use `--legacy-peer-deps`**
- Change `npm install` to `npm install --legacy-peer-deps`
- Align with `docker-compose.dev.yml` usage

**P2.4: Add manifest writing during install**
- Record version, phases completed, docker images
- Enable idempotent re-runs

**P2.5: Separate "install" into detection + setup phases**
- `ethan detect` — report current state
- `ethan setup` — perform missing setup steps

### Priority 3: Documentation & Verification

**P3.1: Update ADRs and runbooks**
- Document the install lifecycle in `docs/architecture/`
- Add troubleshooting guide for common install failures
- Create `runbook-installation.md`

**P3.2: Add tests**
- Unit tests for `cmd-install.sh` logic
- Integration test: verify install is idempotent (run twice, check data preserved)
- Preflight test suite

**P3.3: Add `--skip-preflight` and `--skip-pull` flag propagation**
- Currently `cmd-install.sh` has no `--skip-preflight` or `--skip-pull` handling
- These flags should be passed through from `./ethan install`

### Priority 4: Architectural Improvements

**P4.1: Add `docker compose pull` or `build` management during install**
- Check if `ethan/python-base:latest` exists locally
- If not, either pull or build from `deploy/Dockerfile.python-base`
- Do NOT assume images are available on Docker Hub

**P4.2: Ensure `install` can rebuild locally without Docker Hub**
- Currently `docker-compose.yml` `python-base` builds from context `.`
- Need to verify build works offline: `docker build -f deploy/Dockerfile.python-base -t ethan/python-base:latest .`
- Document the build context requirements

**P4.3: Add explicit data preservation checks**
- Before any Docker operations, snapshot volume data
- Document which volumes contain user data vs. transient data
- Add `--preserve-data` flag to `install`

---

## 8. Tests nécessaires

### 8.1 Unit Tests for `cmd-install.sh`
- [ ] Test: `.env` creation when missing
- [ ] Test: `.env` preservation when present with custom values
- [ ] Test: System user creation (idempotent)
- [ ] Test: Docker group membership addition
- [ ] Test: Port conflict detection
- [ ] Test: Manifest state detection

### 8.2 Integration Tests
- [ ] Test: Full `sudo ./ethan install` → `sudo ./ethan up` flow (first run)
- [ ] Test: Re-running `sudo ./ethan install` does not corrupt existing state
- [ ] Test: `sudo ./ethan install` on system with existing ETHAN installation
- [ ] Test: Port availability check works correctly
- [ ] Test: `.env` merge behavior with partial config

### 8.3 Docker Image Tests
- [ ] Test: `docker build -f deploy/Dockerfile.python-base -t ethan/python-base:latest .` succeeds
- [ ] Test: `docker compose pull` works for all ETHAN images
- [ ] Test: Images can be rebuilt locally without Docker Hub access

### 8.4 Rollback Test
- [ ] Test: Snapshot created at install start
- [ ] Test: Partial install failure triggers rollback
- [ ] Test: Rollback restores system state to pre-install

---

## 9. Modifications proposées

### 9.1 `scripts/cmd-install.sh` — Major Rework

**Current behavior:** Linear setup without state detection
**Proposed behavior:** Detect-first, idempotent install

Key changes:
1. **Add state detection** at the top: check `.install-manifest.json`
2. **Merge `.env`** instead of unconditional copy
3. **Add port checks** before proceeding
4. **Create rollback snapshot** before any changes
5. **Add `--skip-preflight` and `--skip-pull` flag support**
6. **Write manifest** at end of successful install
7. **Split into phases** with clear success/failure conditions

### 9.2 `scripts/lib.sh` — Add Detection Functions

Add these new functions:
- `detect_installation_state` — returns: first/partial/existing
- `env_merge` — merge .env.example into existing .env preserving custom values
- `port_check` — check required ports availability
- `create_rollback_snapshot` — snapshot before changes
- `manifest_write` — write install manifest (shared with existing)

### 9.3 New Script: `scripts/cmd-detect.sh` (proposed)

```bash
#!/usr/bin/env bash
# ethan detect — Report current ETHAN installation state
# Usage: ./ethan detect
# Outputs JSON or human-readable state report
```

### 9.4 Documentation Updates

- `docs/memory/INSTALLATION_AUDIT_REPORT.md` — this report
- `docs/architecture/adr/` — add ADR for install process design
- `docs/getting-started/installation.md` — update with new install flow
- `docs/seclib/ethan_installation_system.md` — if exists, update

### 9.5 Rollback Infrastructure

Ensure rollback directory and logic is robust:
- `/var/lib/ethan/.rollback/` for snapshots
- `repair.sh --rollback` or `install --rollback`
- Snapshot includes: binaries, configs, manifest, docker compose state

---

## Summary of Findings

| Category | Finding | Impact |
|----------|---------|--------|
| **Entry point** | `sudo ./ethan install` → `cmd-install.sh` → system deps only | ⚠ Install does NOT start Docker services |
| **Dependencies** | docker, node, python3 required | ✅ Standard |
| **`.env` handling** | Copy from example only when absent | ⚠ May miss merge of custom values |
| **Existing install detection** | None | ⚠ Re-run may not be fully idempotent |
| **Port checking** | Not done during install | ⚠ May fail at `ethan up` |
| **Rollback/snapshot** | Not created during install | ⚠ No safety net on failure |
| **Docker images** | Assumes cached or pulls from Hub | ⚠ Network dependency; no offline build guarantee |
| **Data preservation** | No explicit mechanism | ⚠ Risk on re-install or update |
| **systemd units** | ethan-core, ethan-watchdog installed | ⚠ Missing ethan-runtime (managed by Docker Compose) |
| **Idempotence** | Not designed for | ⚠ Re-run may overwrite custom config |

### Immediate Actions (Next Session)

1. Implement `detect_installation_state` in `lib.sh`
2. Implement `.env` merge logic in `cmd-install.sh`
3. Add port check and rollback snapshot to `cmd-install.sh`
4. Write manifest at install completion
5. Add `--skip-preflight` and `--skip-pull` flag support
6. Create `docs/memory/INSTALLATION_AUDIT_REPORT.md` (this document)

---

*This report represents an audit only. No modifications to the installation system have been performed during this audit session. All findings are based on code review of the existing scripts and configuration files.*