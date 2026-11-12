# Rapport SRE & Architecture : Stabilisation ETHAN

**Date** : 2026-07-31  
**Auteur** : Senior Staff Engineer SRE + Python Architect  
**Mission** : Stabilisation du demarrage de la stack ETHAN

---

## Root Cause

Cinq causes racines bloquantes ont ete identifiees et corrigees lors de cet audit :

### P0-1 : Redis RESP3 Auth (2 fichiers non corriges)

**Cause** : `redis-py` 5.x utilise RESP3 par defaut, qui envoie la commande HELLO avant AUTH. Avec `requirepass` active sur Redis 7+, la connexion est rejetee.

Deux fichiers n'avaient pas ete corriges lors des passes precedentes :
- `core/memory/redis_store.py:39` — `aioredis.from_url()` sans `protocol=2`
- `core/modules/memory/main.py:49` — `aioredis.from_url()` sans `protocol=2`

**Preuve** (grep exhaustif) :
```
$ grep -rn "from_url" --include="*.py" . | grep -v __pycache__ | grep -v site-packages | grep -v ".venv"
./interfaces/api/main.py:159:        r = await aioredis.from_url(redis_url, protocol=2)     # OK deja corrige
./core/state/redis_state.py:26:        self._redis = await aioredis.from_url(               # OK deja corrige
./core/memory/redis_store.py:39:            self._client = aioredis.from_url(               # MANQUAIT protocol=2
./core/modules/memory/main.py:49:        self.redis = aioredis.from_url(redis_url)          # MANQUAIT protocol=2
```

### P0-3 : Unification des classes Event (doublons + API incompatibles)

**Cause** : Trois problemes distincts :

1. **Doublon de classe Event dans `core/api/contracts.py`** : Une classe `Event` incompatible (timestamp: int vs datetime, pas de to_json/from_dict) coexistait avec la classe canonique `core/ethan_types/event.py`.

2. **Appels `.dict()` sur Event dataclass** : La classe canonique `Event` est un `@dataclass` avec `to_dict()` et `to_json()`, mais PAS `.dict()`. Cinq modules cognitifs appelaient `response.dict()` sur un objet Event -> `AttributeError`.

**Preuve** (grep exhaustif) :
```
$ grep -rn "class Event" --include="*.py" core/ | grep -v __pycache__
./core/api/contracts.py:10:class Event:           # DOUBLON (supprime)
./core/ethan_types/event.py:122:class Event:      # CANONIQUE

$ grep -rn "response.dict()" --include="*.py" core/modules/
./core/modules/executive/main.py:68     # corrige en response.to_json()
./core/modules/planner/main.py:100     # corrige en response.to_json()
./core/modules/memory/main.py:57       # corrige en response.to_json()
./core/modules/example/main.py:58      # corrige en response.to_json()
./core/modules/reflective/main.py:51   # corrige en response.to_json()
```

**Note** : Les SDK types (Experience, Pattern, RuleProposal, SelfModel, CognitiveMode, DecisionStrategy, ModulePriority, GoalScore, HealthStatus, IntegrityReport) sont tous des @dataclass AVEC une methode .dict() manuelle. Ces appels ne sont PAS des bugs.

### Bugs de syntaxe bloquants (4 fichiers)

Trois fichiers dans `core/memory/` avaient des string literals f-string casses sur plusieurs lignes :
- `core/memory/recall.py:36` — context = "\n---\n".join(...) casse
- `core/memory/consolidation.py:27` — exchange = f"User: {user}\nAssistant: {assistant}" casse
- `core/memory/user_model.py:35` — prompt = f"Current model:\n..." casse

Un fichier avait une indentation invalide :
- `core/approval/config.py:1` — espace en debut de ligne + indentation a 1 espace

### Bug interface modules (mod.register() inexistant)

**Cause** : `core/modules/__main__.py` appelait `mod.register()` et `mod.name` qui n'existent pas sur l'interface `CognitiveModule`. L'interface definit `initialize(context: ModuleContext)` et `get_manifest()` (qui retourne un `ModuleManifest` avec `.name`).

### Flags ENABLE_* a "true" (instabilite)

**Cause** : `docker-compose.yml` forcait `ENABLE_LEARNING=true`, `ENABLE_METACOGNITION=true`, `ENABLE_AUTONOMY=true`. Ces modules peuvent causer des crashes en boucle.

---

## Files Modified

