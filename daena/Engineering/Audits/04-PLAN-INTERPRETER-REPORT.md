# ETHAN WebUI — PLAN INTERPRETER REPORT

> **Date** : 2026-08-18
> **Objectif** : Transformer les documents stratégiques en système d'exécution traçable selon le framework [DOCUMENT → DÉCISION → EXIGENCE → TÂCHE → CODE → TEST → VALIDATION].

---

## DOCUMENT 1 : ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md

### 1. Objectif du document
Définir l'architecture unifiée pour la gestion des fournisseurs de LLM (Providers) et des Modèles, en fusionnant les capacités d'ETHAN Core (robuste, sans secrets en DB) et la richesse de l'UX Open WebUI (sélection, routing, healthcheck).

### 2. Décomposition de l'exécution

- **[DECISION]** : Une seule source de vérité pour les modèles et providers : `core/llm/`. Le backend Open WebUI ne doit pas être forké ni instancié. Le WebUI est strictement un *thin client*.
- **[DECISION]** : Les secrets et clés d'API ne seront JAMAIS stockés en base de données, mais conservés dans `core/config/secrets.py` (Vault/Env).

- **[REQUIREMENT]** : L'API `/v1/models` doit renvoyer un catalogue agrégé fusionnant les modèles découverts via les providers et les *custom model cards* définies dans le `ModelStore`.
- **[REQUIREMENT]** : Le WebUI doit réutiliser l'UX `ChatControls.svelte`, `ModelSelector.svelte` et `AddConnectionModal.svelte` en version React/Next.js.

- **[TASK] 1.1** : Ajouter le fournisseur `OpenRouter` (`core/llm/providers/openrouter.py`) avec gestion du mode de routage et fallback multi-providers.
- **[TASK] 1.2** : Ajouter les fournisseurs manquants : `azure.py`, `llamacpp.py`, et activer `gemini.py`, `lmstudio.py`.
- **[TASK] 1.3** : Ajouter le champ technique `model` à `ModelInfo` pour distinguer le nom d'affichage du nom envoyé via l'API provider.
- **[TASK] 1.4** : Créer l'API `GET/PUT /v1/providers/secrets` (réservée Admin) pour l'injection sécurisée de clés.

- **[DEPENDENCY]** : Le système de providers (Task 1.2) doit être achevé avant l'intégration du `AddConnectionModal` dans le WebUI.
- **[RISK]** : Fuite de secrets si les endpoints GET `/v1/providers` exposent les champs `api_key`. *Mitigation* : Filtrer systématiquement les payload de sortie de l'API.
- **[QUESTION]** : Comment gérer le rate-limiting multi-tenant sur des providers mutualisés (Azure/OpenAI) sans config locale ?

- **[VALIDATION]** :
  1. Configurer une clé OpenAI via API et vérifier qu'elle n'est pas inscrite dans PostgreSQL.
  2. Créer une Model Card custom via API et la voir apparaître dans la liste agrégée `/v1/models`.

---

## DOCUMENT 2 : ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md

### 1. Objectif du document
Centraliser et uniformiser la configuration et l'exécution du RAG, de la connaissance, du stockage de fichiers, des outils et serveurs MCP pour que l'ensemble soit pilotable indifféremment par WebUI, CLI ou Desktop.

### 2. Décomposition de l'exécution

- **[DECISION]** : Toutes les interfaces configurent ces 5 domaines via une unique API métier `/v1/config/{domain}` et un bus d'évènements `CONFIG_UPDATED`.
- **[DECISION]** : Suppression totale de la notion de `functions.py` en doublon avec `tools.py` ; unification sous `core/tools/`.

