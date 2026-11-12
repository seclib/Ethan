# IMPLEMENTATION_ROADMAP.md

Roadmap d'implémentation révisée pour DAĒNĀ et DTAI dans ETHAN OS, réorganisée autour des priorités architecturales approuvées par le responsable du projet.

Mission exclusivement de planification et de documentation. **Aucun code de production n'est modifié.**

---

## Ordre de priorité approuvé

| Priorité | Libellé | Criticité |
|----------|---------|-----------|
| **P0** | Sécurité et accès unifié aux capacités des agents | Critique |
| **P1** | Intelligence opérationnelle de DAĒNĀ | Haute |
| **P2** | Intégration DAĒNĀ ↔ DTAI | Haute |
| **P3** | Consolidation de l'architecture et fiabilité | Consolidation |

---

## Règles de lecture

- Chaque mission est décrite avec : identifiant, objectif, état actuel et preuves du code source, périmètre, exclusions explicites, prérequis, stratégie d'implémentation technique, fichiers/modules potentiellement affectés, considérations de sécurité, implications API et contrats de données, stratégie de tests, critères d'acceptation mesurables, risques et considérations de rollback, Définition de Fini (DoD).
- Chaque mission sépare : **faits confirmés** (preuves dans le code), **recommandations architecturales**, **hypothèses non vérifiées**, **questions nécessitant une décision du responsable du projet**.
- Aucune mission ne modifie le code de production sans validation préalable de la roadmap. Chaque mission est vérifiable par des tests.
- Aucune dépendance circulaire n'est introduite. DAĒNĀ ne gère pas le cycle de vie des applications ; DTAI ne gère pas la connaissance.

---

## Dépendance globale entre les priorités

```
P0-1 (HROT dans le cycle d'exécution agent)
   │  (autorisation avant exécution protégée ; fondation de sécurité)
   ▼
P1-1 (récupération Knowledge/RAG par les agents, sous autorisation P0)
   ├──► P1-2 (citations formelles et provenance des sources)
   ├──► P1-3 (gestion de contexte consciente des tokens)
   │
   ▼
P2-1 (contrats de métadonnées canoniques DTAI → DAĒNĀ)
   ├──► P2-2 (stratégie d'événements et de synchronisation)
   └──► P2-3 (gestion des erreurs, cohérence, propriété, anti-circulaire)
   │
   ▼
P3-1 (routeurs API orphelins — identification de l'implémentation canonique)
   ├──► P3-2 (duplication Odin/ComposeService)
   ├──► P3-3 (opérations du cycle de vie des manifests)
   ├──► P3-4 (observabilité et tests d'intégration)
   └──► P3-5 (suppression des composants obsolètes après analyse de dépendances)
```

**Justification de l'ordre :**
- **P0 avant P1** : la récupération de connaissance par les agents (P1) est expressément "soumise à l'autorisation P0". L'autorisation HROT est donc le préalable de sécurité.
- **P1 avant P2** : l'intégration DAĒNĀ ↔ DTAI suppose que la récupération et la provenance de connaissance fonctionnent côté agent (P1), et que l'autorisation est effective (P0).
- **P2 avant P3** : la consolidation (routeurs, duplications, suppression de composants) s'appuie sur la connaissance exacte des contrats et propriétaires établie en P2.
- Le nettoyage des routeurs (ancienne P0-1) passe en **P3** (consolidation) car il n'est pas bloquant pour P1/P2 : `v1.py` est le routeur canonique monté ; les routeurs orphelins ne sont pas appelés par les clients existants.

---

# MISSION P0 — Sécurité et accès unifié aux capacités des agents (Critique)

## Mission P0-1 — Intégration de l'autorisation HROT dans le cycle d'exécution agent (IMPLÉMENTÉE)

### Statut : IMPLÉMENTÉE

