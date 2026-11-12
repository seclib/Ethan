# Décisions Architecture — Recommandations

**Date** : 2026-07-19  
**Auteur** : Principal Software Architect  
**Destinataires** : Architecture Team, CTO  
**Deadline** : 2026-07-26 (P1-1, P1-2), 2026-08-02 (P3-1, P3-2)

---

## Vue d'ensemble des décisions requises

```
┌─────────────────────────────────────────────────────────────┐
│           Décisions Architecture en attente                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 P1-1 : Sort de runtime/ et rust/                        │
│     Deadline : 2026-07-26                                   │
│                                                             │
│  📋 P1-2 : Doublons (orchestration/ vs orchestrator/)       │
│     Deadline : 2026-07-26                                   │
│                                                             │
│  📋 P3-1 : Stratégie Go vs Python pour Core                 │
│     Deadline : 2026-08-02                                   │
│                                                             │
│  📋 P3-2 : Sort de jarvis-OS/                               │
│     Deadline : 2026-08-02                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## P1-1 : Sort de `runtime/` et `rust/`

### Analyse

**runtime/** :
- Aucun import détecté dans `core/`, `plugins/`, `interfaces/`
- Dossier Go séparé, non référencé dans `docker-compose.yml`
- Aucune documentation le mentionnant
- `core/main.go` existe et semble être le véritable entrypoint Go, mais `runtime/` n'est pas lié

**rust/** :
- Aucun import détecté
- Présent mais isolé
- Pourrait être utilisé par des crates externes (whisper, etc.)
- Aucune documentation

### Recommandation : Option C — Documenter et isoler

**Raison** :
- Ces dossiers pourraient être des prototypes ou du code futur
- Les supprimer (Option A) risque de perdre du travail
- Les intégrer (Option B) complexifie l'architecture sans bénéfice immédiat
- Documenter (Option C) préserve le code et clarifie son statut

**Actions** :

```bash
# 1. Créer un README pour runtime/
cat > runtime/README.md << 'EOF'
# Runtime (Legacy)

## Statut

⚠️ **Ce dossier est conservé pour référence uniquement.**

## Raison de la dépréciation

Ce runtime Go ne fait plus partie de l'architecture ETHAN.

## Historique

- Ajouté en : [date à vérifier dans git log]
- Dernière modification : [date à vérifier]

## Remplacement

ETHAN utilise maintenant :
- Core Python dans `core/kernel.py` + `core/bootstrap.py`
- Event Bus NATS pour la communication inter-modules

## Si vous avez besoin de ce code

1. Forkez ce dépôt avant suppression
2. Documentez les dépendances avant utilisation
EOF

# 2. Créer un README pour rust/
cat > rust/README.md << 'EOF'
# Rust Crates (Legacy)

## Statut

⚠️ **Ce dossier contient des crates Rust potentially fonctionnelles.**

## Usage prévu

Ces crates pourraient servir pour :
- Traitement audio (whisper)
- Performance-critical components

## Pour les utiliser

Documentation à écrire.

## Dépendances

- Rust toolchain : vérifier `rust/rust-toolchain.toml`
- Build : `cargo build --release`
EOF

