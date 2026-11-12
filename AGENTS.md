# AGENTS.md — ETHAN Architecture Guidelines


# Première Loi d'ETHAN

ETHAN est le système.

Le Core représente l'intelligence.

Le Runtime représente l'orchestration.

Les Services représentent l'infrastructure.

Les Interfaces représentent les moyens d'interagir avec ETHAN.

---

Une fonctionnalité doit être implémentée dans Core ou Runtime lorsqu'elle continue d'avoir du sens même si toutes les interfaces disparaissent.

Une fonctionnalité appartient à une interface uniquement lorsqu'elle concerne l'affichage, l'expérience utilisateur ou l'interaction.

---

ETHAN doit continuer à fonctionner lorsque :

* la WebUI est arrêtée ;
* le CLI est absent ;
* aucun Desktop n'existe.

---

Les interfaces révèlent ETHAN.

Elles ne le définissent pas.

Une interface peut :

afficher ;
visualiser ;
configurer ;
déclencher ;
superviser.

Une interface ne doit pas :

implémenter la logique métier ;
stocker l'état métier ;
définir les providers ;
définir les agents ;
définir la mémoire ;
définir le RAG ;
définir les missions.

Toute capacité ETHAN doit exister dans Core ou Runtime avant d'être exposée dans une interface.

Les interfaces sont remplaçables.

ETHAN doit continuer à fonctionner même si toutes les interfaces sont arrêtées.

Toute nouvelle fonctionnalité doit répondre à la question :

"Cette capacité appartient-elle à ETHAN ou à son interface ?"

Si elle appartient à ETHAN, elle doit être implémentée dans Core ou Runtime.


## Mission

Tu travailles sur ETHAN, un système d'IA modulaire composé d'un Core, d'un Runtime, de services et de plusieurs interfaces.

ETHAN n'est pas une application Web.
ETHAN est un runtime intelligent auquel différentes interfaces peuvent se connecter.

---

# Principe fondamental

## ETHAN existe indépendamment de ses interfaces.

Les interfaces ne définissent pas ETHAN.

Elles le révèlent.

Les composants suivants sont des interfaces :

* WebUI
* CLI
* Desktop
* Mobile
* API externes

Ils permettent d'interagir avec ETHAN mais ne doivent pas devenir propriétaires des capacités métier.

---

# Source de vérité

La source de vérité doit rester :

```
core/
runtime/
services/
```

Les capacités ETHAN doivent appartenir au Core ou Runtime.

Exemples :

* Providers LLM
* Modèles IA
* Configuration IA
* RAG
* Documents
* Memory
* Planner
* Agents
* Skills
* Knowledge
* Automation

Ces éléments ne doivent pas être implémentés uniquement dans une interface.

---

# Règle absolue : éviter les doublons

Avant de créer une nouvelle fonctionnalité :

1. Vérifier si elle existe déjà dans `core/`
2. Vérifier si elle existe dans `runtime/`
3. Réutiliser l'existant si possible
4. Migrer vers le Core si la logique métier est actuellement dans une interface

Ne jamais créer :

```
core/providers/
interfaces/webui/providers/
```

avec deux logiques différentes.

Il doit exister :

```
core/providers/
```

La WebUI doit uniquement afficher et contrôler.

---

# Responsabilité des interfaces

Les interfaces peuvent contenir :

* composants graphiques
* pages
* formulaires
* thèmes
* navigation
* visualisation
* expérience utilisateur

Les interfaces ne doivent pas contenir :

* logique métier ETHAN
* gestion réelle des providers
* moteur RAG
* mémoire
* planification
* intelligence agentique

---

# Exemple Provider LLM

Mauvais :

```
WebUI
 └── Ollama configuration
 └── modèle actif
 └── logique connexion
```

Correct :

```
ETHAN Core

providers/
 └── ollama

Configuration ETHAN
 └── provider actif

WebUI
 └── affiche
 └── modifie via API
```

---

# Exemple RAG

Mauvais :

```
WebUI
 └── RAG complet
```

Correct :

```
ETHAN Core

rag/
 ├── ingestion
 ├── embeddings
 ├── retrieval
 └── context

WebUI
 └── interface documentaire
```

---

# Architecture cible