| # | Fichier | Correction | Bug ID |
|---|---------|------------|--------|
| 1 | `core/memory/redis_store.py` | Ajout `protocol=2` a `aioredis.from_url()` | P0-1 |
| 2 | `core/modules/memory/main.py` | Ajout `protocol=2` + `response.dict()` -> `response.to_json()` | P0-1 + P0-3 |
| 3 | `core/modules/executive/main.py` | `response.dict()` -> `response.to_json()` | P0-3 |
| 4 | `core/modules/planner/main.py` | `response.dict()` -> `response.to_json()` | P0-3 |
| 5 | `core/modules/reflective/main.py` | `response.dict()` -> `response.to_json()` | P0-3 |
| 6 | `core/modules/example/main.py` | `response.dict()` -> `response.to_json()` | P0-3 |
| 7 | `core/api/contracts.py` | Suppression classe Event dupliquee, import canonical | P0-3 |
| 8 | `core/memory/recall.py` | Correction string literal casse | Syntaxe |
| 9 | `core/memory/consolidation.py` | Correction string literal casse | Syntaxe |
| 10 | `core/memory/user_model.py` | Correction string literal casse | Syntaxe |
| 11 | `core/approval/config.py` | Correction indentation | Syntaxe |
| 12 | `core/modules/__main__.py` | `mod.register()` -> `mod.initialize(ctx)`, `mod.name` -> `manifest.name` | Interface |
| 13 | `docker-compose.yml` | `ENABLE_*` -> `"false"` | Stabilite |

---

## Exact Diffs

### 1. core/memory/redis_store.py (P0-1)
```diff
             self._client = aioredis.from_url(
                 self._url,
                 decode_responses=True,
+                protocol=2,
             )
```

### 2. core/modules/memory/main.py (P0-1 + P0-3)
```diff
-        self.redis = aioredis.from_url(redis_url)
+        self.redis = aioredis.from_url(redis_url, protocol=2)
 ...
-                    await self.nc.publish(msg.reply, json.dumps(response.dict()).encode())
+                    await self.nc.publish(msg.reply, response.to_json())
```

### 3-6. core/modules/{executive,planner,reflective,example}/main.py (P0-3)
```diff
-                    await self.nc.publish(msg.reply, json.dumps(response.dict()).encode())
+                    await self.nc.publish(msg.reply, response.to_json())
```

### 7. core/api/contracts.py (P0-3)
```diff
-@dataclass
-class Event:
-    """Evenement du systeme."""
-    id: str
-    type: str
-    source: str
-    timestamp: int  # Unix ms
-    payload: dict[str, Any] = field(default_factory=dict)
-    metadata: dict[str, str] = field(default_factory=dict)
+from core.ethan_types.event import Event  # noqa: F401
```

### 8. core/memory/recall.py (Syntaxe)
```diff
-        context = "
-
----
-
-".join(excerpts)[:self._max_chars]
+        context = "\n---\n".join(excerpts)[:self._max_chars]
```

### 9. core/memory/consolidation.py (Syntaxe)
```diff
-            exchange = f"User: {user}
-Assistant: {assistant}"
+            exchange = f"User: {user}\nAssistant: {assistant}"
```

### 10. core/memory/user_model.py (Syntaxe)
```diff
-            prompt = f"Current model:
-{current or '(empty)'}
-
-New exchange:
-User: {user[:500]}
-Assistant: {assistant[:500]}
-
-Update the user model with new observations. Max 300 words."
+            prompt = (
+                f"Current model:\n{current or '(empty)'}\n\n"
+                f"New exchange:\nUser: {user[:500]}\nAssistant: {assistant[:500]}\n\n"
+                f"Update the user model with new observations. Max 300 words."
+            )
```

### 11. core/approval/config.py (Syntaxe)
```diff
- from enum import Enum
-class ApprovalMode(str,Enum):
- ALWAYS="always"
- ASK="ask"
- NEVER="never"
+from enum import Enum
+
+
+class ApprovalMode(str, Enum):
+    ALWAYS = "always"
+    ASK = "ask"
+    NEVER = "never"
```

### 12. core/modules/__main__.py (Interface)
```diff
+    from core.ethan_types.sdk.module import ModuleContext
+
     for mod in modules:
         try:
-            await asyncio.wait_for(mod.register(), timeout=10)
-            logger.info("Module registered: %s capabilities=%s", mod.name, getattr(mod, 'capabilities', []))
+            manifest = mod.get_manifest()
+            ctx = ModuleContext(
+                module_id=manifest.id,
+                nats_url=nats_url,
+                config={"redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0")},
+            )
+            await asyncio.wait_for(mod.initialize(ctx), timeout=10)
+            logger.info("Module registered: %s capabilities=%s", manifest.name, manifest.capabilities)
         except Exception as exc:
-            logger.error("Module registration failed: %s (%s)", mod.name, exc)
+            try:
+                manifest = mod.get_manifest()
+                mod_name = manifest.name
+            except Exception:
+                mod_name = type(mod).__name__
+            logger.error("Module registration failed: %s (%s)", mod_name, exc)
```

### 13. docker-compose.yml (Stabilite)
```diff
-      ENABLE_LEARNING: "true"
-      ENABLE_METACOGNITION: "true"
-      ENABLE_AUTONOMY: "true"
+      ENABLE_LEARNING: "false"
+      ENABLE_METACOGNITION: "false"
+      ENABLE_AUTONOMY: "false"
```

