# Correction PYTHONPATH — Import `core.kernel`

## Problème

L'import `core.kernel` échouait lorsqu'on exécutait :

```bash
python3 -c "import core.kernel"
```

ou via le launcher ETHAN sans configuration manuelle de l'environnement.

### Symptômes

```
ImportError: No module named 'core'
```

ou

```
ModuleNotFoundError: No module named 'core.kernel'
```

### Cause racine

1. Le projet ETHAN n'est pas installé en mode éditable (`pip install -e .`)
2. Le launcher `./ethan` ne configurait pas le `PYTHONPATH`
3. Python ne trouvait pas les modules `core`, `sdk`, `plugins`, `runtime` situés à la racine du projet

Les seuls fichiers qui ajoutaient la racine au `sys.path` étaient :
- `core/main.py` (ligne 11)
- `core/bootstrap.py` (ligne 11)

Mais ces ajustements ne s'appliquaient que lorsqu'on importait directement ces fichiers.

## Solution

### Modification du launcher `ethan`

Le fichier `ethan` (racine du projet) configure maintenant automatiquement le `PYTHONPATH` :

```bash
export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"
```

**Ligne ajoutée :**
```bash
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"
```

Cette ligne est ajoutée juste après la définition de `ETHAN_ROOT`, avant l'execution de toute commande.

### Effet

Toutes les commandes exécutées via `./ethan <commande>` héritent maintenant du `PYTHONPATH` configuré :

- ✅ `./ethan cli` → peut importer `core.kernel`
- ✅ `./ethan doctor` → vérifie les imports Python avec succès
- ✅ `./ethan api` → l'API peut importer tous les modules
- ✅ `./ethan webui` → le frontend peut importer les modules Python si nécessaire

## Vérification

### Test 1 : Import direct via le launcher

```bash
cd /home/fatsio/AI/Ethan
./ethan python3 -c "import core.kernel; print('SUCCESS')"
```

**Résultat attendu :**
```
SUCCESS
```

### Test 2 : Doctor

```bash
./ethan doctor
```

**Résultat attendu :**
```
◆ 2. Imports Python
  ✓ core importable
  ✓ core.kernel importable (CognitiveKernel trouvé)
  ✓ sdk importable
  ✓ runtime importable
  ✓ plugins importable
```

### Test 3 : Python depuis la racine (avec PYTHONPATH)

```bash
cd /home/fatsio/AI/Ethan
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 -c "import core.kernel; print('SUCCESS')"
```

**Résultat attendu :**
```
SUCCESS
```

## Impact

### Avant

```bash
$ python3 -c "import core.kernel"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'core'
```

**Solution temporaire requise :**
```bash
export PYTHONPATH="/home/fatsio/AI/Ethan:$PYTHONPATH"
```

### Après

```bash
$ ./ethan doctor
◆ 2. Imports Python
  ✓ core importable
  ✓ core.kernel importable (CognitiveKernel trouvé)
  ...
```

**Aucune configuration manuelle requise.**

## Fichiers modifiés

| Fichier | Modification | Raison |
|---------|--------------|--------|
| `ethan` | Ajout de `export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"` | Configurer automatiquement le chemin Python pour toutes les commandes |

## Conception

### Pourquoi modifier le launcher plutôt qu'installer le package ?

| Approche | Avantages | Inconvénients |
|----------|-----------|---------------|
| **Launcher** (choisie) | ✅ Zéro configuration manuelle<br>✅ Fonctionne immédiatement après `git clone`<br>✅ Pas d'étape d'installation supplémentaire<br>✅ Idempotent (réexécutable) | Négligeable |
| `pip install -e .` | ✅ Standard Python | ❌ Requiert une étape d'installation<br>❌ Peut échouer si dépendances build manquantes<br>❌ Couplage fort avec l'environnement système |
| `.pth` dans site-packages | ✅ Permanent | ❌ Dépend du virtualenv<br>❌ Modification du système Python<br>❌ Casse le principe "portable" |

### Pourquoi `${PYTHONPATH:-}` ?

La syntaxe `${PYTHONPATH:-}` utilise une valeur par défaut vide si `PYTHONPATH` n'est pas défini. Cela évite l'erreur :

```bash
# Sans :- , si PYTHONPATH est vide :
export PYTHONPATH="${ETHAN_ROOT}:"  # ← PYTHONPATH devient ":"
# Certains interprètes Python peuvent interpréter "" comme un chemin vide

# Avec :- :
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"  # ← Si non défini, ajoute simplement ETHAN_ROOT
```

## Maintenance

### Ajouter une nouvelle commande au launcher

Toutes les commandes héritent automatiquement du `PYTHONPATH`. Aucune modification supplémentaire n'est nécessaire.

### Vérifier que PYTHONPATH est bien configuré

```bash
./ethan doctor | grep PYTHONPATH
```

**Résultat attendu :**
```
✓ PYTHONPATH défini : /home/fatsio/AI/Ethan:
```

## Notes techniques

- La modification est **rétrocompatible** : si `PYTHONPATH` était déjà configuré, il est préservé
- Le launcher utilise `export` pour propager la variable aux processus enfants (`exec`)
- La modification est effectuée une seule fois au démarrage du launcher, avant l'`exec` de la commande

## FAQ

**Q : Pourquoi ne pas utiliser des imports relatifs (`from .kernel import ...`) ?**

R : Les imports relatifs nécessitent que le package soit installé ou que le module soit importé depuis l'intérieur du package. Cela complexifie les tests et le développement interactif.

**Q : Est-ce que ça casse l'installation système si ETHAN est installé via pip ?**

R : Non. Si ETHAN est installé via `pip install -e .` ou `pip install .`, les modules sont déjà dans `site-packages`. Le `PYTHONPATH` ajoute un chemin supplémentaire qui sera ignoré si le package est déjà trouvé dans `site-packages`.

**Q : Pourquoi ne pas utiliser un fichier `.env` ?**

R : Les fichiers `.env` nécessitent un outil supplémentaire (`python-dotenv` ou similaire). Le launcher bash est déjà la méthode standard pour configurer l'environnement ETHAN. Ajouter une ligne bash est plus simple et plus cohérent.

**Q : Est-ce que ça fonctionne sous Windows ?**

R : Le launcher `ethan` est un script bash. Sous Windows, il faut utiliser WSL, Git Bash, ou Cygwin. Pour un support natif Windows, un fichier `ethan.bat` ou `ethan.ps1` serait nécessaire (hors périmètre actuel).