```
                  ETHAN

          Core + Runtime + Services

                    |
                    |

              API / Events

                    |

     ---------------------------------

     WebUI        CLI        Desktop

     Interface   Interface   Interface
```

Chaque interface utilise les mêmes capacités ETHAN.

---

# Nouvelle interface

Lors de la création d'une nouvelle interface :

Ne pas recréer ETHAN.

Ne pas recréer :

* providers
* mémoire
* RAG
* agents
* skills
* configuration

Créer uniquement une nouvelle représentation.

Une interface doit demander :

"Quelles capacités ETHAN possède ?"

et non :

"Comment recréer ces capacités ?"

---

# Migration de code existant

Si une fonctionnalité existe dans WebUI mais devrait appartenir au Core :

Ne pas supprimer brutalement.

Procédure :

1. Identifier la logique métier
2. Déplacer vers Core/Runtime
3. Créer une API ou un service d'accès
4. Transformer WebUI en client
5. Vérifier que CLI et autres interfaces peuvent utiliser la même capacité

---

# Vision long terme

ETHAN doit pouvoir fonctionner sans WebUI.

ETHAN doit pouvoir fonctionner sans CLI.

ETHAN doit pouvoir accueillir :

* Desktop Jarvis
* Voice assistant
* Mobile
* Agents autonomes
* Nouveaux providers IA

Toutes ces interfaces doivent découvrir et utiliser le même ETHAN.

---

# Règle finale

Avant toute modification, toujours se demander :

"Est-ce que je construis ETHAN, ou est-ce que je construis seulement une interface pour ETHAN ?"

Si la réponse concerne une capacité intelligente, elle appartient au Core.

---

# Protocole de mémoire inter-sessions — Codex

## Fichiers de mémoire

- `docs/memory/README.md` : conventions minimales.
- `docs/memory/PROJECT_STATE.md` : état courant, prochaine tâche, blocages.
- `docs/memory/DECISIONS.md` : décisions validées, propositions et hypothèses.
- `docs/memory/sessions/YYYY-MM-DD.md` : archives datées de session.

## Début de session

1. Lire `AGENTS.md`, puis `docs/memory/PROJECT_STATE.md`, `docs/memory/DECISIONS.md` et la dernière archive de session disponible.
2. Vérifier l'état du dépôt, notamment les modifications locales et les fichiers non suivis, avant toute action.
3. Croiser les rapports avec le dépôt. Une ancienne intention n'est jamais une décision validée sauf indication explicite.
4. Distinguer les faits vérifiés, les hypothèses et les recommandations.

## Pendant la session

- Réutiliser les structures existantes plutôt que créer des doublons.
- Ne pas modifier le comportement applicatif, les migrations ou la configuration de production pour une simple tâche documentaire.
- Ne jamais archiver de secrets, tokens, mots de passe, clés privées ou données personnelles.

## Fin de session

1. Mettre à jour `docs/memory/PROJECT_STATE.md` avec l'état courant, la prochaine tâche et les blocages.
2. Mettre à jour `docs/memory/DECISIONS.md` uniquement pour les décisions réellement prises et validées.
3. Créer ou actualiser `docs/memory/sessions/YYYY-MM-DD.md` en séparant clairement :
   - changements effectués ;
   - tests exécutés ;
   - résultats ;
   - hypothèses ;
   - tâches non terminées.
4. Préserver les modifications existantes et n'effectuer aucune opération Git destructive.

Toute activité effectuée sur ETHAN doit être enregistrée dans son Engineering Memory. Aucun agent ne doit considérer son travail comme terminé tant que les événements, résultats et preuves correspondants n'ont pas été consignés. Les données brutes doivent être conservées lorsque leur valeur historique ou probante le justifie. Les synthèses ne remplacent jamais les archives originales.

---

# Outilset MCP — Règles d'ingénierie

ETHAN dispose d'un outilset MCP permanent de dix serveurs, configuré globalement
dans `~/.config/opencode/opencode.json` (forme V2 `mcp.servers`). Chaque agent
peut y accéder selon son périmètre : la sélection du serveur est **contextuelle**,
jamais indiscriminée.

