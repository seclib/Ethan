# Analyse Critique de l'Architecture ETHAN

**Document d'audit et de questionnement systématique**  
**Date** : Juin 2026  
**Auteur** : Architecture Team  
**Statut** : Review obligatoire avant toute implémentation

---

## Philosophie de ce document

Ce document ne valide rien. Il questionne tout.

Chaque décision architecturale doit survivre à cette grille d'analyse avant d'être considérée comme stable.

---

## 1. Le Concept : Cognitive OS

### 1.1 Pertinence

**Pourquoi c'est pertinent :**
- L'industrie manque de systèmes persistants et autonomes
- Les chatbots sont réactifs, ETHAN serait proactif
- L'event-driven architecture permet un découplage réel
- La modularité permet l'évolution sans refactoring massif

### 1.2 Limites

**Problèmes identifiés :**

1. **Ambiguïté sémantique** : "Cognitive OS" n'est pas un terme standardisé. Que signifie exactement "OS cognitif" ? Est-ce un OS comme Linux ? Est-ce un runtime comme JVM ? Est-ce un framework comme Django ?

2. **Comparaison impossible** : Sans définition précise, on ne peut pas comparer ETHAN à des alternatives existantes.

3. **Risque de sur-vente** : Le terme "OS" implique une maturité et une stabilité qu'ETHAN n'aura pas avant des années.

### 1.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Cognitive Runtime** | Terme plus modeste, plus précis | Moins de hype, plus réaliste | Moins accrocheur |
| **Agent Framework** | Terme standard, compris | Facile à expliquer | Limité, ne capture pas la vision |
| **Event-Driven AI Platform** | Descriptif, technique | Clair, précis | Long, peu élégant |
| **Autonomous System Substrate** | Terme recherche | Précis, académique | Incompréhensible pour le grand public |

### 1.4 Recommandation

**Garder "Cognitive Runtime" comme terme officiel**, avec "Cognitive OS" comme vision long terme.

**Justification :**
- "Runtime" est précis : c'est un environnement d'exécution
- "Cognitive" capture l'aspect raisonnement
- "OS" reste comme objectif V3, pas comme réalité V1
- Évite la sur-vente tout en restant ambitieux

**Action requise :** Définir formellement ce qu'est un "Cognitive Runtime" dans un glossaire du projet.

---

## 2. L'Orchestrator : Cerveau Central

### 2.1 Pertinence

**Pourquoi c'est pertinent :**
- Point d'entrée unique pour toutes les requêtes
- Coordination centralisée des modules
- Facilite le debugging et le monitoring
- Permet des pipelines complexes

### 2.2 Limites

**Problèmes identifiés :**

1. **Single Point of Coordination** : Si l'Orchestrator crash, tout le système s'arrête. C'est un SPOF (Single Point of Failure).

2. **Bottleneck potentiel** : Toutes les requêtes passent par lui. À haute charge, il devient un goulot.

3. **Complexité cyclomatique** : L'Orchestrator connaît tous les modules. Il viole le principe de séparation des préoccupations.

4. **Couplage fort** : Pour ajouter un module, il faut modifier l'Orchestrator.

### 2.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Orchestrator centralisé** (actuel) | Point d'entrée unique | Simple, facile à debugger | SPOF, bottleneck |
| **Orchestrator hiérarchique** | Plusieurs niveaux d'orchestration | Résilient, scalable | Complexe, difficile à raisonner |
| **Event-driven sans orchestrator** | Les modules réagissent directement aux événements | Pas de SPOF, découplage total | Difficile à debugger, ordre non garanti |
| **Orchestrator par domaine** | Un orchestrateur par type de requête | Spécialisé, performant | Duplication de code, cohérence difficile |

### 2.4 Recommandation

**Garder l'Orchestrator centralisé, mais avec des garde-fous :**

