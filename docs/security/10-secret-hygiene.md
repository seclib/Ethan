# 10 — Hygiène des secrets dans les configurations persistées

> Statut : **implémenté** — deux fuites confirmées par audit sont fermées et
> verrouillées par `tests/security/test_provider_secrets.py` (6 tests) et
> `tests/security/test_rag_config_secrets.py` (4 tests).

Principe appliqué (AGENTS.md) : aucun secret ne doit exister dans le code, le
dépôt, les logs, les events, la mémoire système… **ni dans les configurations
« publiques »** que le Core persiste et que les interfaces lisent. Une
configuration est un document de travail : elle doit survivre à un
GET→PUT sans jamais transporter un secret.

Faille récurrente : une config dite « serialisable » reçoit une clé API à
l'écriture, puis **(a)** est retournée en lecture par un endpoint ouvert aux
rôles de lecture et **(b)** est persistée en clair dans le record store
(PostgreSQL/Redis). Deux corrections réutilisables en découlent.

## 1. Providers LLM — clé API dans `_providers_config`

`ProviderManager._inject_secrets` injectait les clés d'environnement dans
`_providers_config`, la structure considérée comme publique. En conséquence :

- la clé atterrissait dans PostgreSQL/Redis via `set_enabled` → `_save_config`
  (persistance en clair) ;
- `PUT /v1/providers` réécrivait la config **avec** la clé passée en payload,
  un aller-retour qui conservait l'ancienne clé même sans nouvelle saisie ;
- `describe_provider` / `list_models` renvoyaient la config brute.

Correction : la clé quitte la config **à la source**.

| Élément | Rôle |
|---|---|
| `self._api_keys` | dictionnaire en mémoire de process — seule maison des clés |
| `_public_config(config)` | chokepoint : strip `api_key` sur **chaque** sauvegarde |
| `remember_api_key(pid, key)` | API d'écriture pour les routers |
| `api_key_for(pid)` | API de lecture pour les factories |

La clé n'est jamais dans la structure persistée ; l'API ne retourne qu'un
booléen de présence (même modèle que `has_api_key` de TTS/Images). Le router
`providers.py` (PUT) utilise ces helpers.

Tests : `tests/security/test_provider_secrets.py` — pas de clé dans la config
persistée après injection, `GET` sans clé, round-trip PUT sans clé, clé
mémorisée réutilisée par la factory, `_public_config` sur toute sauvegarde.
Mis à jour : `tests/test_provider_manager.py::test_inject_secrets_enables_openai`
(assertion « clé absente de la config »).

## 2. RAG — `vector_backend_config` avec clé Qdrant

`RAGPipeline.get_config()` renvoyait `vector_backend_config` **verbatim** :
la clé API du backend vectoriel lisible via `GET /v1/rag/config` (lecture sans
gate `ADMIN`, réservée au PUT). Pire, `persist_config()` sauvegardait ce
dictionnaire dans le record store (`rag-config/global`) : la clé était écrite
en clair. Enfin, le round-trip GET→PUT de l'éditeur JSON WebUI pouvait
écraser le secret (un booléen `true` remplaçant la valeur).

Correction en quatre garanties indépendantes (`core/rag/pipeline.py`) :

| Helper | Garantie |
|---|---|
| `_SECRET_CONFIG_KEYS` (`{"api_key"}`) | liste déclarative des clés sensibles |
| `redact_backend_config()` | `get_config` : valeur → `bool` (présence uniquement) |
| `persistable_backend_config()` | `persist_config` : clé **absente** du document persisté |
| `_merge_backend_config()` | `configure` : `true` préserve la clé mémorisée, `""` l'efface, une valeur la remplace |

Tests : `tests/security/test_rag_config_secrets.py` — redaction en lecture,
persistance sans secret, survie du secret au round-trip, effacement explicite.
Aucun appel réseau (backend non chargé).


## 3. Audit de surface — vérifications négatives

Balayage des autres surfaces susceptibles de porter un secret ou une entrée
non fiable ; **aucune correction nécessaire** sur ces points :

| Surface | Verdict | Détail |
|---|---|---|
| TTS (`/audio/config`) | ✓ déjà sûr | clé mémoire d'instance, `get_config` strip + `has_api_key`, jamais persistée |
| Images (`/images/config`) | ✓ déjà sûr | même modèle |
| Intégrations | ✓ conforme | credentials uniquement dans le domaine dédié `integration-credentials` ; `_public()` sur lectures et événements ; purge au `delete` ; mutations `PLUGINS` |
| Skills | ✓ conforme | create/update/delete/toggle/valves = `PLUGINS` ; run et lab = `EXECUTE` ; `is_active` vérifié avant exécution ; outils inconnus refusés (422) |
| Plugins install | ✓ conforme | `find_manifest` = catalogue statique en mémoire (aucun chemin construit depuis l'id) ; `_ID_RE = ^[a-z0-9][a-z0-9_-]*$` (ni `/` ni `..`) ; `install_custom` validé ; `connect` refuse les champs `secret` |
| Archives | ✓ conforme | aucun `extractall` ; DOCX = `archive.read("word/document.xml")` (membre fixe) |
| Webhooks | ✓ conforme | aucune route webhook entrante (seule mention : politique `data_protection`) |
| SQL | ✓ conforme | `postgres_state.py` / `security.py` : entièrement paramétrés |
| Uploads | ✓ conforme | `filename` descriptif uniquement ; `file_id` = tempfile/UUID |
| WebUI | ✓ conforme | aucun secret stocké côté client ; type legacy `LLMSettings.api_key` sans usage serveur |

## 4. Règle à appliquer à toute nouvelle surface

Avant d'ajouter un champ à une config persistée, répondre :

1. Ce champ peut-il contenir un secret ? → le placer dans `_api_keys`, un
   domaine dédié ou le secret manager, **jamais** dans la config.
2. La config est-elle lue par un endpoint de lecture ? → passer par le
   chokepoint de redaction (`_public_config` / `redact_backend_config`).
3. La config est-elle persistée ? → passer par le chokepoint de persistance
   (`persistable_backend_config`).
4. Un GET→PUT doit-il survivre ? → préserver la clé via un booléen de
   présence (`true` = conservé, `""` = effacé, valeur = remplacée).

Le même test doit couvrir les trois chemins : lecture, persistance, round-trip.

## Tests

- `tests/security/test_provider_secrets.py` — 6 tests
- `tests/security/test_rag_config_secrets.py` — 4 tests
- `tests/security/` total : **226 passed** (29/09/2026 — incl. `test_runtime_isolation`)
- Suite complète : `pytest tests/` = **1760 passed / 25 skipped** / 0 erreur
- `ruff check` + `ruff format --check` : propres sur les fichiers touchés
