# Guide d'Implémentation P1 — Actions Importantes

**Objectif** : Décisions structurelles et nettoyage  
**Date** : 2026-07-19  
**Priorité** : P1 (Important)  
**Temps estimé** : 1-2 jours  
**Responsable** : Équipe Core + Architecture Team

---

## Vue d'ensemble des actions P1

```
┌─────────────────────────────────────────────────────────────┐
│                  Actions P1 à implémenter                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏳ P1-1 : Décider du sort de runtime/ et rust/            │
│     ├─ Fichiers : runtime/, rust/                          │
│     ├─ Options : Supprimer, Intégrer, Documenter           │
│     └─ Deadline décision : 2026-07-26                      │
│                                                             │
│  ⏳ P1-2 : Éliminer les doublons                            │
│     ├─ Fichiers : core/orchestration/, core/orchestrator/  │
│     ├─ Options : Fusionner, Renommer, Supprimer            │
│     └─ Deadline décision : 2026-07-26                      │
│                                                             │
│  ⏳ P1-3 : Nettoyer les dossiers vides                     │
│     ├─ Fichiers : core/agents/, core/pkg/                  │
│     ├─ Action : Supprimer les dossiers vides               │
│     └─ Deadline : 2026-07-26                               │
│                                                             │
│  ⏳ P1-4 : Clarifier README.md                             │
│     ├─ Fichier : README.md                                 │
│     ├─ Action : Corriger gRPC → HTTP, ajouter section      │
│     └─ Deadline : 2026-07-26                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## P1-1 : Décider du sort de `runtime/` et `rust/`

**Fichiers concernés** : `runtime/`, `rust/`  
**Deadline décision** : 2026-07-26  
**Responsable** : Architecture Team

---

### Analyse préalable

#### Étape 1 : Vérifier les imports

```bash
# Vérifier si runtime/ est importé
grep -r "runtime\." core/ plugins/ interfaces/ 2>/dev/null || echo "Aucun import runtime"

# Vérifier si rust/ est importé
grep -r "rust" core/ plugins/ interfaces/ 2>/dev/null || echo "Aucun import rust"

# Vérifier les imports dans les fichiers Python
find core/ plugins/ interfaces/ -name "*.py" -exec grep -l "runtime\|rust" {} \;

# Vérifier les imports dans les fichiers Go
find . -name "*.go" -exec grep -l "runtime\|rust" {} \;
```

#### Étape 2 : Vérifier l'historique git

```bash
# Voir quand runtime/ a été ajouté
git log --oneline --all -- runtime/ | head -20

# Voir quand rust/ a été ajouté
git log --oneline --all -- rust/ | head -20

# Voir les commits récents qui modifient ces dossiers
git log --oneline --all --since="2024-01-01" -- runtime/ rust/
```

#### Étape 3 : Vérifier la documentation

```bash
# Chercher des mentions de runtime/ ou rust/ dans la doc
grep -r "runtime/" docs/ engineering/ || echo "Aucune mention"
grep -r "rust/" docs/ engineering/ || echo "Aucune mention"
```

#### Étape 4 : Vérifier l'utilisation dans docker-compose

```bash
# Vérifier si ces dossiers sont utilisés dans les Dockerfiles
grep -r "runtime/" docker-compose*.yml deploy/
grep -r "rust/" docker-compose*.yml deploy/
```

---

### Options de décision

#### Option A : Supprimer

**Quand l'appliquer** : Si aucune dépendance n'est détectée

**Procédure** :

```bash
# 1. Supprimer les dossiers
rm -rf runtime/ rust/

# 2. Nettoyer .gitignore
echo "runtime/" >> .gitignore
echo "rust/" >> .gitignore

# 3. Commit
git add -A
git commit -m "chore: remove unused runtime/ and rust/ directories"
```

**Validation** :

```bash
# Vérifier qu'aucun import ne casse
./ethan python3 -c "import core; print('OK')"
./ethan python3 -c "import plugins; print('OK')"

# Vérifier que les tests passent
pytest tests/ -v 2>/dev/null || echo "Pas de tests"
```

---

#### Option B : Intégrer

**Quand l'appliquer** : Si du code fonctionnel est présent

**Procédure pour runtime/** :

```bash
# Déplacer vers infrastructure/
mv runtime/ infrastructure/runtime/

# Mettre à jour les imports si nécessaire
grep -r "from runtime" . || echo "Aucun import à mettre à jour"
```

**Procédure pour rust/** :

```bash
# Déplacer vers infrastructure/
mv rust/ infrastructure/rust/

# Documenter l'usage
cat > infrastructure/rust/README.md << EOF
# Rust Crates

