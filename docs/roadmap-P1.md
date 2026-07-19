# Roadmap P1 — Actions Importantes (Court terme)

**Objectif** : Décisions structurelles et nettoyage  
**Date de création** : 2026-07-19  
**Statut** : En attente d'implémentation  
**Propriétaire** : Équipe Core + Architecture

---

## P1-1 : Décider du sort de `runtime/` et `rust/`

**Fichiers concernés** :
- `runtime/` (racine)
- `rust/` (racine)

### Problème

Deux dossiers présents à la racine du projet :
1. `runtime/` — Runtime Go séparé, aucun lien visible avec `core/`
2. `rust/` — Crates Rust (whisper, etc.), isolé

### Options

#### Option A : Supprimer

**Avantages** :
- Simplifie le projet
- Élimine la confusion
- Réduit la dette technique

**Inconvénients** :
- Perte de code potentiellement fonctionnel
- Si utilisé par des plugins, casse les dépendances

**Action** :
```bash
# Vérifier les imports
grep -r "runtime\." core/ plugins/ interfaces/ || echo "Aucun import détecté"

# Vérifier les imports rust
grep -r "rust" core/ plugins/ interfaces/ || echo "Aucun import détecté"

# Si aucun import : supprimer
rm -rf runtime/ rust/
```

#### Option B : Intégrer

**Avantages** :
- Préserve le code existant
- Permet une migration progressive

**Inconvénients** :
- Complexifie l'architecture
- Mélange des responsabilités

**Action** :
- Si `runtime/` est nécessaire : l'intégrer dans `core/` ou `infrastructure/`
- Si `rust/` est nécessaire : documenter son usage et créer un pont clair

#### Option C : Documenter et isoler

**Avantages** :
- Préserve le code
- Clarifie le rôle

**Inconvénients** :
- Nécessite de la documentation
- Demande de la maintenance

**Action** :
- Créer `docs/runtime.md` et `docs/rust.md`
- Déplacer vers `infrastructure/` si nécessaire
- Ajouter dans `.gitignore` si obsolète

### Décision requise

**À trancher par** : Architecture Team  
**Deadline** : 2026-07-26  
**Décision** : _En attente_

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Analysé** (usage, imports, dépendances)
- [ ] **Décidé** (A, B, ou C)
- [ ] **Implémenté**
- [ ] **Documenté**

---

## P1-2 : Éliminer les doublons

**Fichiers concernés** :
- `core/orchestration/` et `core/orchestrator/`
- `core/registry/module.py` et `core/registry/module_registry.py`

### Problème

Deux dossiers avec des rôles similaires :
1. `core/orchestration/` — contient des outils d'orchestration
2. `core/orchestrator/` — contient l'orchestrator principal

Deux fichiers avec des rôles similaires :
1. `core/registry/module.py` — registration de modules
2. `core/registry/module_registry.py` — registry de modules

### Analyse requise

```bash
# Comparer les contenus
diff core/orchestration/ core/orchestrator/
diff core/registry/module.py core/registry/module_registry.py

# Vérifier les imports
grep -r "from core.orchestration" core/ plugins/ interfaces/
grep -r "from core.orchestrator" core/ plugins/ interfaces/
grep -r "from core.registry.module import" core/ plugins/ interfaces/
grep -r "from core.registry.module_registry import" core/ plugins/ interfaces/
```

### Options

#### Option A : Fusionner

**Avantages** :
- Code unique
- Pas de confusion

**Inconvénients** :
- Risque de régression
- Nécessite des tests

**Action** :
- Fusionner `core/orchestration/*.py` dans `core/orchestrator/`
- Fusionner `core/registry/module.py` dans `core/registry/module_registry.py`
- Mettre à jour tous les imports
- Supprimer les doublons

#### Option B : Renommer et clarifier

**Avantages** :
- Préserve les deux fichiers
- Clarifie les rôles

**Inconvénients** :
- Toujours deux fichiers
- Nécessite de la documentation

**Action** :
- Renommer `core/orchestration/` en `core/orchestration_tools/` si pertinente
- Renommer `core/registry/module.py` en `core/registry/helpers.py` si pertinent
- Documenter la différence

#### Option C : Supprimer le doublon

**Avantages** :
- Simplifie
- Élimine la confusion

**Inconvénients** :
- Perte de code
- Risque de casser des imports

**Action** :
- Déterminer quel fichier est utilisé
- Supprimer l'autre
- Mettre à jour les imports

### Décision requise

