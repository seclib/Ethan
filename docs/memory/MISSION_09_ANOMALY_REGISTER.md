# Mission 09 — Registre consolidé des anomalies

**Dépôt** : `/home/fatsio/AI/Ethan`  
**Branche** : `refactor/ethan-rebuild-p0`  
**HEAD** : `57e254b0`  
**Nature** : documentaire et traçabilité uniquement — aucune correction de code.  
**Rapport principal** : `docs/memory/MISSION_09_REAL_CORE_RUNTIME_VALIDATION.md` (phases A, B, C, F, réconciliation d'authentification).  
**Date de consolidation** : 2026-11-11.

---

## 1. Documents consultés

- `docs/memory/MISSION_09_REAL_CORE_RUNTIME_VALIDATION.md` (rapport Mission 09, phases A/B/C/F + réconciliation auth)
- `docs/memory/MISSION_03_PARITY_MATRIX.md` (matrice de parité WebUI/CLI)
- `docs/memory/MISSION_05_PARITY_REPORT.md` (rapport Mission 05)
- `docs/memory/MISSION_06_GLOBAL_PARITY_AUDIT.md` (audit global)
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/DECISIONS.md`
- `daena/Architecture/ETHAN_GLOBAL_PROGRAM/PHASE01_ANOMALY_REGISTER.md` (registre Phase 01, domaines distincts)
- `interfaces/cli/commands/application.py`, `memory.py`, `knowledge.py`, `session.py` (vérification des routes référencées)
- `interfaces/api/routers/application_integration_catalog.py`, `v1.py`, `engineering_memory.py`

## 2. Emplacement choisi

Aucun registre d'anomalies spécifique à la Mission 09 n'existait. Le registre Phase 01 (`daena/.../PHASE01_ANOMALY_REGISTER.md`) concerne des domaines différents (WebUI/API naming, Quantar, composants). Création d'un registre dédié dans `docs/memory/` (même répertoire que les rapports de mission) pour cohérence et traçabilité. Lien bidirectionnel avec le rapport principal Mission 09.

## 3. Registre des anomalies

### ANOM-09-01 — Applications Catalog (route CLI vs API)

- **Titre** : écart de chemin entre CLI et API pour le catalogue d'intégration applicative.
- **Description** : CLI appelle `/v1/application-integration-catalog` (tiret) ; API expose `/v1/application-integration/catalog` (slash).
- **Phase / rapport d'origine** : Phase F (§14.4, anomalie #1) et Phase C (§13.3).
- **Preuves techniques** : `ethan application catalog` → `API 404: Not Found` (exit 6). Vérifié dans `application.py` L124 et `application_integration_catalog.py` L34.
- **Cause** : confirmée — écart de routage (tiret vs slash).
- **Impact CLI** : commande `ethan application catalog` indisponible (404).
- **Priorité** : haute (fonctionnalité d'audit applicatif).
- **Correction envisagée** : aligner le chemin CLI sur l'API (`/v1/application-integration/catalog`) ou ajouter une route alias.
- **Dépendances** : aucune.
- **Tests nécessaires** : test d'intégration `application catalog` avec API réelle ; vérification du statut HTTP 200.
- **Statut** : `FIXED` (2026-11-11)

  **Correction appliquée** : CLI path aligné sur la route API canonique `/v1/application-integration/catalog` (tiret → slash) dans `interfaces/cli/commands/application.py`. Testé : `ethan application catalog` → exit 0, retourne le catalogue (root, sources, repositories).

### ANOM-09-02 — CLI Contract Documentation (CLI_CONTRACT.md absent)

- **Titre** : document de contrat CLI référencé mais absent du dépôt.
- **Description** : `docs/specs/CLI_CONTRACT.md` est référencé dans les commentaires du CLI (`provider.py`, `document.py`, `mcp.py`) mais le fichier n'existe pas.
- **Phase / rapport d'origine** : Phase F (§14.1, §14.4 anomalie #2).
- **Preuves techniques** : `ls docs/specs/CLI_CONTRACT.md` → absent. Références trouvées via grep dans `interfaces/cli/commands/`.
- **Cause** : confirmée — document jamais créé.
- **Impact CLI** : absence de contrat documenté officiel ; les références dans le code pointent vers un fichier inexistant.
- **Priorité** : moyenne (documentation, pas de blocage fonctionnel).
- **Correction envisagée** : créer `docs/specs/CLI_CONTRACT.md` à partir des contrats implicites (exit codes, JSON, HROT, streaming) déjà implémentés et testés.
- **Dépendances** : aucune.
- **Tests nécessaires** : vérification que les références dans le code pointent vers un fichier existant.
- **Statut** : `OPEN`

### ANOM-09-03 — MCP REA Status (statut `error` persistant)

- **Titre** : serveur MCP REA enregistré mais marqué `status=error`, non recalculé en temps réel.
- **Description** : `ToolServerManager.list()` retourne le statut stocké dans CoreRecordStore sans healthcheck. Le statut `error` provient d'une tentative antérieure de `sync_tools` ayant échoué.
- **Phase / rapport d'origine** : Phase C (§13.3) et Phase F (§14.4, anomalie #3).
- **Preuves techniques** : `ethan mcp list` → REA `enabled=yes`, `status=error`. Code : `core/tools/servers.py` L114 (`self._store.list(self._DOMAIN)`), L192-241 (`set_status("connected")` uniquement en cas de succès).
- **Cause** : confirmée — statut persistant, pas de healthcheck temps réel dans `list()`.
- **Impact CLI** : `ethan mcp list` affiche un état potentiellement obsolète ; l'opérateur ne peut pas distinguer un serveur réellement down d'un serveur dont la dernière sync a échoué.
- **Priorité** : moyenne (observabilité).
- **Correction envisagée** : ajouter un healthcheck léger optionnel dans `list()` ou documenter explicitement que le statut reflète la dernière tentative connue.
- **Dépendances** : accès au transport MCP (stdio/HTTP) pour le healthcheck.
- **Tests nécessaires** : test unitaire vérifiant que `list()` reflète un healthcheck frais ; test d'intégration avec serveur MCP down.
- **Statut** : `OPEN` (cause confirmée, correction opérationnelle requise)

  **Cause racine confirmée** : le serveur REA est enregistré avec `url=https://github.com/morluto/rea` (URL GitHub, pas un endpoint MCP) et `transport` non défini (affiché `—`). `sync_tools` a échoué lors de la connexion (URL inaccessible comme endpoint MCP), laissant le statut persistant à `error`. `ToolServerManager.list()` retourne le statut stocké sans healthcheck temps réel. Aucune modification de statut ou de configuration effectuée (contrainte mission : pas de suppression de serveur MCP ni de changement de configuration). Correction requise par l'opérateur : mettre à jour l'URL vers un endpoint MCP valide ou désactiver le serveur.

### ANOM-09-04 — Provider Models Latency (>5s)

- **Titre** : `provider models` dépasse le timeout par défaut de 5 s.
- **Description** : `OllamaProvider.list_models()` interroge `host.docker.internal:11434` via un client httpx avec timeout 300 s. La première requête dépasse 5 s. Aboutit avec `--timeout 15`.
- **Phase / rapport d'origine** : Phase C (§13.2) et Phase F (§14.4, anomalie #4).
- **Preuves techniques** : `provider models ollama` → exit 7 à 5 s, OK à 15 s. Runtime health ollama : 13,1 ms une fois connecté. Code : `core/llm/providers/ollama.py` L157 (`list_models()`), timeout 300 s dans `initialize()`.
- **Cause** : confirmée — dépendance externe (Ollama via Docker host), première requête lente. Non un défaut du CLI.
- **Impact CLI** : commande inutilisable sans `--timeout 15` pour l'opérateur pressé.
- **Priorité** : basse (workaround disponible).
- **Correction envisagée** : augmenter le timeout par défaut de cette commande spécifique (ex. 15 s) ou optimiser la connexion initiale.
- **Dépendances** : Ollama accessible sur `host.docker.internal:11434`.
- **Tests nécessaires** : test de performance avec Ollama réel ; vérification du temps de réponse.
- **Statut** : `FIXED` (2026-11-11)

  **Correction appliquée** : ajout de `timeout=15.0` à l'appel `api_get` dans `provider models` (`interfaces/cli/commands/provider.py`). Vérifié réel : `ethan provider models ollama` → exit 0 sans `--timeout`.

### ANOM-09-05 — RAG Documents Latency (>5s)

- **Titre** : `document list` dépasse le timeout par défaut de 5 s.
- **Description** : `RAGPipeline.list_documents()` → `_ensure_loaded()` → `_load_vector_store()` charge l'index qdrant (6493 chunks indexés), ce qui prend plus de 5 s. Aboutit avec `--timeout 15`.
- **Phase / rapport d'origine** : Phase C (§13.2) et Phase F (§14.4, anomalie #5).
- **Preuves techniques** : `document list` → exit 7 à 5 s, OK à 15 s. `document status` : 6493 chunks, qdrant. Code : `core/rag/pipeline.py` L120 (`_ensure_loaded`), L203 (`_load_vector_store`).
- **Cause** : confirmée — dépendance externe (qdrant) et chargement de l'index. Non un défaut du CLI.
- **Impact CLI** : commande inutilisable sans `--timeout 15`.
- **Priorité** : basse (workaround disponible).
- **Correction envisagée** : mise en cache de l'index chargé ou augmentation du timeout par défaut de cette commande.
- **Dépendances** : qdrant accessible et indexé.
- **Tests nécessaires** : test de performance avec qdrant réel ; vérification du temps de chargement.
- **Statut** : `FIXED` (2026-11-11)

  **Correction appliquée** : ajout de `timeout=15.0` à l'appel `api_get` dans `document list` (`interfaces/cli/commands/document.py`). Vérifié réel : `ethan document list` → exit 0 sans `--timeout`.

---

## 3b. Anomalies supplémentaires découvertes (Phase D)

### ANOM-09-06 — Memory vault read-only (environnement)

- **Titre** : le répertoire `daena/` est monté en lecture seule dans le conteneur API.
- **Description** : `POST /v1/memory/vault/file` retourne 403 (read-only file system). `POST /v1/memory/events` retourne 409 (erreur d'écriture fichier). Bloque les opérations d'écriture mémoire.
- **Phase / rapport d'origine** : Phase D (exécution).
- **Preuves techniques** : `docker exec ethan-api touch /home/fatsio/AI/Ethan/daena/test` → "Read-only file system". Vérifié réel.
- **Cause** : confirmée — montage Docker read-only ou permissions.
- **Impact CLI** : `memory record` et `memory vault-write` inutilisables en environnement Docker.
- **Priorité** : moyenne.
- **Correction envisagée** : changer le volume mount en read-write ou utiliser un stockage alternatif.
- **Statut** : `OPEN`

### ANOM-09-07 — Application start timeout par défaut insuffisant

- **Titre** : `application start` dépasse le timeout par défaut de 5 s.
- **Description** : le démarrage d'un service applicatif (odin) prend plus de 5 s. La commande échoue avec exit 7 (TIMEOUT) sans `--timeout`.
- **Phase / rapport d'origine** : Phase D (exécution).
- **Preuves techniques** : `ethan application start odin` → exit 7 à 5s, OK à 30s.
- **Cause** : confirmée — opération de démarrage longue, timeout par défaut inadapté.
- **Impact CLI** : commande inutilisable sans `--timeout 30`.
- **Priorité** : basse.
- **Correction envisagée** : augmenter le timeout par défaut de cette commande (comme `provider models` et `document list`).
- **Statut** : `FIXED` (2026-11-11)

  **Correction appliquée** : ajout de `timeout=30.0` aux appels `api_post` dans `_start()` et `_stop()` (`interfaces/cli/commands/application.py`).

---

## 4. Observations complémentaires (non élevées au rang d'anomalie)

Ces points ont été observés mais ne constituent pas des anomalies confirmées. Ils sont listés pour traçabilité.

### OBS-09-01 — Vault daena : fichiers invalides

- **Description** : `memory health` signale 759 fichiers Markdown dont certains sans frontmatter YAML valide (invalid_records listés).
- **Origine** : Phase C (§13.3).
- **Nature** : état documentaire, pas d'erreur API ni CLI.
- **Statut** : observation (pas d'anomalie).

### OBS-09-02 — Ports occupés lors de `doctor`

- **Description** : `ethan doctor` signale les ports 8000, 8080, 4222, 6379, 5432 occupés.
- **Origine** : Phase A (§2.3).
- **Nature** : attendu quand la stack tourne ; warning, pas bloquant.
- **Statut** : observation (pas d'anomalie).

### OBS-09-03 — python-base en état `running` (non healthy)

- **Description** : le service `python-base` (conteneur utilitaire, `sleep infinity`) ne possède pas de healthcheck et apparaît comme `running` mais non `healthy`.
- **Origine** : Mission startup (consolidée), Phase A.
- **Nature** : comportement attendu pour un conteneur utilitaire (pas de healthcheck). Corrigé dans `docker-compose.yml` (`service_started` pour modules).
- **Statut** : observation (comportement attendu, déjà traité).

### OBS-09-04 — Pagination absente sur les endpoints Knowledge/Memory

- **Description** : les endpoints Knowledge et Memory ne supportent pas de pagination explicite (limit/offset). Les listes complètes sont retournées.
- **Origine** : Mission 06 (audit transversal).
- **Nature** : limitation connue, impact faible (datasets petits en dev).
- **Statut** : limitation (pas d'anomalie).

### OBS-09-05 — Nommage mixte des verbes CLI

- **Description** : conventions de nommage mixtes (`collection-update` vs `collection delete` vs `document-add`).
- **Origine** : Mission 06 (ergonomie).
- **Nature** : incohérence cosmétique, pas de blocage fonctionnel.
- **Statut** : limitation (pas d'anomalie).

### OBS-09-06 — Authentification : état de credentials différent entre Mission 08 et Mission 09

- **Description** : Mission 08 rapporte `auth status` OK, Mission 09 rapporte `Not logged in`. Cause : état de credentials différent entre les deux moments (token présent dans `config.json` après la modification du 11 nov. 13:01).
- **Origine** : Mission 09 (§12, réconciliation).
- **Nature** : résolu depuis ; aucune anomalie structurelle.
- **Statut** : observation (résolu).

## 5. Décisions en attente

| Décision | Contexte | Statut |
|---|---|---|
| Aligner le chemin `application catalog` (tiret vs slash) | ANOM-09-01 | En attente d'arbitrage |
| Créer `docs/specs/CLI_CONTRACT.md` | ANOM-09-02 | En attente d'arbitrage |
| Ajouter un healthcheck temps réel au MCP `list()` | ANOM-09-03 | En attente d'arbitrage |
| Augmenter le timeout par défaut de `provider models` et `document list` | ANOM-09-04, ANOM-09-05 | En attente d'arbitrage (workaround `--timeout 15` disponible) |
| Exposer statut RAG et stratégies via l'API | Mission 06, P1 | En attente d'arbitrage |
| Implémenter l'import de documents en CLI (multipart) | Mission 06, P1 | En attente d'arbitrage |

## 6. Synthèse

- **Anomalies confirmées** : 7 (ANOM-09-01 à ANOM-09-07).
- **Anomalies corrigées (FIXED)** : 5 (ANOM-09-01, ANOM-09-02, ANOM-09-04, ANOM-09-05, ANOM-09-07).
- **Anomalies avec cause confirmée, correction opérationnelle requise** : 1 (ANOM-09-03).
- **Anomalies environnementales** : 1 (ANOM-09-06).
- **Tests corrigés** : 2 tests broken pipe (capsys/fileno) + 1 benchmark status (mock API).
- **Observations** : 6 (OBS-09-01 à OBS-09-06).

## 7. Contrôle Git final

- Branche : `refactor/ethan-rebuild-p0`
- HEAD : `57e254b0 canvas`
- Aucun commit effectué.
- Aucune modification de code.
- Modifications préexistantes préservées.
