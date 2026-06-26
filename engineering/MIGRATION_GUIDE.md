# ETHAN Repository Migration Guide

**Version** : 2.0.0  
**From** : Legacy monorepo (v1.x)  
**To** : Component-based architecture (v2.0)

---

## 1. Summary of Changes

| Component | Old Location | New Location | Language |
|-----------|-------------|--------------|----------|
| Core AI engine | `core/` (mixed Python/Go) | `core/cmd/ethan-core/` | Go |
| Runtime | `kernel/bus/`, `core/deployment/` | `runtime/cmd/ethan-runtime/` | Go |
| CLI | `interfaces/cli/` | `cli/ethan/` | Python |
| Plugins | `plugins/` + `core/plugins/` | `plugins/` | Python |
| Docker | `infra/docker/`, `deploy/docker/` | `infrastructure/docker/` | Dockerfile |
| Systemd | `interfaces/cli/systemd/` | `infrastructure/systemd/` | .service |
| Config | `infra/config/` | `infrastructure/config/` | YAML |
| Docs | `docs/` | `docs/` | Markdown |
| Engineering | — | `engineering/` | Markdown |

---

## 2. Migration Steps

### Step 1: Create new directory structure
```bash
# Already done by REPOSITORY.md spec
```

### Step 2: Move Core code
```bash
# Old → New
cp core/main.py core/cmd/ethan-core/  # Entry point
cp core/kernel.py core/internal/kernel/
cp core/bus/*.py core/internal/bus/
cp core/registry/*.py core/internal/registry/
cp core/api/*.py core/internal/api/
cp core/events/*.py core/pkg/events/
cp core/types/*.py core/pkg/types/
cp core/telemetry/*.py core/internal/telemetry/
```

### Step 3: Create Go entry points
```bash
# New files written (not moved):
core/cmd/ethan-core/main.go      # Go binary entry point
runtime/cmd/ethan-runtime/main.go # Go binary entry point
```

### Step 4: Move CLI code
```bash
# Old → New
cp interfaces/cli/ethan cli/ethan/  # Main package
cp interfaces/cli/core/*.py cli/ethan/  # Core CLI modules
cp interfaces/cli/commands/*.py cli/ethan/commands/
```

### Step 5: Move Infrastructure
```bash
# Old → New
cp infra/docker/* infrastructure/docker/
cp infra/systemd/* infrastructure/systemd/
cp infra/config/* infrastructure/config/
cp infra/shell/* infrastructure/shell/
cp infra/scripts/* infrastructure/scripts/
```

### Step 6: Archive legacy code
```bash
# Move old code to legacy/ for reference
mv interfaces/cli/ legacy/cli/
mv core/old_modules/ legacy/core/
```

### Step 7: Update imports
```bash
# Python imports (cli/)
sed -i 's/from core\./from ethan./g' cli/ethan/*.py

# Go imports (core/)
sed -i 's|"github.com/ethan/|"github.com/seclib/Ethan/|g' core/**/*.go
```

### Step 8: Update documentation
```bash
# Update all paths in docs/
# Example: docs/architecture/overview.md
```

### Step 9: Update CI/CD
```bash
# Update .github/workflows/ci.yml paths
```

---

## 3. Rollback Plan

If the migration fails:

1. **Restore old structure**:
   ```bash
   git checkout -- .
   ```

2. **Re-apply only if safe**:
   - Keep `legacy/` directory intact
   - Keep old `docker-compose.yml` at root
   - Keep old `Makefile` at root

3. **No data loss**:
   - All data volumes (PostgreSQL, Redis) are external
   - Configuration files are backed up