1. **Stateless** : l'Orchestrator ne contient aucun état critique
2. **Réplicable** : on peut lancer N instances derrière un load balancer
3. **Idempotent** : chaque requête peut être réexécutée sans effet de bord
4. **Timeout obligatoire** : toute requête doit avoir un timeout

**Justification :**
- Un système cognitif a besoin d'un point de coordination pour maintenir la cohérence
- Les alternatives sont trop complexes pour le MVP
- Les garde-fous éliminent les risques majeurs

**Action requise :** Implémenter l'Orchestrator comme un service stateless avec health checks et auto-scaling.

---

## 3. Event Bus : NATS JetStream

### 3.1 Pertinence

**Pourquoi c'est pertinent :**
- Latence < 1ms
- Durabilité avec JetStream
- Clustering horizontal
- API simple

### 3.2 Limites

**Problèmes identifiés :**

1. **Rétention limitée** : NATS JetStream est conçu pour des événements récents, pas pour de l'event sourcing long terme.

2. **Pas de requêtes complexes** : Impossible de faire des jointures, des agrégations, des filtres avancés.

3. **Dépendance forte** : Tout le système dépend de NATS. Si NATS est down, le système est aveugle.

4. **Opérations** : Nécessite un cluster NATS en production, avec ses propres défis (partitioning, consensus, etc.).

### 3.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **NATS JetStream** (actuel) | Event bus léger, rapide | Rapide, simple, durable | Rétention limitée, pas de requêtes complexes |
| **Apache Kafka** | Event streaming mature | Rétention illimitée, requêtes complexes, écosystème riche | Lourd, ops complexes, latence plus élevée |
| **EventStoreDB** | Event sourcing dédié | Optimisé pour l'event sourcing, projections | Moins mature, écosystème plus petit |
| **Redis Streams** | Streams Redis | Simple, rapide, déjà dans la stack | Pas de rétention longue, pas de requêtes complexes |
| **AWS Kinesis / GCP PubSub** | Cloud-managed | Pas d'ops, scalable | Cloud-only, vendor lock-in |

### 3.4 Recommandation

**Phase 1 (V1) : NATS JetStream**
- Parfait pour le MVP
- Rétention de 1 semaine suffisante pour le debug
- Performance excellente

**Phase 2 (V2) : Migration vers Kafka si nécessaire**
- Si rétention > 1 semaine
- Si besoin de requêtes complexes (Kafka Streams, ksqlDB)
- Si volume > 1M événements/jour

**Garder NATS pour :**
- Communication temps réel entre modules
- Commandes et requêtes synchrones
- Event bus "chaud"

**Ajouter Kafka pour :**
- Event store permanent
- Analytics et reporting
- Replay long terme

**Justification :**
- NATS est le bon outil pour le bon use case (low-latency, short-term)
- Kafka est le bon outil pour l'event sourcing (long-term, complex queries)
- Les deux peuvent coexister

**Action requise :** Concevoir l'Event Store comme une abstraction avec deux backends : NATS (court terme) et Kafka (long terme).

---

## 4. Persistance : PostgreSQL comme Source de Vérité

### 4.1 Pertinence

**Pourquoi c'est pertinent :**
- ACID, fiabilité
- JSONB pour les événements flexibles
- pgvector pour les embeddings
- Écosystème mature

### 4.2 Limites

**Problèmes identifiés :**

1. **Pas optimisé pour le time-series** : Les événements sont des séries temporelles. PostgreSQL n'est pas optimisé pour ça.

2. **Écritures haute fréquence** : Si le système génère 10k événements/secondes, PostgreSQL peut devenir un goulot.

3. **Coût opérationnel** : Maintenir un cluster PostgreSQL haute disponibilité est complexe.

4. **Requêtes analytiques** : Les agrégations sur des millions d'événements sont lentes sans optimisation spécifique.