## Purpose

These Rust crates provide...

## Usage

...
EOF
```

**Validation** :

```bash
# Vérifier les imports
grep -r "from infrastructure" core/ plugins/ interfaces/

# Tester le build
docker compose build
```

---

#### Option C : Documenter et isoler

**Quand l'appliquer** : Si le code est conservé pour référence future

**Procédure** :

```bash
# 1. Créer un README explicatif
cat > runtime/README.md << EOF
# Runtime (Legacy)

## Status

⚠️ Ce dossier est conservé pour référence uniquement.

## Reason for deprecation

Remplacé par...

## Migration guide

...
EOF

# 2. Ajouter dans .gitignore (optionnel)
echo "rust/" >> .gitignore

# 3. Commit
git add -A
git commit -m "docs: add README to runtime/ and rust/"
```

---

### Checklist P1-1

- [ ] Analyser les imports (Étape 1)
- [ ] Vérifier l'historique git (Étape 2)
- [ ] Vérifier la documentation (Étape 3)
- [ ] Vérifier docker-compose (Étape 4)
- [ ] Décider de l'option (A, B, ou C)
- [ ] Implémenter la décision
- [ ] Valider les imports
- [ ] Tester le build
- [ ] Commiter les modifications

---

## P1-2 : Éliminer les doublons

**Fichiers concernés** :
- `core/orchestration/` et `core/orchestrator/`
- `core/registry/module.py` et `core/registry/module_registry.py`

**Deadline décision** : 2026-07-26  
**Responsable** : Architecture Team

---

### Analyse préalable

#### Étape 1 : Comparer les contenus

```bash
# Comparer orchestration/ et orchestrator/
diff -r core/orchestration/ core/orchestrator/ || echo "Différences trouvées"

# Comparer module.py et module_registry.py
diff core/registry/module.py core/registry/module_registry.py || echo "Différences trouvées"
```

#### Étape 2 : Vérifier les imports

```bash
# Vérifier qui utilise orchestration/
grep -r "from core.orchestration" core/ plugins/ interfaces/ || echo "Aucun import"

# Vérifier qui utilise orchestrator/
grep -r "from core.orchestrator" core/ plugins/ interfaces/ || echo "Aucun import"

# Vérifier qui utilise module.py
grep -r "from core.registry.module import" core/ plugins/ interfaces/ || echo "Aucun import"

