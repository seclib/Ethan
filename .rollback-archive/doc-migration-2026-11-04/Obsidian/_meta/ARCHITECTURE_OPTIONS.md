# ARCHITECTURE_OPTIONS — ETHAN Engineering Memory

Date : 2026-11-03
Statut : PROPOSAL
Périmètre : choix architcturaux en attente de validation.

## O1 — Source de vérité documentaire

### Option A — Obsidian comme source unique

- Description : toutes les archives, connaissances et documents opérationnels vivent dans `Obsidian`.
- Avantages : source unique, lisible, hors Git, compatible agents.
- Inconvénients : conflit avec `docs/memory`, `Odsidian` et `/home/fatsio/ethan-knowledge`.
- Risques : perte de provenance si la migration cesse.
- Compatibilité : excellente après arbitrage et sauvegarde.

### Option B — sources multiples conservées

- Description : `docs/memory`, `Odsidian` et `/home/fatsio/ethan-knowledge` coexistent avec Obsidian.
- Avantages : simplicité, pas de suppression.
- Inconvénients : contradiction persistante.
- Risques : duplication et dérive.
- Statut : état actuel.

### Option C — docs Git comme source et Obsidian comme projection dérivée
- Description : Git reste la source des docs opérationnelles; Obsidian ne reçoit que les archives brutes.
- Avantages : oficialité versionnelle.
- Inconvénients : mémoire agent complexe.
- Risques : Obsidian perçu comme dérivé.

## O2 — Knowledge

### Option A — Knowledge dans Obsidian uniquement
- Avantages : mémoire unifiée, provenance et statut.
- Inconvénients : nécessite auth, API et index.
- Risques : les opérations Core complexes perdent leur stock opérationnel actuel.

### Option B — Knowledge conserve son Core opérationnel et Obsidian conserve la mémoire
- Description : `core/knowledge` reste la source opérationnelle; Obsidian conserve les rapports, sources et preuves.
- Avantages : modification limitée, réutilisation.
- Inconvénients : synchronisation éventuelle.
- Statut : approche la plus défensive actuellement.

### Option C — Fusion future dans une Knowledge Service
- Description : service combinant `core/knowledge` et la mémoire documentaire.
- Avantages : long terme.
- Inconvénients : forte complexité.
- Risques : migration de données.

## O3 — Skills

### Option A — Skill store existant comme source, Obsidian comme Memory SKL
- Avantages : réutilise l'existant.
- Inconvénients : gestion de statut et historique dans les rapports.

### Option B — catalogue Skills dans Obsidian
- Avantages : utilisation agent exclusive de la mémoire.
- Inconvénients : dupliquerait la logique source.
- Statut contre : violation de la Première Loi si code selon `core/`.

## O4 — Engineering Memory Service

### Option A — Python-first avec adaptateur Obsidian
- Description : service Python directement observé, API FastAPI et documents Markdown.
- Avantages : compatibilité, performance sufficante pour charge documentaire ici.
- Inconvénients : les hubs à culture plus élevée peuvent exiger Rust.
- Preuves actuelles : implémentation testée en Python, pas Rust.

### Option B — Python service + Rust ingest/event store
- Avantages : haute performance, signature append-only.
- Insconvénients : complexité et dépendance.
- Statut : shadow mode existant déjà.

### Option C — Background collector et file watcher
- Avantags : découplage.
- Inconvénients : risque de doublons, races.
- Risque : augmente complexité sans besoin principal.

## O5 — Persistance et audit

### Option A — Obsidian + Git pour la preuve
- Avantages : lisible, offline.
- Inconvénients : échelle, écritures et conflits.
- Risques : corruption manuelle.

### Option B — Event log append-only tamponné
- Avantages : récupération robuste.
- Inconvénients : étape supplémentaire, plus de code.
- Risques : double écriture.

### Option C — Base de données supplémentaire
- Avantages : requête et index.
- Inconvénients : dépendance, contre le principe de moindre dépendance.
- Statut : non recommandé à ce stade.

## O6 — Publication lisible

### Option A — Export avec allowlist
- Avantages : contrôle maximal.
- Inconvénients : processus à maintenir.
- Risques : docs staging.

### Option B — transformant Observidian entière en repo public
- Avantages : simplicité extatique.
- Inconvénients : fuite historique, secrets et interactions.
- Statut : rejeté par prudence.

### Option C — repo secondaire avec history rebuilt
- Avantages : monorepo propre pour des docs.
- Inconvénients : charge de réécriture et de gouvernance.

## Conclusion

Aucune option n'est sélectionnée par le CTO. Les recommandations sont indiquées comme arguments. Le choix reste à l'utilisateur.