### 1. Objectif
Vérifier et réaliser l'intégration réelle de l'autorisation HROT (`CapabilityAuthorizationService`) dans le cycle d'exécution des agents, définir le point d'entrée canonique d'autorisation, et garantir qu'aucun chemin d'exécution alternatif ne contourne l'autorisation pour les capacités protégées.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/hrot/capability_authorization.py` : `CapabilityAuthorizationService.authorize(request)` existe (599 lignes), évaluation fail-closed en 10 étapes (contexte d'exécution, identité acteur, identité agent, application enregistrée, capacité enregistrée, registration active + approuvée, binding activé + versions de contrat, permissions de l'acteur, policy HROT via `PermissionService.authorize`, ALLOW). Décisions enregistrées dans `self._decisions` (audit trail).
- `core/hrot/durable.py` : `DurableHrotStore` (approbations durables, états PENDING/APPROVED/DENIED/EXPIRED/CONSUMED, anti auto-approbation).
- `core/agents/executor.py` : `execute()` construit le system prompt et boucle sur les appels d'outil (`run_agent_chat`, `MAX_TOOL_ROUNDS = 3`, `SecureToolEnforcer` fail-closed). **Aucun appel à `CapabilityAuthorizationService.authorize` n'est présent dans le flux d'exécution agent** (lignes 212-270 et 437-457 examinées).
- `core/security/prompt_guard.py` : `sanitize_external_content` + `wrap_data_block` (CT-4, séparation données/instructions) déjà appliqué pour skills, knowledge, RAG.
- `core/agents/resources.py` : `resolve_agent_resources` — aucune ressource globale n'est injectée sans sélection explicite.

### 3. Périmètre
- Intégrer `CapabilityAuthorizationService.authorize` avant l'exécution de toute capacité protégée (invocations de capacité, appels d'outil sensibles) dans `executor.py`.
- Définir le point d'entrée canonique d'autorisation pour les agents.
- Garantir le comportement fail-closed : toute exception ou contexte d'exécution incomplet → refus.
- Garantir l'auditabilité : chaque décision d'autorisation enregistrée (qui, quoi, résultat, raison).
- Vérifier qu'aucun chemin d'exécution alternatif (exécution directe, contournement du system prompt) ne bypass l'autorisation.

### 4. Exclusions explicites
- Ne pas modifier le modèle de données HROT existant (`core/hrot/`).
- Ne pas créer un second système d'autorisation parallèle.
- Ne pas toucher aux routes API d'authentification existantes (JWT, API keys).
- Ne pas modifier le comportement des agents quand l'autorisation n'est pas requise (capacités non protégées).

### 5. Prérequis
- `CapabilityAuthorizationService` et `DurableHrotStore` déjà présents et testés (`tests/core/` couvre l'autorisation HROT).
- `SecureToolEnforcer` présent dans le flux d'outil de l'agent.

### 6. Stratégie d'implémentation technique
- Dans `core/agents/executor.py`, avant toute invocation de capacité (`invoke_capability`) et avant tout appel d'outil sensible, appeler le point d'entrée canonique d'autorisation avec le contexte d'exécution (acteur, agent, application, capacité, ressource, action).
- Si l'autorisation est refusée, lever une erreur explicite et non silencieuse, enregistrée dans la trace d'audit.
- Documenter le point d'entrée canonique (fonction dédiée) pour éviter les appels dispersés.

### 7. Fichiers et modules potentiellement affectés
- `core/agents/executor.py` (point d'intégration principal).
- `core/hrot/capability_authorization.py` (utilisation, pas modification de la logique d'évaluation).
- `core/hrot/durable.py` (persistance des décisions, usage existant).
- `core/security/prompt_guard.py` (réutilisation de la séparation données/instructions, pas de modification).

### 8. Considérations de sécurité
- Fail-closed : refus par défaut en cas d'échec, de contexte incomplet ou d'exception.
- Anti-bypass : audit des chemins d'exécution pour s'assurer qu'aucun ne contourne le point d'entrée canonique.
- Pas d'auto-approbation (actrice != approbateur), conformément à `DurableHrotStore`.
- `manifest_fingerprint` : toute modification de manifeste invalide l'autorisation existante.

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API (autorisation interne au Core).
- Contrat interne : `authorize(request)` retourne ALLOW/DENY avec raison, décision traçable.
- Les capacités exposées aux agents conservent leurs `required_permissions` et `execution_constraints` existants.

### 10. Stratégie de tests
- Test d'autorisation réussie (contexte complet, acteur approuvé).
- Test de refus (actrice != approbateur, manifest modifié → `MANIFEST_CHANGED`, capacité non enregistrée).
- Test de fail-closed (exception interne → refus).
- Test d'auditabilité (décision enregistrée avec acteur, capacité, résultat, raison).
- Test d'absence de bypass (révision des chemins d'exécution de `executor.py`).
- Régression : `tests/core/test_agent_authz_hardening.py`, `tests/core/test_agent_ownership_types.py` restent verts.

### 11. Critères d'acceptation mesurables
- Chaque capacité protégée des agents a un chemin d'autorisation documenté.
- Toute opération non autorisée est refusée avec une erreur explicite.
- Chaque décision d'autorisation est auditable (acteur, capacité, ressource, action, résultat, raison, horodatage).
- L'accès des agents à la connaissance suit un modèle de permission explicite.
- Le comportement d'exécution existant est préservé quand l'autorisation n'est pas requise.

### 12. Risques et considérations de rollback
- Risque : fail-closed bloque des exécutions légitimes si le contexte d'exécution est incomplet. Atténuation : valider l'exhaustivité du contexte d'exécution avant déploiement ; rollback par désactivation de l'appel d'autorisation (restauration du comportement precedent).
- Risque : duplication de logique d'autorisation. Atténuation : point d'entrée canonique unique, réutilisation de `CapabilityAuthorizationService`.

### 13. Définition de Fini (DoD)
- `executor.py` appelle le point d'entrée canonique d'autorisation avant toute capacité protégée.
- Tests d'autorisation, refus, fail-closed et auditabilité passent.
- Aucun chemin d'exécution alternatif ne contourne l'autorisation (revue de code).
- `tests/core/test_agent_authz_hardening.py` et `tests/core/test_agent_ownership_types.py` restent verts.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `CapabilityAuthorizationService.authorize` existe et est testé ; `executor.py` n'y appelle pas ; `SecureToolEnforcer` est déjà fail-closed pour les outils ; `resolve_agent_resources` n'injecte rien sans sélection explicite.
- **Recommandations architecturales** : point d'entrée canonique unique pour l'autorisation agent ; intégration avant exécution, pas après ; audit trail réutilisant `_decisions`.
- **Hypothèses non vérifiées** : l'injection effective de `engineering_memory_integration` depuis la composition root (`main.py`) n'est pas prouvée dynamiquement.
- **Questions pour le responsable du projet** : quelles capacités sont considérées "protégées" nécessitant autorisation avant exécution ? Quel niveau de détail d'audit est requis (stockage des décisions, rétention) ?

### Implémentation effectuée (P0-1S)
- core/components/command-palette.tsx : paramètre enforce_hrot supprimé (toujours activé) ; code mort (lignes 272-299) supprimé.
- core/hrot/capability_authorization.py : permission_service obligatoire (lève ValueError si None) ; verify_trusted_principal() appelé dans _evaluate() après résolution du contexte ; _record() logge les exceptions au lieu de les avaler silencieusement.
- tests/interfaces/test_application_capability_execution_p01s.py : 17 nouveaux tests couvrant tous les scénarios P0-1S (autorisation, refus, fail-closed, clés forcée, binding mismatch, persistance, audit, etc).

---

# MISSION P1 — Intelligence opérationnelle de DAĒNĀ (Haute)

## Mission P0-1P — Durable Authorization & Audit Persistence (diagnostic terminé, implémentation en attente)

### Statut : DIAGNOSTIC TERMINÉ (P0-1P Phase B1)

Le diagnostic technique P0-1P (audit technique préalable B1) a été réalisé. Il a révélé que :

- `PermissionService` est créé sans `ApplicationStateStore` dans `core/applications/application_registry.py:124` (mémoire volatile, grants perdus au redémarrage).
- Les décisions d'autorisation (`CapabilityAuthorizationService._decisions`) sont en mémoire uniquement, non persistées.
- `DurableHrotStore` est utilisé séparément dans `core/applications/integration_approval.py:210` pour les approbations HROT, sans lien avec `PermissionService`.
- Aucun pont DurableHrotStore → PermissionService n'existe.

### Conditions à remplir avant l'implémentation P0-1P

1. Injecter un `ApplicationStateStore` dans `PermissionService` (composition root `interfaces/api/main.py`).
2. Persister les décisions d'autorisation dans `_record()` de `CapabilityAuthorizationService`.
3. Créer un pont DurableHrotStore → PermissionService (approbation HROT → grant de permission).
4. Tester redémarrage, révocation, échec de stockage, fail-closed.
5. Revue de sécurité indépendante.

---

## Mission P1-0 — Knowledge Access Security & Integration Audit (planifié)

### Statut : PLANIFIÉ

Objectif : auditer la sécurité et les contrats d'accès à Knowledge/RAG.

Vérifier :
- Authentification et identité des utilisateurs et agents.
- Autorisations et séparation des collections.
- Isolation des données.
- Contrôle des accès aux documents.
- Provenance et traçabilité des résultats.
- Sécurité des API Knowledge existantes.
- Possibilités d'accès depuis des clients externes.

Aucune exposition publique avant validation de sécurité.

---

## Mission P1-1 — Récupération de Knowledge/RAG par les agents pendant l'exécution (sous autorisation P0)

### 1. Objectif
Connecter l'exécution des agents à l'architecture Knowledge et RAG existante, de manière à ce qu'un agent puisse récupérer des connaissances autorisées pendant son exécution effective, en réutilisant les services Engineering Memory et Vault existants, et sous le contrôle de l'autorisation P0.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/agents/executor.py` : `execute()` compile déjà un system prompt contenant des blocs `<data source="knowledge:...">` (nœuds Knowledge via `knowledge_manager.get`, lignes 344-376) et `<data source="rag:...">` (collections via `build_context_multi`, lignes 383-413). L'injection dans le prompt est réelle.
- `core/knowledge/manager.py` : `KnowledgeManager` (CRUD, `search`, `connect`, `ingest_into_rag`) et `KnowledgeCollectionManager` (`retrieve_multi`, `build_context_multi`) existent et sont testés.
- `core/agents/resources.py` : `resolve_agent_resources` résout `knowledge_ids`, `knowledge_collection_ids`, `skill_ids`, `tool_ids`, `folder_ids`, `domain_ids` avec déduplication et gestion des "ghosts" ; aucune ressource globale sans sélection explicite.
- `core/engineering_memory/service.py` : `EngineeringMemoryService` (records, search par composant/type/status, intégrité) et `VaultService` (read-only du vault Obsidian, wikiliens, backlinks, graph).
- `core/memory/manager.py` : `MemoryManager` (8 types de mémoire) existe mais **n'est pas appelé dans `executor.py`** (sous-système parallèle, non branché).
- Tests existants : `tests/test_agent_knowledge_scoping.py` (RAG réel + `KnowledgeCollectionManager` réel, fake provider), `tests/test_agent_resources.py` (résolution, déduplication, isolation inter-agents, ghosts) passent.

### 3. Périmètre
- Garantir que l'agent récupère les connaissances autorisées (nœuds Knowledge spécifiques + collections RAG assignées) pendant son exécution, pas seulement au préchargement du prompt.
- Assurer que la récupération est soumise à l'autorisation P0 (pas de récupération de connaissance non autorisée).
- Réutiliser `EngineeringMemoryService` et `VaultService` existants pour la mémoire technique et le vault documentaire.
- Définir une stratégie de récupération cohérente (quelles collections, quels nœuds, quel top_k, quelle stratégie keyword/semantic/hybrid).
- Éviter toute implémentation parallèle ou dupliquée de Knowledge/RAG.

### 4. Exclusions explicites
- Pas de retrieval autonome "à la volée" piloté par l'agent sans autorisation explicite (l'agent ne consulte pas de lui-même les sources non assignées).
- Pas de nouvelle implémentation RAG ; réutiliser `RAGPipeline` et `KnowledgeCollectionManager`.
- Pas de modification de `core/memory/` pour l'instant (la mémoire cognitive reste un sous-système séparé ; son branchement est une recommandation, pas un blocage de P1).
- Pas de modification du Core/API/RAG au-delà de ce qui est strictement nécessaire à la récupération agent.