### 4.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **PostgreSQL** (actuel) | Base relationnelle polyvalente | Polyvalent, fiable, mature | Pas optimisé pour time-series |
| **EventStoreDB** | Event sourcing dédié | Optimisé pour les événements, projections | Écosystème plus petit, moins flexible |
| **TimescaleDB** | PostgreSQL + time-series | Compatible PostgreSQL, optimisé time-series | Dépendance supplémentaire |
| **Kafka + S3** | Event streaming + stockage objet | Scalable, durable, cheap | Pas de requêtes SQL, latence élevée |
| **CockroachDB** | PostgreSQL distribué | Scalable, ACID, compatible PostgreSQL | Plus complexe, plus cher |

### 4.4 Recommandation

**Phase 1 (V1) : PostgreSQL seul**
- Suffisant pour le MVP
- Volume attendu : < 1M événements/jour
- Simplicité opérationnelle

**Phase 2 (V2) : PostgreSQL + TimescaleDB**
- TimescaleDB en extension PostgreSQL
- Tables time-series pour les événements
- Rétention automatique (TTL)
- Agrégations rapides (continuous aggregates)

**Phase 3 (V3) : EventStoreDB pour l'event sourcing**
- Si le système devient critique
- Besoin de projections complexes
- Besoin de rétention illimitée

**Justification :**
- PostgreSQL est suffisant pour commencer
- TimescaleDB est une extension, pas un remplacement
- Migration progressive sans breaking change

**Action requise :** Concevoir la couche de persistance comme une abstraction avec trois backends : PostgreSQL (V1), TimescaleDB (V2), EventStoreDB (V3).

---

## 5. Modules Cognitifs : Indépendance vs Couplage

### 5.1 Pertinence

**Pourquoi c'est pertinent :**
- Responsabilité unique par module
- Découplage via événements
- Testabilité
- Évolutivité

### 5.2 Limites

**Problèmes identifiés :**

1. **Indépendance illusoire** : Les modules doivent partager du contexte (mémoire, buts, état). L'indépendance totale est impossible.

2. **Latence accrue** : Chaque communication passe par le bus. Si Module A appelle Module B, c'est 3 allers-retours (A → Bus → B → Bus → A) au lieu d'un appel direct.

3. **Complexité de debugging** : Tracer un flux à travers 8 modules est difficile sans outillage sophistiqué.

4. **Cohérence éventuelle** : Si Module A écrit X et Module B écrit Y, et que Y dépend de X, il y a un risque de race condition.

### 5.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Indépendance totale** (actuel) | Modules ne se connaissent pas | Découplage maximal | Latence, complexité |
| **Couplage faible** | Modules peuvent s'appeler directement si nécessaire | Performance, simplicité | Risque de couplage fort |
| **Orchestrator centralisé** | L'orchestrateur coordonne tout | Cohérence, visibilité | SPOF, bottleneck |
| **Shared Kernel** | Modules partagent un état commun | Cohérence, performance | Couplage fort, risque de corruption |

### 5.4 Recommandation

**Hybride : Indépendance par défaut, couplage explicite quand nécessaire**

1. **Par défaut** : communication par événements
2. **Exception** : si un module doit appeler un autre directement, il doit :
   - Déclarer la dépendance explicitement
   - Être validé par le Security Gateway
   - Être tracé dans les logs

**Justification :**
- L'indépendance totale est un idéal, pas une réalité
- Certains cas nécessitent de la synchronisation (ex: Executive → Planner)
- Le couplage explicite est préférable au couplage implicite

**Action requise :** Définir un mécanisme de "dépendances explicites" entre modules, avec validation et traçabilité.

---

## 6. LLM comme Moteur, pas comme Décideur

### 6.1 Pertinence

**Pourquoi c'est pertinent :**
- Garder le contrôle humain
- Éviter la dépendance à un fournisseur
- Sécurité : les LLM ne peuvent pas contourner les règles
- Transparence : chaque décision est tracée

### 6.2 Limites

**Problèmes identifiés :**

1. **Complexité accrue** : Il faut une couche de décision (Executive) au-dessus du LLM. Ça ajoute de la complexité.

2. **Latence** : LLM propose → Executive décide → Exécution. C'est 2 étapes au lieu d'une.

