# ADR-001: Système d'Agents

## Statut
Accepté

## Contexte
Ethan a besoin d'un système d'agents pour orchestrer des tâches complexes. Les agents doivent être spécialisés, indépendants, et communiquer via l'Event Bus.

## Décision
Créer un système d'agents avec :
- **Agent** : classe de base avec cycle de vie (init → run → stop)
- **AgentRegistry** : gestionnaire d'agents
- **Agent spécialisés** : Planner, Research, Developer, Memory, Vision, Voice, Browser, Automation, Security
- Communication via `core/events/` (Event Bus)

## Conséquences
- Les agents sont indépendants et remplaçables
- Nouveaux agents ajoutés sans modifier l'existant
- Communication asynchrone via Event Bus
- Monitoring via Prometheus metrics