| Tâche d'ingénierie | Serveur MCP | Usage prévu |
|---|---|---|
| Documentation | `context7` | documentation officielle de framework, références d'API, versions de dépendances, guides d'implémentation |
| Dépôt | `github` | inspection du dépôt, branches et commits, issues et PR, historique et revue de code |
| Navigateur | `playwright` | test WebUI, automatisation navigateur, vérification fonctionnelle, régression E2E |
| Base de données | `postgres` | inspection de schéma, analyse des tables et relations, exécution de requêtes, vérification de migrations |
| Diagnostic runtime | `sentry` | analyse d'exceptions, erreurs runtime, stack traces, investigation de régressions |
| Recherche web | `firecrawl` | exploration de sites, extraction documentaire, contenu web structuré |
| Recherche technique | `brave-search` | recherche technique externe, découverte de dépôts, comparaisons, documentation courante |
| Problèmes complexes | `sequential-thinking` | architecture complexe, analyse de dépendances, investigations multi-étapes, décision technique |
| Déploiement | `vercel` | inspection de projet, statut de déploiement, diagnostics de build, configuration de déploiement |
| Design | `figma` | inspection de design, composants et design system, spécifications de layout, implémentation design-vers-code |

## Règles obligatoires

1. **Consulte Context7** avant d'implémenter contre une API peu familiere ou
   sensible à la version.
2. **Utilise GitHub** pour comprendre le code existant et son historique avant de
   le modifier.
3. **Utilise Playwright** pour valider le comportement réel de la WebUI quand la
   question porte sur l'interface.
4. **Utilise PostgreSQL** pour vérifier les hypothèses de base de données au
   lieu de les supposer. Le compte MCP est **strictement en lecture seule** :
   aucune écriture, aucun DDL, aucune migration.
5. **Utilise Sentry** pour investigating une erreur runtime réelle.
6. **Utilise Firecrawl et Brave Search** pour la recherche externe.
7. **Utilise Sequential Thinking** pour les problèmes complexes — pas pour les
   opérations triviales.
8. **Utilise Figma** pour implémenter un design existant.
9. **Utilise Vercel** quand l'infrastructure de déploiement est en jeu.
10. **Ne declare jamais qu'une operation MCP a reussi sans avoir verifie son
    resultat.**

## Sélection contextuelle

- La selection du serveur MCP decoule de la nature de la tache, pas de la
  disponibilite d'un outil.
- Un agent ne charge que les serveurs de son perimetre : `database-engineer`
  n'a que `postgres`, `qa-engineer` n'a que `playwright` et `sentry`, etc.
- Le MCP **sequential-thinking** n'apporte rien a une operation triviale : ne
  l'utilise que lorsqu'il ajoute une valeur reelle.
- Les agents delegables : `architect`, `developer`, `frontend-engineer`,
  `qa-engineer`, `database-engineer`, `researcher`, `devops-engineer`,
  `reviewer`. L'agent principal selectionne et delegue.

## Securite

- Les secrets ne sont jamais ecrits dans un fichier de projet. Ils passent par
  des variables d'environnement (`{env:NOM}`).
- **GitHub** : lecture seule par defaut. Issues, PR, commits et branches
  interdits sans autorisation explicite.
- **Vercel** : aucun deploiement declenche sans autorisation explicite.
- **Sentry** : creation d'issue interdite sans autorisation explicite.
- **PostgreSQL** : lecture seule, en plus du compte lui-meme verifie.
- Les permissions et acces existants du depot sont respectes.

## Etat des authentifications

Les serveurs OAuth exigent une connexion une fois pour toutes, via l'interface
`/mcps` d'OpenCode (selectionner le serveur, puis se connecter) :

| Serveur | Authentification | Etat initial |
|---|---|---|
| `context7` | aucune requise | operationnel |
| `firecrawl` | aucune requise (keyless) | operationnel |
| `playwright` | aucune requise | operationnel |
| `postgres` | role SQL en lecture seule | operationnel |
| `sequential-thinking` | aucune requise | operationnel |
| `github` | OAuth | **connexion requise** |
| `sentry` | OAuth | **connexion requise** |
| `vercel` | OAuth | **connexion requise** |
| `figma` | OAuth | **connexion requise** |
| `brave-search` | `BRAVE_API_KEY` | **cle requise** (serveur desactive) |
