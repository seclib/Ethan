# DECISION REGISTER — ETHAN

Date : 2026-11-03
Statut : `PENDING_APPROVAL`
Nature exclusive : préparation pour arbitrage humain.

Légende de statuts dans ce registre :
`USER_REQUIREMENT`, `PROPOSAL`, `USER_APPROVED`, `IMPLEMENTED_CLAIMED`, `PARTIALLY_IMPLEMENTED`, `NOT_IMPLEMENTED`, `BLOCKED`, `PENDING_USER_DECISION`.

## MEM-001 — Cadre mémoire officielle

- Sujet : quelle mémoire doit être officielle.
- Contexte : Phase 1 et 2.
- Question : `Obsidian` doit-elle devenir la source documentaire unique et les autres sources rester respktives ?
- Options : Source unique ; sources multiples ; docs Git primaires.
- Conséquences : dépendance de migration.
- Risques : perte ou duplication.
- Recommandation CTO : conserver les sources historiques et adopter `Obsidian` progressivement.
- Statut : `USER_APPROVED` (ADR-MEM-001, option C, 2026-11-03).
- Référentiel officiel : ADR-MEM-001.

## MEM-002 — Stockage d'origine de Knowledge

- Sujet : où vivent Knowledge et leurs sources.
- Décision associée : ADR-MEM-002.
- Options : Core opérationnel + mémoire ; Obsidian comme source ; service combiné.
- Recommandation antérieure : Core opérationnel reste la source, Obsidian garde la mémoire.
- Décision approuvée : ADR-MEM-002, option Knowledge/Skills sources directement depuis `Obsidian`, données dérivées reconstructibles hors `Obsidian`.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-003 — Skills dans la mémoire

- Sujet : niveau d'intégration Skills et cycle de vie.
- Options : références et snapshots seulement ; catalogue complet ; ne pas dupliquer ; source centrale.
- Recommandation : référencer plutôt que dupliquer, avec source centrale dans `Obsidian/Skills`.
- Décision approuvée : ADR-MEM-003 pour le stockage central et l'historicisation complète des Skills.
- Stockage source approuvé via ADR-MEM-002 pour `Knowledge` et `Skills`.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-004 — Architectures documents officiels

- Sujet : localisation des ADR, ESR, ASR.
- Options : Obsidian seul ; docs Git + Obsidian ; Obsidian comme proposition, Git officialisé après.
- Recommandation : `docs/` pour décision approuvée et Obsidian pour préparation.
- Décision associée : ADR-MEM-004.
- Décision approuvée : Option B — `docs/` héberge les versions officielles approuvées ; Obsidian conserve le contexte, l historique, les preuves et les travaux préparatoires.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-005 — Modèle et IDs

- Sujet : IDs, schémas, préfixes.
- Options : adoption telle quelle ; réduction ; schéma externe.
- Recommandation : adoption minimale mais progressive.
- Décision associée : ADR-MEM-005, option A.
- Décision approuvée : conserver les onze entités existantes comme socle et faire évoluer le modèle progressivement, sans reconstruction intégrale.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-006 — Persistance et fiabilité

- Sujet : atomique vs event log tampon.
- Options : Obsidian seul ; outbox + reprise ; DB supplémentaire.
- Recommandation : commencer Obsidian + outbox si besoin réel.
- Décision associée : ADR-MEM-006, option C.
- Décision approuvée : l architecture de persistance hybride avec Obsidian comme source canonique et couches opérationnelles dérivées.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-007 — Sécurité et HROT

- Sujet : sécurité et permission.
- Options : code-level security policy ; RBAC existant ; permissions custom.
- Recommandation : réutiliser `core/auth` et stricte moindre privilège.
- Décision associée : ADR-MEM-007, option B.
- Décision approuvée : politique de sécurité commune à l ensemble de l écosystème ETHAN, fondée sur Human Root of Trust.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-008 — Backups et restauration

- Sujet : stratégie locale vs externe.
- Options : sauvegarde locale + Git bundle ; sauvegarde locale seule ; aucune.
- Recommandation : bundle externe hors dépôt + periodic check.
- Décision associée : ADR-MEM-008, option C.
- Décision approuvée : stratégie 3-2-1, sauvegardes versionnées, protection, intégrité et restauration avec vérification.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-009 — Confidentialité et publication

- Sujet : stratégie export par allowlist.
- Options : dossier clonable sans historique ; projection only ; no public.
- Recommandation : allowlist + scan + human review.
- Décision associée : ADR-MEM-009, option C.
- Décision approuvée : gouvernance avancée de confidentialité et de publication, avec classification, provenance, contrôles et approbation humaine.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-010 — Intégration Odin

