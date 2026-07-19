# Backend Simplification — ETHAN

## Date : 2026-07-12

## Modifications

### 1. Unification CognitiveKernel (4 → 1)

| Avant | Après | Statut |
|-------|-------|--------|
| `core/kernel.py` (complet, 216 lignes) | **gardé** | ✅ |
| `core/kernel/engine.py` (isolé, 96 lignes) | réexport vers `core/kernel.py` | ✅ supprimé |
| `core/kernel/__init__.py` | supprimé (causait import circulaire) | ✅ supprimé |
| `core/cmd/ethan-core/kernel.py` (legacy) | supprimé (inutilisé) | ✅ supprimé |
| `core/internal/kernel/kernel.py` | doublon non importé, laissé sur place | ⏳ |

Tous les imports (`from core.kernel import CognitiveKernel`) fonctionnent via `core/kernel.py`.

### 2. Suppression APIAdapter (inutilisé)

`interfaces/api/kernel_adapter.py` était un wrapper `KernelClient` jamais branché dans `main.py`. L'API utilise NATS direct via `nats-py` — c'est le bon pattern.

### 3. Fusion modules Docker (8 → 1 service)

| Avant | Après |
|-------|-------|
| module-executive | modules |
| module-planner | ↳ lance les 8 modules via `modules.launcher` |
| module-memory | |
| module-reflective | |
| module-learning | |
| module-metacognition | |
| module-autonomy | |

Docker-compose réduit de 17 à 11 services. Même `Dockerfile.module` utilisé.

## Vérifications
- ✅ `python3 -c "from core.kernel import CognitiveKernel"` OK
- ✅ `yaml.safe_load(docker-compose.yml)` OK
- ✅ frontend : `npm install && npm run build && npm run lint && npm run typecheck` OK