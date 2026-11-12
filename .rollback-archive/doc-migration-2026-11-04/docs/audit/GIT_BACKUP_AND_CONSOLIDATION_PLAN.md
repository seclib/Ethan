# ETHAN — Plan de sauvegarde et consolidation Git

## 1. État actuel vérifié

- Branche active : `refactor/ethan-rebuild-p0`.
- Branches locales : `main`, `refactor/ethan-rebuild-p0`.
- Branches distantes : `origin/main`, `origin/refactor/ethan-rebuild-p0`.
- SHA public connu : `9e57d1c0ef...` pour main et refactor/ethan-rebuild-p0.
- Modifications locales : nombreux staged/unstaged/untracked (plus de 200 entrées `git status --short`).
- Références Cline : 646 checkpoints, 14 sessions.
- turn-diffs : 0.
- Stash : 1 (`stash@{0}: On main: audit-pre-refactoring-state`).
- Archives : `Odsidian/` = 98 Mo, 106 fichiers suivis.
- JWT secret, DB password et tokens sont présents dans `.env` (non tracké).
- Nuances : fichiers untracked ont été créés pendant les lots TRUST; la branche actuelle et `main` partagent le SHA public courant.

## 2. Stratégie de sauvegarde proposée

### A. Bundle Git
Exporter un bundle hors commit :
- `git bundle create ethan-backup.bundle --branches --tags refs/cline/checkpoints/* refs/stash`.
- Sauvegarde les références accessibles, mais pas les modifications de worktree non committées.
- Vérification : `git clone ethan-backup.bundle test-repo` et compare `show-ref`.

### B. Archive complete du worktree
Créer un tar.gz (hors `.env`, `.secrets`, node_modules, .venv) du répertoire entier, incluant untracked et les fichiers modifiés.
- Avantage : récupération intégrale des modifications non commitées.
- Limite : dépend de l'exécution depuis le host, sensible à la présence de données privées.

### C. Archives privées
Export isolé de `Odsidian`, logs, `.env` et `.secrets` sous stockage crypté.
- Indispensable pour ne pas exposer les données personnelles.
- Verification : restaurer dans un répertoire réduit et comparer les signatures.

### D. Configuration locale
Sauvegarder `.env`, `.env.example`, clés et variables d’environnement dans un coffre sécurisé, jamais dans Git.

## 3. Périmètre public / privé

### Public ETHAN
- Code source et tests publiables.
- Documentation d'architecture, runbooks.
- Exemples non sensibles.
- Scripts de déploiement publics.

### Privé / sensible
- `Odsidian`
- conversations et archives Cline versionnées.
- logs.
- rapports internes.
- `.env`, `.secrets`, tokens, DB params.
- données de dev locale et caches.

## 4. Fichiers et références à préserver
- branches `main`, `refactor/ethan-rebuild-p0`;
- branches distantes alignées;
- 646 refs Cline;
- stash `audit-pre-refactoring-state`;
- modifications untracked;
- archives `Odsidian`;
- bundles git locate.

## 5. Plan de consolidation sur main sans fusion
1. Classer les modifications actuelles par domaine :
   - auth/trust-service;
   - configuration/compose/env;
   - WebUI cache/node_modules;
   - docs/security/baseline.
2. Vérifier les différences live vs HEAD (sur `git diff main`, staged, unstaged).
3. Décider manuellement des groupes à merger.
4. Créer (avec accord) une nouvelle branche sanitaire à partir de `main` pour intégrer sans conserver `Odsidian`.
5. Garder `refactor/ethan-rebuild-p0` intact comme archive de développement.
6. Ne pas réécrire l'historique de `main` pour le travail déjà publié, sauf décision séparée.

## 6. Découpage proposé des commits
- Commit 1 : variables d'environnement + compose.
- Commit 2 : WebUI login & proxy (sans archive).
- Commit 3 : TRUST-SERVICE isolation & tests.
- Commit 4 : Documentation public (ADR/ESR consolidés).
- Commit 5 : Baseline audit et docs (hors rapports internes).
- Commit 6 : Archives privées déplacées dans storage séparé.

## 7. Risques résiduels
- Pages `Odsidian` déjà suivis par Git et probablement exposés via `main`.
- 646 refs Cline allouent de l'espace objet Git.
- Modifications untracked rendent la repo difficile à comprendre.
- Tentative de rebase/purge risque d'écraser le travail s'il n'est pas d'abord sauvegardé.

## 8. Procédure de restauration
- Bundle plus archive non-chiffrée + références.
- Sources validées et copied before any git modifications.
- Test restore using `git clone --branch`.
- Conserver les secrets hors du bundle public; utiliser un archive chiffré à part.

## 9. Validations préalables
- Lire `.env` pour variables required et ajouter `NEXT_PUBLIC_WS_URL` + `ETHAN_ALLOWED_WS_ORIGINS` into validated local config.
- Run `docker compose config` without interpolation errors.
- Run `pytest` target sets.
- Verify all baseline docs references.
- Confirm `main` published tree includes or excludes archive.

## Recommandation
Attendre une validation humaine. Je recommande de produire d'abord un sauvegarde locale hors commit (bundle + archive), puis d'évaluer la branche sanitaire sans publier automatiquement. N'exécuter aucun push, merge, checkout ou rebase sans approbation explicite.