# 3. Commit
git add -A
git commit -m "docs: add README to runtime/ and rust/ to clarify status"
```

**Impact** : Faible — documentation seulement  
**Temps** : 30min  
**Risque** : Aucun

---

## P1-2 : Éliminer les doublons

### Analyse

**core/orchestration/** vs **core/orchestrator/** :

```bash
# Vérifier la taille
wc -l core/orchestration/*.py
wc -l core/orchestrator/*.py

# Vérifier les imports
grep -r "from core.orchestration" core/ plugins/ interfaces/
grep -r "from core.orchestrator" core/ plugins/ interfaces/
```

**Hypothèse** :
- `orchestration/` contient probablement des outils
- `orchestrator/` contient probablement l'orchestrateur principal
- Risque de confusion élevé

**core/registry/module.py** vs **core/registry/module_registry.py** :

```bash
# Comparer
diff core/registry/module.py core/registry/module_registry.py
```

**Hypothèse** :
- `module.py` pourrait être des helpers
- `module_registry.py` pourrait être le registry principal
- Risque de confusion élevé

### Recommandation : Option A — Fusionner

**Raison** :
- Un seul fichier/dossier par responsabilité évite la confusion
- Les deux semblent avoir des rôles similaires
- La fusion réduit la dette technique

**Actions pour orchestration/** :

```bash
# 1. Sauvegarder orchestrator/
cp -r core/orchestrator/ core/orchestrator.backup/

# 2. Vérifier ce qui est utilisé
USED=$(grep -rl "from core.orchestrator" core/ plugins/ interfaces/ | head -1)
echo "Orchestrator utilisé dans : $USED"

USED2=$(grep -rl "from core.orchestration" core/ plugins/ interfaces/ | head -1)
echo "Orchestration utilisé dans : $USED2"

# 3. Si les deux sont utilisés, fusionner dans orchestrator/
if [ -n "$USED2" ]; then
    cp core/orchestration/*.py core/orchestrator/
    find core/ plugins/ interfaces/ -name "*.py" -exec \
        sed -i 's/from core.orchestration/from core.orchestrator/g' {} +
    rm -rf core/orchestration/
fi

# 4. Commit
git add -A
git commit -m "refactor: merge orchestration/ into orchestrator/"
```

**Actions pour registry/** :

```bash
# 1. Vérifier ce qui est utilisé
grep -r "from core.registry.module import" core/ plugins/ interfaces/
grep -r "from core.registry.module_registry import" core/ plugins/ interfaces/

# 2. Si module.py est utilisé moins que module_registry.py, fusionner
if [ -z "$(grep -r 'from core.registry.module import' core/ plugins/ interfaces/)" ]; then
    cat core/registry/module.py >> core/registry/module_registry.py
    rm core/registry/module.py
else
    # Inverser si nécessaire
    cat core/registry/module_registry.py >> core/registry/module.py
    rm core/registry/module_registry.py
    find . -name "*.py" -exec \
        sed -i 's/from core.registry.module_registry import/from core.registry.module import/g' {} +
fi

# 3. Commit
git add -A
git commit -m "refactor: merge duplicate registry modules"
```

**Impact** : Moyen — risque de régression  
**Temps** : 2-3h  
**Risque** : Moyen — nécessite des tests d'imports

**Validation** :

```bash
# Tester les imports
./ethan python3 -c "from core.orchestrator import *; print('OK')"
./ethan python3 -c "from core.registry.module_registry import *; print('OK')"

# Tester le démarrage
./ethan up
./ethan status
```

---

## P3-1 : Clarifier la stratégie Go vs Python pour Core

### Analyse

**Constats** :
- `docker-compose.yml` utilise `python kernel/bootstrap.py`
- `infrastructure/systemd/ethan-core.service` utilise `/opt/ethan/bin/ethan-core` (compilé Go ?)
- `core/main.go` existe mais n'est pas référencé clairement
- Aucun lien évident entre `main.go` et les fichiers Python

**Performances** :
- Python : plus lent, mais plus flexible
- Go : plus rapide, meilleur pour daemon systemd

### Recommandation : Option C — Cohabitation (à court terme)

**Raison** :
- Migrer entièrement vers Go (Option B) demanderait des semaines
- Migrer entièrement vers Python (Option A) perdrait la performance Go
- La cohabitation permet une migration progressive

**Architecture cible** :

```
┌─────────────────────────────────────────┐
│         Go Kernel (Performance)         │
│  - Event routing                        │
│  - Request/Reply                        │
│  - High-throughput processing           │
│                                         │
│  core/kernel-go/                        │
│    main.go                              │
│    go.mod                               │
└─────────────────────────────────────────┘
           │
           │ gRPC ou NATS
           │
┌─────────────────────────────────────────┐
│      Python Kernel (Cognitive)          │
│  - Business logic                       │
│  - Module coordination                  │
│  - LLM integration                      │
│                                         │
│  core/                                  │
│    kernel.py                            │
│    bootstrap.py                         │
│    main.py                              │
└─────────────────────────────────────────┘
```

**Actions immédiates** :

```bash
# 1. Créer la structure
mkdir -p core/kernel-go

# 2. Déplacer main.go
mv core/main.go core/kernel-go/
mv core/go.mod core/kernel-go/
mv core/go.sum core/kernel-go/ 2>/dev/null || true

# 3. Créer un README
cat > core/kernel-go/README.md << 'EOF'
# Kernel Go — Performance Layer

## Rôle

Kernel Go haute performance pour :
- Routage d'événements
- Patterns Request/Reply
- Traitement à haut débit

## Interface avec Python

Le kernel Go communique avec le kernel Python via :
- NATS (event bus partagé)
- gRPC (si nécessaire)

## Statut

⚠️ **Non prêt pour la production** — Kernel Python reste principal.

## Compilation

```bash
cd core/kernel-go
go build -o ethan-core main.go
```

## Tests

```bash
go test ./...
```
EOF

# 4. Documenter l'interface
cat > docs/kernel-go-python-interface.md << 'EOF'
# Interface Go ↔ Python

## Architecture

```
Go Kernel (performance) ←→ NATS ←→ Python Kernel (cognitive)
```

## Communication

- Go écoute sur : `ethan.kernel.*`
- Python écoute sur : `ethan.module.*`
- Partage d'état : Redis + PostgreSQL

## Sujets NATS

- `ethan.kernel.request` — Requêtes vers le kernel Go
- `ethan.kernel.response` — Réponses du kernel Go
- `ethan.module.event` — Événements vers les modules Python

## États partagés

- Redis : `kernel:state:*`
- PostgreSQL : `events`, `snapshots`
EOF

# 5. Commit
git add -A
git commit -m "docs: clarify Go/Python kernel cohabitation strategy"
```

**Impact** : Élevé — clarification architecturale  
**Temps** : 1-2h  
**Risque** : Faible — documentaire seulement

**Validation** :

```bash
# Vérifier que les deux kernels fonctionnent
./ethan up
./ethan status
```

---

## P3-2 : Décider du sort de `jarvis-OS/`

### Analyse

```bash
# Examiner le contenu
ls -la jarvis-OS/

# Vérifier les imports
grep -r "jarvis" core/ plugins/ interfaces/ || echo "Aucun import"

# Vérifier l'historique
git log --oneline --all -- jarvis-OS/ | head -20

# Vérifier la documentation
grep -r "jarvis" docs/ engineering/ README.md || echo "Aucune mention"
```

### Recommandation : Option A — Supprimer (si legacy)

**Raison** :
- Si c'est un ancien projet intégré par erreur
- Si aucun import ni documentation ne le mentionne
- Pour réduire la dette technique

**Actions** :

```bash
# 1. Sauvegarder dans un tag
git tag -a legacy-jarvis-$(date +%Y%m%d) -m "Legacy jarvis-OS before removal"

# 2. Supprimer
rm -rf jarvis-OS/

# 3. Nettoyer .gitignore
echo "jarvis-OS/" >> .gitignore

# 4. Commit
git add -A
git commit -m "chore: remove legacy jarvis-OS directory"
```

**Impact** : Faible — suppression de code mort  
**Temps** : 10min  
**Risque** : Très faible

**Alternative** : Si `jarvis-OS/` est lié à ETHAN, utiliser l'Option B (Documenter et déplacer vers `examples/`)

---

## Résumé des décisions

| Décision | Recommandation | Justification | Impact | Temps |
|-----------|---------------|---------------|--------|-------|
| **P1-1** | Option C — Documenter `runtime/` et `rust/` | Préserve le code, clarifie le statut | Faible | 30min |
| **P1-2** | Option A — Fusionner les doublons | Élimine la confusion, réduit la dette | Moyen | 2-3h |
| **P3-1** | Option C — Cohabitation Go/Python | Migration progressive, préserve les deux | Élevé | 1-2h (doc) |
| **P3-2** | Option A — Supprimer `jarvis-OS/` | Réduit la dette technique | Faible | 10min |

---

## Procédure de validation

### Avant toute décision

```bash
# 1. Sauvegarder l'état actuel
git tag -a pre-architecture-decisions-$(date +%Y%m%d) -m "Before P1/P3 architecture decisions"

# 2. Vérifier les tests
./ethan python3 -c "import core; import sdk; import plugins; print('OK')"

# 3. Vérifier le démarrage
./ethan up
./ethan status
./ethan down
```

### Après chaque décision

```bash
# 1. Tester les imports
./ethan python3 -c "import core; print('OK')"

# 2. Tester le démarrage
./ethan up
./ethan status
./ethan down

# 3. Commit avec message clair
git commit -m "docs/refactor: [décision] - [raison courte]"
```

---

## Support

- **Guide P1** : `docs/implementation-guide-P1.md`
- **Guide P3** : `docs/implementation-guide-P3.md`
- **Roadmap P1** : `docs/roadmap-P1.md`
- **Roadmap P3** : `docs/roadmap-P3.md`
- **Roadmap globale** : `docs/roadmap-global.md`

---

## Prochaines étapes

1. **Architecture Team** : Réunir pour valider ces recommandations
2. **Implémenter P1-1** : Documenter `runtime/` et `rust/` (30min)
3. **Implémenter P1-2** : Fusionner les doublons (2-3h)
4. **Implémenter P3-1** : Clarifier Go/Python (1-2h)
5. **Implémenter P3-2** : Supprimer `jarvis-OS/` (10min)

**Deadline** : 2026-07-26 pour P1-1 et P1-2  
**Deadline** : 2026-08-02 pour P3-1 et P3-2

---

**Document préparé par** : Principal Software Architect  
**Date** : 2026-07-19  
**Révision** : 1.0