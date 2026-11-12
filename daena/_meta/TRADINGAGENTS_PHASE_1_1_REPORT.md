# TRADINGAGENTS_PHASE_1_1_REPORT.md

Date : 2026-11-03
Status : PHASE_1_1_ARCHITECTURE_RECONCILED_WITH_DECISIONS_PENDING

## 1. Différences introduites par rapport à la conception initiale

La conception initiale présentait TradingAgents comme un moteur pouvant être "wrapped" et orchestré par un contrôleur d'application de façon implicite. Cela prêtait à confusion sur le fait qu'Odin, Frame et TradingAgents pourraient devenir des composants contrôlés de façon uniforme. La clarification réconciliée impose que chaque application indépendante :
- conserve son propre moteur ;
- conserve ses dépendances ;
- puisse fonctionner sans ETHAN ;
- exige un connecteur dédié au lieu d'un contrôleur imposé.

## 2. Responsabilités par couche

- TradingAgents : engine et analyse.
- ETHAN Core : connecteur, identité, health, API et permission.
- WebUI : présentation.
- Engineering Memory : état et audit.

## 3. Contrat générique proposé

Fichier créé :
- /home/fatsio/AI/Ethan/Obsidian/Knowledge/Architecture/ETHAN_APPLICATION_INTEGRATION_CONTRACT.md

Le contrat établit :
- capacités obligatoires ;
- communication ;
- moteurs et connecteurs ;
- security frontiers ;
- memory scoping.

## 4. Adaptations pour TradingAgents

- Utilisation d'un connecteur dédié.
- Validation des paramètres à travers une API ;
- Reports et logs sont référencés plutôt que copiés.
- Ne pas masquer les erreurs.
- Routes spécifiques.

## 5. Conséquences pour Odin et Frame

- Odin reste dans son conteneur et contenus ;
- Frame expose son WebUI local ;
- ETHAN sert de connecteur.
- Aucune transformation de leur source.

## 6. Décisions encore à approuver

- cadence d'intégration ;
- API locale et conteneur vs process wrapping ;
- timeouts ;
- isolation locale ;
- health policy ;
- publication des synthèses.

## 7. Risques et inconnues

- provider mapping ;
- latence ;
- données externes ;
- audit de dépendance ;
- storage reports ;
- isolate non démontré.

## 8. Confirmation qu'aucun code applicatif n'a été modifié

Aucun changement dans les dépôts TradingAgents ou ETHAN. Les modifications concernent uniquement la documentation Obsidian.

<!-- SHARED_INTELLIGENCE_SECTION -->

## Shared Intelligence Clarification

Les applications indépendantes peuvent demander à ETHAN des capacités d'intelligence compatibles, sans abandonner leur autonomie.

- l'application reste moteur propre ;
- ETHAN propose des capacités ;
- les LLM et modèles réutilisés uniquement après vérification ;
- les Knowledge et Skills restent sous leurs conditions de sécurité ;
- les déclarations d'agents sont distinctes des preuves.
- références : `../Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`.