3. **Risque d'over-engineering** : Pour beaucoup de cas, un LLM qui décide directement est suffisant.

4. **Qui décide de ce que le LLM peut décider ?** : C'est un problème de régression infinie.

### 6.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **LLM propose, ETHAN décide** (actuel) | Couche de décision au-dessus du LLM | Contrôle, sécurité, transparence | Complexité, latence |
| **LLM décide pour les cas simples** | LLM autonome pour les tâches simples | Simplicité, rapidité | Risque de comportements imprévisibles |
| **LLM décide, humain valide** | Validation humaine pour les actions critiques | Sécurité, confiance | Lent, ne scale pas |
| **LLM autonome avec garde-fous** | LLM libre dans des limites définies | Équilibré | Difficile à définir les limites |

### 6.4 Recommandation

**LLM propose, ETHAN décide — mais avec des nuances :**

1. **Niveau 1 (V1)** : LLM propose, Executive décide pour tout
2. **Niveau 2 (V2)** : LLM décide pour les actions LOW risk, Executive valide pour MEDIUM/HIGH
3. **Niveau 3 (V3)** : LLM autonome avec garde-fous, humain notifié pour les actions critiques

**Justification :**
- V1 : sécurité maximale, learning de ce que le LLM peut faire
- V2 : optimisation basée sur les données collectées en V1
- V3 : autonomie progressive basée sur la confiance accumulée

**Action requise :** Définir une matrice de risque qui détermine qui décide (LLM vs Executive vs Humain) selon le type d'action.

---

## 7. Skills vs Workflows

### 7.1 Pertinence

**Pourquoi c'est pertinent :**
- Skills = compétences réutilisables
- Composition possible
- Déclaratif (pas de code)

### 7.2 Limites

**Problèmes identifiés :**

1. **Trop rigide** : Un Skill est un pipeline linéaire. La vraie vie n'est pas linéaire.

2. **Pas de boucles** : Impossible de faire "répéter jusqu'à succès" sans coder un module spécifique.

3. **Pas de parallélisme natif** : Le SkillExecutor exécute séquentiellement. Le parallélisme est un afterthought.

4. **Pas de gestion d'erreur sophistiquée** : Rollback oui, compensation transactionnelle non.

5. **Skills vs Agents** : Quelle est la différence entre un Skill et un Agent ? Ambiguïté.

### 7.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Skills comme pipelines** (actuel) | Séquence d'étapes | Simple, déclaratif | Rigide, pas de boucles |
| **Workflows avec Temporal.io** | Moteur de workflows éprouvé | Robuste, compensations, parallélisme | Dépendance externe, complexité |
| **Agents autonomes** | Agents qui raisonnent et agissent | Flexibles, adaptatifs | Imprévisibles, difficiles à contrôler |
| **State Machines** | Machines à états pour chaque Skill | Prévisible, testable | Rigide, verbeux |

### 7.4 Recommandation

**Évoluer vers un moteur de workflows hybride :**

1. **V1** : Skills comme pipelines (actuel)
2. **V2** : Ajouter des boucles et du parallélisme dans SkillExecutor
3. **V3** : Intégrer Temporal.io ou équivalent pour les workflows critiques

**Garder les Skills pour :**
- Cas simples et bien définis
- Compositions d'outils standards
- Actions répétitives

**Ajouter Workflows pour :**
- Cas complexes avec rollback
- Orchestration longue durée
- Compensations transactionnelles

**Justification :**
- Les Skills sont suffisantes pour 80% des cas simples
- Les Workflows sont nécessaires pour les 20% de cas complexes
- Évolution progressive sans breaking change

**Action requise :** Définir clairement la frontière entre Skill et Workflow. Quand utiliser l'un vs l'autre.

---

## 8. Sécurité Zero Trust

### 8.1 Pertinence

**Pourquoi c'est pertinent :**
- Aucun composant n'est fiable par défaut
- Validation systématique
- Audit complet
- Principe du moindre privilège