- **[REQUIREMENT]** : Le RAG Core doit supporter une architecture hybride (Vecteur + BM25) et s'interfacer avec de multiples vecteurs (Chroma, PGVector, Qdrant).
- **[REQUIREMENT]** : Les outils `builtin` natifs (recherche web, génération d'images, terminal) doivent être intégrés formellement comme Tools dans le Core.

- **[TASK] 2.1** : Développer une Factory Vectorielle (`core/rag/vector/factory.py`) pour dynamiser l'instanciation de Chroma/PGVector/Qdrant.
- **[TASK] 2.2** : Implémenter le `MCPClient` dans `core/tools/mcp_client.py` (*Réalisé au cours de la Phase B*).
- **[TASK] 2.3** : Étendre le `FileStore` avec une abstraction logicielle de Stockage (`core/file_storage/`) supportant Local, S3, GCS et Azure.
- **[TASK] 2.4** : Mettre en place un Reranker externe paramétrable via `core/rag/reranker.py` (ex: ColBERT).

- **[DEPENDENCY]** : La Factory Vectorielle nécessite l'intégration préalable des schémas de configuration unifiés (`/v1/config/rag`).
- **[RISK]** : Perte de performance lors de la synchronisation de gros serveurs MCP si la réponse HTTP timeout. *Mitigation* : Utiliser des workers asynchrones pour le fetch MCP.
- **[QUESTION]** : Quelle politique de nettoyage (Garbage Collection) appliquer sur le FileStore (S3) lorsqu'un document est désindexé de toutes les collections ?

- **[VALIDATION]** :
  1. Uploader un fichier via l'API, l'assigner à une collection et vérifier l'extraction du texte dans les chunks.
  2. Modifier `chunk_size` via `/v1/config/rag`, réindexer le document, et vérifier la nouvelle taille des chunks en DB.

---

## DOCUMENT 3 : ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md

### 1. Objectif du document
Standardiser la gestion des configurations de l'application via une interface riche à 13 onglets (General, Interface, Models, RAG, etc.), en respectant la séparation stricte Core / WebUI.

### 2. Décomposition de l'exécution

- **[DECISION]** : Adoption du mapping de 13 onglets pour l'interface Admin et des onglets dédiés pour la configuration utilisateur, branchés sur `/v1/config`.
- **[DECISION]** : Disparition complète de la persistence de configuration au sein du WebUI.

- **[REQUIREMENT]** : L'API de configuration doit supporter le `PATCH` (fusion récursive) pour éviter d'écraser des paramètres profonds (ex: `rag.embeddings.url`).

- **[TASK] 3.1** : Créer l'architecture de navigation verticale pour les paramètres dans le frontend (*Réalisé en Phase C*).
- **[TASK] 3.2** : Implémenter les composants granulaires de configuration (RAG Chunking settings, Web Search providers form).
- **[TASK] 3.3** : Ajouter les endpoints de JSON Schema (`/v1/config/schema/{domain}`) pour auto-générer les formulaires WebUI.

- **[DEPENDENCY]** : Le schéma JSON des configs (Task 3.3) doit exister pour que le WebUI puisse auto-valider les inputs de Settings.
- **[RISK]** : Désynchronisation de la configuration entre plusieurs instances du Core si Redis n'invalide pas correctement le cache lors du `PATCH`.

- **[VALIDATION]** :
  1. Modifier le paramètre système depuis le WebUI.
  2. Vérifier via le CLI `ethan config get` que le changement est immédiatement pris en compte.

---

## 3. Chaîne d'exécution priorisée (Prochaines Étapes)

Sur base de cette interprétation, la chaîne d'exécution (Code Ready) pour les prochaines étapes est la suivante :

### Chaine 1 : Fusion Functions / Tools
`DOCUMENT: RAG_KNOWLEDGE_FILES_MCP_TOOLS` → `DÉCISION: Zero doublon tools/functions` → `EXIGENCE: Unification` → `TÂCHE: Migrer les built-in vers core/tools/builtin.py et supprimer le router functions` → `CODE: (pending)`

### Chaine 2 : Model Technical Names
`DOCUMENT: MODELS_PROVIDERS` → `DÉCISION: Core as truth` → `EXIGENCE: ModelInfo complet` → `TÂCHE: Ajouter 'model' technique au dataclass ModelInfo` → `CODE: (pending)`

### Chaine 3 : OpenRouter Provider
`DOCUMENT: MODELS_PROVIDERS` → `DÉCISION: Core as truth` → `EXIGENCE: Fallback multi-provider` → `TÂCHE: Implémenter core/llm/providers/openrouter.py` → `CODE: (pending)`
