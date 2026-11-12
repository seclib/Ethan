# Audit de la documentation ETHAN — Phase A / Phase B

Date : 2026-11-04  
Auteur : Codex (agent)  
Statut : **PROPOSED — en attente d’approbation humaine avant toute migration**  
Branche Git : `refactor/ethan-rebuild-p0`  
Commit de base observé : `9e57d1c0`  

## 1. Objet et périmètre

Ce rapport audite `docs/` et `Obsidian/` afin de préparer une migration contrôlée :
- `docs/` devient la **documentation technique officielle et architecturale** d’ETHAN ;
- `Obsidian/` conserve la **mémoire opérationnelle**, l’**historique** et les **preuves**.

Aucune migration n’a été effectuée à ce stade. Ce document est une proposition soumise à approbation.

## 2. État Git avant audit

Observations vérifiées dans le dépôt :
- branche courante : `refactor/ethan-rebuild-p0` ;
- le dépôt contient de nombreux changements stagés et non stagés (voir `git status`) ;
- `docs/` contient un grand nombre de fichiers nouveaux et renommés stagés ;
- `Obsidian/` est entièrement non suivi par Git au moment de l’audit ;
- des suppressions de `Odsidian/` (ancien dossier) apparaissent comme non stagées ;
- un fichier `01-Archives/...` ancien semble avoir été renommé en `Obsidian/`.

Principe appliqué : préserver l’historique Git, ne jamais supprimer ni réécrire brutalement,
utiliser des mouvements traçables (`git mv` ou copie + lien) lors de la migration.

## 3. Volumes et inventaire brut

| Zone | Fichiers | Markdown |
|---|---:|---:|
| `docs/` | 418 | 401 |
| `Obsidian/` | 264 | 257 |
| Autres fichiers Markdown repérés hors docs/Obsidian | 109 | 109 |

Note : le compteur Markdown de `docs/` inclut un fichier nommé avec un accent grave final (`.md` + caractère), à traiter ponctuellement.

## 4. Conventions existantes

### 4.1 Documentation officielle — `docs/`

- Index public : `docs/index.md` (site MkDocs Material) et `docs/INDEX.md` (index technique manuel) ;
- ADR récents non numérotés : `docs/architecture/adr/README.md` ;
- Deux dépôts d’ADR coexistent : `docs/adr/` (21 fichiers) et `docs/architecture/adr/` (16 fichiers) ;
- ESR dans `docs/engineering/esr/` (16 fichiers, dont README) ;
- Aucun répertoire `docs/security/asr` ni fichier préfixé `ASR` dans `docs/` actuellement ;
- `docs/memory/` constitue la mémoire inter-sessions Codex (PROJECT_STATE, DECISIONS, sessions) ;
- `docs/audit/` et `docs/audits/` forment deux répertoires parallèles, à consolider ;
- Liens internes fréquemment absolus (`/docs/...`) ou vers le code source ; nombreux liens rapportés cassés par les vérifications automatiques ;
- `mkdocs.yml` ne référence qu’une partie des documents (public), pas les ADR/ESR internes nombreux.

### 4.2 Mémoire opérationnelle — `Obsidian/`

- `Obsidian/AGENTS.md` impose une initialisation obligatoire et un ordre de lecture ;
- `Obsidian/Operational-Memory/` contient PROJECT_STATE, DECISIONS, TASKS, BLOCKERS, MEMORY_GOVERNANCE ;
- `Obsidian/Knowledge/Architecture/` contient des ADR, ESR, ASR et modèles de mémoire (`ADR-EM-001`, `ESR-EM-001`, `ASR-EM-001`) ;
- `Obsidian/Knowledge/Syntheses/by-agent/` contient les résumés d’agents ;
- `Obsidian/Archives/` et `_meta/` contiennent l’historique brut et les rapports ;
- `Obsidian/Operational-Memory/MEMORY_GOVERNANCE.md` fixe les niveaux de confiance et les statuts ;
- Des copies miroir de `docs/memory/` existent dans `Operational-Memory/sources/docs-memory/` mais sont divergentes.

## 5. Classification proposée par zone

### 5.1 Répartition par fonction

