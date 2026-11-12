# Mission 09 — Phase G — Corrections et validation

**Date** : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`.

## 1. ANOM-09-06 — DAĒNĀ read-write mount

### Diagnostic initial
- Conteneur `ethan-api` montait `/home/fatsio/AI/Ethan:/home/fatsio/AI/Ethan:ro`.
- Le répertoire `daena/` était en lecture seule dans le conteneur.
- `docker exec ethan-api touch .../daena/test` → "Read-only file system".

### Cause racine
Montage Docker en mode read-only (`:ro`) sur l'ensemble du dépôt, incluant `daena/`.

### Correction appliquée
1. Ajout d'un montage dédié dans `docker-compose.yml` :
   ```
   - /home/fatsio/AI/Ethan/daena:/home/fatsio/AI/Ethan/daena:rw
   ```
   (le montage principal reste `:ro` — principe du moindre privilège).
2. Changement de propriété hôte : `sudo chown -R 10001:999 daena` (utilisateur ethan du conteneur, groupe ethan).

### Preuves avant/après
- Avant : `touch` → "Read-only file system".
- Après : `touch` → "WRITE OK", cleanup → "CLEANUP OK".

### Tests réels
- `memory vault-write "test-m09.md" "# Test M09"` → exit 0, fichier créé.
- `memory vault-file "test-m09.md"` → exit 0, contenu vérifié.
- `memory record '{"id":"EVT-TEST-M09",...}'` → exit 0, record créé.
- Nettoyage : `sudo rm` des deux fichiers de test. Vérifié : aucun fichier `*test-m09*` restant.

### Risques résiduels
- Le montage `:rw` expose `daena/` en écriture au conteneur. Le principe du moindre privilège est respecté (seul `daena/` est en écriture, le reste du dépôt reste `:ro`).
- Le chown récursif a changé la propriété de tous les fichiers daena/ de `fatsio:fatsio` (1000:1000) à `ethan:ethan` (10001:999). C'est une modification de propriété hôte.

## 2. ANOM-09-07 — Timeout Application

### Diagnostic initial
`application start odin` dépassait le timeout par défaut de 5 s (exit 7).

### Correction appliquée
Ajout de `timeout=30.0` aux appels `api_post` dans `_start()` et `_stop()` (`interfaces/cli/commands/application.py`).

### Preuves avant/après
- Avant : exit 7 (TIMEOUT) à 5s.
- Après : exit 0 sans `--timeout`.

### Tests réels
- `ethan application start odin` (sans --timeout) → exit 0.
- `ethan application stop odin` (sans --timeout) → exit 0.

## 3. Validations

| Contrôle | Résultat |
|---|---|
| `pytest tests/cli/ethan -q` | **637 passed**, 0 échec |
| `ruff check interfaces/cli` | **All checks passed!** |
| `lint-imports` | **5 kept, 0 broken** |

## 4. Anomalies restantes

- **ANOM-09-03** : serveur REA mal configuré (URL GitHub). Correction opérationnelle requise par l'opérateur.

## 5. Fichiers modifiés

- `docker-compose.yml` — montage daena en read-write
- `interfaces/cli/commands/application.py` — timeout 30s pour start/stop
- Propriété hôte : `daena/` → `ethan:ethan` (10001:999)

## 6. État Git

- Branche : `refactor/ethan-rebuild-p0`
- HEAD : `57e254b0 canvas`
- Aucun commit effectué
- 170 entrées non commitées
