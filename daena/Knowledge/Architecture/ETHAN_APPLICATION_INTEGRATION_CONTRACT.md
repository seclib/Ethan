# ETHAN Application Integration Contract

Date : 2026-11-03
Statut : USER_APPROVED par MEM-014 le 2026-11-03 (cadre décisionnel) ; non implémenté.
Nature : contrat générique approuvé comme décision, en attente des validations et implémentations applicatives.

Ce contrat s'applique à Odin, Frame et TradingAgents.

## 1. Principe

Une application indépendante peut fonctionner sans ETHAN. ETHAN reste une plateforme centrale.

## 2. Capacités obligatoire pour être intégrée

- identity
- version
- compatibility
- health
- discovery (quand ETHAN can reach)
- events (minimum)
- permissions
- documentation

## 3. Capacités facultatives

- state
- logs
- memory reports
- metrics
- resource monitor
- config updates
- full interface proxy

## 4. Communication

Les connecteurs ETHAN ne doivent pas imposer :

- une dépendance au runtime Python d'ETHAN
- une architecture sans service
- des migrations de données permanentes
- la suppression de l'application native

L'authentification et les permissions sont centralisées par ETHAN.

## 5. Moteurs applicatifs

- Odin expose son propre conteneur et contenus
- Frame expose une app web locale
- TradingAgents expose une CLI Python et un moteur LangGraph

Chaque connecteur valide l'application par son moyen réel (HTTP, process, socket ou CLI).

## 6. Security

- pas de trust implicite
- autorisation explicite
- least privilege
- secrets à leur place
- RBAC comme frontière.

## 7. Memory

Seuls les événements d'intégration autorisés sont conservés dans Engineering Memory.

Les données sources restent dans les applications.
