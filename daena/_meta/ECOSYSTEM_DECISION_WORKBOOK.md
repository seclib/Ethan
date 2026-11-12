# ECOSYSTEM_DECISION_WORKBOOK — ETHAN

Date : 2026-11-03
Statut : PROPOSAL
Périmètre : préparation des arbitrages, aucune décision implicement approuvée.

## 1. Décisions approuvées

- MEM-001 : gouvernance mémoire centrale (`USER_APPROVED`)
- MEM-002 : stockage central Knowledge et Skills (`USER_APPROVED`)
- MEM-003 : gouvernance Skills (`USER_APPROVED`)
- MEM-004 : localisation officielle des ADR/ESR/ASR dans docs et Obsidian comme support (`USER_APPROVED`)
- MEM-005 : évolution progressive du modèle (`USER_APPROVED`)
- MEM-006 : architecture hybride (`USER_APPROVED`)
- MEM-007 : politique sécurité commune et Human Root of Trust (`USER_APPROVED`)
- MEM-008 : stratégie 3-2-1, versionnement et restauration (`USER_APPROVED`)
- MEM-009 : gouvernance avancée de confidentialité et publication (`USER_APPROVED`)
- MEM-010 : intégration d'Odin par contrôleur dédié (`USER_APPROVED`)
- MEM-011 : intégration de Frame par contrôleur dédié (`USER_APPROVED`)
- MEM-012 : intégration de TradingAgents par contrôleur dédié et interface WebUI (`USER_APPROVED`)

## 2. Élément encore non approuvé

- MEM-013 — role de Rust dans l'Engineering Memory : `PENDING_USER_DECISION`.
  - Question : faut-il maintenir une implémentation Python-only tant que la contrainte de débit n'est pas démontrée ?
  - Recommandation CTO : rester en Python et n'introduire Rust que sur preuve de goulot d'étranglement.

## 3. Décisions structurantes en attente

### MEM-014 — Contrat générique des applications indépendantes
- Statut : `PENDING_USER_DECISION`
- Question : faut-il adopter une norme commune?
- Options : norme ad hoc; norme minimale; norme complète avec capacités optionnelles.
- Recommandation CTO : norme minimale avec extension documentée.
- Risques : duplication, incompatibilité, sécurité hétérogène.
- Consequences : impact tests, gouvernance et admissions futures.

### MEM-015 — Intelligence partagée
- Statut : `PENDING_USER_DECISION`
- Exemple : l'application indépendante demande à ETHAN des capacités d'intelligence.
- Options : travail intrinsèque; déléagation sélective; orchestration future par agent central.
- Recommandation CTO : déléagation sélective, Atreus reste futur.
- Risques : dérive analytique, fuite de données, latence.

### MEM-016 — Délégation des agents et statut des résultats
- Statut : `PENDING_USER_DECISION`
- Question : comment distinguer action observée, déclarée, vérifiée et approuvée.
- Options : déclaration seule; déclaration + preuves; validation automatique conditionnée.
- Recommandation CTO : option 2 avec preuves.
- Risques : auto-attribution, surcharge et canton.

### MEM-017 — Gouvernance d'Atreus
- Statut : `FUTURE_PLANNED`
- Question : comment préserver la place d'un futur agent central sans le construire ?
- Options : documenter uniquement le contrat; hors périmètre; phase conditionnelle ultérieure.
- Recommandation CTO : options 1 et 3.
- Risques : simulation d'existence, complexité relationnelle.

### MEM-018 — Providers et modèles partagés
- Statut : `PENDING_USER_DECISION`
- Question : quels providers et modèles existants peuvent être réutilisés ?
- Options : aucun partage; partage via adaptateur; mapping indépendant par application.
- Recommandation CTO : mapping indépendant puis mutualisation vérifiée.
- Risques : credentials, divergence de formats and performance.

### MEM-019 — Publication et confidentialité
- Statut : `PENDING_USER_DECISION`
- Question : comment publier sans fuite de données.
- Options : export allowlist; projection seule; pas de publication.
- Recommandation CTO : allowlist + scan + revue humaine.
- Risques : documentation staging, manifests et histoire Git.

### MEM-020 — WebUI et mémoire des agents
- Statut : `PENDING_USER_DECISION`
- Question : l'interface doit-elle rester consultative ou recevoir un flux d'enregistrement ?
- Options : consultatif seul; enregistrements contrôlés; complet avec workflow d'approbation.
- Recommandation CTO : consultatif + enregistrement contrôlé.
- Risques : confusion entre proposition et rapport terminal.

## 4. Contradictions et incohérences

1. Les documents historiques restent présents et rendent difficile une source unique sans suppression contrôlée.
2. Les rapports mentionnent des statuts différents selon leurs phases.
3. La candidature publique est amorcée mais non intégrée à la mémoire.
4. Les tests historiques souffrent de dépendances manquantes et ne sont pas tous réexécutés.
5. Le service Engineering Memory repose sur des adapters non tous activés.
6. Les indices sont présents mais leurs relations ne sont pas complètes.
7. Certains documents mentionnent des composants sans preuve de leur état précis.
8. Les intégrations tierces sont partiellement représentées et restent à vérifier.

## 5. Preuves réellement disponibles

- Code Engineering Memory : 8 modules Python.
- Tests directs disponibles : au minimum 19 dans un ensemble ciblé.
- Scan de secrets local : `no leaks found`.
- Rapports documentaires : plusieurs rapports en `_meta`.
- Sources historiques : `docs/memory`, `Odsidian`, `ethan-knowledge`.
- Guide architectural : Première Loi, conventions et plusieurs ADR existants.
- Échec de collection Pytest : yfinance manquant dans l'environnement actif.

## 6. Ordre recommandé des arbitrages

1. MEM-013 : Rust vs Python pour la scaling selon evidence.
2. MEM-014 : contrat commun.
3. MEM-015 : intelligence partagée.
4. MEM-016 : déléagation et statuts.
5. MEM-017 : Atreus hors périmètre actuel.
6. MEM-018 : providers et modèles.
7. MEM-019 : publication et confidentialité.
8. MEM-020 : WebUI mémoire.

Aucune issue ne doit être considérée validée sans mise à jour du registre et une preuve identifiable.

## 7. Informations incomplètes

- Rôle précis des contrôleurs des applications indépendantes.
- Stratégie exacte de stockage central.
- Relation definitive entre docs et Obsidian.
- Gestion des IDs.
- Politique d'affichage et de traçabilité.
- Intégration intelligente et sécurité HROT.
- Risques restants pour runtime.
- Documentation des changes techniques.
- Tests et preuves pour results.
