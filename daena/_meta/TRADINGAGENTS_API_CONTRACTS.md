# TRADINGAGENTS_API_CONTRACTS.md

Date : 2026-11-03
Statut : PROPOSED

## Principes

- Une API n'expose que des capacités réelles.
- Aucune commande système arbitraire.
- Permissions et RBAC sont obligatoires.
- Les contrats représentent données observées.
- Le moteur TradingAgents n'est jamais importé par appel direct si son interface existe déjà.

## Point d'importance architectural

Compte tenu du fait que TradingAgents est autonome, ETHAN ne doit pas l'absorber ni l'enfermer. Les API proposées sont une frontière de platform, pas des routes obligatoires partout.

## Routes proposées

- `/v1/tools/trading-agents/status`
- `/v1/tools/trading-agents/capabilities`
- `/v1/tools/trading-agents/analyses`
- `/v1/tools/trading-agents/analyses/{id}`
- `/v1/tools/trading-agents/cancel`
- `/v1/tools/trading-agents/logs`
- `/v1/tools/trading-agents/results`

## Responsabilités de l'interface

- accepter les paramètres validés ;
- refuser les entrées ambiguës ;
- vérifier les permissions ;
- renvoyer des états de tâches ;
- collecter les événements Engineering Memory.

## Politique de sécurité

- Authentification et HROT ;
- pas d'auto-approval ;
- pas de secret dans le body ;
- inputs maximaux ;
- errors explicites.

<!-- SHARED_INTELLIGENCE_SECTION -->

## Shared Intelligence Clarification

Les applications indépendantes peuvent demander à ETHAN des capacités d'intelligence compatibles, sans abandonner leur autonomie.

- l'application reste moteur propre ;
- ETHAN propose des capacités ;
- les LLM et modèles réutilisés uniquement après vérification ;
- les Knowledge et Skills restent sous leurs conditions de sécurité ;
- les déclarations d'agents sont distinctes des preuves.
- références : `../Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`.