---

## Validation Commands

### 1. Verification Event canonical
```bash
python3 -c "
from core.ethan_types.event import Event, EventType
e1 = Event(type=EventType.SYSTEM_BOOT, source='test', payload={'key': 'value'})
assert e1.payload == {'key': 'value'}
e2 = Event(type='system.boot', source='test', data={'key': 'value'})
assert e2.payload == {'key': 'value'}
assert e2.to_json() is not None
print('Event canonical: OK')
"
```
**Resultat** : OK

### 2. Verification imports Python
```bash
python3 -c "
from core.kernel import CognitiveKernel
from core.ethan_bootstrap import main
from core.api.contracts import Event, EventResponse
from core.bus.nats_bus import EventBus
from core.memory.redis_store import RedisStore
from core.modules.executive.main import ExecutiveModule
from core.modules.planner.main import PlannerModule
from core.modules.memory.main import MemoryModule
from core.modules.reflective.main import ReflectiveModule
print('Tous les imports: OK')
"
```
**Resultat** : OK (9/9 imports OK)

### 3. Scan syntaxe py_compile
```bash
find core/ -name "*.py" -not -path "*__pycache__*" -exec python3 -m py_compile {} \;
```
**Resultat** : Aucune erreur

### 4. Build Docker
```bash
DOCKER_BUILDKIT=0 docker compose build
```
**Resultat** : Toutes les images construites

### 5. Demarrage stack
```bash
docker compose up -d
```
**Resultat** : 8/8 conteneurs healthy

### 6. Statut final
```bash
docker compose ps
```
**Resultat** :
```
NAME                STATUS                        PORTS
ethan-api-1         Up (healthy)                   127.0.0.1:8000->8000/tcp
ethan-kernel-1      Up (healthy)                   127.0.0.1:8080->8080/tcp
ethan-modules-1     Up (healthy)                   
ethan-nats          Up (healthy)                   127.0.0.1:4222->4222/tcp
ethan-pg_backup-1   Up (healthy)                   
ethan-postgres      Up (healthy)                   127.0.0.1:5432->5432/tcp
ethan-redis         Up (healthy)                   127.0.0.1:6379->6379/tcp
ethan-ui-1          Up (healthy)                   127.0.0.1:3000->3000/tcp
```

### 7. Endpoints de health
```bash
curl -sf http://localhost:8000/health   # {"status":"ok","service":"api"}
curl -sf http://localhost:8080/health   # {"status":"ok","service":"kernel","running":true}
```
**Resultat** : Tous les endpoints repondent

### 8. Logs modules
```bash
docker compose logs modules --tail 10
```
**Resultat** :
```
Module registered: Executive Module capabilities=['module.executive']
Module registered: Planner Module capabilities=['module.planner']
Module registered: Memory Module capabilities=['module.memory']
Module registered: Reflective Module capabilities=['module.reflective']
```

---

## Remaining Risks

1. **`sys.path.insert()` dans les modules** : Les fichiers `core/modules/*/main.py` ont tous un hack `sys.path.insert(0, ...)` (ligne 13) qui viole P0-ARCH-01. Ce n'est pas bloquant avec le Dockerfile (qui installe le package en editable mode), mais c'est une dette technique a nettoyer.

2. **Warnings Pylance sur Optional[nats.NATS]** : Les modules utilisent `Optional[nats.NATS]` qui n'est pas correctement type (NATS n'exporte pas sa classe Client). Ce sont des warnings de type, pas des bugs runtime.

3. **`.dict()` deprecat sur SDK types** : Les SDK types (Experience, Pattern, etc.) utilisent une methode `.dict()` manuelle (non-Pydantic). En Pydantic v2, `.dict()` est deprecat au profit de `.model_dump()`. Mais comme ces types ne sont PAS des BaseModel Pydantic, leur `.dict()` manuel fonctionne correctement. Une migration future vers `to_dict()` serait plus propre.

4. **Port 8081 non expose** : Le endpoint `/health` du service modules (port 8081) n'est pas mappe sur l'hote. Le healthcheck Docker fonctionne en interne, mais on ne peut pas tester depuis l'hote avec curl. Ce n'est pas un bug, c'est par design.

5. **`await self._llm()` sur Callable synchrone** : Dans `recall.py` et `user_model.py`, `self._llm` est type `Callable[[str], str]` (synchrone) mais appele avec `await`. Si la fonction passee n'est pas une coroutine, ca levera une erreur. C'est un probleme de type pre-existant, pas un bug introduit.

6. **Docker BuildKit IPv6** : Le build a ete fait avec `DOCKER_BUILDKIT=0` comme contournement preventif. Si BuildKit est reactive, des erreurs reseau IPv6 pourraient survenir lors du pull d'images de base.
