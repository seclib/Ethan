# AGENT_INTEGRATION.md

Niveau réel d'intégration des agents ETHAN avec Knowledge, RAG, Engineering Memory, documentation, historique des décisions et informations sur les outils et applications. Mission d'investigation uniquement : aucune modification de code.

---

## 1. Architecture des agents et ressources déclarées

### 1.1 Déclaration des ressources par agent
- `core/agents/types.py` — dataclass `Agent` déclare explicitement les ressources autorisées :
  - `knowledge_ids` (nœuds Knowledge spécifiques)
  - `knowledge_collection_ids` (collections RAG)
  - `skill_ids`, `tool_ids`, `folder_ids`, `domain_ids`
  - `memory_scope`, `model`, `provider`, `owner_id`, `agent_type` (USER / SYSTEM / INTERNAL)
- `core/agents/manager.py` (`AgentManager`) : `create` persiste ces ressources dans `CoreRecordStore` (domaine `agents`). `execute` est le point d'entrée unique d'exécution.

### 1.2 Résolution des ressources au moment de l'exécution
- `core/agents/resources.py` (`resolve_agent_resources`) :
  - **Règle absolue** (l. 16-18) : aucune ressource globale n'est injectée sans sélection explicite. Un agent sans sélection ne reçoit rien. Le résolveur ne consulte jamais les catalogues par défaut.
  - Déduplication (`_EffectiveSet`) : une ressource venue de plusieurs sources n'apparaît qu'une fois (première source gagne, dossier d'abord).
  - "Ghosts" : ressources sélectionnées mais absentes du catalogue → listées dans `ghosts`, jamais de crash, jamais de fantôme.
  - Sources : `explicit` (sélection directe sur l'agent) ou `folder:<id>` (via `FolderManager.list_folder_resources`).
- **Statut** : opérationnel, entièrement testé (`tests/test_agent_resources.py`, 419 lignes).

---

## 2. Comment un agent accède à Knowledge et RAG

### 2.1 Construction du contexte (préchargement dans le system prompt)
- `core/agents/executor.py` (`create_agent_executor.execute`, l. 212-270) :
  1. Résolution du provider LLM (l. 240-252).
  2. `resolve_agent_resources(agent, folders, knowledge, collections, skills, tools)` (l. 264-271).
  3. `DomainManager` : pour chaque `agent.domain_ids`, résout les collections et skills rattachés (l. 289-314), ignoré silencieusement si `domain_manager is None`.
  4. Compilation du system prompt (l. 255-435) :
     - Description de l'agent (l. 256-257).
     - **Skills** (l. 323-339) : `skills.get_skill(sid)` pour chaque skill autorisé, contenu sanitisé, enveloppé `<data source="skill:..." kind="skill">`.
     - **Knowledge spécifique** (l. 344-376) : `knowledge_manager.get(item["id"])` pour chaque nœud autorisé, contenu injecté `<data source="knowledge:...">`.
     - **RAG / collections** (l. 383-413) : `knowledge.build_context_multi(task, knowledge_ids)` sur les collections assignées + collections des dossiers + collections des domains. Résultat sanitisé, enveloppé `<data source="rag:..." kind="rag">` avec header `[Connaissances]`.
     - **Tools autorisés** (l. 419-430) : liste textuelle des tools/MCP avec protocole `<tool name="...">...</tool>`.
     - **Capabilities** (l. 432-433).
  5. Construction des messages (l. 437-447) : system + user.
  6. Boucle d'outils bornée `MAX_TOOL_ROUNDS = 3` (l. 36), `SecureToolEnforcer` (fail-closed).
- **Statut** : opérationnel. L'injection de contexte Knowledge/RAG dans le system prompt est réelle.

### 2.2 Pas de retrieval autonome à la volée
- L'agent n'effectue **pas** de retrieval Knowledge/RAG pendant l'exécution (sauf s'il appelle un outil de recherche web). Le contexte est **préchargé dans le system prompt** avant l'appel LLM, sur la base des collections/nœuds assignés à l'agent.
- **Statut** : absence déclarée (pas de RAG "à la volée" piloté par l'agent).

---

## 3. Citations et provenance

| Niveau | Mécanisme | Fichier | Lignes | Opérationnel |
|--------|-----------|---------|--------|--------------|
| Prompt système | `wrap_data_block(source="skill:...", kind="skill")` | `core/agents/executor.py` | 330-337, 369-376, 406-413 | Oui |
| Prompt système | Instruction sticky `STICKY_DATA_INSTRUCTION` | `core/security/prompt_guard.py` | 30-39 | Oui |
| RAG | `[{i}] {title} ({source})\n{content}` | `core/knowledge/collections.py` `build_context_multi` | 528-533 | Oui |
| RAG direct | `RAGContext.build_context` avec `(Source: ...)` | `core/rag/context.py` | 66-70 | Oui |
| Réponse LLM (citations formelles) | **Aucune** | — | — | **Non** — pas d'extraction de citations, pas de footnotes post-génération |

**Constat** : la provenance est présente dans le *prompt* (attributs `source`/`kind`, instruction sticky, `[i] title (source)`), mais il n'y a **pas de traçabilité de citation dans la réponse produite par le LLM** ni de vérification que la réponse s'appuie sur les sources fournies.

---

## 4. Mémoire et Engineering Memory

### 4.1 Engineering Memory (câblage non bloquant)
- `core/engineering_memory/adapters.py` (`EngineeringMemoryIntegration`) :
  - `record_agent_lifecycle` (l. 84-115) : appelé par `AgentManager._record_agent_event` (l. 185-198) sur create/update/delete.
  - `record_knowledge_operation` (l. 166-197) : appelé par `KnowledgeManager._record_knowledge` (l. 218-233).
  - `record_skill_lifecycle` (l. 200-231) : appelé par `core/skills/store.py`.
- Les exceptions sont avalées (non bloquant) avec log d'erreur.
- **Statut** : câblé dans `AgentManager` et `KnowledgeManager` via `set_engineering_memory_integration(...)`, mais accepte `None` et fonctionne sans. L'injection effective depuis la composition root (`interfaces/api/main.py`) n'est pas prouvée dynamiquement.

### 4.2 Mémoire cognitive (core/memory/) — NON branchée aux agents
- `core/memory/manager.py` (`MemoryManager`) : 8 types de mémoire (Working, Short-term, Episodic, Semantic, Procedural, Vector, Event Log, History). `store()` stocke en Vector Memory avec `"embedding": []` (**TODO** embedding manquant, l. 142).
- `core/memory/retrieval.py` (`RetrievalEngine`) : `recall` avec scoring composite. **TODO** embedding de la requête manquant (l. 56).
- **Aucun appel** de `MemoryManager` ou `RetrievalEngine` dans `core/agents/executor.py`.
- **Statut** : sous-système autonome, **non branché sur le flux agent**. La mémoire de travail/épisodique n'est pas injectée dans le system prompt des agents, contrairement au RAG et aux knowledge nodes.

### 4.3 Historique des décisions
- Pas de mécanisme dédié "historique des décisions" consulté par les agents. Les `DECISION` records de l'Engineering Memory existent comme type de record (`core/engineering_memory/models.py`), mais ne sont pas injectés dans le contexte des agents.
- Le Planner (`core/planner/`) ne consulte aucune source de connaissance pour planifier (patterns codés en dur, stratégie LLM en TODO).

---

## 5. Accès aux outils et applications

### 5.1 Outils exposés aux agents
- `executor.py` (l. 419-430) : seuls les `allowed_tools` (résolus via `resolve_agent_resources` à partir de `agent.tool_ids` + contenus de dossiers) sont listés dans le system prompt avec le protocole `<tool name="...">{"param": "val"}</tool>`.
- Exécution : `run_agent_chat` → `_execute_agent_tool` → `ToolExecutor.execute(tool, params, ToolContext(query, user_id=f"agent:{agent_name}", source="agent"))` → `SecureToolEnforcer` (PolicyEngine + Capability + ExfilGuard). **Fail-closed** : aucun ToolManager/enforcer → appel refusé.
- **Statut** : opérationnel, dépend de l'injection d'un `ToolManager` réel dans `create_agent_executor(tools=...)`.

### 5.2 Capacités d'application (DTAI)
- `core/applications/capabilities.py` (`CapabilityRegistry`) : définitions versionnées avec `permission_set()` et `permission_mapping()`.
- `core/applications/capability_contract.py` + `capability_execution.py` : contrats avec `input_schema`/`output_schema` (JSON Schema), `required_permissions`, `timeout_seconds`. `invoke_capability` valide le contrat, le binding, l'activation, l'input_schema, appelle l'implémentation allowlistée (`TRUSTED_IMPLEMENTATION_ALIASES = {"odin.runtime-status", "frame.runtime-status"}`).
- **Statut** : mécanisme réel, mais seuls Odin et Frame ont des implémentations allowlistées. Quantar et TradingAgents n'ont pas de binding d'exécution.

### 5.3 Connexions externes
- `core/integrations/connections/` : connexions OAuth/password vers providers externes, opérations déclarées. L'utilisateur est déduit du JWT. Les tokens ne sont jamais retournés.

---

## 6. Permissions et autorisations

### 6.1 HROT (Human-in-the-loop / Root of Trust Humain)
- `core/hrot/capability_authorization.py` (`CapabilityAuthorizationService.authorize`, 599 lignes) : évaluation fail-closed en 10 étapes (contexte d'exécution, identité acteur, identité agent, application enregistrée, capabilité enregistrée, registration active + approuvée, binding activé + versions de contrat, permissions requises de l'acteur, policy HROT, ALLOW). Décisions enregistrées dans `_decisions` (audit trail).
- `core/hrot/durable.py` (`DurableHrotStore`) : approbations durables (PostgreSQL ou JSONL fallback), états PENDING/APPROVED/DENIED/EXPIRED/CONSUMED, TTL, hash de contenu, anti auto-approbation.
- **Statut** : service autonome existant, **mais non appelé dans le flux d'exécution agent** (`executor.py` n'appelle pas `authorize_agent_capability`). Les permissions d'agent (owner) sont enforcées au niveau API (`interfaces/api/routers/v1.py`), pas au niveau exécution.

### 6.2 Contrôle d'accès agent (API)
- `interfaces/api/routers/v1.py` : 401 non-authentifié, 403 non-propriétaire / utilisateur standard sur agent sans owner / agent system, 422 update sensitive (tool_ids), 403/401 deletion (admin requis).
- Tests : `tests/core/test_agent_authz_hardening.py` (11 tests), `tests/core/test_agent_ownership_types.py` (9 tests), `tests/core/test_agent_execution_context.py` (propagation du contexte d'exécution authentifié).

---

## 7. Limites de contexte

| Limite | Valeur | Fichier | Ligne | Commentaire |
|--------|--------|---------|-------|-------------|
| `max_context_chars` (RAG) | 8000 caractères | `core/rag/pipeline.py` | 62 | Borne brute par caractères, pas de tokens |
| `top_k` (RAG retrieval) | 5 chunks | `core/rag/pipeline.py` | 61 | Configurable |
| `MAX_TOOL_ROUNDS` (agent) | 3 rounds | `core/agents/executor.py` | 36 | Boucle d'outils bornée |
| `ModelInfo.context_length` | 4096 (défaut) | `core/llm/types.py` | 104 | Déclaratif, pas utilisé pour tronquer le prompt |
| RetrievalEngine (mémoire) | top 20 | `core/memory/retrieval.py` | 109 | Non branché sur les agents |

**Constat** : aucune comptabilité de tokens, aucune adaptation à la fenêtre de contexte réelle du modèle sélectionné. Risque de dépassement de fenêtre si `max_context_chars=8000` + system prompt long dépasse la fenêtre du modèle.

---

## 8. Différences entre les types d'agents

| Type | Valeur `agent_type` | Signification | Contraintes observées |
|------|---------------------|---------------|----------------------|
| USER | `user` | Agent créé par un utilisateur | A un `owner_id` ; protège contre lecture/suppression par des tiers (API) |
| SYSTEM | `system` | Composant système | Protégé contre les utilisateurs ordinaires (403) ; peut n'avoir aucun owner |
| INTERNAL | `internal` | Composant interne | Même catégorie que SYSTEM pour l'ownership |

**Aucune différence comportementale dans l'exécution** (`executor.py`) basée sur le type d'agent. Le type ne modifie pas l'injection de connaissance, les outils, ou le RAG. La seule différenciation est au niveau de l'API (contrôle d'accès propriétaire).

---

## 9. Tests existants et couverture réelle

### 9.1 Tests couvrant l'intégration agent → Knowledge/RAG
- `tests/test_agent_knowledge_scoping.py` (156 lignes) : RAG réel + KnowledgeCollectionManager réel, fake provider capturant les messages. Vérifie `[Connaissances]`, titre, contenu dans le system prompt. **Passe.** (LLM faussé, RAG en mode keyword)
- `tests/test_agent_resources.py` (419 lignes) : résolution ressources, déduplication, isolation inter-agents, ghosts, tools. **Passe.**
- `tests/core/test_agent_manager_engineering_memory.py` (38 lignes) : `AgentManager.create` appelle `integration.record_agent_lifecycle(action="created", ...)`. Échec intégration ne bloque pas. **Passe.**
- `tests/core/test_knowledge_skills_integration.py` (40 lignes) : câblage Engineering Memory knowledge/skills. **Passe.**
- `tests/core/test_agent_execution_context.py` (59 lignes) : propagation ExecutionContext jusqu'à l'exécuteur. **Passe.**
- `tests/core/test_agent_authz_hardening.py` (154 lignes) : autorisation API (401/403/422). **Passe.**
- `tests/core/test_agent_ownership_types.py` (108 lignes) : sérialisation owner_id/created_by/agent_type. **Passe.**

### 9.2 Ce qui n'est PAS testé
- Exécution bout en bout avec un LLM réel (tous les tests utilisent un `_FakeProvider`).
- Intégration de `core/memory/` (MemoryManager/RetrievalEngine) dans le flux agent (non branchée).
- HROT dans le flux d'exécution agent (pas d'appel dans `executor.py`).
- Citations formelles dans les réponses LLM.
- Adaptation à la fenêtre de contexte réelle du modèle.

---

## 10. Synthèse : opérationnel vs déclaré

| Mécanisme | Statut | Preuve |
|-----------|--------|--------|
| Agent CRUD + cycle de vie | Opérationnel | `core/agents/manager.py`, tests |
| Exécution agent avec LLM réel | Opérationnel (dépend exécuteur injecté) | `core/agents/executor.py` |
| Injection RAG scoped par collection dans le prompt | Opérationnel | `executor.py` l. 383-413, `tests/test_agent_knowledge_scoping.py` |
| Injection knowledge spécifique (nœuds) | Opérationnel | `executor.py` l. 344-376, `tests/test_agent_resources.py` |
| Injection skills | Opérationnel | `executor.py` l. 323-339 |
| Séparation données/instructions (CT-4) | Opérationnel | `executor.py` + `core/security/prompt_guard.py` |
| Exécution d'outils avec SecureToolEnforcer | Opérationnel (fail-closed) | `executor.py` l. 125-189 |
| Résolution ressources (dédup, ghosts) | Opérationnel | `core/agents/resources.py`, `tests/test_agent_resources.py` |
| Contrôle d'accès agent (owner/API) | Opérationnel | API routes, `tests/core/test_agent_authz_hardening.py` |
| Engineering Memory (câblage agent/knowledge) | Déclaré + câblé, non bloquant | `AgentManager._record_agent_event`, `KnowledgeManager._record_knowledge`, tests |
| Mémoire cognitive `core/memory/` dans le flux agent | **Non branché** | Aucun appel dans `executor.py` |
| RAG auto-ingestion depuis Knowledge | Déclaré (`ingest_into_rag` existe) mais non automatique | Nécessite passage explicite d'un `RAGPipeline` |
| Citations formelles dans les réponses LLM | **Absent** | Provenance uniquement dans le prompt |
| Planner utilisant Knowledge/RAG | **Absent** | `core/planner/` ne consulte aucune source de connaissance |
| HROT dans le flux d'exécution agent | **Non appelé** | Service autonome, pas d'intégration dans `executor.py` |
| Limite de contexte par tokens | **Absent** | Borne en caractères (8000) uniquement |

---

## 11. Recommandations (constat, non action)

1. Brancher `core/memory/` (RetrievalEngine) dans le flux d'exécution agent : aujourd'hui la mémoire de travail/épisodique n'est pas injectée dans le system prompt, contrairement au RAG et aux knowledge nodes.
2. Ajouter une étape de comptage/tronquation de tokens basée sur `ModelInfo.context_length` pour éviter le dépassement de fenêtre.
3. Connecter le HROT `CapabilityAuthorizationService` dans `executor.py` si les capacités applicatives doivent être autorisées à l'exécution.
4. Clarifier l'injection de `engineering_memory_integration` dans la composition root (interfaces) pour s'assurer que les événements agent/knowledge sont effectivement enregistrés en production.
5. Déclarer l'absence de citations formelles comme une limitation documentée si la traçabilité source dans les réponses est requise.

Fin de l'évaluation de l'intégration agent.
