# Réunion Architecture — Décisions en attente

**Date** : 2026-07-19  
**Réunion** : Architecture Team  
**Durée estimée** : 30min  
**Préparé par** : Principal Software Architect

---

## Ordre du jour

```
┌─────────────────────────────────────────────────────────────┐
│              Décisions Architecture — Réunion               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. P1-1 : Sort de runtime/ et rust/ (5min)                │
│  2. P1-2 : Doublons orchestration/ vs orchestrator/ (10min)│
│  3. P3-1 : Stratégie Go vs Python pour Core (10min)        │
│  4. P3-2 : Sort de jarvis-OS/ (5min)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Contexte

L'audit d'architecture ETHAN (voir `architecture-audit.md`) a identifié 17 actions correctives organisées en 4 priorités.

**4 actions nécessitent une décision architecturale**avant le 2026-08-02 :

| ID | Priorité | Décision requise | Deadline |
|----|----------|------------------|----------|
| P1-1 | Important | Sort de `runtime/` et `rust/` | 2026-07-26 |
| P1-2 | Important | Doublons `orchestration/` vs `orchestrator/` | 2026-07-26 |
| P3-1 | Optimisation | Stratégie Go vs Python pour Core | 2026-08-02 |
| P3-2 | Optimisation | Sort de `jarvis-OS/` | 2026-08-02 |

---

## Décision 1 : P1-1 — Sort de `runtime/` et `rust/`

### Situation actuelle

```
runtime/ — Dossier Go séparé, aucun lien avec core/
rust/ — Crates Rust isolées (whisper, etc.)
```

**Constat** :
- Aucun import détecté dans `core/`, `plugins/`, `interfaces/`
- Non référencés dans `docker-compose.yml`
- Aucune documentation
- Code mort potentiel

### Options

#### Option A : Supprimer
**Avantages** :
- Simplifie le projet
- Élimine la confusion
- Réduit la dette technique

**Inconvénients** :
- Perte de code potentiellement fonctionnel
- Irréversible sans git tag

**Quand** : Si aucune dépendance détectée

---

#### Option B : Intégrer
**Avantages** :
- Préserve le code
- Migration progressive possible

**Inconvénients** :
- Complexifie l'architecture
- Mélange des responsabilités

**Quand** : Si code fonctionnel à réutiliser

---

#### Option C : Documenter et isoler *(recommandé)*
**Avantages** :
- Préserve le code
- Clarifie le statut
- Aucun risque

**Inconvénients** :
- N'élimine pas la dette technique
- Demande de la maintenance

**Quand** : Si code conservé pour référence future

---

### Recommandation

**Option C** — Documenter et isoler

**Raison** : Préserve le travail existant sans risquer de casser des dépendances cachées.

**Actions** (30min) :
1. Créer `runtime/README.md` (legacy, non utilisé)
2. Créer `rust/README.md` (crates Rust, statut à clarifier)
3. Commit : `docs: add README to runtime/ and rust/`

---

### Vote requis

- [ ] **Accepter recommandation** (Option C)
- [ ] **Option A** — Supprimer
- [ ] **Option B** — Intégrer
- [ ] **À revoir** — Besoin d'analyse complémentaire

---

## Décision 2 : P1-2 — Doublons `orchestration/` vs `orchestrator/`

### Situation actuelle

```
core/orchestration/ — Outils d'orchestration (potentiellement vide)
core/orchestrator/ — Orchestrateur principal
core/registry/module.py — Helpers (potentiellement)
core/registry/module_registry.py — Registry principal
```

**Constat** :
- Deux dossiers/fichiers avec rôles similaires
- Risque de confusion élevé
- Possible doublon de code

### Options

#### Option A : Fusionner *(recommandé)*
**Avantages** :
- Code unique
- Pas de confusion
- Réduit la dette technique

**Inconvénients** :
- Risque de régression modéré
- Nécessite tests d'imports

**Quand** : Si rôles similaires confirmés

---

#### Option B : Renommer et clarifier
**Avantages** :
- Préserve les deux
- Clarifie les rôles

**Inconvénients** :
- Toujours deux fichiers
- Demande de la documentation

**Quand** : Si rôles différents

---

#### Option C : Supprimer le doublon
**Avantages** :
- Simplifie
- Élimine la confusion

**Inconvénients** :
- Perte de code
- Risque de casser des imports

**Quand** : Si un seul est utilisé

---

### Recommandation

**Option A** — Fusionner

**Raison** : Un seul fichier/dossier par responsabilité = architecture plus claire.

**Actions** (2-3h) :
1. Sauvegarder `core/orchestrator/` et `core/registry/module_registry.py`
2. Vérifier les imports (quel fichier est utilisé)
3. Fusionner dans le fichier le plus utilisé
4. Mettre à jour tous les imports
5. Tester : `./ethan python3 -c "from core.orchestrator import *"`
6. Tester démarrage : `./ethan up && ./ethan status`
7. Commit : `refactor: merge duplicate orchestration/ and registry/ modules`

**Validation** :
```bash
# Tests imports
./ethan python3 -c "import core.orchestrator; print('OK')"
./ethan python3 -c "import core.registry.module_registry; print('OK')"

