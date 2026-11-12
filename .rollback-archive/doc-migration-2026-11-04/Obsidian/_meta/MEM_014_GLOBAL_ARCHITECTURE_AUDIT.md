# MEM_014_GLOBAL_ARCHITECTURE_AUDIT

Date : 2026-11-03
Statut : audit global en lecture seule
Périmètre : Phases 1 à 7 de MEM-014

## 1. Synthèse exécutive

Les sept phases forment un socle cohérent et progressif pour l'identité, la découverte, les permissions, les contrats, la conformité, la résilience et l'observabilité des applications indépendantes.

État réel :
- 7 modules implémentés dans `core/applications/`.
- Schémas, spécifications et rapports par phase disponibles.
- 79 tests ciblés passent pour les modules MEM-014.
- Aucune application réelle n'a été lancée ni intégrée.
- Les registres opérationnels critiques restent en mémoire.

Conclusion : fondation solide pour la préparation des intégrations réelles, mais pas encore prête pour une exploitation de production sans persistance et tests d'intégration.

## 2. État réel des sept phases

| Phase | État | Preuve |
|---|---|---|
| 1 — Manifest & validator | Implémenté | `core/applications/models.py`, `validator.py`, 8 tests |
| 2 — Discovery | Implémenté | `discovery.py`, 10 tests |
| 3 — Permissions / HROT | Implémenté | `permissions.py`, 9 tests |
| 4 — Extension contracts | Implémenté | `contracts.py`, 7 tests |
| 5 — Compliance | Implémenté | `compliance.py`, 13 tests |
| 6 — Resilience / lifecycle | Implémenté | `resilience.py`, 9 tests |
| 7 — Observability | Implémenté | `observability.py`, 12 tests |

## 3. Matrice décisions / spécifications / code / tests

| Domaine | Décision | Spécification | Code | Tests |
|---|---|---|---|---|
| Identité | Application ≠ instance | `application-identity.md` | `models.py` | Phase 1 |
| Manifeste YAML | strict | `application-manifest.md` | `models.py` / `validator.py` | Phases 1, audit |
| Découverte | read-only, locale | `application-capability-discovery.md` | `discovery.py` | Phase 2 |
| Permissions | HROT explicite | `application-permissions-hrot.md` | `permissions.py` | Phase 3 |
| Contrat | types distincts | `application-integration-contract.md` | `contracts.py` | Phase 4 |
| Conformité | règles versionnées | `application-compliance.md` | `compliance.py` | Phase 5 |
| Résilience | machine à états | `application-resilience-lifecycle.md` | `resilience.py` | Phase 6 |
| Observabilité | schéma versionné | `application-observability-engineering-memory.md` | `observability.py` | Phase 7 |

## 4. Résultats des tests

Commande exécutée :
```bash
./.venv/bin/python -m pytest tests/core/test_application_manifest.py tests/core/test_application_manifest_robustness.py tests/core/test_application_capability_discovery.py tests/core/test_application_permissions_phase3.py tests/core/test_application_extension_contracts_phase4.py tests/core/test_application_compliance_phase5.py tests/core/test_application_resilience_phase6.py tests/core/test_application_observability_phase7.py -q
```

Résultat : `79 passed, 1 warning`.

## 5. Constats classés

### CRITICAL
Aucun constat critique confirmé dans le périmètre implémenté. Aucune exécution d'application n'a été déclenchée par les modules MEM-014.

### HIGH

#### MEM014-AUDIT-001 — Registres de sécurité et d'observabilité en mémoire
- Module : `permissions.py`, `resilience.py`, `observability.py`, `discovery.py`
- Preuve : classes `PermissionService`, `EventCollector`, `IdempotencyRegistry`, `ApplicationDiscoveryService` utilisent des structures en mémoire.
- Conséquence : perte des autorisations, événements et états après redémarrage ; désynchronisation possible.
- Recommandation : persister les décisions HROT et les évaluations critiques ; conserver les événements non critiques dans un journal borné.
- Phase : 3, 6, 7

