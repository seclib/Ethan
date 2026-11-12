# Décisions — ETHAN

Ce fichier distingue les décisions validées, les propositions et les hypothèses. Une ancienne intention n'est pas une décision validée tant qu'elle n'est pas marquée comme telle avec une trace documentaire.

## Décisions validées

### D-001 — Hybride WebUI (2026-08-17)

- **Statut** : validée.
- **Source** : `Obsidian/Engineering/Audits/00-ETAT-DES-LIEUX.md`, section « Contradiction résolue — Décision validée (2026-08-17) ».
- **Contenu** : conserver la WebUI Next.js existante comme base, enrichir avec les concepts UX d'Open WebUI, ne pas abandonner la base existante.
- **Conséquence** : la stratégie de migration historique mentionnant un fork Open WebUI est adaptée, pas suivie littéralement.

### D-002 — Mémoire Codex minimale sans code applicatif (2026-11-01)

### D-003 — Formalisation documentaire de MEM-014 (2026-11-03)

- **Statut** : validée (formalisation documentaire uniquement).
- **Source** : décision utilisateur approuvée ; `Obsidian/_meta/DECISION_REGISTER.md` ; `Obsidian/Architecture/ADR/ADR-MEM-014-application-integration-governance-and-capabilities.md`.
- **Contenu** : MEM-014 (contrat d'interopérabilité, gouvernance, formats, états de capacités, permissions, conformité, résilience, observabilité, ordre de réalisation, trois plans) passe de `PROPOSAL` à `USER_APPROVED`. Aucune implémentation technique.



- **Statut** : validée au titre de la demande documentaire ; validation inter-sessions reste à confirmer.
- **Source** : requête utilisateur et ajout dans `docs/memory/`.
- **Contenu** : mettre en place un système documentaire minimal, sans modification de code, de migration ou de configuration de production.

### D-003 — Formalisation documentaire de MEM-014 (2026-11-03)

- **Statut** : validée (formalisation documentaire uniquement).
- **Source** : décision utilisateur approuvée ; `Obsidian/_meta/DECISION_REGISTER.md` ; `Obsidian/Architecture/ADR/ADR-MEM-014-application-integration-governance-and-capabilities.md`.
- **Contenu** : MEM-014 (contrat d'interopérabilité, gouvernance, formats, états de capacités, permissions, conformité, résilience, observabilité, ordre de réalisation, trois plans) passe de `PROPOSAL` à `USER_APPROVED`. Aucune implémentation technique.

### D-004 — DAĒNĀ P2.7 : découverte documentaire native dans ETHAN Core (2026-11-12)

- **Statut** : validée (implémentation réalisée et testée).
- **Source** : mission « ETHAN OS — DAĒNĀ P2.7.1 — Implémentation native du Knowledge
  Discovery dans ETHAN Core » ; `docs/architecture/dana-p2-7-knowledge-discovery.md`.
- **Contenu** :
  - La découverte documentaire est un **service Core**, pas une Skill ECC, pas un
    agent, pas un daemon. `core/resources/discovery.py` assure le scan pur,
    `core/resources/registry.py` orchestre l'enregistrement et le cycle de vie.
  - **Direction de dépendance unique** : `discovery.py` n'importe pas
    `registry.py`. Le cycle d'import historique est éliminé à la source, sans
    import différé fragile.
  - **Identité documentaire** : UUIDv5 ancré sur le chemin canonique seul, afin
    qu'un changement de titre ou de contenu soit détecté comme une mise à jour
    et non comme une ressource nouvelle. Le catalogue des Skills conserve son
    ancrage `type + chemin + titre`.
  - **Classification** : déterministe, extensible (tables ouvertes), jamais
    arbitraire ; chaque document porte sa justification. `SKILL` est réservé au
    catalogue OpenCode et aux déclarations explicites.
  - **États de traitement** : `discovered` / `extracted` / `indexed` sont des
    états conceptuels portés par `metadata["knowledge_state"]` ; `indexed` n'est
    posé que si l'ingestion RAG a réellement abouti.
  - **Relations documents↔Skills** : uniquement structurelles (le document
    réside dans le répertoire de la Skill) ou nominales (titres normalisés
    strictement identiques).
  - **Aucune dépendance, base, daemon ou stockage parallèle** ajouté.
- **Conséquence** : le socle documentaire est disponible dans ETHAN Core et
  exploitable par la WebUI, l'interface MCP et les agents autorisés sans script
  externe. P2.8 (traçabilité), P2.9 (MCP) et P2.10 (agents) restent hors périmètre.

### D-005 — Identité KnowledgeNode alignée sur le stable_id de la ressource (2026-11-12)

- **Statut** : validée (extension rétrocompatible de `KnowledgeManager.create`).
- **Source** : constat d'exécution — `km.create()` générait un `uuid4()`, donc le
  lien `ResourceRecord ↔ KnowledgeNode` était rompu au rechargement (les 391
  Skills se retrouvaient avec `knowledge_node_id: None`).
- **Contenu** : `KnowledgeManager.create(..., node_id=None)` accepte un
  identifiant imposé. À `None`, le comportement historique est conservé
  (UUID4). Avec un identifiant, la création devient idempotente et le nœud est
  aligné sur l'identité de la ressource.
- **Conséquence** : le lien resource↔connaissance survit au rechargement ;
  les nœuds sont recréés de façon idempotente en stockage mémoire.

### D-006 — DAĒNĀ P2.8.0 : correspondance canonique des catégories documentaires (2026-11-12)

- **Statut** : validée (implémentation réalisée, testée, corpus vérifié intact).
- **Source** : mission « DAĒNĀ P2.8.0 — Document Correspondence Repair » ;
  `docs/architecture/dana-p2-7-knowledge-discovery.md` §11.
- **Contenu** :
  - La destination d'une catégorie `RecordType` doit désigner un répertoire
    **réellement présent** dans le corpus `daena/`. Trois chemins anglais
    (`Knowledge/Components`, `Knowledge/Tests`, `Knowledge/Dependencies`)
    n'y ont jamais existé ; ils provenaient de `daena/Metadata/REGISTRY.md`
    (`PROPOSED`, 2026-11-03), antérieur à la migration vers les noms français.
  - Correspondance canonique : `Composants`, `Tests-et-Preuves`, `Decisions`,
    `Incidents`, `Archives/Events`, `Operational-Memory`, `_meta`,
    `Archives/Rapports-Agents`, et la couche `Knowledge` pour `DEPENDENCY`
    (aucun sous-répertoire dédié dans le corpus).
  - Sources de vérité, par ordre de fraîcheur : `daena/INDEX.md`,
    `daena/AGENTS.md`, `daena/README.md` (2026-11-11).
  - La résolution d'une destination est **strictement en lecture seule** :
    `destination_exists()`, `resolve_destination()` et `corpus_mapping()` ne
    créent, ne déplacent et ne modifient rien.
  - `ObsidianPersistence(require_existing_destination=True)` refuse d'écrire
    dans une destination absente du corpus ; le défaut `False` préserve le
    comportement historique et les appels existants.
  - Les identifiants, métadonnées, provenance et chemins sources des
    enregistrements existants sont préservés : la correction ne porte que sur
    la destination.
- **Conséquence** : une écriture Engineering Memory ne peut plus créer un
  répertoire parallèle dans le corpus. Le contrat est exposé aux interfaces
  futures (WebUI, MCP) via `corpus_mapping()`.




### P-001 — Plan Phase 3D sécurité (session actuelle, non versionnée)

- **Statut** : proposition, pas décision validée.
- **Source** : échange de la session actuelle (non versionné), à croiser avec le dépôt.
- **Contenu** : `session_version`, gate d'autorisation central, machine d'états bootstrap, durcissement WebSocket et API keys.
- **Remarque** : tant qu'aucune implémentation et aucune validation tests n'est réalisée, ces éléments restent des propositions.

### D-007 — DAĒNĀ P2.8.1 : source de verite unique par type de donnee (2026-11-12)

- **Statut** : validée (implémentation réalisée, testée, migration préparée non exécutée).
- **Source** : mission « DAĒNĀ P2.8.1 — Unification de la persistance » ;
  `docs/architecture/dana-p2-8-1-persistence-unification.md`.
- **Contenu** :
  - **Une seule source de vérité par type de donnée.** `CoreRecordStore`
    (PostgreSQL) porte les enregistrements structurés : `knowledge`,
    `rag-documents`, `projects`, `missions`, et désormais `resources`.
    Redis reste un cache (TTL 300 s), jamais une autorité.
  - **Les données de nature documentaire restent sur fichier.** Les
    `MemoryRecord` de l'Engineering Memory demeurent en Markdown + YAML dans
    `daena/` : ce sont des objets destinés à la lecture humaine, pas des lignes
    de table. Imposer le store de records à ces données serait artificiel.
  - **`registry-meta.json` n'est plus une autorité concurrente** : il reste
    l'export portable et l'amorçage, tandis que
    `core_domain_records[resources]` fait foi. `ResourceRepository`
    (`core/resources/repository.py`) porte ce contrat, sans logique métier.
  - **Un chemin de persistance explicite fait foi.** Le fallback global qui
    ignorait un `registry_meta_path` explicite est supprimé : il rendait la
    persistance non déterministe (un registre de test chargeait le registre
    global).
  - **L'identité du KnowledgeNode est alignée sur le `stable_id`** (D-005), ce
    qui rend les nœuds durables : les nœuds produits par la découverte
    disparaissaient au redémarrage alors que les métadonnées affirmaient
    `indexed`.
  - **Le round-trip préserve la provenance** : `discovered_at` et
    `last_verified` sont relus, l'historique de découverte n'est plus écrasé.
- **Conséquence** : la persistance des connaissances, des ressources et de la
  mémoire d'ingénierie est cohérente et durable. Le **câblage runtime** du
  `ResourceRegistry` sur le store partagé relève de **P2.8.6** (intégration
  fonctionnelle), hors périmètre de P2.8.1. La migration
  `registry-meta.json` → `core_domain_records[resources]` est préparée
  (`scripts/migrate_registry_to_pg.py`, dry-run par défaut) et **n'a pas été
  exécutée** sur les données réelles : elle requiert une autorisation
  explicite distincte.

### D-008 — DAĒNĀ P2.8.2 : les ancrages projet sont une relation dediee (2026-11-12)

- **Statut** : validée (implémentation réalisée, testée).
- **Source** : mission « DAĒNĀ P2.8.2 — Introduction des ancrages projet » ;
  `docs/architecture/dana-p2-8-2-project-anchors.md`.
- **Contenu** :
  - **Relation dédiée plutôt que champ identique.** Le rattachement vit dans
    `core_domain_records[project-anchors]`, pas dans un `project_id` ajouté aux
    cinq modèles concernés (`MemoryRecord`, `KnowledgeNode`, `ResourceRecord`,
    `Mission`, `ArchivedSession`). Raison : une connaissance, une ressource
    ou un événement d'ingénierie peut appartenir légitimement à plusieurs
    projets ; la relation porte sa propre provenance ; **aucune migration de
    schéma ni de données** n'est nécessaire ; le chemin de requête et la règle
    d'isolation sont uniques.
  - **La portée est dérivée, jamais stockée.** `GLOBAL` (aucune ancre active),
    `PROJECT` (une ancre), `MULTI_PROJECT` (plusieurs). Un champ de portée
    stocké finirait par contradire les relations.
  - **Identifiant d'ancre déterministe** : UUIDv5 de
    `(target_type, target_id, project_id)` — le rattachement est idempotent.
  - **Exclusivité par nature** : `Mission` et `ArchivedSession` appartiennent à
    un seul projet ; `KnowledgeNode`, `ResourceRecord` et `MemoryRecord` sont
    partageables. La règle est appliquée par le service, pas par le client.
  - **Identité de projet stable** : l'ancre ne dénormalise que l'identifiant ;
    un renommage de projet n'affecte pas les ancres. Un projet inactif est
    refusé pour un **nouveau** rattachement, les ancres existantes restent
    valides.
  - **Isolation** : `filter_by_project()` retourne le global et le sien, jamais
    l'exclusif d'un autre projet.
  - **Données historiques** : aucun projet inventé, aucun rattachement déduit.
    Les 100 KnowledgeNode, 118 MemoryRecord et 536 ResourceRecord existants
    restent de portée `GLOBAL` et exploitables ; un rattachement ultérieur
    explicite reste possible.
  - **Le service est Core-owned** (`core/projects/anchors.py`). Les routes API
    ne contiennent aucune règle métier.
- **Conséquence** : le projet devient un contexte structurant de la
  connaissance ETHAN, sans toucher au schéma des données existantes. Le
  `ResourceRegistry` n'étant pas encore branché sur le store partagé
  (P2.8.6), les ancres de type `resource` n'ont pas encore de cible réelle
  en production ; l'API d'ancrage est complète et testée.

### D-008 (complément) — Consolidation fonctionnelle des Project Anchors (2026-11-12)

- **Statut** : complément validé (la décision D-008 reste inchangée ; ce
  complément précise son application, sans la remplacer).
- **Source** : mission « Mission 02 — Stabilisation fonctionnelle / DAĒNĀ
  P2.8.2 » ; `docs/architecture/dana-p2-8-2-project-anchors.md` §12 à §17.
- **Contenu** :
  - **La relation, la portée et l'identité d'ancre de D-008 sont
    conservées.** La consolidation ne remet en cause ni la relation
    dédiée, ni la portée dérivée, ni l'identifiant UUIDv5 déterministe,
    ni l'exclusivité des missions et sessions. Elle corrige des défauts
    d'**application** de ces règles.
  - **Exclusivité garantie par section critique.** Le `CoreRecordStore` ne
    fournissait aucune garantie de concurrence : `save()` est un upsert
    simple, `get()` et `list()` avalent les pannes. Un contrôle suivi d'une
    écriture laissait donc une fenêtre réelle entre deux rattachements
    concurrents d'une cible exclusive. Le store reçoit une primitive
    minimale et compatible — `atomic(guard)` : transaction PostgreSQL et
    `pg_advisory_xact_lock` ; repli `asyncio.Lock` par clé sans
    PostgreSQL. Le contrôle **et** l'écriture se font dans cette section,
    sur **tous** les chemins (création, réactivation, rattachement
    répété). **Aucune nouvelle base, aucun nouveau daemon, aucune
    migration, aucun changement de schéma.**
  - **Existence des cibles : trois verdicts, jamais deux.** L'existence est
    résolue auprès de la **vraie source** de chaque type (domaine `knowledge`
    pour `KnowledgeManager`, `resources` pour `ResourceRepository`,
    `missions` pour `MissionManager`, le vault documentaire pour les
    documents d'ingénierie via un résolveur injecté). Source alimentée et
    cible absente → rattachement **refusé**. Source non alimentée ou
    inaccessible → rattachement **accepté**, mais l'ancre consigne
    `target_existence: unresolvable` : l'existence n'est jamais prétendument
    vérifiée. Un domaine vide signifie « source non alimentée », pas
    « donnée absente ».
  - **Panne technique ≠ règle métier.** `ProjectAnchorStoreUnavailable`
    (technique) est distinct de `ProjectAnchorError` (métier). Le store
    expose des lectures et écritures **strictes** qui ne déguisent pas une
    panne en absence de donnée. Conséquence HTTP : 503 pour la panne,
    422 pour la règle violée, 404 pour l'ancre absente.
  - **L'inventaire ne ment pas.** Un inventaire inaccessible n'est plus
    rendu par une liste vide : l'API expose `status: ok | unavailable` avec
    le motif. `global_targets()` refuse de renvoyer une liste vide quand la
    source n'a pas pu être consultée.
  - **Validation symétrique.** `attach()` et `detach()` partagent la même
    validation : type reconnu, identifiants non vides, normalisation
    identique des deux côtés (bord normalisé, contenu jamais réécrit).
  - **L'historique est conservé, pas résumé.** L'ancre porte une liste de
    **cycles** (`history`) : date de rattachement, auteur, métadonnées, date
    de détachement, verdict d'existence. La réactivation n'efface plus les
    métadonnées d'origine. Extension **rétrocompatible** : une ancre
    antérieure sans `history` est reconstituée avec un cycle implicite
    dérivé de son état courant.
  - **Isolation : trois niveaux distincts.** Le filtrage existe dans le
    service (**TESTED**), il est exposé par les routes (**TESTED**), mais
    `KnowledgeManager` et le pipeline RAG ne lui sont pas branchés
    (**PARTIAL**) et aucune isolation n'est démontrée en production
    (**NOT_VERIFIED**). L'affirmation d'une isolation globale serait
    inexacte.
- **Conséquence** : la règle d'exclusivité est réellement opposable, les
  erreurs ne sont plus confondues, l'existence des cibles est établie —
  ou explicitement non établie. Le périmètre des ancres reste celui de
  D-008 : le branchement de `KnowledgeManager` et du RAG appartient aux
  phases P2.8.3 à P2.8.8, qui ne sont pas engagées.

### D-009 — DAĒNĀ P2.8.3 : la traçabilité des interventions est un service Core immuable (2026-11-12)

- **Statut** : validée (implémentation réalisée, testée, validée en exécution).
- **Source** : mission « DAĒNĀ Automatic Engineering Traceability » ;
  `docs/architecture/dana-p2-8-3-traceability.md`.
- **Contenu** :
  - **Un service Core, pas une fonctionnalité d'interface.** La logique de
    traçabilité vit dans `core/engineering_memory/traceability.py`
    (`TraceabilityService`). Les routes HTTP, le plugin OpenCode, la CLI et
    la WebUI ne sont que des clients : aucune logique métier, aucun stockage
    propre. Une seule source documentaire — le vault `daena/` via
    l'Engineering Memory — aucune base supplémentaire, aucun second moteur
    de journalisation.
  - **Les types existants sont réutilisés.** Un rapport d'intervention est un
    `ENGINEERING_EVENT`, une anomalie un `INCIDENT`, une dette une
    `TECHNICAL_DEBT`. Aucun type nouveau n'est créé : la promotion des
    décisions en documents `Decision` reste hors périmètre (P2.8.4).
  - **Immuabilité et historique par événements corrélés.** Un document n'est
    jamais réécrit. Un changement d'état d'anomalie, une divergence de
    contenu sont des événements `ENGINEERING_EVENT` corrélés par
    `correlation_id` : le document d'origine reste lisible et la chronologie
    reste reconstituable. Un identifiant réutilisé avec un contenu différent
    produit un conflit explicite, jamais un écrasement.
  - **Charge utile structurée.** `MemoryRecord` reçoit un champ `metadata`
    optionnel (rétrocompatible). Sans lui, le contrôle automatique de fin
    d'intervention ne pourrait pas vérifier ses huit conditions sans.parser
    du Markdown. La comparaison d'idempotence passe par une forme canonique
    JSON, le YAML relisant certaines chaînes comme des dates et produisant
    de faux conflits.
  - **Contrôle de fin explicite.** Huit conditions vérifiées, résultat
    détaillé (`complete`, `persisted`, `missing`, `unresolved_anomalies`).
    Un rapport non persisté ne peut pas être déclaré documenté : la route
    renvoie `409` et l'échec de persistance `503`, avec trace de secours
    rejouable hors du corpus.
  - **Aucune fuite de secret.** Rédaction structurée avant persistance
    (12 motifs, y compris les formes françaises), contrôle secondaire par la
    `SecurityPolicy` de l'Engineering Memory, marqueur `[REDACTE…]` explicitement
    accepté.
  - **Intégration réelle, vérifiée.** Le point d'intégration OpenCode est le
    système de **plugins** (`.opencode/plugins/`), pas `~/.config/opencode/hooks/`
    qui est un mécanisme Claude Code. `session.idle` **n'est pas émis** en
    OpenCode v2.2.6 : la capture s'appuie sur `session.execution.succeeded`,
    vérifié en exécution réelle (rapport créé dans le vault). L'outil
    `daena_traceability` permet l'enrichissement par l'agent.
  - **Autorisation par portée machine.** Les clients machine-à-machine ne
    portent pas de rôle RBAC ; `require_memory_scope()` accepte une portée
    (`memory:traceability`) portée par le principal HROT, ou une permission
    RBAC pour les sessions humaines. Le modèle des routes machine existantes
    (`odin_ai`, `gods_eye_view_ai`) est repris, rien n'est contourné.
- **Conséquence** : toute intervention technique laisse une trace
  consultable dans DAĒNĀ, sans introduire de stockage parallèle. Les
  limites assumées sont documentées (granularité au tour d'agent, capture
  automatique `NOT_VERIFIED`, vault non inscriptible par l'utilisateur hôte).

## Hypothèses / dette technique

- `core/auth` et l'authentification API sont potentiellement sur plusieurs frontières (`core/auth/`, `interfaces/api/auth.py`, `interfaces/api/main.py`) ; la consolidation devra être validée par des tests.
- `require_memory_scope()` ajoute une seconde forme d'autorisation à côté du RBAC ; la consolidation du modèle d'autorisation reste à faire.
- Le volume important de changements locaux non commités complique toute comparaison avec l'état documentaire.
- Les rapports de session peuvent signaler des intentions non implémentées ; toujours croiser avec le dépôt.

## Règles de validation

- Toute décision ajoutée ici doit contenir au minimum : date, statut, source, contenu, conséquence pratique.
- Ne pas convertir une hypothèse en décision validée.
- Ne jamais archiver de secret ou de donnée personnelle.

### D-004 — Interface CLI/TUI ETHAN comme client Core (2026-11-10)

- **Statut** : validée.
- **Source** : Mission C1 ; `Obsidian/Architecture/ADR/ADR-4010-cli-tui.md`.
- **Contenu** : le TUI plein écran (`interfaces/cli/tui/`) est une interface
  ETHAN qui projette les contrats Core via la frontière HTTP unique, sans
  duplication de logique métier, sans stockage de sessions indépendant et
  sans permission locale contournant HROT. Aucune nouvelle dépendance lourde.
- **Conséquence** : `ethan cli` (sans argument) et `ethan tui` lancent le
  TUI ; la compatibilité `ethan cli <commande>` est préservée.

## MEM-014 Phase 1 — Décisions techniques validées (2026-11-03)

- `core/applications/` reste la source unique de l'identité et du manifeste applicatifs.
- Version de contrat ETHAN prise en charge : `1.0.0`.
- Les capacités applicatives sont un vocabulaire ouvert contrôlé syntaxiquement, sans registre fermé à cette phase.
- Les manifestes sont strictement bornés au niveau des champs racine autorisés.