**À trancher par** : Architecture Team  
**Deadline** : 2026-07-26  
**Décision** : _En attente_

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Analysé** (contenu, imports, dépendances)
- [ ] **Décidé** (A, B, ou C)
- [ ] **Implémenté**
- [ ] **Documenté**

---

## P1-3 : Nettoyer les dossiers vides

**Fichiers concernés** :
- `core/agents/` (vide)
- `core/pkg/` (vide)
- `__pycache__/` (présents dans le repo)

### Problème

Dossiers vides qui polluent le repository et créent de la confusion.

### Action

```bash
# Supprimer les dossiers vides
rm -rf core/agents/ core/pkg/

# Vérifier les __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Validation

```bash
# Vérifier qu'aucun dossier vide ne subsiste
find core/ -type d -empty
```

### Impact

- **Avant** : Dossiers vides, confusion
- **Après** : Repository propre

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## P1-4 : Clarifier la documentation README.md

**Fichier concerné** : `README.md`  
**Sections** : 5-8, 28-43, 557+

### Problèmes

1. **Section 1.1** : Mentionne gRPC mais l'API est HTTP
2. **Section 5** : Définit gRPC (port 50051) mais ce port n'existe pas
3. **Section 7.4** : Mentionne `/health` mais le healthcheck utilise `/v1/health`

### Actions

#### P1-4.1 : Corriger la section "API exposée"

**Ligne 28-43** :

```markdown
## ETHAN Core — Kernel Isolé

`core/` est un **kernel IA totalement isolé** :

| Règle | Status |
|-------|--------|
| Pas d'import `cli/` | ✅ |
| Pas d'import `interfaces/` | ✅ |
| Pas d'import `plugins/` | ✅ |
| Pas de `os.getenv()` | ✅ |
| Pas de `sys.path` hacking | ✅ |
| Pas de `signal` handling | ✅ |
| Pas de `print()` / `input()` | ✅ |

**API exposée** :
- **HTTP REST** (port 8000) — Endpoints: `/health`, `/version`, `/api/v1/*`
- **WebSocket** (port 8000) — Endpoint: `/api/v1/events/ws`
- **Python API** — `CognitiveKernel` injecté via dépendances
```

#### P1-4.2 : Corriger la section "Boot Lifecycle"

**Ligne 557+** :

```yaml
# Healthcheck
ExecStartPost=/opt/ethan/bin/ethanctl healthcheck --timeout 30
# Health endpoint
Endpoint: GET http://localhost:8000/health
```

#### P1-4.3 : Ajouter une section "Architecture réelle"

```markdown
### Architecture réelle (2026-07-19)

> **Note** : Cette section reflète la réalité du code, pas la vision théorique.

**Stack actuelle** :
- **Core** : Python (CognitiveKernel dans `core/kernel.py`)
- **API** : FastAPI (`interfaces/api/main.py`)
- **Event Bus** : NATS JetStream
- **Persistence** : PostgreSQL + Redis
- **Orchestration** : Docker Compose

**Non utilisé** :
- `core/main.go` (entrypoint Go jamais utilisé)
- `runtime/` (runtime Go séparé)
```

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Corrigé** dans README.md
- [ ] **Validé** par l'équipe

---

## Résumé P1

| ID | Action | Priorité | Fichier | Statut |
|----|--------|----------|---------|--------|
| P1-1 | Décider du sort de `runtime/` et `rust/` | **P1** | `runtime/`, `rust/` | ⏳ En attente de décision |
| P1-2 | Éliminer les doublons (`orchestration/` vs `orchestrator/`) | **P1** | `core/orchestration/`, `core/orchestrator/` | ⏳ En attente d'analyse |
| P1-3 | Nettoyer les dossiers vides | **P1** | `core/agents/`, `core/pkg/` | ⏳ En attente |
| P1-4 | Clarifier README.md | **P1** | `README.md` | ⏳ En cours |

### Actions immédiates

1. **Analyser** les dépendances vers `runtime/` et `rust/`
2. **Décider** de la stratégie (supprimer, intégrer, documenter)
3. ** Comparer** `core/orchestration/` et `core/orchestrator/`
4. **Supprimer** les dossiers vides
5. **Mettre à jour** README.md

---

## Notes

- P1 nécessite des décisions architecturales
- Impliquer l'Architecture Team pour P1-1 et P1-2
- P1-3 et P1-4 peuvent être faits rapidement

**Dernière mise à jour** : 2026-07-19