#### MEM014-AUDIT-002 — Simulation possible d'une approbation humaine par chaîne de caractères
- Module : `permissions.py`, `grant_permission`
- Preuve : `approved_by` seul peut créer une permission si aucune `HumanAuthority` n'est fournie et qu'un principal est indiqué.
- Conséquence : un appelant peut se présenter comme approuvateur sans preuve HROT réelle.
- Recommandation : exiger systématiquement une `HumanAuthority` valide pour toute permission accordée.
- Phase : 3

#### MEM014-AUDIT-003 — Absence de tests d'intégration chaînés
- Modules : toutes les phases
- Preuve : seuls des tests unitaires par phase existent ; aucune suite relie manifeste → découverte → contrat → conformité → permission → cycle de vie.
- Conséquence : régressions transversales possibles.
- Recommandation : créer des scénarios déterministes de chaîne complète sans lancer d'application.
- Phase : 8

### MEDIUM

#### MEM014-AUDIT-004 — Compatibilité permission/capacité par préfixe
- Module : `contracts.py`
- Preuve : `_permission_compatible` accepte toute permission commençant par une capacité plus un séparateur.
- Conséquence : mapping trop permissif, risque de contourner le principe de moindre privilège.
- Recommandation : privilégier un mapping explicite et obligatoire pour les permissions non strictement égales.
- Phase : 4

#### MEM014-AUDIT-005 — Exécuteur résilient asynchrone simulé
- Module : `resilience.py`
- Preuve : `run_async` délègue à `run` synchrone et n'exécute pas de timeout réel.
- Conséquence : limitation des garanties pour les intégrations asynchrones futures.
- Recommandation : implémenter réellement la voie asynchrone si Odin/Frame l'utilisent.
- Phase : 6

#### MEM014-AUDIT-006 — API publiques multiples et alias explosifs
- Modules : `__init__.py`, tous les modules MEM-014
- Preuve : très nombreux alias (`PermissionManager`, `CapabilityDiscovery`, etc.).
- Conséquence : surface d'API large et maintenance complexe.
- Recommandation : documenter une API canonique minimale et marquer les alias comme compatibilité.
- Phase : toutes

#### MEM014-AUDIT-007 — Vocabulaire de capacités ouvert
- Modules : `models.py`, `discovery.py`
- Preuve : aucune whitelist de capacités applicatives.
- Conséquence : capacités arbitraires acceptées ; contrôle sémantique reports à une phase ultérieure.
- Recommandation : définir un registre initial de capacités d'intégration MEM-014.
- Phase : 2, 4

### LOW

#### MEM014-AUDIT-008 — Invalidation des évaluations obsolètes laisse des résultats en mémoire
- Modules : `compliance.py`
- Preuve : `invalidate` supprime par identifiant ou condensat, mais ne détecte pas automatiquement toutes les évaluations liées à un manifeste modifié si l'appelant n'indique pas les paramètres.
- Conséquence : consultation de rapports obsolètes possible.
- Recommandation : lier chaque évaluation au manifeste dans un index et invalider automatiquement par identité.
- Phase : 5

#### MEM014-AUDIT-009 — Tolérance aux événements en double
- Module : `observability.py`
- Preuve : `record` accepte les événements avec le même `event_id` sans déduplication.
- Conséquence : duplication de références.
- Recommandation : dédupliquer par `event_id` et `source` ou marquer explicitement les doublons.
- Phase : 7

### INFO

#### MEM014-AUDIT-010 — Fonctionnalités non implémentées volontairement
- Persistance durable.
- Approbation cryptographique HROT.
- Intégration réelle d'Odin, Frame ou TradingAgents.
- Auto-restart contrôlé.
- Backend d'observabilité externe.
- Ces absences sont documentées comme limites, pas comme défauts actuels.

## 6. Inventaire de persistance

