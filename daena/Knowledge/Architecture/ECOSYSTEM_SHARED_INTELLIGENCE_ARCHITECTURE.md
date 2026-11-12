# ETHAN — Architecture d'intelligence partagée pour les applications indépendantes

Date : 2026-11-03
Statut : USER_APPROVED par MEM-014 le 2026-11-03 (cadre décisionnel) ; non implémenté
Applicabilité : Odin, Frame, TradingAgents et futures applications de l'écosystème.

## 1. Principe

Les applications indépendantes conservent leur moteur, leurs données, leurs dépendances et leur interface native.

Elles peuvent demander à ETHAN des capacités d'intelligence compatibles :
- exécution d'un agent ;
- appel à un LLM ;
- accès à une Skill autorisée ;
- recherche dans Knowledge ;
- synthèse ou validation ;
- production de rapports ;
- référencement de preuves.

ETHAN n'absorbe pas le moteur de l'application. Elle propose une capacité et reste maître de son propre cycle.

## 2. Autonomie

L'application doit continuer avec ses propres agents, modèles et ressources si ETHAN est inaccessible.

Si ETHAN est indisponible :
- le moteur local reste utilisable selon ses capacités propres ;
- les tâches dépendant d'ETHAN sont marquées comme reportées ou manquantes ;
- aucune substitution silencieuse ne doit transformée une analyse locale ;
- l'interface ETHAN WebUI affiche l'état réel de disponibilité.

## 3. Orchestration et déléguations

Trois niveaux sont à distinguer :

1. Orchestration locale par l'application ;
2. Delegation à un agent ETHAN ;
3. Orchestration future par un agent central éventuel, aujourd'hui nommé Atreus, seulement si sa conception est validée.

Atreus n'existe pas aujourd'hui. Son futur contrat doit demeurer compatible avec cette couche d'intelligence partagée sans devenir requis.

## 4. Contrat d'intelligence partagée

Requête :

- contexte ;
- capability demandée ;
- input validé ;
- contraintes ;
- identifiant de trace ;
- TTL / deadline ;
- exigences de sensibilité ;
- identité de l'application.

Réponse :

- résultat structurel ;
- statut ;
- provenance ;
- version de l'agent ou modèle utilisé ;
- limites ;
- citations ;
- identifiant de preuve ;
- erreur normalisée.

## 5. Permissions

- HROT reste l'autorité finale.
- L'application déclare son identité.
- ETHAN valide le jeton et les permissions.
- Moindre privilège.
- Isolation des contextes.
- Révocation possible.
- Aucun agent ne s'auto-attribue une permission.
- Aucune clé HROT accessible aux agents, outils ou applications.

## 6. Contexte et isolation

- Les données transmises sont validées.
- Les contexts ne s'entremêlent pas.
- Les données confidentielles ne transitent pas.
- Les références par ID plutôt que contenu lorsqu'il est possible.
- Les preuves doivent rester interprétables dans leur source.

## 7. TradingAgents — répartition

Ce qui reste interne :

- ré Roles des agents et leurs échanges internes ;
- logique de marché ;
- graphique du workflow ;
- mémoire des décisions et du raisonnement ;
- rapports et résultats analytiques.

Ce qui peut être délégué à ETHAN :
- vérification de disponibilité et politiques ;
- recherche de knowledge complémentaire ;
- utilisation de modèles LLM compatibles ;
- gestion d'agents auxillaires ;
- stockage de résultats ;
- traçabilité dans Engineering Memory.

## 8. Capacités communes aux autres applications

- Odin : tablet, logs, versioning, health et alerte.
- Frame : health, documentation et synthèse possible.
- Les autres applications peuvent réutiliser le même contrat.

## 9. Règles anti-duplication

- La connaissance d'origine reste sur son site d'application.
- La mémoire partagée n'est pas un miroir permanent.
- Les synthèses doivent pointer vers la source.
- Les versions doivent être traçables.
- Les dépendances et permissions doivent être examinées.

## 10. Risques

- HROT preserved.
- abus d'accès à Knowledge.
- biais analytiques.
- Non déterminisme des LLM.
- coûts et latence.
- spoofing d'application.
- confusion entre analyse et exécution réelle.

## 11. Règle de décision

Ce document propose un contrat générique. Il ne fait pas de d'Atreus une fonctionnalité existante. Toute application aura une solution dédiée sauf décision ultérieure.