# Tests démarrage
./ethan up
./ethan status
./ethan down
```

---

### Vote requis

- [ ] **Accepter recommandation** (Option A — Fusionner)
- [ ] **Option B** — Renommer et clarifier
- [ ] **Option C** — Supprimer le doublon
- [ ] **À revoir** — Besoin d'analyse complémentaire

---

## Décision 3 : P3-1 — Stratégie Go vs Python pour Core

### Situation actuelle

```
core/
├── main.go      # Entrypoint Go (théorique, jamais utilisé)
├── go.mod       # Module Go (jamais compilé)
├── kernel.py    # Kernel Python (réel, utilisé par Docker)
├── bootstrap.py # Bootstrap Python (utilisé)
└── main.py      # Entrypoint Python (utilisé)
```

**Constat** :
- Dualité Go/Python source de confusion
- `docker-compose.yml` utilise Python (`python kernel/bootstrap.py`)
- `core/main.go` existe mais n'est pas référencé
- Systemd mentionne `/opt/ethan/bin/ethan-core` (Go compilé ?)

**Performances** :
- Python : flexible, écosystème riche, mais plus lent
- Go : performant, compilation statique, mais migration coûteuse

### Options

#### Option A : Tout migrer vers Python
**Avantages** :
- Cohérence du codebase
- Meilleure maintenabilité
- Écosystème Python riche

**Inconvénients** :
- Perte performances Go
- Migration importante

**Quand** : Si performance Go non critique

---

#### Option B : Tout migrer vers Go
**Avantages** :
- Performance
- Compilation statique
- Meilleur pour daemon systemd

**Inconvénients** :
- Migration très importante (semaines)
- Perte flexibilité Python
- Réécriture complète des modules

**Quand** : Si performance critique

---

#### Option C : Cohabitation *(recommandé)*
**Avantages** :
- Préserve le code existant
- Migration progressive possible
- Meilleur des deux mondes

**Inconvénients** :
- Dualité maintenue
- Complexité accrue

**Quand** : Si on veut préserver les deux à court terme

---

### Recommandation

**Option C** — Cohabitation (migration progressive)

**Raison** :
- Migrer entièrement vers Go demanderait des semaines
- Migrer entièrement vers Python perdrait la performance Go
- La cohabitation permet une migration progressive

**Architecture cible** :

```
┌─────────────────────────────────────────┐
│  Go Kernel (performance)                │
│  - Event routing                        │
│  - Request/Reply                        │
│  - High-throughput processing           │
│  core/kernel-go/                        │
│    main.go                              │
│    go.mod                               │
└─────────────────────────────────────────┘
           │
           │ NATS / gRPC
           │
┌─────────────────────────────────────────┐
│  Python Kernel (cognitive)              │
│  - Business logic                       │
│  - Module coordination                  │
│  - LLM integration                      │
│  core/                                  │
│    kernel.py                            │
│    bootstrap.py                         │
│    main.py                              │
└─────────────────────────────────────────┘
```

**Actions** (1-2h) :
1. Créer `core/kernel-go/` et déplacer `core/main.go` + `core/go.mod`
2. Créer `core/kernel-go/README.md` (rôle, compilation, tests)
3. Créer `docs/kernel-go-python-interface.md` (interface)
4. Commit : `docs: clarify Go/Python kernel cohabitation strategy`

**Validation** :
```bash
# Vérifier que Python fonctionne toujours
./ethan up
./ethan status
./ethan down