- Sujet : intégration observable.
- Options : adapter + audit hooks ; pas d'integration automatique ; full collection.
- Recommandation : adapter non invasive, consultative.
- Décision associée : ADR-MEM-010, Option B approuvée après substitution.
- Décision historique : l'option C a été initialement retenue, puis explicitement remplacée.
- Décision applicable : Option B — intégration native par contrôleur ETHAN dédié.
- Décision approuvée : l'option B constitue désormais la décision applicable au 2026-11-03.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-011 — Intégration Frame

- Sujet : adapter de santé et metadata.
- Recommandation : plugin boundary et lecture passive.
- Décision associée : ADR-MEM-011, Option B.
- Décision approuvée : intégration native par contrôleur ETHAN dédié à Frame, selon les principes d intégration d Odin avec adaptation à Frame.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-012 — TradingAgents

- Sujet : exiger des inspections réelles.
- Recommandation : ne pas prétendre à l'intégration.
- Décision associée : ADR-MEM-012, Option B.
- Décision approuvée : intégration de TradingAgents via contrôleur ETHAN dédié, WebUI dédiée et moteur original conservé.
- Statut : `USER_APPROVED` le 2026-11-03.

## MEM-013 — Architecture hybride pragmatique orientée performance

- **Statut avant révision :** `PROPOSAL` (Rust comme socle principal, Python complémentaire).
- **Décision historique antérieure :** Python-only comme première orientation; puis proposition Rust-majoritaire sous révision utilisateur.
- Décision associée : ADR-MEM-013.
- Décision humaine approuvée : option hybride pragmatique — conserver Python pour les composants existants, privilégier Rust lorsque des mesures et évaluations techniques démontrent un avantage significatif, sans réécriture systématique.
- Autorité : Human Root of Trust.
- Date d'approbation : 2026-11-03.
- **Statut :** `USER_APPROVED` le 2026-11-03.

### Références associées

- ADR-MEM-013 — Architecture hybride pragmatique orientée performance.
- `Obsidian/_meta/MEM_013_RUST_PYTHON_ARCHITECTURE_PROPOSAL.md`
- `Obsidian/_meta/MEM_013_REVISION_REPORT.md`

### Limites

Cette décision n'autorise aucune migration, suppression, modification de schéma, modification applicative ni réorganisation de données. La répartition réelle des langages devra être fondée sur des mesures techniques vérifiables.

## MEM-014 — Contrat interopérabilité, gouvernance et capacités des applications indépendantes

- Sujet : contrat générique pour Odin, Frame, TradingAgents et futures applications.
- Décision associée : ADR-MEM-014, `Obsidian/Architecture/ADR/ADR-MEM-014-application-integration-governance-and-capabilities.md`, statut `USER_APPROVED`.
- Statut actuel : `USER_APPROVED` le 2026-11-03.
- Nature : fondation contractuelle approuvée ; non implémentée.
- Options historiques :
  1. aucune norme commune ;
  2. norme minimale extensible ;
  3. contrat complet obligatoire.
- Recommandation CTO conservée : norme minimale obligatoire, avec extensions versionnées.
- Contrainte : les applications gardent leurs runtimes, données, dépendances et autorité locale.
- Planes : Ecosystem Control Plane, Shared Intelligence Plane, Independent Application Plane.

Décision formalisée (neuf points) :

1. Validation technique automatisée par ETHAN et approbation humaine HROT pour l'intégration officielle et les permissions sensibles.
2. Formats des contrats : YAML (manifestes), JSON (échanges), JSON Schema (validation), OpenAPI (API HTTP), Markdown (documentation).
3. États des capacités : `DECLARED`, `VERIFIED`, `AVAILABLE`, `AUTHORIZED`.
4. Permissions : identité, authentification, autorisation, HROT, moindre privilège, traçabilité.
5. Distinction entre extensions, plugins, applications indépendantes et Skills.
6. Processus de conformité : déclaration, validation automatique, rapport, approbation humaine, surveillance.
7. Résilience : timeout, retry contrôlé, circuit breaker, idempotence, détection de panne, événements différés, reprise contrôlée.
8. Observabilité : événements communs, journaux conservés par les applications, traçabilité dans Engineering Memory.
9. Ordre de réalisation : identité/versionnement ; découverte des capacités ; permissions/HROT ; contrats d'extensions ; conformité ; résilience ; observabilité et Engineering Memory.

Risques : couplage, promesse excessive d'Atreus, duplication de gouvernance.