### 8.2 Limites

**Problèmes identifiés :**

1. **Overhead** : Chaque événement est validé, chaque action est vérifiée. Ça ajoute de la latence.

2. **Complexité** : Gérer les permissions, les policies, les rôles, c'est complexe.

3. **Faux sentiment de sécurité** : "Zero Trust" est un buzzword. Si mal implémenté, c'est pire que pas de sécurité du tout.

4. **Performance** : À haute charge, les vérifications de sécurité deviennent un bottleneck.

### 8.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Zero Trust** (actuel) | Vérification systématique | Sécurité maximale | Overhead, complexité |
| **Defense in Depth** | Plusieurs couches de sécurité | Robuste, flexible | Complexe, coûteux |
| **Trust but Verify** | Confiance par défaut, vérification ciblée | Simple, performant | Risqué si mal configuré |
| **Capability-Based Security** | Permissions par capability | Fin, flexible | Complexe à implémenter |

### 8.4 Recommandation

**Zero Trust avec optimisations :**

1. **Validation en cascade** : validation rapide d'abord (signature, schéma), puis validation lente (permissions, policies)
2. **Cache de permissions** : éviter de vérifier les mêmes permissions à chaque fois
3. **Fast Path** : pour les événements internes (module → kernel), réduire les vérifications
4. **Slow Path** : pour les événements externes (interface → kernel), vérification complète

**Justification :**
- Zero Trust est le bon principe
- Mais il doit être implémenté intelligemment pour ne pas tuer les performances
- Le cache et les chemins rapides/lents résolvent le problème de latence

**Action requise :** Concevoir le Security Gateway comme un pipeline de validation avec fast path et slow path.

---

## 9. Architecture Multi-Langages (Go + Python + Rust)

### 9.1 Pertinence

**Pourquoi c'est pertinent :**
- Go pour le kernel (performance)
- Python pour les modules (écosystème AI)
- Rust pour les performances critiques (PyO3)

### 9.2 Limites

**Problèmes identifiés :**

1. **Complexité opérationnelle** : 3 langages, 3 toolchains, 3 écosystèmes de dépendances.

2. **Debugging** : Un bug peut être dans n'importe quel langage. Les stack traces sont hétérogènes.

3. **Recrutement** : Trouver des développeurs maîtrisant Go + Python + Rust est difficile.

4. **Build** : 3 compilateurs/interpreters, 3 systèmes de build.

5. **Typage** : Les interfaces entre langages sont des points de friction (serialization, marshaling).

### 9.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Go + Python + Rust** (actuel) | Meilleur outil pour chaque job | Performance, productivité, écosystème | Complexité, 3 langages |
| **Tout Python** | Un seul langage | Simplicité, écosystème AI | Performance (GIL) |
| **Tout Rust** | Un seul langage, performant | Performance, sécurité mémoire | Courbe d'apprentissage, temps de dev |
| **Go + Python** | Sans Rust | Simplicité, performance acceptable | Moins de performance pour les cas critiques |
| **Python + Rust (PyO3)** | Rust pour les performances critiques | Meilleur des deux mondes | Complexité des bindings |

### 9.4 Recommandation

**Phase 1 (V1) : Go + Python**
- Kernel en Go
- Modules en Python
- Pas de Rust pour l'instant

**Phase 2 (V2) : Ajouter Rust progressivement**
- Identifier les goulots de performance
- Implémenter en Rust via PyO3
- Mesurer l'impact

**Phase 3 (V3) : Rust pour les modules critiques**
- LLM inference
- Event bus processing
- Memory retrieval

**Justification :**
- V1 : simplicité, time-to-market
- V2 : optimisation basée sur des données réelles
- V3 : performance maximale là où ça compte

**Action requise :** Établir des benchmarks de performance avant d'ajouter Rust. Ne pas optimiser prématurément.

---

## 10. Monorepo vs Multi-Repos

### 10.1 Pertinence