# Compiler Go (si nécessaire)
cd core/kernel-go && go build -o /tmp/ethan-core main.go
```

**Note** : Cette décision ne change PAS le fonctionnement actuel. Elle clarifie seulement la stratégie à long terme.

---

### Vote requis

- [ ] **Accepter recommandation** (Option C — Cohabitation)
- [ ] **Option A** — Tout migrer vers Python
- [ ] **Option B** — Tout migrer vers Go
- [ ] **À revoir** — Besoin d'analyse complémentaire (performances, ressources)

---

## Décision 4 : P3-2 — Sort de `jarvis-OS/`

### Situation actuelle

```
jarvis-OS/ — Dossier à la racine, nature inconnue
```

**Constat** :
- Présent à la racine du projet ETHAN
- Aucun import détecté dans `core/`, `plugins/`, `interfaces/`
- Aucune mention dans la documentation
- Nature inconnue (legacy ? projet lié ? monorepo ?)

### Options

#### Option A : Supprimer *(recommandé)*
**Avantages** :
- Réduit la dette technique
- Simplifie le repository
- Élimine la confusion

**Inconvénients** :
- Irréversible sans git tag
- Perte de code si jamais utilisé

**Quand** : Si legacy/projet externe

---

#### Option B : Documenter et déplacer vers `examples/`
**Avantages** :
- Préserve le code
- Clarifie la relation avec ETHAN

**Inconvénients** :
- Mélange des projets
- Demande de la maintenance

**Quand** : Si projet lié à ETHAN

---

#### Option C : Documenter comme projet séparé
**Avantages** :
- Clarifie la séparation
- Préserve le code

**Inconvénients** :
- Complexifie le repo
- Demande de la maintenance

**Quand** : Si monorepo intentionnel

---

### Recommandation

**Option A** — Supprimer (si legacy)

**Raison** : Si c'est un ancien projet intégré par erreur, il faut le supprimer pour réduire la dette technique.

**Actions** (10min) :
1. Créer un tag git : `git tag -a legacy-jarvis-YYYYMMDD -m "Legacy jarvis-OS before removal"`
2. Supprimer `jarvis-OS/`
3. Ajouter à `.gitignore`
4. Commit : `chore: remove legacy jarvis-OS directory`

**Alternative** : Si `jarvis-OS/` est lié à ETHAN, utiliser Option B (Documenter et déplacer vers `examples/`)

---

### Vote requis

- [ ] **Accepter recommandation** (Option A — Supprimer)
- [ ] **Option B** — Documenter et déplacer vers `examples/`
- [ ] **Option C** — Documenter comme projet séparé
- [ ] **À revoir** — Besoin d'analyse du contenu de `jarvis-OS/`

---

## Vote et validation

### Processus de vote

Pour chaque décision, l'Architecture Team doit :

1. **Discuter** (5min par décision)
2. **Voter** : Acceptation, Rejet, ou À revoir
3. **Valider** : Si accepté, implémenter dans les 48h

### Validation post-décision

```bash
# 1. Tester les imports
./ethan python3 -c "import core; import sdk; import plugins; print('OK')"

# 2. Tester le démarrage
./ethan up
./ethan status
./ethan down

# 3. Commit
git commit -m "docs/refactor: [décision] - [raison courte]"
```

---

## Actions immédiates post-réunion

### Si toutes les décisions sont acceptées

**P1-1** (30min) :
```bash
# Créer les README
cat > runtime/README.md << 'EOF'
# Runtime (Legacy)
⚠️ Conservé pour référence uniquement.
EOF

cat > rust/README.md << 'EOF'
# Rust Crates (Legacy)
⚠️ Crates Rust potentiellement fonctionnelles.
EOF

git add -A && git commit -m "docs: clarify runtime/ and rust/ status"
```

**P1-2** (2-3h) :
```bash
# Fusionner les doublons (voir implementation-guide-P1.md)
./ethan python3 -c "from core.orchestrator import *; print('OK')"
git add -A && git commit -m "refactor: merge duplicate modules"
```

**P3-1** (1-2h) :
```bash
# Clarifier Go/Python
mkdir -p core/kernel-go
mv core/main.go core/kernel-go/
mv core/go.mod core/kernel-go/

cat > core/kernel-go/README.md << 'EOF'
# Kernel Go — Performance Layer
⚠️ Non prêt pour la production. Python reste principal.
EOF

git add -A && git commit -m "docs: clarify Go/Python cohabitation"
```

**P3-2** (10min) :
```bash
# Supprimer jarvis-OS/
git tag -a legacy-jarvis-$(date +%Y%m%d) -m "Legacy jarvis-OS"
rm -rf jarvis-OS/
echo "jarvis-OS/" >> .gitignore
git add -A && git commit -m "chore: remove legacy jarvis-OS"
```

---

## Support

- **Recommandations détaillées** : `docs/architecture-decisions.md`
- **Guides d'implémentation** : `docs/implementation-guide-P1.md`, `docs/implementation-guide-P3.md`
- **Audit complet** : `docs/architecture-audit.md`
- **Roadmap globale** : `docs/roadmap-global.md`

---

## Notes de réunion

*À remplir pendant la réunion*

**Présents** :
- [ ] Architecture Team
- [ ] CTO
- [ ] Équipe Core
- [ ] Équipe DevOps

**Décisions prises** :

1. P1-1 : [Accepté / Rejeté / À revoir]
   - *Notes* :

2. P1-2 : [Accepté / Rejeté / À revoir]
   - *Notes* :

3. P3-1 : [Accepté / Rejeté / À revoir]
   - *Notes* :

4. P3-2 : [Accepté / Rejeté / À revoyer]
   - *Notes* :

**Actions post-réunion** :
- [ ] P1-1 : Implémenté par [nom] — Deadline [date]
- [ ] P1-2 : Implémenté par [nom] — Deadline [date]
- [ ] P3-1 : Implémenté par [nom] — Deadline [date]
- [ ] P3-2 : Implémenté par [nom] — Deadline [date]

**Prochaine réunion** : [date]

---


**Document préparé par** : Principal Software Architect  
**Date** : 2026-07-19  
**Révision** : 1.0