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
