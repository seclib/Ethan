# TRADINGAGENTS_IMPLEMENTATION_ROADMAP.md

Date : 2026-11-03
Statut : PROPOSED

## Principes de réconciliation

TradingAgents est une application indépendante. ETHAN conserve sa plateforme centrale et ne possède pas les sources TradingAgents.

## Phases

1. Final audit et licence.
2. Mapping provider.
3. Contrôleur externe dans ETHAN.
4. API et tests non destructifs.
5. WebUI et permissions.
6. Engineering Memory.
7. Tests de sécurité et résilience.
8. Publication externe uniquement par sélection.
9. Documentation et consolidation.
10. Contrôle des applications autonomes sur site.

## Conditions

- Aucune dépendance inutile.
- Architeclture documentation-first.
- Aucun code modifié dans cette phase.

<!-- SHARED_INTELLIGENCE_SECTION -->

## Shared Intelligence Clarification

Les applications indépendantes peuvent demander à ETHAN des capacités d'intelligence compatibles, sans abandonner leur autonomie.

- l'application reste moteur propre ;
- ETHAN propose des capacités ;
- les LLM et modèles réutilisés uniquement après vérification ;
- les Knowledge et Skills restent sous leurs conditions de sécurité ;
- les déclarations d'agents sont distinctes des preuves.
- références : `../Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md`.
