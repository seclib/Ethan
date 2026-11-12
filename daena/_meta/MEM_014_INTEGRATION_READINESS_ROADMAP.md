# MEM_014_INTEGRATION_READINESS_ROADMAP

Date : 2026-11-03
Objectif : passer du socle MEM-014 aux intégrations réelles d'Odin, Frame et TradingAgents.

## Étape 1 — Sécuriser le socle

1. Rendre obligatoire `HumanAuthority` pour toute permission accordée.
2. Persister les décisions HROT et autorisations.
3. Ajouter des tests de chaîne complète déterministes.
4. Durcir le mapping permission/capacité.

## Étape 2 — Capability registry

1. Définir une liste initiale de capacités d'intégration.
2. Documenter chaque capacité.
3. Valider la syntaxe et la cohérence avec les permissions.

## Étape 3 — Resilience opérationnelle

1. Finaliser la voie asynchrone.
2. Implémenter les timeouts réels.
3. Persister les états de cycle de vie critiques.

## Étape 4 — Adaptateurs applicatifs

Pour Odin :
- Manifeste et identité.
- Capacités `health`, `state`, `logs`.
- Permissions minimales.
- Contrat et conformité.
- Supervision via Docker Compose.
- Observabilité.

Pour Frame :
- Manifeste Web.
- Capacités `state`, `full_interface_proxy` si pertinent.
- Permissions UI.
- Conformité et supervision compose.
- Observabilité.

Pour TradingAgents :
- Manifeste CLI/LangGraph.
- Capacités `research-analysis`, `reports`.
- Permissions en lecture.
- Contrat et conformité.
- Supervision de processus.
- Observabilité.

## Étape 5 — Validation finale

1. Tests end-to-end déterministes sans lancement reel.
2. Contrôles HROT.
3. Contrôles de conformité.
4. Vérification documentaire.
5. Publication limitée et allowlist.

## Prochaine action recommandée

Appliquer d'abord les corrections de sécurité Phase 3, puis ajouter les tests de chaîne complète.