**Pourquoi c'est pertinent :**
- Code partagé (types, events)
- Build atomique
- Versioning cohérent

### 10.2 Limites

**Problèmes identifiés :**

1. **Taille** : Un monorepo avec 100k lignes de code devient ingérable.

2. **Build time** : Chaque modification rebuild tout le projet.

3. **Permissions** : Tout le monde a accès à tout le code.

4. **Dépendances** : Les cycles de dépendances sont difficiles à détecter.

### 10.3 Alternatives

| Approche | Description | Avantages | Inconvénients |
|----------|-------------|-----------|---------------|
| **Monorepo** (actuel) | Tout dans un seul repo | Simplicité, code partagé | Taille, build time |
| **Multi-repos** | Un repo par module | Indépendance, permissions granulaires | Code dupliqué, versioning complexe |
| **Hybride** | Core en monorepo, modules en multi-repos | Meilleur des deux mondes | Complexité de gestion |
| **Packages** | Modules publiés comme packages | Réutilisabilité, versioning | Overhead de publication |

### 10.4 Recommandation

**Monorepo pour V1 et V2, migration vers hybride pour V3 :**

1. **V1-V2** : Monorepo avec structure modulaire claire
2. **V3** : Si le projet dépasse 200k lignes de code, migrer vers :
   - `ethan-core` (monorepo) : kernel, types, events, bus
   - `ethan-modules` (monorepo) : modules cognitifs
   - `ethan-interfaces` (monorepo) : CLI, API, UI
   - `ethan-plugins` (multi-repos) : plugins et skills

**Justification :**
- Monorepo est parfait pour le MVP et la croissance
- La migration vers hybride est possible sans breaking change
- Les packages (PyPI, npm) pour les plugins permettent l'écosystème

**Action requise :** Définir des limites claires dans le monorepo (qui peut modifier quoi, quels sont les cycles interdits).

---

## 11. Questions Sans Réponse (Blocker pour le Code)

### 11.1 Questions Critiques

**Q1 : Comment gérer les cycles de dépendances entre modules ?**
- Module A émet événement X
- Module B écoute X, émet Y
- Module A écoute Y
- → Cycle implicite

**Q2 : Comment garantir l'ordre des événements dans un système distribué ?**
- NATS garantit l'ordre par subject
- Mais si Module A publie sur subject X puis Y, et Module B publie sur Y puis X, quel est l'ordre global ?

**Q3 : Comment gérer les migrations de schéma d'événements ?**
- Si EventType v1 a des champs A, B
- Et EventType v2 a des champs A, B, C
- Comment gérer la rétrocompatibilité ?

**Q4 : Comment tester un système distribué ?**
- Comment écrire un test d'intégration qui couvre Module A → Bus → Module B → Module C ?
- Comment mocker le bus dans les tests unitaires ?

**Q5 : Comment gérer les secrets dans un système distribué ?**
- Module A a besoin d'un API key
- Module B a besoin d'un autre API key
- Comment distribuer les secrets sans les exposer ?

**Q6 : Quelle est la granularité des événements ?**
- Un événement par action utilisateur ?
- Un événement par décision système ?
- Un événement par changement d'état ?

**Q7 : Comment gérer les timeouts et les retries ?**
- Si Module A timeout, qui notifie l'utilisateur ?
- Si Module B crash après avoir écrit dans Redis, comment garantir la cohérence ?

**Q8 : Quelle est la taille maximale d'un événement ?**
- Un événement peut-il contenir un fichier de 10MB ?
- Ou seulement des références ?

### 11.2 Recommandations

**Avant d'écrire du code, il faut :**

1. **Définir un ADR pour chaque question ci-dessus**
2. **Écrire un document de "Event Schema Governance"**
3. **Implémenter un "Integration Test Harness" pour tester les flux complets**
4. **Définir une stratégie de migration de schéma d'événements**
5. **Choisir un secret manager (Vault, AWS Secrets Manager, etc.)**

---

