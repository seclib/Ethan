# ETHAN — Cognitive Runtime

**Version** : 1.0.0  
**Statut** : Architecture  
**Dernière mise à jour** : Juin 2026

---

## Table des matières

1. [Vision](#vision)
2. [Mission](#mission)
3. [Philosophie](#philosophie)
4. [Qu'est-ce qu'ETHAN ?](#quest-ce-quethan)
5. [Ce qu'ETHAN n'est pas](#ce-quethan-nest-pas)
6. [Les principes fondamentaux](#les-principes-fondamentaux)
7. [Les objectifs](#les-objectifs)
8. [Les priorités](#les-priorités)
9. [Les valeurs du projet](#les-valeurs-du-projet)
10. [Les règles d'architecture](#les-règles-darchitecture)
11. [Les responsabilités du Core](#les-responsabilités-du-core)
12. [Les interfaces](#les-interfaces)
13. [Les fournisseurs LLM](#les-fournisseurs-llm)
14. [Les outils](#les-outils)
15. [Les Skills](#les-skills)
16. [Le système de mémoire](#le-système-de-mémoire)
17. [La sécurité](#la-sécurité)
18. [Les événements](#les-événements)
19. [Les flux de données](#les-flux-de-données)
20. [Les décisions d'architecture](#les-décisions-darchitecture)
21. [Les objectifs V1](#les-objectifs-v1)
22. [Les objectifs V2](#les-objectifs-v2)
23. [La vision V3](#la-vision-v3)
24. [Les conventions de développement](#les-conventions-de-développement)
25. [Les règles à respecter avant toute contribution](#les-règles-à-respecter-avant-toute-contribution)
26. [Les erreurs d'architecture à éviter](#les-erreurs-darchitecture-à-éviter)
27. [Les principes SOLID appliqués au projet](#les-principes-solid-appliqués-au-projet)
28. [Les principes Zero Trust](#les-principes-zero-trust)
29. [Les décisions importantes](#les-décisions-importantes)
30. [Les futurs axes d'évolution](#les-futurs-axes-dévolution)

---

## Vision

ETHAN est un **système d'exploitation cognitif** (Cognitive OS).

Ce n'est pas un chatbot. Ce n'est pas un agent IA. Ce n'est pas une application.

ETHAN est un **substrat** — une infrastructure logicielle qui héberge, planifie et gère des modules de raisonnement autonomes.

La vision est simple : créer un système capable de maintenir une cognition persistante, modulaire et observable, indépendamment de toute interface utilisateur.

### Ce qu'ETHAN n'est pas

| Concept | Pourquoi ce n'est pas ETHAN |
|---------|----------------------------|
| **Chatbot** | Un chatbot répond quand on lui parle. ETHAN observe, réfléchit et agit même quand personne ne lui demande. |
| **Agent OpenAI** | Un agent OpenAI est un wrapper autour d'une API. ETHAN est un OS complet avec état persistant, modules indépendants et event bus. |
| **OpenJarvis** | OpenJarvis devient une interface parmi d'autres. ETHAN Core est totalement indépendant. |
| **Application web** | Une application web est un client-serveur. ETHAN est un runtime distribué avec event bus, persistance et modules autonomes. |
| **Framework LLM** | Un framework LLM appelle des modèles. ETHAN traite les LLM comme des moteurs de raisonnement remplaçables. |

### Mission

Fournir une infrastructure de cognition autonome où :

- L'intelligence est **persistante** (elle survit aux redémarrages)
- Les modules sont **indépendants** (pas d'appels directs entre modules)
- Le système est **observable** (chaque événement est tracé)
- Les décisions sont **déléguées** (le kernel orchestre, les modules raisonnent)
- Les interfaces sont **remplaçables** (CLI, Web, Desktop, API, Shell)

### Problème résolu

L'industrie construit des chatbots. Des assistants. Des agents.

Tous partagent le même défaut fondamental : **ils sont réactifs**.

Ils attendent un prompt. Ils n'ont pas d'état persistant. Ils oublient quand on ferme l'onglet.

ETHAN résout ce problème en étant :

- **Event-driven** : les modules réagissent à des événements, pas à des prompts
- **Stateful** : l'état est externalisé (Redis + PostgreSQL)
- **Autonome** : le système peut poursuivre des buts sans intervention humaine
- **Modulaire** : chaque capacité est un contrat versionné

### Pertinence de l'architecture

L'architecture modulaire par événements est pertinente car :

1. **Découplage** : les modules ne se connaissent pas, ils communiquent par événements
2. **Évolutivité** : on peut ajouter des modules sans modifier le kernel
3. **Résilience** : un module qui crash ne fait pas tomber le système
4. **Observabilité** : chaque événement est tracé, rejouable, auditable
5. **Testabilité** : chaque module peut être testé isolément

### Risques de cette approche

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **Complexité architecturale** | Courbe d'apprentissage steep | Documentation exhaustive, exemples, ADRs |
| **Latence réseau** (NATS) | Dégradation des performances | Cache Redis, optimisations, profiling |
| **Dépendance à NATS** | Single point of failure | Clustering NATS, fallback in-memory |
| **Sur-ingénierie** | Développement lent | MVP d'abord, itérations rapides |
| **Maintenance** | Coût élevé | Automatisation, tests, CI/CD |

### Avantages

- **Extensibilité** : ajouter une skill = ajouter un plugin
- **Interopérabilité** : toute interface peut se connecter via l'event bus
- **Traçabilité** : chaque décision est tracée dans PostgreSQL
- **Résilience** : le kernel redémarre les modules en cas de crash
- **Évolutivité** : les modules peuvent être répartis sur plusieurs machines

### Inconvénients

- **Complexité initiale** : plus de composants à comprendre
- **Overhead** : chaque événement passe par NATS + Redis + PostgreSQL
- **Debugging** : tracer un flux à travers 8 modules demande de l'outillage
- **Opérations** : nécessite NATS, Redis, PostgreSQL en production

### Choix problématiques dans le futur

| Choix actuel | Problème potentiel | Alternative |
|--------------|-------------------|-------------|
| **NATS comme event bus** | Si NATS devient un goulot | Kafka pour le long terme, NATS pour le court terme |
| **PostgreSQL pour tout** : PostgreSQL peut ne pas scaler pour les événements à haute fréquence | Event store dédié (EventStoreDB, Kafka) |
| **Python comme langage principal** : Le GIL limite la concurrence | Rust pour les modules critiques (en cours) |
| **Redis pour la mémoire working** : Redis est single-threaded | Memcached ou Redis Cluster |
| **Architecture monorepo** : Le monorepo peut devenir ingérable | Packages séparés avec versions indépendantes |

### Choix à modifier

1. **Kernel Go vs Python** : Le kernel Go est une bonne idée pour la performance, mais ajoute de la complexité. **Recommandation** : garder le kernel Go pour l'event bus et le routing, mais déplacer la logique métier dans des modules Python.

2. **Event Bus NATS vs Kafka** : NATS est excellent pour le low-latency, mais Kafka est plus mature pour le event sourcing. **Recommandation** : commencer par NATS, migrer vers Kafka si les besoins de rétention dépassent 1 semaine.

3. **PostgreSQL comme unique source de vérité** : PostgreSQL est polyvalent, mais pas optimisé pour le time-series. **Recommandation** : ajouter TimescaleDB pour les métriques et EventStoreDB pour les événements.

4. **Skills comme workflows** : Le système de Skills actuel est trop rigide. **Recommandation** : implémenter un vrai moteur de workflows (temporal.io ou équivalent).

---

## Philosophie

### Principes directeurs

1. **Le kernel n'est pas intelligent** : il route des événements, il ne raisonne pas.
2. **Les modules sont autonomes** : ils ne s'appellent pas directement, ils émettent des événements.
3. **Les interfaces sont des fenêtres** : elles ne contiennent aucune logique métier.
4. **L'état est externalisé** : Redis pour le live, PostgreSQL pour le permanent.
5. **Les LLM sont des moteurs** : ils proposent, ETHAN décide.

### Postulats

- L'intelligence n'est pas un appel à un modèle. C'est un pipeline de modules spécialisés.
- Un module ne peut pas remplacer le kernel. Le kernel ne peut pas remplacer un module.
- La persistance n'est pas optionnelle. Sans état, il n'y a pas de cognition.
- L'observabilité n'est pas un luxe. Sans traces, il n'y a pas de confiance.

---

## Les principes fondamentaux

### 1. Event-Driven Only

Toute communication entre modules se fait par événements sur le bus.

**Interdit** : appels de fonctions directes entre modules.  
**Obligatoire** : émettre un événement, laisser le kernel router.

### 2. Modular Independence

Chaque module est un processus indépendant avec une responsabilité unique.

- Executive : coordination des buts
- Planner : décomposition en tâches
- Memory : stockage et rappel
- Reflective : évaluation des outcomes
- Autonomy : initiative autonome
- Learning : amélioration continue

### 3. Kernel Neutrality

Le kernel est un orchestrateur, pas un décideur.

- Il ne raisonne pas
- Il ne choisit pas de stratégie
- Il route, il schedule, il stocke l'état

### 4. Model Agnostic

Aucune dépendance sur un fournisseur LLM spécifique.

- OpenAI, Anthropic, Google, Ollama, vLLM, SGLang, llama.cpp
- Tous sont des moteurs d'inférence remplaçables
- Le LLM Manager sélectionne le meilleur selon le contexte

### 5. State Externalization

Tout état critique est externalisé.

- **Redis** : état live (TTL, atomic ops)
- **PostgreSQL** : état permanent (event sourcing, snapshots)
- **Interdit** : état in-memory non reconstructible

### 6. Plugin-First

Toute extension se fait par plugin, jamais par modification du core.

- CLI plugins : ajout de commandes
- Module plugins : ajout de capacités
- Skills : compositions d'outils

### 7. Observability by Default

Tout événement est loggé. Toute transition d'état est enregistrée.

- Event sourcing complet
- Traces distribuées (correlation_id, span_id)
- Métriques temps réel
- Pas de mutation silencieuse

### 8. Failure is Normal

Les modules crash. Le bus se partitionne. Les réseaux tombent.

- Le kernel redémarre les modules (backoff exponentiel)
- L'état survit aux redémarrages
- Les événements sont durables (NATS JetStream + PostgreSQL)

### 9. No Secrets in Code

Les secrets vivent dans des variables d'environnement, Docker secrets ou un vault.

- Jamais dans le code source
- Jamais dans les événements
- Jamais dans les logs

### 10. Namespace Isolation

Aucun module ne touche aux clés d'état d'un autre module sans déclaration explicite.

- Isolation au niveau infrastructure
- Permissions par capability
- Pas de partage implicite

---

## Les responsabilités du Core

Le Core d'ETHAN est responsable de :

### Kernel

- **Router** : distribuer les événements aux modules selon les capabilities
- **Scheduler** : exécution temporelle et conditionnelle
- **State Manager** : lecture/écriture Redis, commit PostgreSQL
- **Capability Registry** : contrats des modules, validation, requêtes
- **Goal Manager** : suivi et évaluation des buts actifs
- **Telemetry** : santé des modules, latence, taux d'erreur

**Ce que le kernel NE fait PAS** :

- Il ne raisonne pas
- Il n'exécute pas la logique métier des modules
- Il n'interprète pas les payloads des événements

### Modules

- **Executive** : coordination des buts, gestion des priorités
- **Planner** : décomposition de buts en DAG de tâches
- **Memory** : stockage, rappel, contexte, embeddings
- **Reflective** : évaluation des outcomes, auto-évaluation
- **Autonomy** : initiation de buts, action autonome
- **Learning** : extraction de patterns, propositions d'amélioration
- **Metacognition** : conscience système, gestion des ressources

**Ce que les modules NE font PAS** :

- Ils ne s'appellent pas directement
- Ils ne contournent pas le bus d'événements
- Ils ne contiennent pas d'interface utilisateur

---

## Les interfaces

Les interfaces sont des clients fins. Elles traduisent les actions utilisateur en événements et observent l'état du système.

### Principe

> Aucune interface ne contient de logique métier.

### Interfaces officielles

| Interface | Location | Transport | Rôle |
|-----------|----------|-----------|------|
| **CLI** | `cli/` | exec local | Interface principale |
| **Web UI** | `ethan-ui/` | HTTP/SSE | Interface browser |
| **Desktop** | `desktop/` | Tauri | Application native |
| **API REST** | `api/` | HTTP/REST | Accès machine |
| **Shell** | `ethan-shell/` | exec local + completion | Intégration shell |
| **VSCode** | `frontend/` | TCP/WebSocket | Extension éditeur |

### Contrat des interfaces

1. **Pas de logique métier** : toute décision passe par le Core
2. **Pas d'appel direct aux modules** : tout passe par l'event bus
3. **Lecture d'état via API** : jamais accès direct à Redis/PostgreSQL
4. **Actions = événements** : toute action utilisateur émet un événement

### Équivalence

Toutes les interfaces sont interchangeables. Aucune n'est privilégiée.

```
Utilisateur
    │
    ├─► CLI ──► Event Bus
    ├─► Web UI ──► Event Bus
    ├─► Desktop ──► Event Bus
    ├─► API ──► Event Bus
    └─► Shell ──► Event Bus
```

---

## Les fournisseurs LLM

### Principe

Les LLM sont des **moteurs de raisonnement**, pas des décideurs.

Ils proposent. ETHAN décide.

### Architecture

```
LLM Manager
    │
    ├─► OpenAI (GPT-4, GPT-4o)
    ├─► Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
    ├─► Google (Gemini 1.5 Pro, Gemini 2.0)
    ├─► Ollama (Llama 3, Mistral, Gemma)
    ├─► vLLM (Llama, Mixtral)
    ├─► SGLang (multi-model)
    ├─► llama.cpp (GGUF)
    └─► LiteLLM (agrégateur)
```

### Sélection

Le LLM Manager choisit le meilleur moteur selon :

- **Complexité de la requête** : simple → local, complexe → cloud
- **Coût** : préférence pour les modèles locaux gratuits
- **Latence** : temps de réponse maximal acceptable
- **Capacités** : vision, code, reasoning, etc.
- **Disponibilité** : fallback si un moteur est indisponible

### Contrat

Tout fournisseur LLM implémente l'interface `InferenceEngine` :

```python
class InferenceEngine(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: Context) -> LLMResponse:
        """Génère une réponse."""
        pass

    @abstractmethod
    async def stream(self, prompt: str, context: Context) -> AsyncIterator[str]:
        """Stream une réponse token par token."""
        pass
```

### Interdits

- Un module ne dépend pas d'un fournisseur spécifique
- Aucune logique métier dans le LLM Manager
- Les prompts système ne contiennent pas de décisions système

---

## Les outils

### Principe

Un outil est une capacité atomique avec un contrat explicite.

### Architecture

```
Tool Registry (catalogue)
    │
    ├─► Tool Selector (scoring)
    ├─► Tool Executor (exécution)
    └─► Tool Monitor (surveillance)
```

### Contrat d'outil

```python
@dataclass
class Tool:
    id: str
    name: str
    description: str
    capabilities: list[str]
    cost_per_call: float
    avg_duration_ms: float
    risk_level: RiskLevel
    required_permissions: list[str]
```

### Catégories

| Catégorie | Exemples | Risk Level |
|-----------|----------|------------|
| **Read** | web_search, file_read, pdf_reader | LOW |
| **Write** | file_write, code_writer | MEDIUM |
| **Execute** | shell_exec, code_runner, docker_build | HIGH |
| **Network** | http_request, api_call | MEDIUM |
| **System** | process_kill, service_restart | CRITICAL |

### Sécurité

- Chaque outil déclare ses permissions
- Le Security Gateway valide avant exécution
- Les outils CRITICAL nécessitent une confirmation utilisateur
- Sandboxing pour les outils HIGH/CRITICAL

---

## Les Skills

### Principe

Une Skill est une **compétence de haut niveau** composée d'outils.

### Exemples

- **Programming** : analyse → écriture → review → tests
- **Web Search** : recherche → extraction → résumé
- **PDF Analysis** : lecture → extraction → analyse
- **Email Reader** : connexion → récupération → parsing
- **Project Creator** : scaffolding → dépendances → Git → config

### Architecture

```
Skill Registry (catalogue)
    │
    ├─► Skill Selector (scoring)
    ├─► Skill Executor (pipeline)
    └─► Skill Composer (composition)
```

### Contrat de Skill

```python
@dataclass
class Skill:
    id: str
    name: str
    description: str
    steps: list[SkillStep]
    required_tools: list[str]
    estimated_duration_ms: int
    risk_level: str
```

### Pipeline

Chaque Skill est un pipeline d'étapes :

```
Étape 1 → Étape 2 → Étape 3 → ...
   │          │          │
   ▼          ▼          ▼
 Outil A    Outil B    Outil C
```

- Dépendances explicites (`depends_on`)
- Étapes optionnelles (`optional=True`)
- Retry policy par étape
- Rollback en cas d'erreur

### Composition

Plusieurs Skills peuvent être composées :

- **Séquentiel** : Skill A → Skill B → Skill C
- **Parallèle** : Skill A + Skill B + Skill C (si indépendantes)
- **Conditionnel** : Si Skill A réussit → Skill B, sinon → Skill C

---

## Le système de mémoire

### Principe

La mémoire est **persistante**, **immutable** et **interrogeable**.

### Architecture

```
Memory Manager
    │
    ├─► Working Memory (Redis)
    │   - État de session actif
    │   - Contexte de conversation
    │   - Cache récent (TTL)
    │
    ├─► Long-term Memory (PostgreSQL)
    │   - Event log (append-only)
    │   - Historique des buts
    │   - Patterns appris
    │   - Snapshots d'état
    │
    └─► Vector Store (pgvector / ChromaDB)
        - Embeddings sémantiques
        - Recherche par similarité
```

### Propriétés

1. **Immutable** : les entrées ne sont jamais modifiées, seulement ajoutées
2. **Traçable** : chaque entrée a un parent (chaîne de causalité)
3. **Isolée** : aucun module ne touche aux clés d'un autre module
4. **Interrogeable** : recherche par similarité sémantique

### Context Assembly

Le Context Manager assemble le contexte pour les modules :

```
Requête
    │
    ▼
Memory Manager
    │
    ├─► Récupérer historique récent (Redis)
    ├─► Récupérer souvenirs pertinents (pgvector)
    ├─► Récupérer buts actifs (PostgreSQL)
    │
    ▼
Contexte assemblé → Module consommateur
```

---

## La sécurité

### Principe

**Zero Trust** : aucun composant n'est fiable par défaut.

### Architecture

```
Security Gateway
    │
    ├─► Validation (signatures, schémas)
    ├─► Permissions (RBAC par capability)
    ├─► Policy Engine (rules, rate limiting)
    └─► Audit (logs, traces)
```

### Couches

1. **Input Validation** : valider tous les événements entrants
2. **Permission Check** : vérifier les permissions avant chaque action
3. **Policy Engine** : règles métier (rate limiting, quotas)
4. **Audit Log** : tracer toute action sensible

### Secrets

- **Jamais dans le code**
- **Jamais dans les événements**
- **Jamais dans les logs**
- Stockage : variables d'environnement, Docker secrets, Vault

### Sandboxing

- Outils HIGH/CRITICAL exécutés dans des sandbox
- Isolation par namespace Linux
- Limitation des ressources (CPU, RAM, réseau)

---

## Les événements

### Principe

Toute communication est un événement sur le bus.

### Architecture

```
Event Bus (NATS JetStream)
    │
    ├─► Publishers (interfaces, modules)
    ├─► Subscribers (modules, kernel)
    └─► Persistence (PostgreSQL)
```

### Schéma d'événement

```json
{
  "id": "uuid",
  "type": "module.action",
  "source": "module_name",
  "timestamp": "ISO8601",
  "payload": {},
  "context": {
    "correlation_id": "uuid",
    "span_id": "uuid",
    "parent_span_id": "uuid"
  }
}
```

### Garanties

- **At-least-once** : NATS durable subscriptions
- **Ordre par sujet** : ordering garanti par subject
- **Pas de perte** : JetStream + backup PostgreSQL
- **Replay** : les événements sont rejouables depuis n'importe quel point

### Subjects

```
ethan.interface.<source>.<action>
ethan.module.<name>.<event_type>
ethan.capability.<name>
ethan.memory.<action>
ethan.system.<action>
```

---

## Les flux de données

### Flux synchrone (CLI / API)

```
1. Utilisateur envoie une requête
2. Interface normalise → Intent Object
3. Interface émet événement sur NATS
4. Kernel reçoit, valide, route
5. Modules exécutent, écrivent Redis
6. Kernel commit transitions dans PostgreSQL
7. Interface observe le changement d'état
8. Interface présente le résultat
```

### Flux asynchrone (autonome)

```
1. Module détecte une condition
2. Module émet événement autonome
3. Kernel route vers modules intéressés
4. Pipeline s'exécute sans utilisateur
5. Mises à jour d'état (Redis + PostgreSQL)
6. Goal Manager évalue le progrès
```

### Flux cognitif complet

```
Requête utilisateur
    │
    ▼
Orchestrator
    │
    ├─► Cognition (analyse d'intention)
    │       │
    │       ▼
    │   Memory (contexte)
    │       │
    │       ▼
    │   LLM (raisonnement)
    │       │
    │       ▼
    │   Planner (décomposition)
    │       │
    │       ▼
    │   Tools (exécution)
    │       │
    │       ▼
    │   Reflective (évaluation)
    │
    ▼
Réponse
```

---

## Les décisions d'architecture

### Pourquoi un Kernel Go ?

- **Performance** : le routing d'événements doit être rapide
- **Concurrence** : goroutines pour le parallélisme
- **Typage fort** : détection d'erreurs à la compilation
- **Déploiement** : binaire statique, pas de runtime

**Alternative** : Python avec FastAPI + asyncio.  
**Pourquoi pas** : le GIL limite la concurrence, moins performant pour le routing haute fréquence.

### Pourquoi NATS ?

- **Latence** : < 1ms pour le routing
- **Durabilité** : JetStream pour la persistance
- **Scalabilité** : clustering horizontal
- **Simplicité** : API minimaliste

**Alternative** : Kafka.  
**Pourquoi pas** : trop lourd pour le use case, ops plus complexes.

### Pourquoi PostgreSQL ?

- **Polyvalence** : relationnel + JSONB + pgvector
- **Fiabilité** : ACID, 20 ans de maturité
- **Écosystème** : outils, monitoring, backups

**Alternative** : EventStoreDB pour les événements, TimescaleDB pour les métriques.  
**Pourquoi pas maintenant** : surcharge opérationnelle pour le MVP. Migration possible plus tard.

### Pourquoi Redis ?

- **Vitesse** : in-memory, < 1ms
- **Structures** : strings, hashes, streams, sets
- **TTL** : expiration automatique

**Alternative** : Memcached (moins de fonctionnalités) ou Redis Cluster (pour le scale).  
**Pourquoi Redis** : bon compromis fonctionnalités/performance.

### Pourquoi Python pour les modules ?

- **Écosystème** : ML/AI, NLP, data science
- **Productivité** : développement rapide
- **Interopérabilité** : bindings Rust via PyO3 pour les performances critiques

**Alternative** : Tout Rust.  
**Pourquoi pas** : courbe d'apprentissage, temps de développement plus long.

---

## Les objectifs V1

### MVP fonctionnel

- [x] Kernel Go avec routing d'événements
- [x] Event Bus NATS JetStream
- [x] 6 modules cognitifs de base
- [x] Persistance Redis + PostgreSQL
- [x] CLI fonctionnelle
- [x] API REST
- [x] 5 Skills intégrées
- [x] Tool Manager avec 20+ outils
- [x] LLM Manager multi-provider
- [x] Sécurité Zero Trust basique

### Critères de succès V1

1. Un utilisateur peut envoyer une requête via CLI
2. Le système décompose le but en tâches
3. Les outils sont exécutés en sandbox
4. Le résultat est retourné avec traçabilité complète
5. L'état persiste après redémarrage

---

## Les objectifs V2

### Autonomie

- [ ] Goal Manager avec évaluation automatique
- [ ] Module Autonomy (initiative de buts)
- [ ] Module Learning (amélioration continue)
- [ ] Module Metacognition (conscience système)
- [ ] Planification autonome (sans prompt utilisateur)

### Évolutivité

- [ ] Clustering NATS
- [ ] Redis Cluster
- [ ] Sharding PostgreSQL
- [ ] Distribution des modules sur plusieurs machines

### Observabilité

- [ ] Traces distribuées (OpenTelemetry)
- [ ] Dashboards Grafana
- [ ] Alertes automatiques
- [ ] Replay d'événements pour debugging

---

## La vision V3

### Cognitive OS

ETHAN devient un véritable système d'exploitation cognitif :

- **Multi-utilisateurs** : isolation par namespace
- **Multi-tenancy** : plusieurs instances sur la même infrastructure
- **Marketplace** : plugins et skills partagés
- **Apprentissage fédéré** : amélioration sans partage de données
- **Auto-évolution** : le système améliore sa propre architecture

### Recherche

- **Efficacité énergétique** : métriques FLOPs/watt
- **Raisonnement symbolique** : intégration de logique formelle
- **Conscience de soi** : métacognition avancée
- **Éthique** : gardes fous, alignement, transparence

---

## Les conventions de développement

### Structure du code

```
core/
├── types/          # Dataclasses partagés
├── bus/            # Event Bus
├── config/         # Configuration
├── plugins/        # Système de plugins
├── agents/         # Agents de base
├── events/         # Système d'événements
├── cognition/      # Module Cognition
├── memory/         # Module Memory
├── planner/        # Module Planner
├── executive/      # Module Executive
├── tools/          # Tool Manager
├── llm/            # LLM Manager
├── skills/         # Skills System
├── security/       # Sécurité
├── orchestrator/   # Orchestrator Principal
└── ...
```

### Nommage

- **Fichiers** : `snake_case.py`
- **Classes** : `PascalCase`
- **Fonctions** : `snake_case()`
- **Constantes** : `UPPER_CASE`
- **Modules** : `lowercase`

### Documentation

- Docstrings Google style
- Type hints obligatoires
- README par module
- ADR pour les décisions importantes

### Tests

- pytest pour les tests unitaires
- pytest-asyncio pour les tests async
- Couverture > 80%
- Tests d'intégration pour les flux complets

---

## Les règles à respecter avant toute contribution

1. **Lire l'architecture** : comprendre le système avant de modifier
2. **Ouvrir une issue** : discuter avant d'implémenter
3. **Suivre les conventions** : cohérence du code
4. **Tester** : toute fonctionnalité doit être testée
5. **Documenter** : mettre à jour la doc
6. **Review** : toute modification doit être reviewée
7. **Pas de breaking change** sans discussion préalable
8. **Respecter les principes** : event-driven, modular, observable

---

## Les erreurs d'architecture à éviter

### 1. Couplage fort entre modules

**Interdit** : `module_a.call(module_b.method())`  
**Obligatoire** : `event_bus.publish("module_a.action", data)`

### 2. État in-memory critique

**Interdit** : stocker l'état dans des variables globales  
**Obligatoire** : Redis/PostgreSQL pour tout état critique

### 3. Logique métier dans les interfaces

**Interdit** : le CLI prend des décisions  
**Obligatoire** : le CLI émet des événements, le Core décide

### 4. Dépendance à un fournisseur LLM

**Interdit** : `import openai` dans un module métier  
**Obligatoire** : utiliser l'abstraction `InferenceEngine`

### 5. Mutation silencieuse

**Interdit** : modifier l'état sans émettre d'événement  
**Obligatoire** : toute modification passe par le bus

### 6. Secrets dans le code

**Interdit** : `API_KEY = "sk-..."`  
**Obligatoire** : `API_KEY = os.environ["API_KEY"]`

### 7. Module monolithique

**Interdit** : un module qui fait tout  
**Obligatoire** : responsabilité unique par module

---

## Les principes SOLID appliqués au projet

### Single Responsibility

Chaque module a une seule raison de changer :

- Executive : coordination des buts
- Planner : décomposition en tâches
- Memory : stockage/rappel
- Reflective : évaluation
- Autonomy : initiative
- Learning : amélioration

### Open/Closed

Ouvert à l'extension, fermé à la modification :

- Ajouter une skill = plugin, pas de modification du core
- Ajouter un outil = enregistrement, pas de modification du core
- Ajouter une interface = client fin, pas de modification du core

### Liskov Substitution

Tout module peut être remplacé par un autre implémentant la même interface :

```python
class CognitiveModule(ABC):
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        pass
```

### Interface Segregation

Les interfaces sont minimales et spécifiques :

- `EventBus` : publish, subscribe, close
- `InferenceEngine` : generate, stream
- `StorageBackend` : write, read, checkpoint

### Dependency Inversion

Les modules dépendent d'abstractions, pas d'implémentations :

```python
# Bon
class Executive:
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus

# Mauvais
class Executive:
    def __init__(self, nats_client: NATSClient):
        self._bus = nats_client
```

---

## Les principes Zero Trust

### 1. Never trust, always verify

Tout événement est validé avant traitement.

### 2. Least privilege

Chaque module a les permissions minimales nécessaires.

### 3. Assume breach

Le système est conçu pour fonctionner même si un composant est compromis.

### 4. Explicit allow

Tout ce qui n'est pas explicitement autorisé est interdit.

### 5. Audit everything

Toute action est tracée dans PostgreSQL.

---

## Les décisions importantes

### ADR-001 : Kernel en Go

**Décision** : Le kernel (routing, scheduling) est implémenté en Go.  
**Contexte** : Besoin de performance pour le routing d'événements haute fréquence.  
**Conséquences** : Ajout de complexité (deux langages), mais performance justifiée.

### ADR-002 : NATS comme Event Bus

**Décision** : NATS JetStream pour l'event bus.  
**Contexte** : Besoin de latence < 1ms, durabilité, scalabilité.  
**Conséquences** : Dépendance à NATS, mais excellente DX et performance.

### ADR-003 : PostgreSQL comme source de vérité

**Décision** : PostgreSQL pour la persistance événementielle.  
**Contexte** : Besoin de fiabilité, ACID, requêtes complexes.  
**Conséquences** : Single point of stockage, mais mature et polyvalent.

### ADR-004 : Architecture modulaire par événements

**Décision** : Communication 100% événementielle entre modules.  
**Contexte** : Découplage, observabilité, résilience.  
**Conséquences** : Complexité initiale, mais évolutivité maximale.

### ADR-005 : LLM comme moteur, pas comme décideur

**Décision** : Les LLM proposent, ETHAN décide.  
**Contexte** : Éviter la dépendance à un fournisseur, garder le contrôle.  
**Conséquences** : Nécessite une couche de décision (Executive), mais garde l'humain dans la boucle.

---

## Les futurs axes d'évolution

### Court terme (V1)

- Finaliser les 8 modules cognitifs
- Implémenter les pipelines de base
- Tester l'intégration complète
- Documentation utilisateur

### Moyen terme (V2)

- Autonomie (Goal Manager, Autonomy Module)
- Learning loop (amélioration continue)
- Observabilité (traces, dashboards)
- Clustering (multi-machine)

### Long terme (V3)

- Cognitive OS (multi-utilisateurs, multi-tenancy)
- Marketplace (plugins, skills partagés)
- Apprentissage fédéré
- Auto-évolution

---

## Conclusion

ETHAN n'est pas un produit. C'est un **substrat**.

Il ne répond pas à des questions. Il héberge de la cognition.

Il n'oublie pas quand on ferme l'interface. Il maintient l'état.

Il ne dépend pas d'un modèle. Il supporte tous les fournisseurs.

Il ne centralise pas le contrôle. Il orchestre, il ne décide pas.

ETHAN fournit la structure. L'intelligence vient de comment on l'utilise.

C'est la différence entre un outil et un runtime.

---

**Document maintenu par l'équipe ETHAN.**  
**Dernière révision : Juin 2026**