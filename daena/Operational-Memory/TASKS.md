# TASKS — ETHAN

## Priorité haute

| Task | Statut | Source | Notes |
|---|---|---|---|
| Valider l'accessibilité et la visibilité de `seclib/Ethan` via GitHub | BLOCKED | environnement sans réseau et token invalide | metadata locale uniquement |
| Reconcilier `INDEX.md` Source A avec index Source B | IN_PROGRESS | `_meta/INDEX_ODSIDIAN_SOURCE.md`, `_meta/odsidian-metadata/...` | comptes contradictoires à résoudre |
| Vérifier la candidate publique avant toute publication | PLANNED | `/home/fatsio/AI/Ethan-Public-Candidate` | runtime WebUI non testé |
| Préparer la stratégie public/private | PLANNED | `/tmp/ETHAN_PHASE2_SEPARATION_PLAN.md` | aucune branche publique créée |

## Organisation documentaire

| Task | Statut | Source | Notes |
|---|---|---|---|
| Fusionner les sources de mémoire | IN_PROGRESS | `/tmp/ETHAN_OBSIDIAN_MERGE_PLAN.md` | copie effectuée, validation en cours |
| Conserver les six éléments uniques | CONFIRMED | `_meta/SOURCE_INVENTORY.md` | copies présentes et à vérifier par SHA |
| Consolider les 84 doublons exacts | CONFIRMED | hash comparison | un seul exemplaire dans la cible |
| Maintenir archives immuables | CONFIRMED | conventions du vault | pas de modification des archives |
| Tester les liens internes | IN_PROGRESS | `INDEX.md`, méta | script manuel et inspection |
| Mettre à jour les références `Odsidian` | PLANNED | dépôt principal | uniquement si nom final confirmé |

## Vérification et sécurité

| Task | Statut | Source | Notes |
|---|---|---|---|
| Rechercher secrets dans `Obsidian/` | IN_PROGRESS | outils locaux | exécuter gitleaks ou équivalent |
| Valider sources intactes après migration | IN_PROGRESS | `git status` et parité SHA | en cours |
| Comparer manifeste de copies | IN_PROGRESS | `_meta/MIGRATION_REPORT.md` | à compléter |
| Réorganiser les artifacts volumineux | PLANNED | inventaire | pas de déplacement automatique |

## Documentation

| Task | Statut | Source | Notes |
|---|---|---|---|
| Lire `AGENTS.md` principal comme règle de base | CONFIRMED | `/home/fatsio/AI/Ethan/AGENTS.md` | aucune duplication inutile |
| Actualiser `PROJECT_STATE.md` | IN_PROGRESS | cette migration | état Git du 2026-11-03 |
| Actualiser `DECISIONS.md` | IN_PROGRESS | cette migration | statuts confirmés/plannifiés |
| Maintenir `_meta/MIGRATION_REPORT.md` | IN_PROGRESS | cette migration | preuves à compléter |

## ODIN C3 — Adoption API Geospatial (mise à jour 2026-11-09)

| Task | Statut | Source | Notes |
|---|---|---|---|
| C3.2–C3.9 : migrations `odin/geo` (cockpitCloudEffects, naturalEarthRegions, analystEngine, hud, locations, annotationEngine) | COMPLETE (TESTED, non commit) | `Engineering/Plans/ODIN_C3_GEOSPATIAL_CAMPAIGN.md` | diffs non committés, un fichier/une ligne chacun |
| C3.10 : migration `src/annotations/drawMode.js` | COMPLETE (TESTED, non commit) | campagne §3/§4 — 14/14 direct, 8/8 `drawTool` indirect | export `greatCircleM` préservé à l'octet près |
| C3.11 : audit cumulatif (inventaire + matrice de coût limite + divergence report) | COMPLETE (READ-ONLY) | campagne §7/§7.2 — 6 consommateurs restants, reconquantification du « five » C3.10 | aucune modification de code |
| Audits C3.5 (`transitFeeds.js`) et C3.7 (cumulatif) | COMPLETE | rapports C3.5/C3.7 | report et priorisation documentés |
| Décision de report `transitFeeds.js` | CONFIRMED | `DEC-2026-003` | coût +3 × 6 groupes disproportionate ; condition de renversement non survenue |
| Blocage `carto-dark` (gevActions) | RESOLU (C3.16) | `BLOCKERS.md` B-05 | alias `carto-dark` + enum `set_map_stack` corrigés ; suite redevenue 95/95 |
| C3.12 : migration `src/layers/cctv/model.js` (+3 exactes `cctv-layer`) | COMPLETE (TESTED, non commit) | campagne §3/§4/§7.2 — modelSpecs 19/19, source 7/7, videoPlayback 6/6, headingConfidence 7/7, boundaries exit 0, import-directions exit 0 | wrapper exposé `haversineKm` préservé à l'octet près ; import = une ligne |
| C3.13 : migration `src/layers/bikeshare/model.js` (+3 exactes `bikeshare-layer`) | COMPLETE (TESTED, non commit) | campagne §3/§4/§7.2 — 8 suites bikeshare 46/46 (2+5+2+12+5+10+7+3), boundaries exit 0, import-directions exit 0 | wrapper exposé `haversineKm` préservé à l'octet près ; import = une ligne |
| C3.14 : migration `src/data/trafficBounds.js` (+3 exactes `traffic-layer`) | COMPLETE (TESTED, non commit) | campagne §3/§4/§7.2 — trafficBounds 10/10, traffic/source 38/38, boundaries exit 0, import-directions exit 0 | 3 symboles résolus ; calculs angulaires (L48) préservés à l'octet près ; import = une ligne |
| C3.16 : résolution B-05 + migration GEV `src/voice/gevActions.js` vers `odin/geo` (+0 groupe) | COMPLETE (TESTED, non commit) | campagne §5/§7 — B-05 résolu (alias `carto-dark` + enum `set_map_stack`, suite 95/95) ; migration import `odin/geo` complétée ; boundaries exit 0, import-directions exit 0, ESM OK | seul diff source = 2 lignes (`../geoDistance.js` → `odin/geo` + alias `carto-dark`) |
