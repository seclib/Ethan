# Constitution Architecturale d'Ethan OS

> Version 1.0 — Document fondateur

---

## 1. Nature du système

Ethan OS n'est pas une application.

C'est un **système d'exploitation pour intelligence artificielle autonome**.

Il orchestre des capacités, des agents et des flux d'information.

---

## 2. Principe fondamental

Le système est construit sur une règle absolue :

> **Le Core ne dépend jamais de technologies.**

Il dépend uniquement d'interfaces (Ports).

Les implémentations sont des Adapters.

---

## 3. Séparation stricte des responsabilités

Le système est divisé en domaines indépendants :

* **Core** — raisonnement
* **Memory** — mémoire
* **Knowledge** — connaissance
* **Agents** — comportements
* **Capabilities** — actions
* **Providers** — modèles IA
* **Infrastructure** — runtime

Aucun domaine ne doit accéder directement à un autre domaine interne.

---

## 4. Principe d'abstraction

Toute interaction externe passe par une abstraction.

Exemples :

* LLM → Provider
* Docker → Capability
* Redis → Memory Provider
* PostgreSQL → Memory Provider
* Qdrant → Memory Provider

Le Core ignore complètement les implémentations.

---

## 5. Principe d'orchestration

Ethan ne "fait pas".

Ethan **décide**.

Chaque action suit ce flux :

```
Perception → Analyse → Planification → Exécution → Observation → Mémoire
```

---

## 6. Event-driven system

Tout est un événement.

* Input utilisateur
* Décision du planner
* Appel de capability
* Résultat d'exécution
* Mise à jour mémoire

Les composants ne s'appellent jamais directement.

Ils réagissent aux événements.

---

## 7. Capability Model

Toute action est une Capability.

Une capability est :

* autonome
* interchangeable
* isolée
* testable

Le Core ne connaît pas les outils.

Il connaît des capacités.

---

## 8. Provider Model

Les modèles IA sont interchangeables.

Le Core ne connaît pas :

* Ollama
* OpenAI
* Anthropic

Il connaît uniquement :

> "Je demande une capacité de raisonnement"

---

## 9. Memory Principle

La mémoire n'est pas un stockage.

C'est un système de cognition.

Elle est :

* structurée
* hiérarchisée
* évolutive
* indépendante des bases de données

---

## 10. Evolution principle

Le système doit être :

* extensible sans modification du Core
* modulaire
* remplaçable
* testable
* observable

---

## 11. Safety principle

Aucune action ne peut être exécutée sans :

* validation du système
* contexte clair
* traçabilité

---

## 12. Final goal

Ethan OS doit devenir :

> Un système autonome capable de percevoir, raisonner, agir et apprendre dans un environnement numérique complexe.

---

*Document fondateur. Tout RFC ou modification doit respecter ces principes.*