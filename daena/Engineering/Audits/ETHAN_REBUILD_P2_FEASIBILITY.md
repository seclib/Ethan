# ETHAN — Rapport de faisabilité P2 (fork WebUI isolé Open WebUI v0.9.1)

- **Date** : 2026-10-29
- **Branche ETHAN** : `refactor/ethan-rebuild-p0`
- **Candidat** : `/home/fatsio/AI/Ethan/rebuild/webui-candidate` (worktree Git détaché)
- **Provenance** :
  - source : `/home/fatsio/AI/Ethan/examples/open-webui`
  - remote : `https://github.com/open-webui/open-webui`
  - tag : `v0.9.1`
  - commit : `0a8a620fb6fd4c914494f56ac06475bd5f95a985`
  - licence : Open WebUI License + historique MIT/BSD ; clause de marque restrictive
  - notices : `LICENSE`, `LICENSE_HISTORY`, `LICENSE_NOTICE` préservées

## 1. Conditions respectées

- Aucun clone par-dessus ETHAN (worktree dédié sous racine ETHAN).
- Aucun volume/secret de production utilisé; `DATA_DIR=/tmp/ethan-openwebui-test-data`, secret éphémère marqué de test.
- Port 3001 non utilisé; aucune tentative de service réseau public n'a réussi dans le sandbox (binding TCP refusé), donc aucun port candidat n'a été consommé.
- Ollama hôte non réinstallé; tentative de démarrage sans changement d'Ollama; non joignable dans ce sandbox.

## 2. Commandes exécutées et résultats

1. Vérification environnement :
   - `git status --short`, `git worktree list`
   - `df -h` : espace disponible ~132G sur `/home/fatsio/AI/Ethan`.
2. Création worktree propre :
   - `git -C examples/open-webui worktree add --detach /home/fatsio/AI/Ethan/rebuild/webui-candidate v0.9.1`
   - résultat : HEAD `0a8a620fb`, status court vide au moment de la création.
3. Build frontend :
   - dépendances runtime front réutilisées par lien symbolique vers `/home/fatsio/AI/ethan-webui-fork/node_modules` (lecture seule).
   - commande : `cd rebuild/webui-candidate && ./node_modules/.bin/vite build`
   - résultat : succ ès (`✓ built in 1m 21s`, site wrote `build`).
4. Import backend :
   - `PYTHONPATH=.../candidate/backend:.../.venv/... python -c 'import open_webui.main; print("IMPORT_OK")'`
   - résultat : `IMPORT_OK` (migrations SQLite appliquées localement dans `/tmp/ethan-openwebui-test-data`).
5. Tentatives non complètes / limites :
   - `npm run check` dans l'ancien fork bloqué en écriture dans `.svelte-kit` (montage ro) — contourné par build direct.
   - `npm run pyodide:fetch` a échoué réseau (pypi.org DNS).
   - In-process `TestClient` / marche `/health` n'a pas abouti dans les délais car l'application tente de charger un modèle d'embedding distant; tentatives d'annulation avec Ctrl-C.
   - Démarrage réseau réel bloqué par seccomp (`PermissionError: Operation not permitted` pour bind).
   - Ollama non joignable dans ce sandbox.

## 3. Vérification authentification et routes

- Import et migration backend ont réussi (`IMPORT_OK`), ce qui valide la cohérence minimale du socle.
- Pas de vérification HTTP complète dans cet environnement (pas de bind, réseau restreint).
- L'auth frontend/backend n'a pas été exercée en navigateur (limitation sandbox).
- Tests disponibles upstream non exécutés ici pour limiter coût et risque; à lancer en CI ou hôte autorisé.

## 4. Analyse de personnalisation et écarts ETHAN

- Stack SvelteKit vs WebUI ETHAN actuelle en Next.js/React: migration complète à budgéter.
- Backend Open WebUI doit être remplacé/proxifié par API ETHAN pour respecter AGENTS.md.
- Assets et frontend sont riches et buildables sans erreur.
- Licence: clause de marque reste bloquante pour un produit ETHAN rebrandé.
- Dépendances lourdes: Python 3.11-3.12 seulement; PyTorch/ML libraries et téléchargements à gérer hors ligne.
- Multiples modèles/embeddings par défaut créent des dépendances réseau.

## 5. Verdict

Socle Open WebUI v0.9.1 est réellement buildable en isolation et son backend importable. La faisabilité technique du frontend existe. La bascule de marque et d'API reste bloquée par des décisions non résolues (licence + contrats + environnement réseau).

## 6. Prochaines actions

- Lancer `npm run check` et tests upstream sur hôte réseau autorisé.
- Évaluer backend shim vs adaptation API.
- Maintenir worktree clean; ne pas transformer avant décision D-01.