## 12. Incohérences et Ambiguïtés

### 12.1 Incohérences

**I1 : Kernel Go vs Modules Python**
- Le README dit "Kernel Go pour le routing"
- Mais `core/` est entièrement en Python
- **Incohérence** : où est le kernel Go ? Dans `kernel/` ? Comment communique-t-il avec `core/` ?

**I2 : Event Bus**
- Le README mentionne NATS JetStream
- Mais `core/bus/` implémente un InMemoryBus et des backends abstraits
- **Incohérence** : quel est le bus par défaut en production ?

**I3 : Modules vs Agents**
- Le README parle de "modules cognitifs"
- Mais il y a aussi `core/agents/`
- **Incohérence** : quelle est la différence entre un module et un agent ?

### 12.2 Ambiguïtés

**A1 : Qu'est-ce qu'un "but" (goal) ?**
- Est-ce une intention utilisateur ?
- Est-ce un objectif système autonome ?
- Est-ce les deux ?

**A2 : Qu'est-ce qu'une "capability" ?**
- Est-ce un outil ?
- Est-ce une compétence ?
- Est-ce un service ?

**A3 : Quelle est la frontière entre Executive et Planner ?**
- Executive coordonne les buts
- Planner décompose en tâches
- Mais qui décide de la décomposition ?

**A4 : Qu'est-ce que "Cognition" ?**
- Est-ce l'analyse d'intention ?
- Est-ce le raisonnement ?
- Est-ce les deux ?

### 12.3 Actions Requises

**Avant toute implémentation :**

1. **Résoudre I1** : Définir l'interface entre kernel Go et modules Python
2. **Résoudre I2** : Choisir le bus par défaut pour V1
3. **Résoudre I3** : Définir la différence module vs agent
4. **Clarifier A1-A4** : Écrire des définitions formelles dans un glossaire

---

## 13. Recommandations Globales

### 13.1 Ce qui doit être fait AVANT le code

1. **Définir un Event Schema Governance** : comment créer, versionner, migrer des événements
2. **Définir un Module Contract** : interface, permissions, dépendances
3. **Définir un Testing Strategy** : comment tester un système distribué
4. **Définir un Secret Management Strategy** : où, comment, qui accède aux secrets
5. **Résoudre les incohérences I1-I3** : clarifier l'architecture
6. **Clarifier les ambiguïtés A1-A4** : écrire les définitions

### 13.2 Ce qui peut être fait EN PARALLÈLE

1. **Implémenter le kernel Go** : il est bien défini
2. **Implémenter les types Python** : ils sont stables
3. **Implémenter l'Event Bus abstrait** : l'abstraction est bonne
4. **Écrire les tests unitaires** : ils servent de documentation

### 13.3 Ce qui ne doit PAS être fait

1. **Ne pas implémenter de modules complets** : les interfaces ne sont pas stabilisées
2. **Ne pas optimiser prématurément** : pas de Rust avant d'avoir mesuré
3. **Ne pas ajouter de dépendances externes** : pas de Temporal.io, pas de Kafka avant V2
4. **Ne pas documenter des fonctionnalités qui n'existent pas** : éviter le "architecture astronautics"

---

## Conclusion

Cette analyse critique n'a pas pour but de décourager. Elle a pour but de **construire sur des bases solides**.

ETHAN est un projet ambitieux. L'ambition est bonne. Mais l'ambition sans rigueur architecturale mène à la dette technique.

**Les prochaines étapes :**

1. Répondre aux 8 questions critiques (section 11)
2. Résoudre les 3 incohérences (section 12.1)
3. Clarifier les 4 ambiguïtés (section 12.2)
4. Écrire les ADRs manquants
5. **Seulement ensuite**, commencer à coder

Un projet qui prend le temps de bien réfléchir avant d'agir va 10x plus vite qu'un projet qui code d'abord et réfléchit après.

**ETHAN mérite cette rigueur.**

---

**Document à relire et challenger par toute l'équipe avant implémentation.**