| Fonction | Zone recommandée | Exemples de zones actuelles |
|---|---|---|
| Architecture et descriptions de composants | `docs/architecture/` | docs/architecture/, Obsidian/Knowledge/Architecture |
| ADR | `docs/adr/` + `docs/architecture/adr/` (à unifier) | docs/adr/, docs/architecture/adr/, Obsidian/Knowledge/Architecture/ADR-* |
| ESR | `docs/engineering/esr/` | docs/engineering/esr/, Obsidian/Knowledge/Architecture/ESR-* |
| ASR | `docs/security/` (convention ASR à introduire si validée) | Obsidian/Knowledge/Architecture/ASR-* uniquement |
| API, contrats, intégrations | `docs/api/`, `docs/specs/` | docs/api/, docs/specs/, Obsidian/Knowledge/Architecture/*CONTRACT* |
| Guides d’installation et d’exploitation | `docs/getting-started/`, `docs/operations/`, `docs/deployment/` | docs/getting-started/, docs/operations/, docs/deployment/ |
| Procédures techniques pérennes | `docs/operations/` | docs/operations/, Obsidian/Knowledge/Procedures |
| Comptes rendus et sessions | `Obsidian/Operational-Memory/` | docs/memory/sessions/, Obsidian/Archives/ |
| État courant et blocages | `Obsidian/Operational-Memory/` | docs/memory/PROJECT_STATE.md, Obsidian/Operational-Memory/ |
| Avancement et roadmap de travail | `Obsidian/Operational-Memory/` ou `Obsidian/_meta/` | docs/plans/, docs/plans/execution/ |
| Historique de travail et notes temporaires | `Obsidian/Archives/` | docs/audit/, docs/audits/, plans d’interface |
| Références vers la documentation officielle | `Obsidian/` (liens vers `docs/`) | INDEX.md, Knowledge/INDEX_ETHAN_KNOWLEDGE.md |

### 5.2 Actions proposées par type

| Action | Sens | Concernés |
|---|---|---|
| CONSERVER | reste dans `docs/` | architecture, api, deployment, development, esr, schemas, specs, security de conception, runbooks |
| DÉPLACER | de `docs/` vers `Obsidian/` (operational/historique) | audit, audits, plans, plans/execution, incidents, mémoire de session |
| MIGRER | de `Obsidian/Knowledge/` vers `docs/` | ADR-EM, ESR-EM, ASR-EM, modèles de mémoire et contrats techniques |
| SCINDER | extraire la partie durable, conserver l’historique | documents mixtes (architecture audits, security assessments, plans) |
| RÉFÉRENCER | pas de déplacement, lien canonique | Obsidian sources/docs-memory, INDEX, rapports d’agents |

## 6. Doublons, collisions et points d’attention

1. **Deux dépôts d’ADR** dans `docs/` : `docs/adr/` et `docs/architecture/adr/` partagent des numéros proches et une autorité concurrente.
2. **Collisions numériques** :
   - `ADR-1013` = frame-fork et knowledge-task-lifecycle ;
   - `ADR-1014` = frame-service-integration et retrieval-permission-scope ;
   - `ESR-014` = frame-fork et knowledge-observability.
3. **Deux répertoires d’audit** : `docs/audit/` et `docs/audits/`.
4. **Mémoire inter-sessions dupliquée et divergente** : `docs/memory/` vs `Obsidian/Operational-Memory/sources/docs-memory/` ; le fichier `PROJECT_STATE.md` diffère (298 vs 48 lignes).
5. **Documents mixtes nombreux** dans `docs/` : audits, auth flow, UI migrations, benchmarks, chartes sécurité ; ils mélangent preuve historique et exigence durable.
6. **Liens fragiles** : chemins absolus `/docs/...`, références vers source/archives CodeSpaces/CI non présents ; liens relatifs vers `api-reference/ethan/...` inexistants.
7. **Documentation au style open-jarvis** dans `docs/index.md` (produit externe) cohabite avec la documentation ETHAN HROT/MEM_014 : risque de confusion de public et de frontière produit.
8. **Obsidian n’est pas suivi par Git** : toute migration depuis Obsidian vers docs introduit ces fichiers dans Git, à approuver pour le suivi/versionnement.
9. **Noms instables** : plusieurs fichiers racine `ACCOUNTS_SUMMARY.md`, `architecture-decisions-summary.md`, `auth_flow_audit.md` au lieu d’une convention uniforme.

## 7. Risques de migration

| Risque | Impact | Atténuation |
|---|---|---|
| Perte de contexte historique | Élevé | Ne jamais supprimer ; déplacer avec `git mv` ou conserver copie et lien |
| Liens cassés dans Obsidian | Élevé | Mettre à jour `INDEX.md`, `_meta/LINK_MANIFEST.csv`, `LINK_MANIFEST.csv` et liens Markdown |
| Promouvoir une proposition au rang de décision | Élevé | Vérifier le statut dans `Operational-Memory/MEMORY_GOVERNANCE.md` et sources Git |
| Doublons contradictoires dans les ADR | Moyen | Créer une annexe de réconciliation avant fusion, sans réécrire l’historique |
| Surcharge du site MkDocs | Moyen | Décider quels documents intègrent la nav publique ; garder les ADR/ESR comme références internes |
| Toucher à la mémoire d’agent (`docs/memory`) | Moyen | Aligner `AGENTS.md` et les opérateurs avant déplacement ; éviter de casser le protocole de session |
| Fichiers non suivis et stash existant | Moyen | Faire un inventaire/commit intermédiaire sur demande avant migration |
| Caractères/espaces dans les noms | Faible | Normaliser seulement dans des copies, pas dans les originaux sans validation |

## 8. Plan d’exécution proposé (Phase C)

1. **Valider le plan** avec le propriétaire (humain) — obligatoire.
2. **Créer la documentation d’approbation dans Obsidian** (ce rapport) et mettre à jour `INDEX.md` pour le référencer.
3. **Préparer un état Git propre** : documenter l’état actuel, éventuellement créer un commit de sauvegarde si demandé.
4. **Unifier la nomenclature ADR** :
   - choisir un emplacement canonique (`docs/adr/` recommandé) ;
   - lister les collisions ;
   - créer une annexe de réconciliation sans modifier les ADR historiques.
5. **Migrer les rapports/audits/plans d’interface** de `docs/` vers `Obsidian/_meta/` ou `Operational-Memory/`, en conservant des liens de redirection ou des stubs.
6. **Migrer les documents techniques durables d’Obsidian** (`ADR-EM-*`, `ESR-EM-*`, `ASR-EM-*`, modèles de mémoire, contrats) vers `docs/adr/`, `docs/engineering/esr/`, `docs/security/` et `docs/architecture/` avec conservation des provenances.
7. **Mettre à jour les liens** internes et Obsidian (INDEX, manifests, AGENTS).
8. **Mettre à jour les index** (`docs/INDEX.md`, `Obsidian/INDEX.md`, éventuellement index ADR/ESR).
9. **Valider** : absence de fichier perdu, liens relatifs vérifiés, comparaison Git avant/après, rapport final.

## 9. Décisions requises avant migration

1. L’emplacement canonique des ADR : `docs/adr/` ou `docs/architecture/adr/` ?
2. L’introduction d’une convention ASR sous `docs/security/` ou `docs/engineering/asr/` ?
3. Le traitement de `docs/index.md` de style open-jarvis face à la documentation interne ETHAN : fusionner, séparer ou remplacer ?
4. Le maintien ou la migration de `docs/memory/` vers `Obsidian/Operational-Memory/sources/` ?
5. Le degré de déplacement des audits/plans de `docs/` : migration complète vs simple référencement depuis Obsidian ?
6. La normalisation des noms de fichiers (casse, accents, espaces) : oui/non et selon quelle règle ?
7. Le sort des copies mirror `Operational-Memory/sources/docs-memory` : synchroniser puis supprimer la copie, ou conserver comme archive ?

## 10. Résultat attendu

- `docs/` identifiable comme source officielle technique et architecturale ;
- `Obsidian/` identifiable comme mémoire opérationnelle et historique ;
- pas de copies divergentes sans lien canonique ;
- aucune perte de document ni de contexte ;
- liens vérifiés et index à jour ;
- rapport final Phase D.

---

## Annexe A — Inventaire `docs/` (classification et action proposée)

| Chemin (relatif à docs/) | Classe | Destination proposée | Action proposée |
|---|---|---|---|
| `ACCOUNTS_SUMMARY.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `ARCHITECTURE_KERNEL_CORE.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `AUDIT_INTEGRATION_2026-10-08.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `AUDIT_REPORT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `AUDIT_SKILLS_ECC_INTEGRATION.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `AUTH_ARCHITECTURE.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `AUTH_FINAL_VALIDATION.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `AUTH_FLOW_AUDIT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `Audit Architecture — WebUI vs Core Runtime.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `Audit Fonctionnel WebUI Dashboard (PLAN MODE).md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `DOUBLE_AUTH_AUDIT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `ETHAN_ENGINEERING_ROADMAP.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `ETHAN_MASTER_PLAN.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `ETHAN_STABILITY_REPORT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `GITHUB_ISSUES.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `INDEX.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `LLM_PROVIDERS_ARCHITECTURE.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `PRODUCTION_READINESS.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `Plan de Consolidation Architecture ETHAN.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `README_CHANGELOG.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `Rapport SRE & Architecture.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `Rapport_SRE_Stabilisation_Final.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `SECURITY_AUDIT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `SECURITY_AUDIT_REPORT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `STABILITY_REPORT.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `TECHNICAL_DEBT_ANALYSIS.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `VALIDATION_FINALE_ODIN.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `adr/ADR-001-agent-system.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1003-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1004-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1005-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1006-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1008-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1009-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1010-rag-strategies.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1011-rag-strategy.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1012-document-vector-persistence.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1013-frame-fork.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1013-knowledge-task-lifecycle.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1014-frame-service-integration.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1014-retrieval-permission-scope.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1015-embedding-model-compatibility.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-1016-production-vector-backend.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-2001-implementation.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-MEM-014-HROT-PRODUCTION-CRYPTO.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-MEM-014-PHASE-41-APPLICATION-ECOSYSTEM.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-MEM-014-PHASE-8-PERSISTENCE.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `adr/ADR-MEM-014-application-integration-governance-and-capabilities.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `api/CONTRACTS-API.md` | API / contrats / intégrations | docs/api/ (officiel) | CONSERVER |
| `api/ETHAN_REBUILD_P1_CONTRACTS.md` | API / contrats / intégrations | docs/api/ (officiel) | CONSERVER |
| `api/contract-v1.md` | API / contrats / intégrations | docs/api/ (officiel) | CONSERVER |
| `api/openapi.v1.json` | API / contrats / intégrations | docs/api/ (officiel) | CONSERVER |
| `api/openapi.yaml` | API / contrats / intégrations | docs/api/ (officiel) | CONSERVER |
| `architecture-audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `architecture-decisions-summary.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `architecture-decisions.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `architecture.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `architecture/ARCHITECTURE-CIBLE.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-Event-Flow.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-Level1-System-Context.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-Level2-Containers.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-Level3-Components-Kernel.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-Level4-Code-View.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/C4-README.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/ETHAN_KNOWLEDGE_SKILLS_TOOLS_MCP.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/ETHAN_REBUILD_P1_REQUIREMENTS_MATRIX.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/ETHAN_REBUILD_P1_TARGET_ARCHITECTURE.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/ETHAN_RESPONSE_RENDERER.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/ETHAN_WEBUI_TARGET_ARCHITECTURE.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/OPENWEBUI_ETHAN_MAPPING.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/README_ARCHITECTURE_REFERENCE.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/RUST-MIGRATION-AUDIT.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/adr/ADR-3001-unified-record-store.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3002-providers-source-of-truth.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3003-projects-domain.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3004-vector-store-record.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3005-folders-vs-domains.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3006-api-contracts.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-3007-deprecation-settings-legacy.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4001-capability-manager.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4002-install-on-demand.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4003-data-lifecycle.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4004-core-source-of-truth.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4005-extension-trust-model.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4006-rebuild-target-architecture.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4007-open-webui-fork-license-gate.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/ADR-4008-rust-event-store-shadow-mode.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/adr/README.md` | ADR (décision d’architecture) | docs/ (officiel) — conserver, puis fusionner les deux dépôts d’ADR | CONSERVER + FUSION À PRÉVOIR |
| `architecture/agents.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/api-core-boundary-refactoring.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/channels.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/communication-graph.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/consolidation-plan.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/critical-analysis.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/current.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/decisions.md` | Architecture (décisions + état courant) | docs/architecture/ (référence) + Obsidian (contexte) | EXAMINER INDIVIDUELLEMENT |
| `architecture/design-principles.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/duplicate-detection.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/engine.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/file-folder-consolidation.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/intelligence.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/knowledge/document-pipeline.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/learning.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/llm-unification-plan.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/local-knowledge-api-contract.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/local-knowledge-domain.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/local-knowledge-storage-audit.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/memory.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/migration-report.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/osiris-port-management.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/overview.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/proposed.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/query-flow.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/reviews/unified-ai-providers-review.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/reviews/webui-platform-review.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/security.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/skills.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/terminal-webui.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `architecture/webui-core-audit.md` | Architecture (mixte: proposition + historique) | docs/architecture/ (technique) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT / SCINDER |
| `architecture/webui-platform-architecture-assessment.md` | Architecture et descriptions de composants | docs/architecture/ (officiel) | CONSERVER |
| `assets/OpenJarvis_Architecture.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/README.md` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/coding-assistant.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/cost-savings.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/discord-companion.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/morning-brief.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `assets/showcase/persistent-memory.png` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `audit-boot-mechanism.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `audit-ethan-up-RESUME.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `audit-ethan-up.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `audit-plugins.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `audit/CLINE_CHECKPOINT_INVENTORY.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/CLINE_RECOVERY_ANALYSIS.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_API_HEALTHCHECK_DIAGNOSTIC.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_COMPONENT_INTERFACE_INVENTORY_P0.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_PERSISTENT_DATA_REGISTRY_P0.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_PUBLIC_PRIVATE_INVENTORY.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_PUBLIC_PRIVATE_SEPARATION.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P0_AUDIT.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P1_RISK_REGISTER.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P2_FEASIBILITY.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P3` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P3_VERTICAL_PROTOTYPE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_REBUILD_P5_VALIDATION_GATE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_WEBUI_CTO_REVIEW.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_WEBUI_GAP_ANALYSIS.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/ETHAN_WEBUI_INITIAL_ARCHITECTURE_AUDIT.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/GIT_BACKUP_AND_CONSOLIDATION_PLAN.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/GIT_SECURITY_AND_HISTORY_AUDIT.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/OPENWEBUI_COMPONENT_REFERENCE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/OPENWEBUI_FORK_FEASIBILITY.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/OPENWEBUI_UX_REFERENCE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/WEBUI_CURRENT_STATE.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/WEBUI_DOCUMENTARY_INVENTORY.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/WEBUI_IMPLEMENTATION_STATUS.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit/WEBUI_PRIORITIES.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audit_rapport.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `audits/CLI_PRODUCTION_AUDIT.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/api-startup-fix.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/duplicate-data-integrity.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/file-management-regression.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/rag-settings-regression.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/reference-comparison-odysseus-canirun.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `audits/transparency-readability-audit.md` | Audit (historique de travail et rapports d’agent) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER |
| `auth_architecture_audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `auth_audit_report_3.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `auth_flow_audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `boot-dev-extensions.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `boot-from-scratch.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `boot_sequence_audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `cto-review-completed.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `deployment.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `deployment/api-server.md` | Déploiement / exploitation | docs/deployment/ (officiel) | CONSERVER |
| `deployment/docker.md` | Déploiement / exploitation | docs/deployment/ (officiel) | CONSERVER |
| `deployment/index.md` | Déploiement / exploitation | docs/deployment/ (officiel) | CONSERVER |
| `deployment/launchd.md` | Déploiement / exploitation | docs/deployment/ (officiel) | CONSERVER |
| `deployment/systemd.md` | Déploiement / exploitation | docs/deployment/ (officiel) | CONSERVER |
| `design/2026-05-05-apple-silicon-pearl-mining-design.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-05-05-pearl-coordination-discussion-draft.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-05-05-vllm-pearl-mining-integration-design.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-05-05-vllm-pearl-mining-integration-plan.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-09-30-cartographie-interfaciale.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-09-30-ux-refonte-cartographie.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-09-30-webui-settings-honesty.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/2026-10-01-cartographie-webui-ux.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/ETHAN_CAPABILITIES_UX.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/ETHAN_WEBUI_UX_ANALYSIS.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `design/ETHAN_WEBUI_UX_PARITY_SPEC.md` | Design technique / plan d’implémentation | docs/design/ (officiel) ou Obsidian (operational) selon statut | EXAMINER INDIVIDUELLEMENT |
| `desktop-auto-update.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `development/ETHAN_WEBUI_FORK_STRATEGY.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/contributing.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/mining-nvidia-validation.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/mining.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/pearl-model-enablement.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/release-checklist.md` | Développement / contribution | docs/development/ (officiel) | CONSERVER |
| `development/roadmap.md` | Plan de développement / roadmap | Obsidian (mémoire opérationnelle) ou docs selon gouvernance | EXAMINER INDIVIDUELLEMENT |
| `doctor.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `downloads.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/BASELINE_VALIDATION.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/ETHAN_ROADMAP.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/ETHAN_SECURITY_ASSESSMENT.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/ETHAN_TECHNICAL_BASELINE.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/ETHAN_TECHNICAL_DEBT.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/baseline/ETHAN_TEST_BASELINE.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/benchmarks/knowledge-bottleneck-analysis.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/benchmarks/knowledge-performance-baseline.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/benchmarks/knowledge-postgres-environment.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/benchmarks/knowledge-postgres-validation.md` | Mesures, baselines, preuves techniques | docs/engineering/ (evidence officielle) ou Obsidian/_meta (preuves) | EXAMINER INDIVIDUELLEMENT |
| `engineering/esr/ESR-001-capability-model.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-002-installation-engine.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-003-docker-provisioning.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-004-local-provisioning.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-005-webui-capability-manager.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-006-security-model.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-007-knowledge-collections.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-008-knowledge-sources.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-010-knowledge-index.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-011-knowledge-search.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-012-knowledge-rag-permissions.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-013-knowledge-tasks.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-014-frame-fork.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-014-knowledge-observability.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/ESR-015-frame-service.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `engineering/esr/README.md` | ESR (exigence système) | docs/engineering/esr/ (officiel) | CONSERVER |
| `ethan-launcher.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `ethan-up.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `frontend_auth_audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `gen_install_script.py` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `gen_ref_pages.py` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `getting-started/configuration.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/install.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/installation.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/linux.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/macos.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/quickstart.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/snippets.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/windows-native.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `getting-started/wsl2.md` | Guide d’installation / démarrage | docs/getting-started/ (officiel, guide utilisateur) | CONSERVER |
| `gods-eye-view-integration.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `hardening.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `implementation-guide-P0.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `implementation-guide-P1.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `implementation-guide-P2.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `implementation-guide-P3.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `incidents/RUNTIME-001.md` | Incident / post-mortem | Obsidian/Knowledge/Incidents (mémoire opérationnelle) | DÉPLACER |
| `includes/abbreviations.md` | Inclusions MkDocs (snippets) | docs/includes/ (site officiel) | CONSERVER |
| `index.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `installation.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `javascripts/docsearch-init.js` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `javascripts/leaderboard.js` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `leaderboard.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `learning/ace.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `memory/DECISIONS.md` | État courant / décisions (mémoire opérationnelle) | Obsidian/Operational-Memory/ (mémoire opérationnelle) | ALIGNER LES SOURCES (DÉCISION REQUISE) |
| `memory/PROJECT_STATE.md` | État courant / décisions (mémoire opérationnelle) | Obsidian/Operational-Memory/ (mémoire opérationnelle) | ALIGNER LES SOURCES (DÉCISION REQUISE) |
| `memory/README.md` | Mémoire inter-sessions Codex | Obsidian/Operational-Memory/sources/docs-memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `memory/sessions/2026-11-01.md` | Mémoire inter-sessions Codex | Obsidian/Operational-Memory/sources/docs-memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `memory/sessions/2026-11-02.md` | Mémoire inter-sessions Codex | Obsidian/Operational-Memory/sources/docs-memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `memory/sessions/2026-11-03.md` | Mémoire inter-sessions Codex | Obsidian/Operational-Memory/sources/docs-memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `memory/sessions/2026-11-04.md` | Mémoire inter-sessions Codex | Obsidian/Operational-Memory/sources/docs-memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `odin-direct-docker-compose.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `operations/ETHAN_REBUILD_P1_RUNBOOK.md` | Procédure d’exploitation / runbook | docs/operations/ (officiel) | CONSERVER |
| `operations/backup-volumes-procedure.md` | Procédure d’exploitation / runbook | docs/operations/ (officiel) | CONSERVER |
| `operations/webui-refresh.md` | Procédure d’exploitation / runbook | docs/operations/ (officiel) | CONSERVER |
| `overrides/main.html` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `p1_audit_report.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `plans/ETHAN_WEBUI_ARCHITECTURE_MATRIX.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_MASTER_PLAN.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_MIGRATION_STRATEGY.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_OPENWEBUI_MIGRATION.md`` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ETHAN_WEBUI_V2_ARCHITECTURE.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/OPENWEBUI_ETHAN_MIGRATION_ANALYSIS.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/chat-agent-model-selector.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/chat-composer-simplification.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/chat-layout-visual-polish.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/chat-ui-deduplication.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/00-ETAT-DES-LIEUX.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/01-PHASE-A-CONSOLIDATION.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/02-PHASE-B-MCP.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/03-PHASE-C-SETTINGS.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/04-PLAN-INTERPRETER-REPORT.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/execution/SESSION-REPORT-2026-08-18.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/odysseus-cleanup-audit.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/openwebui-ethan-ui-migration.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/openwebui-migration-final-audit.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/openwebui-shell-migration.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/sidebar-openwebui-behavior.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-agent-selector.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-chat-composer.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-chat-context.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-cleanup.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-config-pages-refactor.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-navigation.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-agent-model-selectors.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-config-pages.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-final-audit.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-refactor-audit.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-shell-implementation.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/ui-openwebui-target-architecture.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/webui-navigation-first-experience.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/webui-port-3001-validation.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/webui-port-3001.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plans/webui-ux-polish-audit.md` | Plan / migration / audit opérationnel | Obsidian (mémoire opérationnelle et historique) | DÉPLACER |
| `plugins/gods-eye-view-ai.md` | Plugin / intégration | docs/plugins/ (officiel) ou Obsidian | EXAMINER INDIVIDUELLEMENT |
| `plugins/odin-compose-controller.md` | Plugin / intégration | docs/plugins/ (officiel) ou Obsidian | EXAMINER INDIVIDUELLEMENT |
| `pythonpath-fix.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `rfc/RFC-0001-email-inbox.md` | RFC (proposition) | docs/rfc/ (officiel en tant que proposition technique) | CONSERVER (avec statut explicite) |
| `rfc/RFC-0002-deep-research.md` | RFC (proposition) | docs/rfc/ (officiel en tant que proposition technique) | CONSERVER (avec statut explicite) |
| `rfc/RFC-0003-cookbook.md` | RFC (proposition) | docs/rfc/ (officiel en tant que proposition technique) | CONSERVER (avec statut explicite) |
| `roadmap-P0.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `roadmap-P1.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `roadmap-P2.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `roadmap-P3.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `roadmap-global.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `runbook.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `schemas/application-manifest.schema.json` | Schéma / contrat | docs/schemas/ (officiel) | CONSERVER |
| `security/01-security-audit.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/02-constitution-design.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/03-policy-hierarchy.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/04-policy-engine.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/05-capability-system.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/06-data-protection.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/07-ecosystem-integration.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/08-control-plane-hardening.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/09-extension-hardening.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/10-secret-hygiene.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/11-runtime-isolation.md` | Sécurité (conception / architecture) | docs/security/ (officiel, ASR) | CONSERVER |
| `security/CI_CD_SECURITY_ASSESSMENT.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/CTO_SECURITY_ARCHITECTURE_REVIEW.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/DEPENDENCY_SECURITY_INVENTORY.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/DOCKER_IMAGE_SECURITY_ASSESSMENT.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/ETHAN_CONSTITUTION.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/GITHUB_SECURITY_ASSESSMENT.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/RED_TEAM_SECURITY_REVIEW.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/SECRET_EXPOSURE_ASSESSMENT.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_ASSET_INVENTORY.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_AUDIT_RECONCILIATION.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_BACKLOG.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_EVIDENCE_REGISTER.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_PROGRAM_CHARTER.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_RISK_REGISTER.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_ROADMAP.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/SECURITY_TEST_PLAN.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/SECURITY_VERIFICATION_MATRIX.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/TRUST_BOUNDARIES_REGISTER.md` | Sécurité (audit/registre opérationnel) | docs/security/ (référence) + Obsidian (historique) | EXAMINER INDIVIDUELLEMENT |
| `security/WEBUI_AUTH_ARCHITECTURE.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/WEBUI_AUTH_CURRENT_STATE.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/WEBUI_AUTH_SETUP.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/WEBUI_AUTH_THREAT_MODEL.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `security/public-release-allowlist-denylist.md` | Sécurité (référence / procédure) | docs/security/ (officiel) | CONSERVER |
| `service-orchestration.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `showcase/CONTRIBUTING.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/coding-assistant.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/cost-savings.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/discord-companion.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/index.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/morning-brief.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `showcase/persistent-memory.md` | Vitrine / exemples | docs/showcase/ (officiel) | CONSERVER |
| `specs/CLI_CONTRACT.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-capability-discovery.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-catalog-phase41.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-compliance.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-contract-validator.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-identity.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-integration-contract.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-integration-readiness.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-manifest.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-observability-engineering-memory.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-permissions-hrot.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-persistence-mem014.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/application-resilience-lifecycle.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `specs/capability-registry.md` | Spécification technique | docs/specs/ (officiel) | CONSERVER |
| `sre-runbook.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `sre_stability_audit.md` | Document racine (rapport/plan historique) | Obsidian/_meta/ ou Operational-Memory (mémoire opérationnelle) | DÉPLACER OU RÉFÉRENCER |
| `stylesheets/extra.css` | Ressource site (asset) | docs/ (ressource) | CONSERVER |
| `telemetry.md` | Documentation racine (guide officiel possible) | docs/ (officiel) | EXAMINER INDIVIDUELLEMENT |
| `testing/agent-qa-runbook.md` | Tests / validation | docs/testing/ (officiel) | CONSERVER |
| `tutorials/code-companion.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `tutorials/deep-research.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `tutorials/index.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `tutorials/messaging-hub.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `tutorials/scheduled-ops.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `tutorials/skills-workflow.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/agent-traces.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/agents.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/benchmarks.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/channels-and-connectors.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/channels.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/chat-simple.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/cli.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/code-assistant.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/deep-research.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/evaluations.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/llm-guided-spec-search.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/mcp-external-servers.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/memory.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/mining-apple-silicon.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/mining.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/morning-digest.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/pearl.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/projects.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/python-sdk.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/rag-strategies.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/scheduled-monitor.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/scheduler.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/security.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/skills.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/system-exec.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/telemetry.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `user-guide/tools.md` | Guide utilisateur | docs/ (officiel) | CONSERVER |
| `webui/open-webui-migration-report.md` | Documentation WebUI / interface | docs/webui/ (officiel, présentation d’interface) | CONSERVER |
| `webui/open-webui-reference.md` | Documentation WebUI / interface | docs/webui/ (officiel, présentation d’interface) | CONSERVER |

## Annexe B — Inventaire `Obsidian/` (classification et action proposée)

| Chemin (relatif à Obsidian/) | Classe | Destination proposée | Action proposée |
|---|---|---|---|
| `AGENTS.md` | Index / gouvernance locale | Obsidian (mémoire opérationnelle) | CONSERVER |
| `Archives/Conversations/cline/2026-06-12/1781261826788.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-12/1781262561008.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-12/1781265677020.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-13/1781324525374.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-13/1781326479958.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-14/1781438417220.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-14/1781440243749.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-14/1781445007397.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-15/1781506386208.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-16/1781448124733.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-16/1781584795579.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-17/1781619688061.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-17/1781684089320.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781696790844.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781759466869.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781763556859.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781763556860.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781773490515.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-18/1781773629795.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-19/1781790224363.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-19/1781845301775.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-19/1781847538003.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-19/1781852108784.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-19/1781855138200.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-20/1781926691577.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-20/1781927049974.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-21/1781928390660.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-21/1782049607778.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-22/1782110267799.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-23/1782122303274.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-24/1782236030293.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-24/1782277746766.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-24/1782282405489.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-24/1782291853665.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-24/1782299082878.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-06-26/1782299840579.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-08/1782460736319.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-08/1783480315445.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-09/1783498502281.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-12/1783841799690.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-18/1783595051689.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-19/1784446073123.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-19/1784465617197.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-20/1784468478017.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-21/1784553716546.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-22/1784629956873.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-22/1784702896150.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-22/1784714379731.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-23/1784720147277.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-23/1784780539134.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-30/1784803567417.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-31/1785382419039.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-31/1785475619469.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-31/1785478061904.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-07-31/1785497242482.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-02/1785510775651.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-02/1785663110020.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-03/1785676074904.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-03/1785748404435.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-04/1785763683280.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-11/1786194792842.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-11/1786441307139.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-12/1785821621715.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-12/1786516782485.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786520589377.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786588790163-part-01.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786588790163-part-02.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786588790163-part-03.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786588790163-part-04.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-13/1786588790163-part-05.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-14/1786592167914.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-14/1786689632319.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-14/1786691977752.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-14/1786694120897.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-15/1786715813776.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-15/1786767655858.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-15/1786771650555.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-17/1786773027890.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-17/1786962026659.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1786966184691.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1787028404021.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1787031131780.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1787040529358.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1787043334788.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-18/1787050182381.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-19/1787051436064.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/cline/2026-08-23/1787143354523.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-01.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-02.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-03.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-04.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/codex/2026-10-23/01a16882-fc47-73c2-85e1-a6093f0dbfd9.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/copilot/2026-04-24/b19268d9-cfc6-4cf3-b3cf-142ff2d72088.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/copilot/2026-05-25/36e60f5c-6fff-4b49-91db-77a2eb8078d6.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Conversations/from-ethan-knowledge/cline/2026-08-13/1786588790163.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Events/EVT-20261103T132131362051-OBSERVED-ethan-api-gateway-started.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `Archives/Events/EVT-20261103T150233966728-OBSERVED-ethan-api-gateway-started.md` | Archive historique | Obsidian/Archives (immutables) | CONSERVER (ne jamais réécrire) |
| `INDEX.md` | Index / gouvernance locale | Obsidian (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Architecture/ADR-EM-001-engineering-memory-architecture.md` | ADR (décision d’architecture, mémoire) | docs/adr/ ou docs/architecture/adr (officiel) — copier/migrer | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/ASR-EM-001-engineering-memory-security.md` | ASR (exigence de sécurité, mémoire) | docs/security/ (officiel, nouvelle convention ASR à définir) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/EM-SERVICE-ARCHITECTURE.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/ESR-EM-001-engineering-memory.md` | ESR (exigence système, mémoire) | docs/engineering/esr (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/ETHAN_APPLICATION_INTEGRATION_CONTRACT.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/MEMORY_DATA_MODEL.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/Architecture/RECORD_TEMPLATES.md` | Architecture / contrat de mémoire (technique) | docs/architecture/ ou docs/specs (officiel) | CANDIDAT À LA MIGRATION |
| `Knowledge/INDEX_ETHAN_KNOWLEDGE.md` | Connaissance technique (Obsidian) | Obsidian/Knowledge (mémoire) ou docs selon nature | EXAMINER INDIVIDUELLEMENT |
| `Knowledge/Syntheses/by-agent/cline-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Syntheses/by-agent/cline-summary.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Syntheses/by-agent/codex-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Syntheses/by-agent/codex-summary.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Syntheses/by-agent/copilot-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Syntheses/by-agent/copilot-summary.md` | Synthèse agent (résumé) | Obsidian/Knowledge/Syntheses (mémoire opérationnelle) | CONSERVER |
| `Knowledge/Sécurité/PERMISSION_MODEL.md` | Modèle de permission / sécurité | docs/security/ (officiel) | CANDIDAT À LA MIGRATION |
| `Metadata/REGISTRY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/BLOCKERS.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/DECISIONS.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/DOCUMENTATION_AUDIT_REPORT_2026-11-04.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/MEMORY_GOVERNANCE.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/PROJECT_STATE.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/TASKS.md` | Mémoire opérationnelle | Obsidian/Operational-Memory (mémoire opérationnelle) | CONSERVER |
| `Operational-Memory/sources/docs-memory/DECISIONS.md` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `Operational-Memory/sources/docs-memory/PROJECT_STATE.md` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `Operational-Memory/sources/docs-memory/README.md` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `Operational-Memory/sources/docs-memory/sessions/2026-11-01.md` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `Operational-Memory/sources/docs-memory/sessions/2026-11-02.md` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `Operational-Memory/sources/ethan-knowledge-meta/sync-state.json` | Copie source de docs/memory ou snapshot externe | Obsidian/Operational-Memory/sources (mémoire opérationnelle) | CONSERVER (ne pas synchroniser aveuglément) |
| `README.md` | Index / gouvernance locale | Obsidian (mémoire opérationnelle) | CONSERVER |
| `_meta/ADR_MEM_010_RECONCILIATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ADR_MEM_011_RECONCILIATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ADR_MEM_012_RECONCILIATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/AGENT_MEMORY_PROTOCOL_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ARCHITECTURE_OPTIONS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/AUDIT-ARCHIVES_ODSIDIAN.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/CLEANUP_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/CONSOLIDATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/CTO_RECONSTRUCTION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/DECISION_REGISTER.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/DELIVERY_GATE_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ECOSYSTEM_ARCHITECTURE_VALIDATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ECOSYSTEM_CAPABILITY_MATRIX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ECOSYSTEM_DECISION_GAPS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ECOSYSTEM_DECISION_WORKBOOK.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_APPLICATION_INTEGRATION_COMPARISON.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_25_PLUGINS_UI_RELIABILITY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_26_RICH_RESPONSE_UI.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_27_RICH_RESPONSE_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_28_PLUGINS_UI_REPAIR.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_29_PLUGINS_TOOLS_SEPARATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_30_AUTHENTICATED_RUNTIME_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_30_PLUGINS_SYSTEM_RECOVERY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_31_RICH_RESPONSE_BROWSER_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_32_FRAMES_OPERATIONAL_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_33_FRAMES_RUNTIME_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_36A_QUANTAR_RENAMING.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_36_QUANTAR_FUNCTIONAL_IMPLEMENTATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_37A_QUANTAR_SECURITY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_37B_QUANTAR_RUNTIME_SECURITY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_37_QUANTAR_SECURITY_RUNTIME.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_38_QUANTAR_RUNTIME_BOUNDARY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_39_QUANTAR_DEDICATED_RUNTIME.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_40B_QUANTAR_E2E_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_40C_QUANTAR_APPLICATION_ACTIVATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_40E_QUANTAR_LIFECYCLE_IMPLEMENTATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_42_QUANTAR_ACTION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_PHASE_42_QUANTAR_ACTIVATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_QUANTAR_COMPOSESERVICE_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_QUANTAR_ODIN_CONTROLLER_COMPARISON.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_QUANTAR_PHASE_42E_RUNTIME_REPAIR.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_QUANTAR_PHASE_43_CONTROLLER.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/ETHAN_UNIFIED_CONTROLLER_STUDY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/FILE_MANIFEST.csv` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/INDEX_ODSIDIAN_SOURCE.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/LINK_MANIFEST.csv` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MASTER_IMPLEMENTATION_ROADMAP.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEMORY_EVENT_LOG.ndjson` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_013_REVISION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_013_RUST_PYTHON_ARCHITECTURE_PROPOSAL.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_ARCHITECTURE_COHERENCE_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_CAPABILITY_REGISTRY_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_COMPLIANCE_AUDIT_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_FORMALIZATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_FORMATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_GLOBAL_ARCHITECTURE_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_HROT_HARDENING_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_HROT_OPERATIONAL_READINESS_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_HROT_PRODUCTION_CRYPTO_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_IMPLEMENTATION_READINESS_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_IMPLEMENTATION_ROADMAP.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_INTEGRATION_READINESS_ROADMAP.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PERSISTENCE_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_12_SECURITY_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_13_APPLICATION_INTEGRATION_READINESS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_14_END_TO_END_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_15_ODIN_PILOT_READINESS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_16_ODIN_PILOT_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_17_ODIN_WEBUI_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_18_ODIN_OPERATIONAL_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_19_3_AUTHENTICATED_RUNTIME_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_19_ODIN_RUNTIME_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_1_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_20_FRAMES_PILOT_READINESS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_21_FRAMES_RUNTIME_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_22_RUNTIME_AUTH_READINESS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_23_NATS_RUNTIME_ALIGNMENT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_24_AUTH_WEBUI_ODIN_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_2_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_34_QUANTAR_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_35_QUANTAR_PILOT_INTEGRATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_3_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_41_APPLICATION_ECOSYSTEM.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_4_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_5_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_6_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MEM_014_PHASE_7_IMPLEMENTATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/MIGRATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/PHASE_19_1_NATS_BACKEND_RECOVERY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/PHASE_1_3_ARBITRATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/PHASE_2_VALIDATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/POST_MIGRATION_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/PRODUCTION_READINESS_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_AUTHENTICATED_BROWSER_VALIDATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_CLEAN_REBUILD_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_COMPOSE_CLEANUP.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_REAL_ACTIVATION_FIX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_REAL_TASK_RUNTIME.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/QUANTAR_REBUILD_INVENTORY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/README_ODSIDIAN_SOURCE.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/RECONCILIATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/REGISTRY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/SOURCE_INVENTORY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_API_CONTRACTS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_ARCHITECTURE.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_CAPABILITY_MATRIX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_CONTROLLER_DESIGN.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_DEPENDENCY_INVENTORY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_IMPLEMENTATION_ROADMAP.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_INTEGRATION_GAPS.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_PHASE_0_1_VALIDATION_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_PHASE_1_1_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_PHASE_1_REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_PROVIDER_COMPATIBILITY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_SECURITY_DESIGN.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_TECHNICAL_AUDIT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_UI_SPECIFICATION.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/TRADINGAGENTS_UPSTREAM_RUNTIME_STUDY.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/VERIFICATION_MATRIX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/odsidian-metadata/COVERAGE-REPORT.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/odsidian-metadata/PARTS-INDEX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/odsidian-metadata/conventions.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/odsidian-metadata/sync-state.json` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/1786588790163.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/INDEX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/by-agent/cline-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/by-agent/codex-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/by-agent/copilot-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/ethan-knowledge/sync-state.json` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/odsidian/INDEX.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/odsidian/by-agent/cline-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/odsidian/by-agent/codex-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/odsidian/by-agent/copilot-summary.md` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |
| `_meta/source-snapshots/odsidian/sync-state.json` | Métadonnées / gouvernance / registres | Obsidian/_meta et Metadata (mémoire opérationnelle) | CONSERVER |

## Annexe C — Fichiers Markdown repérés hors `docs/` et `Obsidian/`

- `.clinerules/AGENTS.md`
- `.clinerules/CODE_OF_CONDUCT.md`
- `.clinerules/Principe.md`
- `.clinerules/cognitive.md`
- `.clinerules/direction.md`
- `.clinerules/directive.md`
- `.clinerules/secret.md`
- `.clinerules/senior_cto.md`
- `AGENTS.md`
- `README.md`
- `SECURITY.md`
- `core/README.md`
- `core/deployment/scripts/pearl/README.md`
- `core/tools/pearl-reference-oracle/README.md`
- `deploy/postgres/migrations/README.md`
- `design/README.md`
- `design/phase-01-audit/comparison.md`
- `design/phase-01-audit/jarvis-os-analysis.md`
- `design/phase-01-audit/webui-audit.md`
- `design/phase-02-product/future-pages.md`
- `design/phase-02-product/product-vision.md`
- `design/phase-03-design-system/accessibility.md`
- `design/phase-03-design-system/components.md`
- `design/phase-03-design-system/design-system.md`
- `design/phase-03-design-system/design-tokens.md`
- `design/phase-03-design-system/patterns.md`
- `design/phase-03-design-system/themes.md`
- `design/phase-04-wireframes/wireframes.md`
- `design/phase-05-architecture/frontend-architecture.md`
- `design/phase-05-user-flows/user-flows.md`
- `design/phase-06-architecture/architecture.md`
- `design/phase-06-roadmap/migration-plan.md`
- `design/phase-07-prototype/prototype.md`
- `design/phase-08-implementation/analysis.md`
- `design/phase-08-implementation/roadmap.md`
- `design/phase-08-roadmap/roadmap.md`
- `design/reports/P0_implementation_report.md`
- `engineering/MIGRATION_GUIDE.md`
- `engineering/STABILITY_PLAN.md`
- `engineering/adr/ADR-001-initial-architecture.md`
- `engineering/adr/ADR-1001-core-is-not-an-executor.md`
- `engineering/adr/ADR-1002-planner-executor-separation.md`
- `engineering/adr/ADR-1003-single-entry-intent-model.md`
- `engineering/adr/ADR-1006-capability-composition-pattern.md`
- `engineering/adr/ADR-1007-event-driven-architecture.md`
- `engineering/adr/ADR-1008-plugin-discovery-loading.md`
- `engineering/adr/ADR-1009-safety-permission-model.md`
- `engineering/architecture/BACKEND_SIMPLIFICATION.md`
- `engineering/architecture/LEGACY_MIGRATION.md`
- `engineering/architecture/MIGRATION_LEGACY_TO_CORE.md`
- `engineering/architecture/MIGRATION_STATUS.md`
- `engineering/architecture/PACKAGING.md`
- `engineering/architecture/constitution.md`
- `engineering/reports/ai-infrastructure-report.md`
- `engineering/reports/architecture-audit.md`
- `engineering/reports/architecture-map.md`
- `engineering/reports/architecture-overview.md`
- `engineering/reports/cto-production-audit.md`
- `engineering/reports/dependency-analysis.md`
- `engineering/reports/dependency-map.md`
- `engineering/reports/deployment-analysis.md`
- `engineering/reports/docker-foundation-report.md`
- `engineering/reports/infrastructure-overview.md`
- `engineering/reports/memory-api.md`
- `engineering/reports/memory-architecture.md`
- `engineering/reports/memory-lifecycle.md`
- `engineering/reports/memory-providers.md`
- `engineering/reports/rebranding-report.md`
- `engineering/reports/repository-audit.md`
- `engineering/reports/risks-and-technical-debt.md`
- `engineering/reports/runtime-flow.md`
- `engineering/reports/technical-risks.md`
- `engineering/rfc/RFC-000-bootstrap.md`
- `engineering/rfc/rfc-0001-ethan-core-architecture.md`
- `engineering/rfc/rfc-007-architecture-constitution.md`
- `engineering/rfc/rfc-008-cognitive-kernel-phase-0.2.md`
- `engineering/standards/architecture-lint.md`
- `engineering/standards/engineering-principles.md`
- `engineering/templates/ADR_TEMPLATE.md`
- `engineering/templates/RFC_TEMPLATE.md`
- `infrastructure/config/configs/openjarvis/prompts/personas/jarvis.md`
- `infrastructure/config/configs/openjarvis/prompts/personas/neutral.md`
- `infrastructure/secrets/README.md`
- `infrastructure/windows/README.md`
- `interfaces/bridge/openwebui/event_bus_contract.md`
- `interfaces/cli/README.md`
- `interfaces/webui/CLAUDE.md`
- `interfaces/webui/README.md`
- `interfaces/webui/docs/API_CLIENTS.md`
- `interfaces/webui/docs/ETHAN_WEBUI_AUDIT_FINAL.md`
- `interfaces/webui/docs/ETHAN_WEBUI_MIGRATION_STATUS.md`
- `interfaces/webui/docs/ETHAN_WEBUI_PRODUCTION_CHECKLIST.md`
- `interfaces/webui/docs/ETHAN_WEBUI_SCORECARD.md`
- `interfaces/webui/docs/ETHAN_WEBUI_TECHNICAL_DEBT.md`
- `interfaces/webui/docs/FRONTEND_COMPONENTS.md`
- `interfaces/webui/docs/WEBUI_ROADMAP.md`
- `interfaces/webui/docs/audits/webui-coherence-audit.md`
- `interfaces/webui/docs/audits/webui-input-focus-audit.md`
- `interfaces/webui/docs/audits/webui-interaction-audit.md`
- `interfaces/webui/docs/ethan_webui_migration_plan.md`
- `interfaces/webui/docs/webui/README.md`
- `interfaces/webui/playwright-report/data/121f1e5acd31810f8f2ba5d6023efe660664f0a4.md`
- `interfaces/webui/playwright-report/data/b856b425d52501ac144ffebb7c83d62d9a81700b.md`
- `interfaces/webui/playwright-report/data/f31c1a3a50284cbeff98341c00c1d2018716e44c.md`
- `interfaces/webui/test-results/login-Login-—-accès-et-for-00de2-utilisateur-reste-sur-login-chromium/error-context.md`
- `interfaces/webui/test-results/login-Login-—-accès-et-for-c84ef-ogin-en-conservant-la-cible-chromium/error-context.md`
- `interfaces/webui/test-results/login-Login-—-accès-et-for-f87b2-n-expose-le-formulaire-réel-chromium/error-context.md`
- `interfaces/webui/tests/e2e/README.md`
- `sdk/AGENTS.md`

## Annexe D — Points de vérification Phase D (rappel)

- Vérifier les liens Markdown relatifs et Obsidian impactés ;
- Vérifier que chaque document déplacé est accessible depuis son index ou référence principale ;
- Vérifier qu’aucun document n’a été perdu ou écrasé ;
- Comparer l’état Git avant et après ;
- Énumérer déplacements, créations, modifications, liens corrigés, validations, problèmes restants, décisions humaines.