### 5. Prérequis
- P0-1 (autorisation HROT dans le cycle d'exécution agent).
- `KnowledgeCollectionManager.retrieve_multi` et `build_context_multi` déjà opérationnels.
- `RAGPipeline.retrieve` déjà opérationnel (stratégies auto/keyword/semantic/hybrid).

### 6. Stratégie d'implémentation technique
- Dans `executor.py`, maintenir l'injection des blocs `<data source="knowledge:...">` et `<data source="rag:...">` dans le system prompt, désormais gérée par le point d'autorisation P0 (seules les ressources autorisées sont injectées).
- Définir la stratégie de récupération par défaut (top_k, stratégie auto, scopage par collection via `document_ids` pour éviter le retrieve global + post-filtre).
- Réutiliser `EngineeringMemoryService.search` pour la mémoire technique et `VaultService.search`/`backlinks` pour le vault documentaire quand pertinent.

### 7. Fichiers et modules potentiellement affectés
- `core/agents/executor.py` (injection conditionnée par l'autorisation P0).
- `core/agents/resources.py` (éventuelle extension pour exposer les ressources autorisées à la récupération).
- `core/knowledge/collections.py` (réutilisation, pas modification de la logique de retrieval).
- `core/engineering_memory/service.py` (réutilisation pour la mémoire technique).

### 8. Considérations de sécurité
- La récupération de connaissance est gated par l'autorisation P0 : seuls les nœuds et collections assignés et autorisés à l'agent sont injectés.
- Séparation données/instructions (CT-4, `prompt_guard.py`) préservée : les données externes restent enfermées dans `<data>` avec provenance.
- Pas d'injection de ressources globales implicites (règle de `resources.py`).

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API.
- Contrat interne : les blocs de données injectés portent `source` (`knowledge:...`, `rag:...`) et `kind`, avec provenance.
- Les collections RAG conservent leur contrôle d'accès (owner/admin/grants user-groupe read/write).

### 10. Stratégie de tests
- Test : agent avec `knowledge_collection_ids` reçoit un contexte RAG dans son system prompt (réutiliser `tests/test_agent_knowledge_scoping.py` avec fake provider).
- Test : agent sans collection assignée n'a pas de section `[Connaissances]`.
- Test : ressource ghost (collection disparue) dégradée gracieusement sans crash.
- Test : autorisation P0 gating — connaissance non assignée à l'agent n'est pas injectée.
- Régression : `tests/test_agent_resources.py`, `tests/test_agent_knowledge_scoping.py` restent verts.

### 11. Critères d'acceptation mesurables
- Les agents peuvent récupérer des connaissances autorisées pendant leur exécution effective.
- Les sources récupérées restent traçables (attribut `source`/`kind` dans les blocs `<data>`).
- Aucune implémentation parallèle ou dupliquée de Knowledge/RAG n'est introduite.
- La récupération respecte l'autorisation P0 (pas de connaissance non autorisée).

### 12. Risques et considérations de rollback
- Risque : injection de trop de contexte dans le system prompt (dépassement de fenêtre). Atténuation : borner par `max_context_chars` existant ; P1-3 (tokens) affine cela. Rollback : réduire `top_k` ou désactiver l'injection RAG pour un agent donné.
- Risque : récupération de connaissance non autorisée. Atténuation : gating P0. Rollback : désactiver l'injection RAG tant que P0 n'est pas validé.

### 13. Définition de Fini (DoD)
- L'agent récupère les nœuds Knowledge et collections RAG assignés et autorisés pendant son exécution.
- Les sources sont traçables via `source`/`kind`.
- Tests de récupération, gating P0, et dégradation ghost passent.
- `tests/test_agent_knowledge_scoping.py` et `tests/test_agent_resources.py` restent verts.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : l'injection Knowledge/RAG dans le system prompt existe déjà (`executor.py` lignes 344-413) ; `resolve_agent_resources` et `retrieve_multi` sont testés ; `core/memory/` n'est pas appelé dans `executor.py`.
- **Recommandations architecturales** : garder l'injection préchargée dans le system prompt (pas de retrieval autonome à la volée) tant que P0 n'est pas pleinement validé.
- **Hypothèses non vérifiées** : l'injection effective de `engineering_memory_integration` depuis la composition root (`main.py`) n'est pas prouvée dynamiquement.
- **Questions pour le responsable du project** : les nœuds Knowledge et collections RAG doivent-ils être gérés par une autorisation distincte de celle des capacités applicatives ?

---

## Mission P1-2 — Citations formelles et provenance des sources (P1)

### 1. Objectif
Établir la provenance des sources et la gestion formelle des citations dans les réponses des agents : distinguer l'information récupérée des conclusions générées par le modèle, et permettre à l'agent d'identifier l'origine de l'information utilisée dans ses réponses.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/agents/executor.py` : les blocs de données injectés portent `source` (`skill:...`, `knowledge:...`, `rag:...`) et `kind`, avec instruction sticky `STICKY_DATA_INSTRUCTION` via `core/security/prompt_guard.py` (lignes 30-39).
- `core/knowledge/collections.py` : `build_context_multi` produit `[{i}] {title} ({source})\n{content}` (lignes 528-533).
- `core/rag/context.py` : `RAGContext.build_context` inclut `(Source: titre — source)` (lignes 66-70).
- **Aucun mécanisme de citation formelle** (footnotes, `[src:1]`) n'est extrait de la réponse générée par le LLM (constat dans `executor.py` et `prompt_guard.py`).

### 3. Périmètre
- Ajouter un mécanisme de citation formelle (ex. `[src:N]`) dans les réponses des agents, mappé aux sources du contexte.
- Permettre la résolution d'une citation vers son enregistrement source vérifiable (titre, source, type).
- Déclarer explicitement l'absence de citation comme une limitation si elle ne peut être implémentée complètement.

### 4. Exclusions explicites
- Pas de vérification automatique que la réponse du LLM s'appuie réellement sur les sources fournies (impossible à garantir de manière fiable post-génération).
- Pas de post-traitement lourd de citation qui bloquerait la réponse en cas d'absence.
- Pas de modification du modèle LLM ou du provider.

### 5. Prérequis
- P1-1 (récupération Knowledge/RAG par les agents, sources déjà injectées avec `source`/`kind`).

### 6. Stratégie d'implémentation technique
- Étendre `prompt_guard.py` : l'instruction sticky rappelle que les blocs `<data>` sont des données récupérées avec provenance.
- Dans `executor.py`, ajouter une fonction utilitaire de résolution de citation `[src:N]` vers `(titre, source)` du document RAG/knowledge du contexte.
- Le post-traitement de citation reste optionnel et en dégradation gracieuse (absence de citation ne bloque pas la réponse).

### 7. Fichiers et modules potentiellement affectés
- `core/agents/executor.py` (fonction de résolution de citation, post-traitement optionnel).
- `core/security/prompt_guard.py` (instruction sticky étendue).
- `core/rag/context.py` (numérotation des sources cohérente, réutilisation).

### 8. Considérations de sécurité
- Les citations ne doivent pas révéler de métadonnées internes au-delà de ce qui est déjà dans le contexte injecté.
- Pas de citation d'informations non autorisées (gating P0/P1-1 préservé).

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API.
- Contrat interne : format de citation `[src:N]` et fonction de résolution vers `(titre, source)`.

### 10. Stratégie de tests
- Test : détection de citation `[src:1]` dans une réponse de test.
- Test : résolution de citation `[src:N]` vers `(titre, source)` du contexte.
- Test : absence de citation ne bloque pas la réponse (dégradation gracieuse).

### 11. Critères d'acceptation mesurables
- La réponse de l'agent peut contenir des références `[src:N]` mappées aux sources du contexte.
- Une fonction utilitaire permet de résoudre `[src:N]` vers `(titre, source)` du document RAG/knowledge.
- L'absence de citation ne bloque pas la réponse (dégradation gracieuse).
- L'information utilisée dans les réponses est identifiable par son origine (source).

### 12. Risques et considérations de rollback
- Risque : extraction de citations depuis un texte généré par LLM est imperfecte. Atténuation : traiter comme une aide, pas une preuve absolue ; dégradation gracieuse. Rollback : désactiver le post-traitement de citation.

### 13. Définition de Fini (DoD)
- Fonction de résolution de citation `[src:N]` → `(titre, source)` implémentée et testée.
- L'information utilisée dans les réponses est identifiable par son origine.
- Dégradation gracieuse en cas d'absence de citation.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : les blocs `<data>` portent déjà `source`/`kind` ; `build_context_multi` numérote les sources ; aucune citation formelle n'existe dans les réponses LLM.
- **Recommandations architecturales** : citation formelle comme aide à la traçabilité, pas comme preuve absolue ; dégradation gracieuse.
- **Hypothèses non vérifiées** : la fiabilité de l'extraction de citations depuis un texte LLM n'est pas évaluée.
- **Questions pour le responsable du projet** : le niveau de formalisme des citations requis (simple `[src:N]` ou traçabilité stricte vers un enregistrement source) ?

---

## Mission P1-3 — Gestion de contexte consciente des tokens (P1)

### 1. Objectif
Introduire une gestion de contexte consciente des tokens en utilisant les informations de la fenêtre de contexte du modèle (`ModelInfo.context_length`), définir les limites de qualité, pertinence et contexte de la récupération, et éviter le dépassement de la fenêtre du modèle.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/rag/pipeline.py` : `max_context_chars = 8000` (défaut, borne en caractères bruts, ligne 62), `top_k = 5` (défaut, ligne 61).
- `core/llm/types.py` : `ModelInfo.context_length` défaut 4096 (déclaratif, ligne 104), **non utilisé pour tronquer le prompt**.
- `core/rag/context.py` : `RAGContext.build_context` assemble un contexte borné par caractères avec sources (lignes 37-86).
- `core/rag/embeddings.py` : `RAGEmbeddings` utilise `LLMClient` ; mode mock (vecteurs nuls de dim 8) si absent (lignes 39-48).

### 3. Périmètre
- Remplacer ou compléter la borne brute de 8000 caractères par un comptage de tokens estimé basé sur `ModelInfo.context_length`.
- Définir les limites de qualité, pertinence et contexte de la récupération (top_k, max_context, troncation).
- Émettre un avertissement si le contexte est tronqué.
- Ne pas introduire de tokenizer réel dans le Core (dépend du provider LLM) ; utiliser une estimation (ex. caractères/4) avec avertissement.

### 4. Exclusions explicites
- Pas de tokenizer réel intégré au Core (dépend du provider LLM sélectionné au runtime).
- Pas de modification du modèle LLM ou de sa fenêtre de contexte déclarée.
- Pas d'adaptation dynamique complexe sans données réelles de tokenizer.

### 5. Prérequis
- P1-1 (récupération Knowledge/RAG par les agents, contexte déjà injecté avec `max_context_chars`).
- `ModelInfo.context_length` déjà présent (déclaratif).

### 6. Stratégie d'implémentation technique
- Dans `core/rag/pipeline.py` et `core/rag/context.py`, ajouter un comptage de tokens estimé basé sur `ModelInfo.context_length` du modèle sélectionné.
- Borner le contexte injecté à cette limite (en tokens estimés).
- Émettre un avertissement si le contexte est tronqué.
- `RAGPipeline.stats()` reflète le mode de comptage utilisé.

### 7. Fichiers et modules potentiellement affectés
- `core/rag/pipeline.py` (`max_context_chars`, comptage tokens).
- `core/rag/context.py` (troncation consciente des tokens).
- `core/llm/types.py` (réutilisation de `ModelInfo.context_length`, pas de modification).
- `core/agents/executor.py` (construction du system prompt, réutilisation).

### 8. Considérations de sécurité
- Pas de fuite d'information : le comptage de tokens ne révèle que des métriques de taille, pas du contenu.
- Le troncation ne doit pas supprimer de manière sélective des sources autorisées de façon à biaiser la réponse (troncation neutre, par ordre de pertinence).

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API.
- `RAGPipeline.stats()` et `get_config()` reflètent le mode de comptage et la limite effective.

### 10. Stratégie de tests
- Test : le contexte injecté ne dépasse pas `ModelInfo.context_length` (tokens estimés) pour le modèle sélectionné.
- Test : avertissement émis si le contexte est tronqué.
- Test : `RAGPipeline.stats()` reflète le mode de comptage utilisé.
- Test de dépassement de fenêtre avec un modèle à petite fenêtre.

### 11. Critères d'acceptation mesurables
- La construction du contexte respecte les limites de tokens du modèle sélectionné.
- Les échecs de récupération ou de troncation sont observables et gérés explicitement (avertissement).
- Aucune implémentation parallèle de gestion de contexte n'est introduite.

### 12. Risques et considérations de rollback
- Risque : estimation caractères/4 imprécise. Atténuation : avertissement documenté, marge de sécurité. Rollback : revenir à la borne 8000 caractères.
- Risque : troncation biaisée. Atténuation : troncation neutre par ordre de pertinence.

### 13. Définition de Fini (DoD)
- Le contexte injecté respecte `ModelInfo.context_length` (tokens estimés).
- Avertissement de troncation implémenté.
- `RAGPipeline.stats()` reflète le mode de comptage.
- Tests de troncation et de dépassement de fenêtre passent.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `max_context_chars=8000` (caractères bruts) ; `ModelInfo.context_length=4096` déclaratif et inutilisé ; pas de tokenizer dans le Core.
- **Recommandations architecturales** : estimation caractères/4 avec marge de sécurité et avertissement ; ne pas intégrer de tokenizer réel tant qu'aucun provider n'est sélectionné.
- **Hypothèses non vérifiées** : la précision de l'estimation caractères/4 n'est pas évaluée.
- **Questions pour le responsable du projet** : quelle marge de sécurité appliquer entre le contexte et la fenêtre du modèle ?

---

# MISSION P2 — Intégration DAĒNĀ ↔ DTAI (Haute)

## Mission P2-1 — Contrats de métadonnées canoniques (DTAI → DAĒNĀ, lecture seule)

### 1. Objectif
Établir le contrat de métadonnées canonique permettant à DAĒNĀ d'indexer, en lecture seule, les métadonnées des applications et capacités DTAI (manifest, contrats, empreintes, états de cycle de vie) sans gérer leur cycle de vie. Définir la propriété de chaque entité de données et prévenir les dépendances circulaires.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/applications/application_registry.py` : `ApplicationIntegrationRegistry` (enregistrement, états REGISTERED/VALIDATED/AVAILABLE/UNAVAILABLE/WITHDRAWN, verrou fcntl).
- `core/applications/capabilities.py` : `CapabilityRegistry` (définitions versionnées, `CapabilityDefinition` avec statut, sensibilité, permissions).
- `core/applications/capability_contract.py` : `ApplicationCapabilityContract` (contrats avec `input_schema`/`output_schema` JSON Schema, `required_permissions`, `timeout_seconds`).
- `core/applications/permissions.py` : `PermissionService`, `HumanAuthority`, `PermissionScope`, `PermissionGrant`, `manifest_fingerprint` (SHA-256 canonique).
- `core/applications/manifest_repository.py` : stockage SQLite durable (`delete()` lève `NotImplementedError` — pas de suppression silencieuse).
- `core/engineering_memory/vault.py` : `VaultService` (read-only par construction, lecture du vault Obsidian).
- `core/knowledge/manager.py` : `KnowledgeManager` (nœuds de type SOURCE/RULE/DOCUMENT).
- **Aucun contrat explicite actuel entre DTAI et DAĒNĎ** : les deux systèmes sont indépendants ; pas d'indexation des métadonnées DTAI dans le vault ou Knowledge.

### 3. Périmètre
- Définir les métadonnées canoniques à indexer (manifest, contrats de capacité, empreintes, états de cycle de vie).
- Définir la propriété de chaque entité : DTAI reste propriétaire canonique de l'état du cycle de vie des applications ; DAĒNĀ reste propriétaire canonique de la connaissance et de la mémoire.
- Indexer en lecture seule via l'API publique ou `CoreRecordStore` (jamais d'import direct des services DTAI dans DAĒNĀ).
- Prévenir les dépendances circulaires (DAĒNĀ lit DTAI via API publique/CoreRecordStore ; DTAI n'importe pas VaultService/KnowledgeManager).

### 4. Exclusions explicites
- DAĒNĀ ne démarre, n'arrête, n'installe ni ne désinstalle aucune application.
- Pas de création d'un second Application Manager, Registry ou moteur d'intégration.
- Pas d'écriture dans les stores DTAI depuis DAĒNĀ (lecture seule).

### 5. Prérequis
- P0-1 (autorisation HROT — l'indexation des métadonnées DTAI peut exposer des informations sensibles ; l'accès à ces index par les agents doit être autorisé).
- `ApplicationIntegrationRegistry`, `CapabilityRegistry`, `CapabilityCapabilityContract` déjà présents.

### 6. Stratégie d'implémentation technique
- Créer un module d'indexation lecture seule (ex. `core/applications/daena_indexer.py` ou similaire) appelé depuis l'API ou un job léger.
- Pour chaque application enregistrée : produire un nœud Knowledge (type SOURCE) avec le manifest et un record Engineering Memory (type COMPONENT/EVIDENCE) avec `manifest_fingerprint`.
- Pour chaque capacité enregistrée : produire un nœud Knowledge (type RULE) avec `input_schema`/`output_schema`.
- Toute modification de manifeste invalide l'empreinte et produit un nouvel enregistrement (traçabilité).
- L'indexation se fait via `CoreRecordStore` ou l'API publique, sans importer les services DTAI.

### 7. Fichiers et modules potentiellement affectés
- Nouveau module d'indexation lecture seule (à créer dans `core/applications/` ou `core/engineering_memory/`).
- `core/applications/application_registry.py` (événements d'indexation, réutilisation).
- `core/engineering_memory/service.py` (écriture des records EVIDENCE/COMPONENT, réutilisation).
- `core/knowledge/manager.py` (création des nœuds Knowledge, réutilisation).

### 8. Considérations de sécurité
- L'indexation est lecture seule ; aucune information secrète (clés API, tokens) n'est indexée (les secrets sont déjà exclus des configs persistées, voir `persistable_backend_config` dans `core/rag/pipeline.py`).
- L'accès des agents aux métadonnées indexées est gated par l'autorisation P0.
- `manifest_fingerprint` détecte les modifications post-autorisation.

### 9. Implications API et contrats de données
- Contrat de métadonnées canonique : manifest (app_id, name, version, publisher, digest), contrat de capacité (capability_id, category, input/output_schema), empreinte (`manifest_fingerprint`), état de cycle de vie.
- Propriété : DTAI = état du cycle de vie ; DAĒNĀ = connaissance et mémoire indexées.
- Aucun nouvel endpoint API externe (indexation interne).

### 10. Stratégie de tests
- Test : application enregistrée produit un nœud Knowledge SOURCE et un record Engineering Memory avec `manifest_fingerprint`.
- Test : capacité enregistrée produit un nœud Knowledge RULE avec `input_schema`/`output_schema`.
- Test : modification de manifeste invalide l'empreinte et produit un nouvel enregistrement.
- Test : absence de dépendance circulaire (DAĒNĀ n'importe pas VaultService/KnowledgeManager depuis DTAI).

### 11. Critères d'acceptation mesurables
- DAĒNĀ peut récupérer des informations documentées sur les applications DTAI enregistrées.
- DTAI reste le propriétaire canonique de l'état du cycle de vie des applications.
- DAĒNĀ reste le système canonique de connaissance et de mémoire.
- Les modifications et événements sont traçables à leur application ou intégration d'origine.
- Les contrats sont explicites et versionables.
- DAĒNĀ ne démarre/arrête/installe/désinstalle aucune application (revue de code).

### 12. Risques et considérations de rollback
- Risque : dépendance circulaire si DAĒNĀ importe des services DTAI. Atténuation : lecture via API publique/CoreRecordStore uniquement. Rollback : retirer l'import direct.
- Risque : indexation de données sensibles. Atténuation : exclusion des secrets, gating P0. Rollback : désactiver l'indexation.

### 13. Définition de Fini (DoD)
- Module d'indexation lecture seule fonctionnel (manifest → nœud SOURCE, contrat → nœud RULE, empreinte → record EVIDENCE).
- Traçabilité des modifications de manifeste via `manifest_fingerprint`.
- Absence de dépendance circulaire confirmée par revue de code.
- DAĒNĀ ne gère pas le cycle de vie des applications.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `ApplicationIntegrationRegistry`, `CapabilityRegistry`, `CapabilityContract`, `manifest_fingerprint`, `VaultService` read-only existent ; aucun contrat DTAI→DAĒNĀ actuel.
- **Recommandations architecturales** : indexation lecture seule via API publique/CoreRecordStore ; DTAI propriétaire du cycle de vie, DAĒNĀ propriétaire de la connaissance.
- **Hypothèses non vérifiées** : l'injection effective de `engineering_memory_integration` depuis `main.py` n'est pas prouvée dynamiquement.
- **Questions pour le responsable du projet** : quelles métadonnées DTAI exactement doivent être indexées dans DAĒNĀ (tout le manifest ou un sous-ensemble) ?

---

## Mission P2-2 — Stratégie d'événements et de synchronisation (P2)

### 1. Objectif
Définir la stratégie d'événements et de synchronisation entre DTAI et DAĒNĀ : indexer les événements et l'historique DTAI, gérer le versioning et la provenance, et rendre ces informations récupérables par les agents autorisés.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/applications/observability.py` : `EventCollector`, `IntegrationEvent`, `OBSERVABILITY_SCHEMA_VERSION` ; `ApplicationIntegrationRegistry` enregistre des événements (registration, etc.) avec `event_id`, `schema_version`, `app_id`, `instance_id`, `timestamp`, `event_type`, `operation`, `status`, `provenance`, `evidence_refs`, `origin`.
- `core/capability_manager/manager.py` : opérations persistées dans `CoreRecordStore` (domaine `capability_operations`), rétention 24h, 50 max, réconciliation au démarrage (`recover_operations`).
- `core/applications/manifest_repository.py` : version incrémentée à chaque `update`.
- `core/engineering_memory/service.py` : `_append_audit` écrit dans `_meta/MEMORY_EVENT_LOG.ndjson` (audit log des événements mémoire).
- Pas de stratégie de synchronisation explicite DTAI → DAĒNĀ aujourd'hui.

### 3. Périmètre
- Définir quels événements DTAI sont indexés dans DAĒNĀ (registration, changement de cycle de vie, invocation de capacité, modification de manifeste).
- Définir la stratégie de synchronisation (événementiel, batch, ou à la demande).
- Gérer le versioning des manifests et la provenance des événements.
- Rendre ces informations récupérables par les agents autorisés (via Knowledge/RAG ou Engineering Memory).

### 4. Exclusions explicites
- Pas de synchronisation bidirectionnelle (DTAI reste propriétaire de l'état ; DAĒNą indexe en lecture).
- Pas de nouveau bus d'événements ; réutiliser `EventBus` et `EventCollector` existants.
- Pas de modification du cycle de vie DTAI existant.

### 5. Prérequis
- P2-1 (contrats de métadonnées canoniques).
- P0-1 (autorisation — l'accès des agents aux événements indexés doit être autorisé).

### 6. Stratégie d'implémentation technique
- Réutiliser `EventCollector` / `IntegrationEvent` pour capturer les événements DTAI pertinents.
- Projeter les événements sélectionnés dans DAĒNĀ via `EngineeringMemoryService` (records de type ENGINEERING_EVENT) ou `KnowledgeManager` (nœuds), selon la nature de l'information.
- Versioning : chaque `manifest_repository.update` incrémente la version ; l'empreinte (`manifest_fingerprint`) détecte les changements.
- Provenance : chaque événement indexé porte `origin` (application/integration d'origine) et `evidence_refs`.

### 7. Fichiers et modules potentiellement affectés
- `core/applications/observability.py` (sélection des événements à projeter, réutilisation).
- `core/applications/manifest_repository.py` (versioning, réutilisation).
- `core/engineering_memory/service.py` (écriture des records d'événements, réutilisation).
- `core/knowledge/manager.py` (éventuelle création de nœuds pour les événements significatifs).

### 8. Considérations de sécurité
- Les événements indexés ne doivent pas contenir de secrets (tokens, clés API).
- L'accès des agents aux événements est gated par l'autorisation P0.
- `manifest_fingerprint` garantit l'intégrité de la provenance.

### 9. Implications API et contrats de données
- Contrat d'événement : `event_id`, `schema_version`, `app_id`, `instance_id`, `timestamp`, `event_type`, `operation`, `status`, `provenance`, `evidence_refs`, `origin`.
- Versioning : incrémentation de version à chaque modification de manifeste.
- Aucun nouvel endpoint API externe.

### 10. Stratégie de tests
- Test : un événement de changement de cycle de vie DTAI est projeté dans DAĒNĀ (record Engineering Memory ou nœud Knowledge).
- Test : le versioning de manifeste est conservé (empreinte change si manifeste modifié).
- Test : la provenance (`origin`, `evidence_refs`) est préservée.
- Test : accès aux événements indexés gated par l'autorisation P0.

### 11. Critères d'acceptation mesurables
- Les événements DTAI (registration, cycle de vie, invocation, modification de manifeste) sont indexés et récupérables.
- Le versioning et la provenance sont préservés.
- L'accès aux événements par les agents est soumis à l'autorisation P0.
- Pas de dépendance circulaire (DTAI n'importe pas les services de lecture de DAĒNĀ).

### 12. Risques et considérations de rollback
- Risque : surcoût de collecte d'événements. Atténuation : ne projeter que les événements significatifs. Rollback : réduire le périmètre d'événements indexés.
- Risque : fuite de métadonnées sensibles. Atténuation : exclusion des secrets, gating P0.

### 13. Définition de Fini (DoD)
- Stratégie d'événements et de synchronisation définie et implémentée (lecture seule).
- Versioning et provenance des événements préservés.
- Accès aux événements indexés gated par P0.
- Tests d'événements, versioning, provenance passent.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `EventCollector`/`IntegrationEvent` existent ; opérations persistées 24h/50 max ; `manifest_repository.update` incrémente la version ; `_append_audit` écrit le audit log ndjson.
- **Recommandations architecturales** : projeter uniquement les événements significatifs ; réutiliser `EventBus`/`EventCollector` ; pas de nouveau bus.
- **Hypothèses non vérifiées** : la fréquence et le volume des événements DTAI en production ne sont pas connus.
- **Questions pour le responsable du projet** : quels événements DTAI doivent être indexés dans DAĒNĀ (tous ou un sous-ensemble significatif) ?

---

## Mission P2-3 — Gestion des erreurs, cohérence, propriété et prévention des dépendances circulaires (P2)

### 1. Objectif
Définir la gestion des erreurs et de la cohérence entre DTAI et DAĒNĀ, clarifier la propriété de chaque entité de données, et prévenir les dépendances circulaires entre les deux systèmes.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/applications/manifest_repository.py` : `delete()` lève `NotImplementedError` (pas de suppression silencieuse ; retrait par policy, pas suppression silencieuse).
- `core/applications/capability_execution.py` : `TRUSTED_IMPLEMENTATION_ALIASES = {"odin.runtime-status", "frame.runtime-status"}` ; `invoke_capability` valide contrat, binding, activation, input_schema (jsonschema), appelle l'implémentation allowlistée avec timeout, retourne `CapabilityExecutionResult`.
- `core/applications/permissions.py` : `manifest_fingerprint` détecte les modifications post-autorisation (`MANIFEST_CHANGED`).
- Pas de stratégie d'erreur/cohérence explicite entre DTAI et DAĒNĀ aujourd'hui.
- Pas de dépendance circulaire actuelle (les deux systèmes sont indépendants).

### 3. Périmètre
- Définir le comportement en cas d'erreur d'indexation (DAĒNĀ ne doit pas bloquer DTAI).
- Définir la propriété de chaque entité : DTAI = état du cycle de vie des applications ; DAĒNĀ = connaissance et mémoire.
- Prévenir les dépendances circulaires (DAĒNĀ lit DTAI via API publique/CoreRecordStore ; DTAI n'importe pas les services de DAĒNĀ).
- Définir la gestion de la cohérence (que se passe-t-il si un manifeste est modifié ou retiré côté DTAI ?).

### 4. Exclusions explicites
- DAĒNĀ ne gère pas le cycle de vie des applications.
- DTAI ne gère pas la connaissance.
- Pas de suppression silencieuse de manifests (respecter `NotImplementedError` de `manifest_repository.delete`).

### 5. Prérequis
- P2-1 (contrats de métadonnées canoniques).
- P0-1 (autorisation).

### 6. Stratégie d'implémentation technique
- L'indexation DTAI → DAĒNĀ est fire-and-forget avec dégradation gracieuse : une erreur d'indexation ne doit pas bloquer l'opération DTAI.
- En cas de modification/retrait de manifeste côté DTAI, l'empreinte change et un nouvel enregistrement est produit côté DAĒNĀ (traçabilité, pas de suppression silencieuse).
- Revue de code pour confirmer l'absence d'import des services DAĒNĀ depuis DTAI.

### 7. Fichiers et modules potentiellement affectés
- Module d'indexation lecture seule (créé en P2-1).
- `core/applications/manifest_repository.py` (gestion du retrait par policy, réutilisation).
- `core/applications/capability_execution.py` (gestion d'erreur d'invocation, réutilisation).

### 8. Considérations de sécurité
- Une erreur d'indexation côté DAĒNĀ ne doit pas exposer d'information interne ni bloquer DTAI.
- L'absence de dépendance circulaire est une propriété de sécurité (isolation des systèmes).

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API.
- Contrat d'erreur : dégradation gracieuse, journalisation de l'erreur d'indexation sans blocage de DTAI.

### 10. Stratégie de tests
- Test : erreur d'indexation côté DAĒNą ne bloque pas l'opération DTAI (dégradation gracieuse).
- Test : absence d'import des services DAĒNĀ depuis les modules DTAI (revue de code / test d'import).
- Test : modification de manifeste produit un nouvel enregistrement côté DAĒNĀ (pas de suppression silencieuse).

### 11. Critères d'acceptation mesurables
- Une erreur d'indexation DTAI → DAĒNĀ ne bloque pas DTAI.
- La propriété de chaque entité est claire (DTAI = cycle de vie, DAĒNĀ = connaissance/mémoire).
- Aucune dépendance circulaire entre DTAI et DAĒNĀ.
- Pas de suppression silencieuse de manifests.

### 12. Risques et considérations de rollback
- Risque : couplage accidentel via import. Atténuation : test d'import + revue de code. Rollback : retirer l'import.
- Risque : incohérence entre l'état DTAI et l'index DAĒNĀ. Atténuation : empreinte `manifest_fingerprint` + traçabilité (pas de suppression silencieuse).

### 13. Définition de Fini (DoD)
- Gestion d'erreur d'indexation en dégradation gracieuse (DTAI non bloqué).
- Propriété des entités documentée.
- Absence de dépendance circulaire confirmée.
- Tests d'erreur et d'absence d'import passent.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `delete()` lève `NotImplementedError` ; `invoke_capability` valide contrat+binding+activation+schema ; `manifest_fingerprint` détecte les modifications ; pas de dépendance circulaire actuelle.
- **Recommandations architecturales** : indexation fire-and-forget avec dégradation gracieuse ; empreinte pour traçabilité ; pas de suppression silencieuse.
- **Hypothèses non vérifiées** : le volume d'erreurs d'indexation en production n'est pas connu.
- **Questions pour le responsable du projet** : quelle politique de retrait (witdrawal) appliquer quand une application est retirée côté DTAI (marquer comme retiré dans l'index DAĒNĀ ou conserver l'historique) ?

---

# MISSION P3 — Consolidation de l'architecture et fiabilité (Consolidation)

## Mission P3-1 — Routeurs API orphelins : identification de l'implémentation canonique (P3)

### 1. Objectif
Résoudre les routeurs API orphelins : identifier l'implémentation canonique pour chaque responsabilité API, vérifier la propriété des endpoints, les conflits de routes et l'exposition OpenAPI, et supprimer ou monter les routeurs de manière explicite — sans montage aveugle.

### 2. État actuel et preuves du code source (faits confirmés)
- `interfaces/api/main.py` : monte le router `v1` (ligne 147-160) ainsi que d'autres routers dédiés (`knowledge_imports`, `web_ingest`, `web_search`, `capabilities`, etc.).
- `interfaces/api/routers/knowledge.py` : routeurs définis mais **non montés** dans `main.py` (orphelins, dupliqués dans `v1.py`).
- `interfaces/api/routers/engineering_memory.py` : routeur défini mais **non monté** dans `main.py` (orphelin, chevauche `/v1/memory/*` de `v1.py` mais ajoute des routes vault/records uniques).
- `interfaces/api/routers/v1.py` : contient les endpoints Knowledge, Memory/Facts et RAG réels (montés).
- Aucun test pour `engineering_memory.py`, `capabilities.py`, `knowledge.py` (dédié), `knowledge_imports.py`.
- Pas de schéma Pydantic d'entrée dans les handlers (`dict[str, Any]` partout, validation déléguée aux managers Core).

### 3. Périmètre
- Identifier l'implémentation canonique pour chaque responsabilité API (Knowledge, Memory, RAG, etc.).
- Vérifier la propriété des endpoints (quel routeur possède quel endpoint).
- Vérifier les conflits de routes et l'exposition OpenAPI.
- Monter explicitement le routeur canonique ou supprimer les routeurs orphelins redondants.
- Ne pas monter les routeurs orphelins "en aveugle" sans vérifier les conflits.

### 4. Exclusions explicites
- Ne pas monter un routeur orphelin sans avoir vérifié qu'il ne crée pas de conflit de route avec `v1.py`.
- Ne pas modifier les handlers existants de `v1.py` au-delà de ce qui est nécessaire pour résoudre l'ambiguïté.
- Ne pas introduire de nouveaux endpoints.

### 5. Prérequis
- P2-1 (contrats de métadonnées — les métadonnées DTAI indexées peuvent utiliser les endpoints Knowledge/RAG canoniques).
- Analyse des conflits de routes (grep des appels côté client).

### 6. Stratégie d'implémentation technique
- Grep des appels aux endpoints orphelins côté client (WebUI, tests) pour vérifier s'ils sont utilisés.
- Comparer `knowledge.py` et `engineering_memory.py` avec `v1.py` pour identifier les endpoints uniques (s'il y en a) vs les doublons.
- Décider : monter explicitement le routeur canonique (si endpoints uniques justifiés) ou supprimer les routeurs orphelins (si purement redondants).
- Vérifier l'exposition OpenAPI (pas d'endpoints dupliqués).

### 7. Fichiers et modules potentiellement affectés
- `interfaces/api/main.py` (montage explicite ou suppression).
- `interfaces/api/routers/knowledge.py` (suppression si redondant).
- `interfaces/api/routers/engineering_memory.py` (suppression ou montage explicite des routes vault/records uniques).
- `interfaces/api/routers/v1.py` (éventuelle consolidation des routes uniques).

### 8. Considérations de sécurité
- Pas d'endpoint exposé accidentellement sans autorisation (tous les endpoints montés doivent avoir leur `require_permission` approprié).
- Vérifier que les routes vault/records (si conservées) ont bien `memory_read_permission` / `memory_record_permission`.

### 9. Implications API et contrats de données
- Une responsabilité API = une implémentation canonique.
- Pas d'endpoints dupliqués dans OpenAPI.
- Pas de casse des clients existants (vérifier les appels côté client avant suppression).

### 10. Stratégie de tests
- Test : pas d'endpoint dupliqué dans l'OpenAPI généré.
- Test : `npx tsc --noEmit` (WebUI) et les tests Python API restent verts.
- Test : grep des appels côté client aux endpoints orphelins (vérifier qu'aucun client ne dépend d'une route orpheline avant suppression).
- Régression : `tests/interfaces/test_knowledge_tree.py`, `tests/interfaces/test_rag_strategies.py`, `tests/interfaces/test_engineering_memory_vault_router.py` restent verts.

### 11. Critères d'acceptation mesurables
- Une implémentation canonique par responsabilité API.
- Aucun endpoint dupliqué dans OpenAPI.
- Aucun client existant cassé.
- Le comportement existant reste compatible.

### 12. Risques et considérations de rollback
- Risque : casser un client qui appelle une route orpheline. Atténuation : grep des appels avant suppression ; rollback par restauration du routeur orphelin.
- Risque : exposer une route sans autorisation. Atténuation : vérifier `require_permission` sur chaque route conservée.

### 13. Définition de Fini (DoD)
- Implémentation canonique identifiée et montées/supprimées explicitement.
- Aucun endpoint dupliqué dans OpenAPI.
- Tests API et typecheck WebUI verts.
- Aucun client cassé (revue des appels côté client).

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `knowledge.py` et `engineering_memory.py` non montés, dupliqués dans `v1.py` ; `v1.py` contient les endpoints réels montés ; aucun test pour les routeurs orphelins.
- **Recommandations architecturales** : ne pas monter en aveugle ; vérifier les conflits de route et les appels client avant toute décision.
- **Hypothèses non vérifiées** : les routes vault/records uniques de `engineering_memory.py` ne sont peut-être pas appelées par le client WebUI (le WebUI utilise `v1.py` pour `/v1/memory/facts`/`events`).
- **Questions pour le responsable du projet** : faut-il conserver les routes vault/records uniques de `engineering_memory.py` ou les intégrer dans `v1.py` ?

---

## Mission P3-2 — Duplication Odin/ComposeService (P3)

### 1. Objectif
Investiguer et résoudre la duplication entre `core/plugins/odin.py` (`OdinService`, 819 lignes, ne hérite pas de `ComposeService`) et `core/plugins/compose_service.py` (cycle de vie Docker générique), en faisant hériter `OdinService` de `ComposeService` si possible sans perte de fonctionnalité.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/plugins/compose_service.py` : `ComposeService` générique (start, stop, restart, install, uninstall, get_status, get_logs, check_health, confinement, allowlist des commandes docker compose).
- `core/plugins/odin.py` : `OdinService` (819 lignes) duplique massivement `ComposeService` (`_run_docker`, `get_status`, `start`, `stop`, `restart`, `install`, `uninstall`, `get_logs`, `_build_status_dict`). Ne hérite **pas** de `ComposeService`.
- `core/plugins/frame.py` : `FrameService` hérite proprement de `ComposeService` (pas de duplication comme Odin).
- `core/plugins/quantar.py` : `QuantarService` hérite de `ComposeService`.

### 3. Périmètre
- Faire hériter `OdinService` de `ComposeService` pour supprimer la duplication (~700 lignes).
- Préserver les spécificités d'Odin (port 4173, santé HTTP `http://127.0.0.1:4173/`, redaction des secrets dans les logs, contrôleur externe optionnel via `ETHAN_ODIN_CONTROLLER_URL`/`TOKEN`, `get_metadata()` lit `package.json`).

### 4. Exclusions explicites
- Pas de modification du comportement de cycle de vie d'Odin (start/stop/restart/install/uninstall/get_status/get_logs identiques).
- Pas de modification des endpoints API Odin.

### 5. Prérequis
- P2-1 (contrats de métadonnées — Odin est une application DTAI enregistrée).
- Compréhension complète des spécificités d'Odin avant refactor.

### 6. Stratégie d'implémentation technique
- Extraire les méthodes communes de `OdinService` vers `ComposeService` (ou faire hériter `OdinService` de `ComposeService` et surcharger uniquement les spécificités).
- Préserver le contrôleur externe, la santé HTTP, la redaction des secrets et `get_metadata()`.
- Tester que `OdinService` conserve toutes ses fonctionnalités après refactor.

### 7. Fichiers et modules potentiellement affectés
- `core/plugins/odin.py` (refactor vers héritage).
- `core/plugins/compose_service.py` (éventuelle extension pour accueillir les spécificités Odin si nécessaire).

### 8. Considérations de sécurité
- Préserver la redaction des secrets dans les logs d'Odin.
- Préserver l'allowlist des commandes docker compose et le confinement (`compose.yaml` exactement à `<repo>/compose.yaml`).

### 9. Implications API et contrats de données
- Aucun changement d'API (le comportement est identique).
- Aucun changement de contrat de données.

### 10. Stratégie de tests
- Test de démarrage/arrêt/santé d'Odin après refactor.
- Test de redaction des secrets dans les logs.
- Régression : tests Odin existants restent verts.

### 11. Critères d'acceptation mesurables
- `OdinService` hérite de `ComposeService` sans perte de fonctionnalité.
- Les tests existants Odin passent.
- La duplication de code est mesurablement réduite (diff avant/après).

### 12. Risques et considérations de rollback
- Risque : perte d'une spécificité d'Odin lors du refactor. Atténuation : tests complets avant/après ; rollback par restauration de `odin.py`.
- Risque : régression du cycle de vie Docker. Atténuation : tests d'intégration avec Docker réel si disponible.

### 13. Définition de Fini (DoD)
- `OdinService` hérite de `ComposeService`.
- Fonctionnalité Odin préservée (tests verts).
- Duplication mesurablement réduite.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `OdinService` duplique `ComposeService` (~700 lignes) et ne l'hérite pas ; `FrameService` et `QuantarService` héritent proprement.
- **Recommandations architecturales** : refactor incrémental vers l'héritage, préserver toutes les spécificités Odin.
- **Hypothèses non vérifiées** : la santé HTTP d'Odin (`http://127.0.0.1:4173/`) et le contrôleur externe ne sont pas testés dans ce périmètre.
- **Questions pour le responsable du projet** : les spécificités d'Odin (contrôleur externe, port 4173) doivent-elles être généralisées dans `ComposeService` pour les futures applications ?

---

## Mission P3-3 — Opérations du cycle de vie des manifests (P3)

### 1. Objectif
Compléter les opérations du cycle de vie des manifests là où justifié, en respectant la politique de retrait (pas de suppression silencieuse).

### 2. État actuel et preuves du code source (faits confirmés)
- `core/applications/manifest_repository.py` : `ApplicationManifestRepository` (SQLite, `create`, `update` version incrémentée, `get_current`, `get`, `by_id`, `list`). **`delete()` lève `NotImplementedError`** (politique de retrait par policy, pas suppression silencieuse).
- `core/applications/application_registry.py` : `withdraw(app_id, instance_id, reason)` → état `WITHDRAWN`, `available=False`.
- Pas d'endpoint de mise à jour du code source de l'application (pas de git pull automatisé).

### 3. Périmètre
- Vérifier si des opérations de cycle de vie des manifests sont manquantes et justifiées (ex. mise à jour de version, retrait formel).
- Respecter la politique : pas de suppression silencieuse (`delete()` reste `NotImplementedError`).
- Ne pas créer de mécanisme de mise à jour du code source (git pull) sans décision du propriétaire.

### 4. Exclusions explicites
- Pas de suppression silencieuse de manifests.
- Pas de mécanisme automatisé de mise à jour du dépôt d'application (git clone/pull) sans décision propriétaire.
- Pas de nouvelle opération destructive.

### 5. Prérequis
- P2-1 (contrats de métadonnées canoniques).
- P2-3 (gestion des erreurs et cohérence).

### 6. Stratégie d'implémentation technique
- Revue des opérations existantes (`create`, `update`, `withdraw`, `register`) pour identifier les lacunes justifiées.
- Si une opération est manquante et justifiée, l'ajouter en respectant `manifest_fingerprint` et la politique de retrait.
- Documenter la décision de ne pas ajouter une opération si elle n'est pas justifiée.

### 7. Fichiers et modules potentiellement affectés
- `core/applications/manifest_repository.py` (éventuelle ajout d'opération justifiée).
- `core/applications/application_registry.py` (réutilisation).

### 8. Considérations de sécurité
- Toute modification de manifeste invalide l'empreinte (`manifest_fingerprint`) et donc l'autorisation liée.
- Pas de suppression silencieuse.

### 9. Implications API et contrats de données
- Contrat de versioning des manifests (incrémentation à chaque `update`).
- Aucun nouvel endpoint API externe sans décision propriétaire.

### 10. Stratégie de tests
- Test : mise à jour de manifeste incrémente la version et change l'empreinte.
- Test : `withdraw` passe l'application en état `WITHDRAWN`.
- Test : `delete()` lève `NotImplementedError` (pas de suppression silencieuse).

### 11. Critères d'acceptation mesurables
- Les opérations du cycle de vie des manifests sont complètes là où justifiées.
- Pas de suppression silencieuse.
- L'empreinte change à chaque modification de manifeste.

### 12. Risques et considérations de rollback
- Risque : ajout d'une opération non justifiée. Atténuation : revue de propriétaire ; rollback par retrait de l'opération.
- Risque : incohérence de versioning. Atténuation : tests de versioning.

### 13. Définition de Fini (DoD)
- Opérations de cycle de vie des manifests revues et complètes là où justifiées.
- `delete()` reste `NotImplementedError` (pas de suppression silencieuse).
- Tests de versioning et de withdraw passent.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `delete()` lève `NotImplementedError` ; `withdraw` existe ; pas de mise à jour de code source automatisée.
- **Recommandations architecturales** : respecter la politique de retrait ; ne pas ajouter d'opération non justifiée.
- **Hypothèses non vérifiées** : le besoin d'opérations supplémentaires de cycle de vie n'est pas confirmé par le propriétaire.
- **Questions pour le responsable du projet** : quelles opérations de cycle de vie des manifests sont considérées comme manquantes et justifiées ?

---

## Mission P3-4 — Observabilité et tests d'intégration (P3)

### 1. Objectif
Améliorer l'observabilité des opérations DTAI (métriques de cycle de vie, temps d'installation, taux d'échec, santé des applications) et compléter les tests d'intégration.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/applications/observability.py` : `EventCollector`, `IntegrationEvent`, `OBSERVABILITY_SCHEMA_VERSION` ; `ApplicationIntegrationRegistry` enregistre des événements d'intégration.
- `core/capability_manager/manager.py` : opérations persistées dans `CoreRecordStore` (domaine `capability_operations`), rétention 24h, 50 max, réconciliation au démarrage.
- `core/metrics/` : analytics, telemetry, logging_config, healthcheck ; Prometheus et OpenTelemetry optionnels.
- Pas de test E2E complet (découverte → enregistrement → installation → démarrage → arrêt → suppression) avec Docker réel.
- Pas de test pour `engineering_memory.py`, `capabilities.py`, `knowledge.py` (dédié), `knowledge_imports.py`.

### 3. Périmètre
- Enrichir l'observabilité des opérations DTAI (événements d'intégration, santé).
- Compléter les tests d'intégration (notamment pour les routeurs et fonctionnalités non testés).
- Ne pas créer de nouveaux services d'observabilité ; réutiliser `EventBus`, `AuditStore`, `core/metrics/`.

### 4. Exclusions explicites
- Pas de nouveau service d'observabilité.
- Pas de test E2E avec Docker réel sans environnement disponible.
- Pas de modification du comportement existant.

### 5. Prérequis
- P2-1 (contrats de métadonnées).
- P3-1 (routeurs canoniques identifiés).

### 6. Stratégie d'implémentation technique
- Vérifier que chaque opération DTAI (install, start, stop, uninstall, invoke) génère un événement `IntegrationEvent`.
- Ajouter des tests d'intégration pour les fonctionnalités non couvertes (routeurs, observabilité).
- Réutiliser `AuditStore` et `EventBus` pour l'audit.

### 7. Fichiers et modules potentiellement affectés
- `core/applications/observability.py` (événements d'intégration, réutilisation).
- `core/capability_manager/manager.py` (opérations persistées, réutilisation).
- Nouveaux tests d'intégration (à créer dans `tests/`).

### 8. Considérations de sécurité
- Les événements d'observabilité ne doivent pas contenir de secrets.
- L'audit est accessible uniquement via les canaux autorisés.

### 9. Implications API et contrats de données
- Contrat d'événement d'observabilité : réutiliser `IntegrationEvent` existant.
- Aucun nouvel endpoint API externe.

### 10. Stratégie de tests
- Test : chaque opération DTAI génère un événement `IntegrationEvent`.
- Test : consultation de l'historique des opérations (24h/50 max existant).
- Test d'intégration pour les fonctionnalités non couvertes.

### 11. Critères d'acceptation mesurables
- Chaque opération DTAI génère un événement `IntegrationEvent`.
- Un endpoint ou une vue permet de consulter l'historique des opérations.
- Tests d'intégration pour les fonctionnalités non couvertes passent.

### 12. Risques et considérations de rollback
- Risque : surcoût de collecte si trop granulaire. Atténuation : événements significatifs uniquement.
- Risque : test E2E avec Docker indisponible. Atténuation : tests avec mocks si Docker absent.

### 13. Définition de Fini (DoD)
- Événements d'intégration pour chaque opération DTAI.
- Historique des opérations consultable.
- Tests d'intégration pour les fonctionnalités non couvertes.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : `EventCollector`/`IntegrationEvent` existent ; opérations persistées 24h/50 max ; pas de test E2E avec Docker réel.
- **Recommandations architecturales** : événements significatifs uniquement ; réutiliser `EventBus`/`AuditStore`.
- **Hypothèses non vérifiées** : disponibilité de Docker réel pour les tests E2E.
- **Questions pour le responsable du projet** : quels événements d'observabilité sont prioritaires ?

---

## Mission P3-5 — Suppression des composants obsolètes (P3, dernière)

### 1. Objectif
Supprimer les composants obsolètes ou redondants uniquement après une analyse de dépendances complète, sans casser les clients existants.

### 2. État actuel et preuves du code source (faits confirmés)
- `core/plugins/odin.py` duplique `core/plugins/compose_service.py` (~700 lignes) — à résoudre en P3-2 avant toute suppression.
- `skills.py` vs `skills_import.py` : duplication des endpoints `/skills/export` et `/skills/import`.
- Alias multiples du registre d'applications (`ApplicationIntegrationRegistry`, `ApplicationRegistry`, `IntegrationRegistry`).
- `ApplicationDiscoveryService` : ~12 alias.
- `core/plugins/registry.py` présent.

### 3. Périmètre
- Après résolution des duplications (P3-2), supprimer les composants redondants confirmés inutilisés.
- Vérifier qu'aucun client (WebUI, CLI, tests) ne dépend du composant avant suppression.
- Ne pas supprimer un composant dont l'usage n'est pas confirmé.

### 4. Exclusions explicites
- Pas de suppression sans analyse de dépendances préalable.
- Pas de suppression d'un composant dont l'usage est incertain.
- Pas d'opération Git destructive.

### 5. Prérequis
- P3-2 (duplication Odin résolue).
- Analyse de dépendances complète (grep des imports et appels).

### 6. Stratégie d'implémentation technique
- Grep des imports et appels pour chaque composant candidat à suppression.
- Vérifier les tests qui référencent le composant.
- Supprimer uniquement si aucun client ni test ne dépend de lui.
- Documenter chaque suppression.

### 7. Fichiers et modules potentiellement affectés
- À déterminer après analyse de dépendances (candidats : alias du registre, `skills_import.py` si redondant avec `skills.py`).

### 8. Considérations de sécurité
- Pas de suppression d'un composant d'autorisation ou de sécurité sans revue.
- Pas de casse des clients existants.

### 9. Implications API et contrats de données
- Aucun nouvel endpoint API.
- Vérifier que la suppression ne casse pas OpenAPI ni les clients.

### 10. Stratégie de tests
- Test d'import et d'appel pour chaque composant candidat (vérifier l'absence de dépendance).
- Tests de régression après chaque suppression.
- `npx tsc --noEmit` (WebUI) et tests Python restent verts.

### 11. Critères d'acceptation mesurables
- Aucun composant supprimé sans analyse de dépendances confirmant l'absence de clients.
- Aucun client cassé.
- Tests de régression verts après chaque suppression.

### 12. Risques et considérations de rollback
- Risque : suppression d'un composant encore utilisé. Atténuation : grep + tests avant suppression ; rollback par restauration (git, pas de destructive operation — restauration manuelle si nécessaire).
- Risque : casse d'OpenAPI. Atténuation : vérification OpenAPI après suppression.

### 13. Définition de Fini (DoD)
- Analyse de dépendances complète pour chaque composant candidat.
- Suppression uniquement des composants confirmés inutilisés.
- Tests de régression verts.

### 14. Sépare : faits confirmés / recommandations / hypothèses / questions
- **Faits confirmés** : duplications identifiées (Odin/ComposeService, skills.py/skills_import.py, alias du registre, ApplicationDiscoveryService).
- **Recommandations architecturales** : suppression uniquement après analyse de dépendances et tests de régression.
- **Hypothèses non vérifiées** : l'usage réel de chaque composant candidat n'est pas confirmé sans grep.
- **Questions pour le responsable du projet** : quels composants dupliqués sont confirmés inutilisables et peuvent être supprimés ?

---

## Dépendances et ordre d'exécution révisé

```
P0-1 (HROT agent execution) ──► P1-1 (Knowledge/RAG retrieval agent)
                                  ├──► P1-2 (citations formelles)
                                  ├──► P1-3 (gestion de contexte tokens)
                                  │
                                  ▼
                            P2-1 (contrats métadonnées DTAI→DAĒNĀ)
                                  ├──► P2-2 (événements et synchronisation)
                                  └──► P2-3 (erreurs, cohérence, propriété, anti-circulaire)
                                  │
                                  ▼
                            P3-1 (routeurs API orphelins — canonique)
                                  ├──► P3-2 (duplication Odin/ComposeService)
                                  ├──► P3-3 (cycle de vie manifests)
                                  ├──► P3-4 (observabilité et tests d'intégration)
                                  └──► P3-5 (suppression composants obsolètes)
```

**Ordre d'exécution recommandé :**
1. **P0-1** — HROT dans le cycle d'exécution agent (sécurité critique, fondement de P1/P2).
2. **P1-1** — Récupération Knowledge/RAG par les agents (dépend de P0-1).
3. **P1-2** — Citations formelles (dépend de P1-1).
4. **P1-3** — Gestion de contexte consciente des tokens (dépend de P1-1).
5. **P2-1** — Contrats de métadonnées canoniques DTAI → DAĒNĀ (dépend de P0-1 et P1-1).
6. **P2-2** — Stratégie d'événements et de synchronisation (dépend de P2-1).
7. **P2-3** — Gestion des erreurs, cohérence, propriété, anti-circulaire (dépend de P2-1).
8. **P3-1** — Routeurs API orphelins (identification du canonique ; consolidation, ne bloque pas P1/P2).
9. **P3-2** — Duplication Odin/ComposeService (dépend de P3-1 pour le contexte canonique).
10. **P3-3** — Cycle de vie des manifests (dépend de P2-1, P2-3).
11. **P3-4** — Observabilité et tests d'intégration (dépend de P2-1, P3-1).
12. **P3-5** — Suppression des composants obsolètes (dernière, après analyse de dépendances complète).

**Raison du déplacement de l'ancienne P0-1 (routeurs) en P3 :** le nettoyage des routeurs est une tâche de consolidation, pas un blocage de sécurité. `v1.py` est le routeur canonique monté ; les routeurs orphelins ne sont pas appelés par les clients existants. P0 doit se concentrer sur l'autorisation HROT, qui est une condition préalable à la récupération de connaissance par les agents (P1).

---

## Risques globaux révisés

| Risque | Probabilité | Impact | Atténuation |
|--------|-------------|--------|-------------|
| Dépendance circulaire DAĒNĀ ↔ DTAI | Moyenne | Élevée | DAĒNĀ lit via API publique/CoreRecordStore uniquement ; DTAI n'importe pas les services DAĒNĀ |
| HROT fail-closed bloque des exécutions légitimes | Moyenne | Élevée | Contexte d'exécution complet avant autorisation ; rollback par désactivation de l'appel |
| Pas de tokenizer réel | Élevée | Moyenne | Estimation caractères/4 avec marge de sécurité et avertissement ; rollback vers 8000 caractères |
| Casse de client lors de la suppression de routeurs orphelins | Moyenne | Moyenne | Grep des appels client avant suppression ; rollback par restauration |
| Duplication Odin/ComposeService non résolue | Faible | Faible | Refactor incrémental, tests avant/après |
| Extraction de citations LLM imperfecte | Moyenne | Basse | Traiter comme aide, pas preuve absolue ; dégradation gracieuse |

---

Fin de la roadmap révisée. En attente de validation explicite du responsable du projet avant toute implémentation.