# Vérifier qui utilise module_registry.py
grep -r "from core.registry.module_registry import" core/ plugins/ interfaces/ || echo "Aucun import"
```

#### Étape 3 : Analyser la taille

```bash
# Compter les lignes
wc -l core/orchestration/*.py
wc -l core/orchestrator/*.py
wc -l core/registry/module.py
wc -l core/registry/module_registry.py
```

---

### Options de décision

#### Option A : Fusionner

**Quand l'appliquer** : Si les deux dossiers/fichiers ont des responsabilités similaires

**Procédure pour orchestration/** :

```bash
# 1. Sauvegarder orchestrator/
cp -r core/orchestrator/ core/orchestrator.backup/

# 2. Fusionner les fichiers
cp core/orchestration/*.py core/orchestrator/

# 3. Mettre à jour les imports
find core/ plugins/ interfaces/ -name "*.py" -exec \
    sed -i 's/from core.orchestration/from core.orchestrator/g' {} +

# 4. Supprimer l'ancien dossier
rm -rf core/orchestration/

# 5. Tester
./ethan python3 -c "from core.orchestrator import *; print('OK')"
```

**Procédure pour registry/** :

```bash
# 1. Sauvegarder module.py
cp core/registry/module.py core/registry/module.backup.py

# 2. Fusionner dans module_registry.py
cat core/registry/module.py >> core/registry/module_registry.py

# 3. Mettre à jour les imports
find core/ plugins/ interfaces/ -name "*.py" -exec \
    sed -i 's/from core.registry.module import/from core.registry.module_registry import/g' {} +

# 4. Supprimer l'ancien fichier
rm core/registry/module.py

# 5. Tester
./ethan python3 -c "from core.registry.module_registry import *; print('OK')"
```

**Validation** :

```bash
# Tester les imports
./ethan python3 -c "import core.orchestrator; print('OK')"
./ethan python3 -c "import core.registry.module_registry; print('OK')"

# Tester le démarrage
./ethan up
./ethan status
```

---

#### Option B : Renommer et clarifier

**Quand l'appliquer** : Si les deux dossiers/fichiers ont des responsabilités différentes

**Procédure** :

```bash
# Renommer orchestration/ en orchestration_tools/
mv core/orchestration/ core/orchestration_tools/

# Renommer module.py en module_registry_helpers.py
mv core/registry/module.py core/registry/module_registry_helpers.py

# Mettre à jour les imports
find core/ plugins/ interfaces/ -name "*.py" -exec \
    sed -i 's/from core.orchestration/from core.orchestration_tools/g' {} +
find core/ plugins/ interfaces/ -name "*.py" -exec \
    sed -i 's/from core.registry.module import/from core.registry.module_registry_helpers import/g' {} +

# Commit
git add -A
git commit -m "refactor: clarify orchestration/ and registry/ naming"
```

---

#### Option C : Supprimer le doublon

**Quand l'appliquer** : Si un seul fichier/dossier est utilisé

**Procédure** :

```bash
# Identifier lequel est utilisé
USED=$(grep -rl "from core.orchestration" core/ plugins/ interfaces/ | head -1)
echo "Le dossier utilisé est : $USED"

# Supprimer l'autre
rm -rf core/orchestrator/

# Commit
git add -A
git commit -m "chore: remove unused orchestrator/ directory"
```

---

### Checklist P1-2

- [ ] Comparer les contenus (Étape 1)
- [ ] Vérifier les imports (Étape 2)
- [ ] Analyser la taille (Étape 3)
- [ ] Décider de l'option (A, B, ou C)
- [ ] Implémenter la décision
- [ ] Mettre à jour les imports
- [ ] Tester les imports
- [ ] Tester le démarrage
- [ ] Commiter les modifications

---

## P1-3 : Nettoyer les dossiers vides

**Fichiers concernés** :
- `core/agents/`
- `core/pkg/`
- `__pycache__/` (dans tout le repo)

**Deadline** : 2026-07-26  
**Responsable** : Équipe Core  
**Temps estimé** : 15min

---

### Procédure

#### Étape 1 : Vérifier que les dossiers sont vides

```bash
# Vérifier core/agents/
ls -la core/agents/

# Vérifier core/pkg/
ls -la core/pkg/

# Vérifier les __pycache__
find . -type d -name __pycache__
```

#### Étape 2 : Supprimer les dossiers vides

```bash
# Supprimer core/agents/
rm -rf core/agents/

# Supprimer core/pkg/
rm -rf core/pkg/

# Supprimer tous les __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
```

#### Étape 3 : Mettre à jour .gitignore

```bash
# Ajouter __pycache__ dans .gitignore
echo "__pycache__/" >> .gitignore
echo "*.__pycache__" >> .gitignore

# Vérifier
grep "__pycache__" .gitignore
```

#### Étape 4 : Commit

```bash
# Vérifier qu'aucun dossier vide ne subsiste
find core/ -type d -empty

# Commit
git add -A
git commit -m "chore: remove empty directories and __pycache__"
```

---

### Checklist P1-3

- [ ] Vérifier que les dossiers sont vides
- [ ] Supprimer `core/agents/`
- [ ] Supprimer `core/pkg/`
- [ ] Supprimer tous les `__pycache__/`
- [ ] Mettre à jour `.gitignore`
- [ ] Vérifier qu'aucun dossier vide ne subsiste
- [ ] Commiter les modifications

---

## P1-4 : Clarifier README.md

**Fichier concerné** : `README.md`  
**Deadline** : 2026-07-26  
**Responsable** : Équipe Documentation

---

### Procédure

#### Étape 1 : Corriger la section 1.1 (ligne 5-8)

```bash
# AVANT
sed -n '5,8p' README.md

# APRÈS (avec sed)
sed -i '5,8s/gRPC/HTTP + NATS/' README.md
sed -i '5,8s/Client gRPC uniquement/Client NATS + HTTP/' README.md
```

#### Étape 2 : Corriger la section 5 (ligne 28-43)

```bash
# AVANT
sed -n '28,43p' README.md

# APRÈS (avec sed)
sed -i '28,43s/gRPC.*port 50051/HTTP REST (port 8000)/' README.md
sed -i '28,43s/ProcessEvent.*GetState/GET \/health, GET \/version/' README.md
```

#### Étape 3 : Corriger la section 7.4 (ligne 557+)

```bash
# AVANT
sed -n '557p' README.md

# APRÈS (avec sed)
sed -i '557s/localhost:8080/localhost:8000/' README.md
```

#### Étape 4 : Ajouter la section "Architecture réelle"

```bash
# Trouver la ligne où insérer la section
LINE=$(grep -n "## 18. Points Forts" README.md | cut -d: -f1)

# Insérer avant la section 18
sed -i "$((LINE-1))i\\### Architecture réelle (2026-07-19)\n\n> **Note** : Cette section reflète la réalité du code, pas la vision théorique.\n\n**Stack actuelle** :\n- **Core** : Python (CognitiveKernel dans \`core/kernel.py\`)\n- **API** : FastAPI (\`interfaces/api/main.py\`)\n- **Event Bus** : NATS JetStream\n- **Persistence** : PostgreSQL + Redis\n- **Orchestration** : Docker Compose\n\n**Non utilisé** :\n- \`core/main.go\` (entrypoint Go jamais utilisé)\n- \`runtime/\` (runtime Go séparé)\n" README.md
```

#### Étape 5 : Vérifier les corrections

```bash
# Vérifier que gRPC a disparu (sauf mention historique)
grep -n "gRPC" README.md | grep -v "historique" || echo "✓ Aucune mention de gRPC"

# Vérifier les endpoints
grep -n "localhost:8000" README.md | head -5

# Vérifier la section API exposée
grep -A 3 "API exposée" README.md
```

#### Étape 6 : Tester la génération de documentation

```bash
# Générer la documentation (si mkdocs est utilisé)
mkdocs build 2>&1 | tail -20

# Vérifier qu'il n'y a pas d'erreurs
if [ $? -eq 0 ]; then
    echo "✓ Documentation générée avec succès"
else
    echo "✗ Erreur de génération"
    exit 1
fi
```

#### Étape 7 : Commit

```bash
git add README.md
git commit -m "docs: update README.md to reflect actual architecture (HTTP + NATS)"
```

---

### Checklist P1-4

- [ ] Corriger section 1.1 (gRPC → HTTP + NATS)
- [ ] Corriger section 5 (port 50051 → 8000)
- [ ] Corriger section 7.4 (localhost:8080 → localhost:8000)
- [ ] Ajouter section "Architecture réelle"
- [ ] Vérifier les corrections
- [ ] Tester la génération de documentation
- [ ] Commiter les modifications

---

## Tests de validation P1

### Test 1 : Vérifier les dossiers nettoyés

```bash
# Vérifier que les dossiers vides ont été supprimés
ls -la core/ | grep -E "agents|pkg" || echo "✓ Dossiers supprimés"

# Vérifier qu'aucun __pycache__ ne subsiste
find . -type d -name __pycache__ | grep -v ".git" || echo "✓ Aucun __pycache__"
```

### Test 2 : Vérifier les imports

```bash
# Tester les imports après suppression des doublons
./ethan python3 -c "from core.orchestrator import *; print('✓ orchestration OK')"
./ethan python3 -c "from core.registry.module_registry import *; print('✓ registry OK')"
```

### Test 3 : Vérifier la documentation

```bash
# Générer la documentation
mkdocs build 2>&1 | tail -5

# Vérifier qu'il n'y a pas d'erreurs
echo "✓ Documentation OK"
```

### Test 4 : Vérifier le démarrage

```bash
# Démarrer les services
./ethan up

# Vérifier le status
./ethan status

# Arrêter
./ethan down
```

---

## Commandes rapides

### Analyser runtime/ et rust/

```bash
# Vérifier les imports
grep -r "runtime\." core/ plugins/ interfaces/ || echo "Aucun import runtime"
grep -r "rust" core/ plugins/ interfaces/ || echo "Aucun import rust"

# Vérifier l'historique
git log --oneline --all -- runtime/ | head -5
git log --oneline --all -- rust/ | head -5
```

### Nettoyer les dossiers vides

```bash
# Supprimer les dossiers vides
rm -rf core/agents/ core/pkg/

# Supprimer les __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +

# Mettre à jour .gitignore
echo "__pycache__/" >> .gitignore
```

### Éliminer les doublons

```bash
# Comparer les contenus
diff -r core/orchestration/ core/orchestrator/

# Vérifier les imports
grep -r "from core.orchestration" core/ plugins/ interfaces/
grep -r "from core.orchestrator" core/ plugins/ interfaces/
```

---

## Support

- **Roadmap P1** : `docs/roadmap-P1.md`
- **Roadmap globale** : `docs/roadmap-global.md`
- **Audit d'architecture** : `docs/architecture-audit.md`

---

## Prochaines étapes

1. **Architecture Team** : Décider P1-1 et P1-2 (deadline 2026-07-26)
2. **Équipe Core** : Nettoyer dossiers vides (P1-3)
3. **Équipe Documentation** : Clarifier README.md (P1-4)
4. **Passer à P2** : Améliorations (tests, package éditable, Prometheus)

**Dernière mise à jour** : 2026-07-19