| Élément | Volatil | Persisté | Reconstructible | Risque |
|---|---|---|---|---|
| Manifeste YAML | Non | Oui | Oui | Faible |
| Contrat | Non | Oui si fichier | Oui | Faible |
| Découverte | Oui | Non | Oui | Moyen |
| Permissions accordées | Oui | Non | Non | Élevé |
| Autorisations évaluées | Oui | Non | Partiellement | Moyen |
| Événements d'observabilité | Oui | Non | Non | Moyen |
| Registre d'idempotence | Oui | Non | Partiellement | Moyen |
| Machine à états | Oui | Non | Partiellement | Moyen |
| Engineering Memory | Selon le backend existant | Oui | Non | Faible |

Stratégie recommandée :
- Persisters les décisions HROT et autorisations accordées.
- Conserver les événements opérationnels dans un journal borné et non dans l'Engineering Memory.
- Conserver uniquement les événements significatifs dans l'Engineering Memory.
- Reconstructe la découverte et la conformité à partir des manifestes et contrats.

## 7. Analyse HROT

Points solides :
- Refus par défaut.
- Séparation entre capacité déclarée et permission accordée.
- Contrat d'autorité humaine.
- Expiration et révocation.
- Invalidation sur changement de manifeste.

Risque principal :
- La possibilité de créer une permission avec un `approved_by` textuel sans `HumanAuthority` valide affaiblit la garantie HROT.

Recommandation :
- Rendre `HumanAuthority` obligatoire pour toute transition vers `GRANTED`.

## 8. Analyse des dépendances

Les modules MEM-014 utilisent uniquement la bibliothèque standard Python et les dépendances déjà présentes dans le projet (`PyYAML`, tests via pytest). Aucune nouvelle dépendance applicative n'a été introduite.

## 9. État de préparation des applications réelles

### Odin
- Type : application indépendante basée sur conteneur et contrôleur Python.
- Source observable : `core/plugins/odin.py` fournit métadonnées, santé, logs et lifecycle via Docker Compose.
- Requis : manifeste stable, identité, capacités `health`, `state`, `logs`, `config_updates`, permissions minimales, contrat, conformité, supervision, observabilité.
- Adaptateur nécessaire : oui.
- Préparation actuelle : partielle.

### Frame
- Type : application indépendante Web.
- Source observable : `core/plugins/frame.py` hérite de `ComposeService`.
- Requis : manifeste, identité, capacités `full_interface_proxy` ou `state`, contrat, permissions, observabilité.
- Adaptateur nécessaire : oui.
- Préparation actuelle : partielle.

### TradingAgents
- Type : application indépendante CLI Python/LangGraph.
- Requis : manifeste, identité, capacités `research-analysis`, `reports`, permissions en lecture, contrat, conformité, cycle de vie processus.
- Adaptateur nécessaire : oui.
- Préparation actuelle : conceptuelle.

## 10. Risques résiduels

- Persistance opérationnelle absente pour permissions et événements.
- Simulation possible d'approbation HROT par chaîne.
- Compatibilité permission/capacité permissive.
- Absence de tests d'intégration chaînés.
- Surface API importante.
- Capacités applicatives sans registre sémantique.

## 11. Recommandations priorisées

1. Rendre obligatoire `HumanAuthority` pour toute permission accordée.
2. Persister les décisions HROT, permissions accordées et évaluations critiques.
3. Ajouter des tests d'intégration chaînés déterministes.
4. Réduire la compatibilité permission/capacité à un mapping explicite.
5. Finaliser la voie asynchrone réelle de résilience.
6. Définir un registre initial de capacités.
7. Documenter l'API canonique et marquer les alias de compatibilité.
8. Préparer les adaptateurs Odin, Frame et TradingAgents.

## 12. Conclusion

Le socle MEM-014 est cohérent, testé et exploitable comme fondation. Les risques restants concernent principalement la persistance, la preuve HROT et l'intégration applicative réelle.
