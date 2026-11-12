# TRADINGAGENTS_CONTROLLER_DESIGN.md

Date : 2026-11-03
Statut : PROPOSED
Alignement : architecture d'intégration application indépendante.

## 1. Boundary

ETHAN fournit un connecteur dédié. TradingAgents reste une application autonome.

Un changement majeur par rapport à une conception process interne est que le contrôleur ETHAN ne doit pas supposer que l'application vit dans le même arbre de code ETHAN.

## 2. Responsabilités

ETHAN :
- détention des permissions ;
- health ;
- lancement et arrêt via contrôle de process dédié ;
- journalisation ;
- retrieving reports lorsque explicitement accordé.

TradingAgents :
- business logic ;
- LLM calls ;
- data access ;
- checkpoints ;
- report writing ;
- environment.

## 3. Interfaces possibles

Option A : l'application expose une API locale minimaliste.
Option B : ETHAN lance un processus et en surveille les sorties et sockets.
Option C : ETHAN utilise l'interface native via le contrôleur.

Le choix dépend de l'architecture réelle de la cible. Le code présenté montre une API/CLI et un package Python; il n'y a pas de serveur REST par défaut. L'API locale est donc une possibilité, pas une certitude.

## 4. Procédure d'administration

`probe`, `ps`, `start`, `stop`, `restart`, `logs`, `config`, `health`, `report(pointer)`.

Les routes peuvent être exposées seulement lorsque la politique le permet et le contrôleur est disponible.

## 5. Règles de sécurité

- moindre privilège ;
- pas d'arbitraire execution ;
- pas de secrets dans logs ;
- pas d'accès Docker directement pour tout agent ;
- rapport et contrôle attitré par human.

## 6. Observabilité

Chaque événement doit conserver la provenance et le statut. Obsidian garde la mémoire; ETHAN garde l'audit.

## 7. Limites

Le contrôleur réel doit être conçu seulement après audit final et sur le principe d'application indépendante.

<!-- SHARED_INTELLIGENCE_SECTION -->

## Shared Intelligence Clarification

Les applications indépendantes peuvent demander à ETHAN des capacités d'intelligence compatibles, sans abandonner leur autonomie.

- l'application reste moteur propre ;
- ETHAN propose des capacités ;
- les LLM et modèles réutilisés uniquement après vérification ;
- les Knowledge et Skills restent sous leurs conditions de sécurité ;
- les déclarations d'agents sont distinctes des preuves.
- références : `../Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`.
