# ODIN — Campagne C3 : Adoption de l'API Geospatial (C3.0–C3.9)

Date : 2026-11-09
Statut : COMPLETE (C3.16 terminé le 2026-11-09 ; B-05 résolu — alias `carto-dark` + enum `set_map_stack` — migration GEV `gevActions.js` vers `odin/geo` complétée ; phase migratrice close — DEFERRED : `transitFeeds.js`, plus de blocage GEV résolu)
Nature : Enregistrement de campagne / suivi
ID : `PLAN-ODIN-C3-001`
Dépôt : `/home/fatsio/AI/Ethan/examples/odin` — branche `main`
Référence d'architecture : `Knowledge/Architecture/ODIN_GEOSPATIAL_API.md`

---

## 1. Objet

Consolider les consommateurs ODIN du module de distance hérité vers l'API publique canonique
`odin/geo`, un consommateur par étape, sans changement de comportement. Les migrations ne
modifient que des imports et restent non committées tant qu'elles ne sont pas autorisées.

## 2. État Git vérifié (2026-11-09)

| Élément | État | Statut |
|---|---|---|
| Branche | `main` | VERIFIED |
| HEAD | `57e0bb46ead5143ab37e91e374e1ef9a09168cb8` (`feat(odin): integrate Space features and geospatial foundation`, C1+C2, 72 fichiers) | VERIFIED |
| Non committé (campagne) | 11 imports + `scripts/package-boundaries.json` (C3.4 : +3 `geography` ; C3.12 : +3 `cctv-layer` ; C3.13 : +3 `bikeshare-layer` ; C3.14 : +3 `traffic-layer` ; C3.15 : +3 × 2 `civil-flights`, `aircraft-mechanics`) | VERIFIED |
| `examples/odin/AGENTS.md` | Non tracké, préservé tel quel (interdiction de stage/commit) | VERIFIED |
| Staged | AUCUN — jamais staged | VERIFIED |
| Commits / push de la campagne | AUCUN | VERIFIED |

Détail des huit diffs d'import (chaque migration = exactement une ligne) :

| Fichier | Avant | Après |
|---|---|---|
| `src/cockpitCloudEffects.js` | `import { greatCircleMeters } from './geoDistance.js';` | `from 'odin/geo';` |
| `src/data/naturalEarthRegions.js` | `import { EARTH_RADIUS_KM, greatCircleKm } from '../geoDistance.js';` | `from 'odin/geo';` |
| `src/data/analystEngine.js` | `import { greatCircleKm } from '../geoDistance.js';` | `from 'odin/geo';` |
| `src/hud.js` | `import { greatCircleKm } from './geoDistance.js';` | `from 'odin/geo';` |
| `src/locations.js` | `import { greatCircleKm } from './geoDistance.js';` | `from 'odin/geo';` |
| `src/annotations/annotationEngine.js` | `import { greatCircleMeters } from '../geoDistance.js';` | `from 'odin/geo';` |
| `src/annotations/drawMode.js` | `import { greatCircleMeters } from '../geoDistance.js';` | `from 'odin/geo';` |
| `src/layers/cctv/model.js` | `import { greatCircleKm } from '../../geoDistance.js';` | `from 'odin/geo';` |
| `src/layers/bikeshare/model.js` | `import { greatCircleKm } from '../../geoDistance.js';` | `from 'odin/geo';` |
| `src/data/trafficBounds.js` | `import { EARTH_RADIUS_KM, greatCircleKm, isGeoPoint } from '../geoDistance.js';` | `from 'odin/geo';` |
| `src/data/routePlausible.js` | `import { EARTH_RADIUS_KM, greatCircleKm, isGeoPoint } from '../geoDistance.js';` | `from 'odin/geo';` |

## 3. Historique des campagnes

| Étape | Contenu | Statut | Preuve |
|---|---|---|---|
| C1 | Extraction du core géospatial (`src/geo/distance.js`) | Complète, committée dans `57e0bb4` | VERIFIED (git) |
| C2 | Exports package `./geo`+`./geospatial`, groupe `geospatial-core`, migration `regionalModel.js`, consolidation commit `57e0bb4` (72 fichiers) | Complète, committée | VERIFIED (git) / tests REPORTED |
| C3.0 | API publique publiée sous `./geo` et `./geospatial` | Complète | VERIFIED (`package.json`) |
| C3.1 | Inventaire des consommateurs façade (17 classés par risque) | Complète | REPORTED |
| C3.2 | Migration `cockpitCloudEffects.js` | Complète | VERIFIED (diff) — 4 tests REPORTED |
| C3.3 | Audit `naturalEarthRegions.js` (READY WITH CONDITIONS) | Complète | REPORTED |
| C3.4 | Migration `naturalEarthRegions.js` + `geography` groupe +3 (`index/crs/geometry`) | Complète | VERIFIED (2 diffs) — 15 tests REPORTED |
| C3.5 | Audit `transitFeeds.js` → DEFERRED (6 groupes × +3) | DÉCISION DE REPORT | REPORTED + `DEC-2026-003` |
| C3.6 | Audit + migration `analystEngine.js` (coût limite zéro) | Complète | VERIFIED — 43 tests VERIFIED (9 nov.) |
| C3.7 | Audit cumulatif + migration `hud.js` (coût limite zéro) | Complète | VERIFIED — hudLocality 9/9, hudAltitudeDatum 6/6, hudSummaryResponse 8/8 (VERIFIED) |
| C3.8 | Migration `locations.js` (coût limite zéro, 3 groupes géo-complets) | Complète | VERIFIED — 34/34 tests (VERIFIED) |
| C3.9 | Migration `annotations/annotationEngine.js` (coût limite zéro) | Complète | VERIFIED — 23/23 direct, 7/7 indirect `adminOutline` (VERIFIED) |
| C3.10 | Migration `annotations/drawMode.js` (coût limite zéro) | Complète | VERIFIED — 14/14 direct, 8/8 indirect `drawTool` (VERIFIED) |
| C3.11 | Audit cumulatif post-C3.10 + décision de coût limite (READ-ONLY) | Complète | VERIFIED — 7 migrations confirmées, 6 consommateurs source restants, matrice §7bis |
| C3.12 | Migration `layers/cctv/model.js` + 3 déclarations `cctv-layer` | Complète | VERIFIED — modelSpecs 19/19, source 7/7, videoPlayback 6/6, headingConfidence 7/7 ; boundaries exit 0 |
| C3.13 | Migration `layers/bikeshare/model.js` + 3 déclarations `bikeshare-layer` | Complète | VERIFIED — 8 suites bikeshare 46/46 (2+5+2+12+5+10+7+3) ; boundaries exit 0 ; wrapper `haversineKm` préservé à l'octet près |
| C3.14 | Migration `data/trafficBounds.js` + 3 déclarations `traffic-layer` | Complète | VERIFIED — trafficBounds 10/10, traffic/source 38/38 ; boundaries exit 0 ; 3 symboles résolus depuis `odin/geo`, calculs angulaires (L48) préservés à l'octet près |
| C3.15 | Migration `data/routePlausible.js` + 3 × 2 groupes (`civil-flights`, `aircraft-mechanics`) | Complète | VERIFIED — routePlausible 5/5, boundaries exit 0, import-directions exit 0, ESM OK |

## 4. Preuves de validation

Ne PAS présenter comme une suite cumulée — chaque étape dispose de ses suites propres.

### 4.1 Évidence de tests (ré-exécuté le 2026-11-09 = VERIFIED ; sinon REPORTED)

| Campagne | Suite | Résultat | Statut |
|---|---|---|---|
| C3.2 | `cockpitCloudEffects` tests | 4 pass | REPORTED (session précédente) |
| C3.4 | `naturalEarthRegions` tests | 15 pass | REPORTED (session précédente) |
| C3.6 | `src/data/analystEngine.test.mjs` | 43 tests, 43 pass, 0 fail | VERIFIED |
| C3.7 | `src/hudLocality.test.mjs` | 9 tests, 9 pass, 0 fail | VERIFIED |
| C3.7 | `src/hudAltitudeDatum.test.mjs` | 6 tests, 6 pass, 0 fail | VERIFIED |
| C3.7 | `src/hudSummaryResponse.test.mjs` | 8 tests, 8 pass, 0 fail | VERIFIED |
| C3.8 | `src/locations.test.mjs` | 34 tests, 34 pass, 0 fail | VERIFIED |
| C3.9 | `src/annotations/annotationEngine.test.mjs` | 23 tests, 23 pass, 0 fail | VERIFIED |
| C3.9 | `src/annotations/adminOutline.test.mjs` (indirect) | 7 tests, 7 pass, 0 fail | VERIFIED |
| C3.10 | `src/annotations/drawMode.test.mjs` | 14 tests, 14 pass, 0 fail | VERIFIED |
| C3.10 | `src/annotations/drawTool.test.mjs` (indirect) | 8 tests, 8 pass, 0 fail | VERIFIED |
| C3.12 | `src/layers/cctv/modelSpecs.test.mjs` | 19 tests, 19 pass, 0 fail | VERIFIED |
| C3.12 | `src/layers/cctv/source.test.mjs` | 7 tests, 7 pass, 0 fail | VERIFIED |
| C3.12 | `src/layers/cctv/videoPlayback.test.mjs` | 6 tests, 6 pass, 0 fail | VERIFIED |
| C3.12 | `src/layers/cctv/headingConfidence.test.mjs` | 7 tests, 7 pass, 0 fail | VERIFIED |
| C3.13 | `src/data/bikeshare.test.mjs` | 2 tests, 2 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/barcelonaSystems.test.mjs` | 5 tests, 5 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/brPbscCities.test.mjs` | 2 tests, 2 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/failureReporting.test.mjs` | 12 tests, 12 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/latamPbscCities.test.mjs` | 5 tests, 5 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/proxyRoute.test.mjs` | 10 tests, 10 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/spainCitiesSystems.test.mjs` | 7 tests, 7 pass, 0 fail | VERIFIED |
| C3.13 | `src/layers/bikeshare/usPbscCities.test.mjs` | 3 tests, 3 pass, 0 fail | VERIFIED |
| C3.14 | `src/data/trafficBounds.test.mjs` | 10 tests, 10 pass, 0 fail | VERIFIED |
| C3.14 | `src/layers/traffic/source.test.mjs` | 38 tests, 38 pass, 0 fail | VERIFIED |
| C3.15 | `src/data/routePlausible.test.mjs` | 5 tests, 5 pass, 0 fail | VERIFIED |

### 4.2 Validation de limite (statique, VERIFIED à chaque étape exécutée)

- `npm run check:boundaries` — exit 0 à C3.6/C3.7/C3.8/C3.9 (chaque exécution reconstruit l'intégralité
  des groupes avec la porte `check-package-ownership`).
- `node scripts/check-import-directions.mjs` — exit 0, sortie `{"modules":1029,"portableEntries":80}`.
- `scripts/package-boundaries.json` : toutes les migrations C3.6→C3.9 étaient à coût limite zéro
  (groupes participants déjà géo-complets) ; seule modification de la campagne = C3.4
  (`geography` groupe : +`src/geo/geometry.js`, +`src/geo/crs.js`, +`src/geo/index.js`, plus une
  nouvelle ligne de fin — cosmétique).

### 4.3 Résolution API publique (VERIFIED)

`import('odin/geo')` en ESM Node : `greatCircleKm`/`greatCircleMeters` exportés et appelables ;
`EARTH_RADIUS_KM = 6371.0088` ; auto-distance = `0` ; période d'équateur de 1° ≈ `111195` m ;
coordonnées invalides (ex. `lat: 91`, `lon: 999`) → `Infinity`.

### 4.4 Compatibilité comportementale (VERIFIED par construction + diff)

La façade `src/geoDistance.js` est un ré-export pur du module canonique, donc façade et package
résolvent vers le MÊME objet fonction. Les comparaisons avant/après des régions de call-site,
wrappers (`haversineKm`, `_haversineKm`, `greatCircleM`) et `formatDistance` sont identiques à l'octet
près pour C3.6–C3.9 (régions extraites conformes). Les tests existants (y compris les
`@deprecated` wrappers positionnels) couvrent les comportements préservés.

### 4.5 Intégrité Git (VERIFIED à chaque étape)

- Pré-vol/post-vol : branche + HEAD inchangés ; zéro fichiers staged ; zéro commits/push ;
  modifications préexistantes intactes ; `AGENTS.md` non tracké et jamais touché.
- Un seul fichier source par étape, avec exactement une ligne d'import remplacée
  (confirmé par `git diff -- <file>` étape par étape).

## 5. Échecs baselines connus (HORS campagne C3)

| Suite | Échec | Cause | Lien |
|---|---|---|---|
| `telegeographySubmarineCables.test.mjs` | 1 | aliase carte manquant `carto-dark` | préexistant |
| `voice/gevActions.test.mjs` | 1/95 — `set_map_stack 'carto-dark' has no self-mapping alias` → résolu le C3.16 (alias `carto-dark` + enum `set_map_stack` ; suite redevenue **95/95**) | idem | → B-05 résolu (C3.16) |

Ces échecs préexistaient à la campagne C3 et n'ont pas été corrigés (intouchés par stratégie).

## 6. Candidats reportés / en attente

| Fichier | Statut | Coût limite / raison |
|---|---|---|
| `src/data/transitFeeds.js` | DEFERRED (C3.5) | +3 dans 6 groupes (incl. groupe node `transit-provider`) pour un wrapper + un call site interne — `DEC-2026-003` |
| `src/voice/gevActions.js` | MIGRÉ (C3.16) | B-05 résolu (alias `carto-dark` + enum `set_map_stack`) ; migration vers `odin/geo` complétée — coût limite zéro |
| `src/annotations/drawMode.js` | MIGRÉ (C3.10, 2026-11-09) | coût limite zéro ; export `greatCircleM(a,b)` préservé à l'octet près (régions comparées avant/après) |
| `src/layers/cctv/model.js` | MIGRÉ (C3.12, 2026-11-09) | +3 documentées dans `cctv-layer` ; wrapper exposé `haversineKm` préservé à l'octet près |
| `src/layers/bikeshare/model.js` | MIGRÉ (C3.13, 2026-11-09) | +3 documentées dans `bikeshare-layer` ; wrapper exposé `haversineKm` préservé à l'octet près |
| `src/data/trafficBounds.js` | MIGRÉ (C3.14, 2026-11-09) | +3 documentées dans `traffic-layer` ; 3 symboles (`EARTH_RADIUS_KM`, `greatCircleKm`, `isGeoPoint`) résolus depuis `odin/geo` ; calculs angulaires préservés |
| `src/data/routePlausible.js` | MIGRÉ (C3.15, 2026-11-09) | +3 × 2 groupes (`civil-flights`, `aircraft-mechanics`) ; 3 symboles (`EARTH_RADIUS_KM`, `greatCircleKm`, `isGeoPoint`) résolus depuis `odin/geo` ; formules et validations préservées |

Exclus (sémantiquement non interchangeables, voir la doc d'architecture §6.3) :
`adminBoundaries.js`, `tools/area.js`, `satellitePass.js`, `layers/installations/model.js`, tests de façade/parité.

## 7. Audit cumulatif C3.11 (2026-11-09) — restitution et divergences résolues

### 7.1 Reconciliation des divergences de rapport (VERIFIED)

**Divergence 1 — « cinq consommateurs restants » vs six candidats énumérés.** Le rapport C3.10
indiquait « five remaining consumers » : c'était un sous-comptage. Le recensement vivant du
2026-11-09 donne exactement **6 consommateurs source restants de la façade**
(`transitFeeds`, `trafficBounds`, `routePlausible`, `bikeshare/model`, `cctv/model`, `gevActions`).
Cause probable : l'exclusion opérationnelle du candidat DEFERRED (`transitFeeds`) d'un comptage
mentalement interprété. Ne PAS réécrire les rapports antérieurs : la présente note qualifie
explicitement le décompte, le tableau §6 fait foi.

**Divergence 2 — valeurs de sanity ESM différentes entre C3.9 (≈111195 m) et C3.10 (≈111404 m).**
Aucune incohérence : les paires d'entrées diffèrent, les deux résultats sont canoniquement exacts :

| Contrôle | Entrées (dég.) | Sortie canonique (VERIFIED 2026-11-09) |
|---|---|---|
| C3.9 | `{lat:0,lon:0} → {lat:0,lon:1}` | **111195.080 m** — exactement l'arc équatorial de 1° `2πR/360` pour R=6371.0088 km |
| C3.10 | `{lat:30,lon:-97} → {lat:29.5,lon:-96}` | **111403.653 m** — jambe Δlat 0.5° × Δlon 1° à lat ≈ 29.75° (cos) |

Unité : mètres via `greatCircleMeters` ; les deux appelés le même symbole canonique `odin/geo`.

### 7.2 Matrice de coût limite — consommateurs restants (VERIFIED contre le JSON vivant)

| Consumer | Owning groups | Groups needing +3 | Groupes touchés | Tests (signal 2026-11-09) | Recommandation |
|---|---|---|---|---|---|
| `src/layers/cctv/model.js` | `cctv-layer` + 2×application | `cctv-layer` (1) | 1 × +3, browser | modelSpecs 19/19 VERIFIED + suites layer | **MIGRÉ (C3.12)** — déclarations exactement +3 posées, boundaries exit 0, wrapper `haversineKm` intact |
| `src/layers/bikeshare/model.js` | `bikeshare-layer` + 2×application | `bikeshare-layer` (1) | 1 × +3, browser | 46 pass sur 8 suites VERIFIED (2026-11-09, exécution C3.13) | **MIGRÉ (C3.13)** — déclarations exactement +3 posées, boundaries exit 0, wrapper `haversineKm` intact |
| `src/data/trafficBounds.js` | `traffic-layer` + 2×application | `traffic-layer` (1) | 1 × +3, browser | trafficBounds 10/10 + traffic/source 38/38 VERIFIED | **MIGRÉ (C3.14)** — déclarations exactement +3 posées, boundaries exit 0, calculs angulaires intacts |
| `src/data/routePlausible.js` | `civil-flights`, `aircraft-mechanics` + 2×application | 2 groupes | 2 × +3, browser | routePlausible 5/5 VERIFIED | **MIGRÉ (C3.15)** — déclarations exactes +3 × 2 posées, boundaries exit 0, formules intactes |
| `src/voice/gevActions.js` | `application-components` (géo-complet) | 0 | 0 | gevActions 95/95 — B-05 résolu (alias + enum), migration vers `odin/geo` complétée (C3.16) | **MIGRÉ (C3.16)** — coût limite zéro, boundaries inchangés |
| `src/data/transitFeeds.js` | 8 groupes, 2 complets | 6 groupes (incl. node `transit-provider`) | 6 × +3 | transitFeeds 28/28 (rapport C3.7) | **DEFERRED** — `DEC-2026-003` ; condition de renversement NON survenue (`package.json` n'expose toujours que `./geo`/`./geospatial` → `src/geo/index.js`) |
| Tests importeurs de la façade (`naturalEarthRegions.test`, `trafficBounds.test`, `routePlausible.test`) | hors production | — | — | — | **NOT A CONSUMER (production)** — tests, conservés jusqu'à décision de retrait de façade |
| `src/geo/distance.test.mjs`, `src/geoDistance.test.mjs` | hors production | — | — | — | **NOT A CONSUMER (production)** — tests de contrat/parité, imports de façade contractuels |

Catégories de recommandation : READY (coût limite nulle) = **aucun restant** ;
DEFERRED (disproportionné) = transitFeeds ; BLOCKED (baseline) = gevActions.

## 7bis. Clôture de la phase migratrice — état après C3.16 (TERMINÉE)

La campagne C3 (C1 → C3.16) est terminée sur le périmètre « élargissement limité » :

1. **Coût nulle** : aucun consommateur restant après C3.16 (les 12 migrations à ce jour).
2. **Élargissement double (2 groupes × +3)** : réalisé — `routePlausible.js` (`civil-flights`, `aircraft-mechanics`).

Consommateurs restants, désormais non migrables dans le cadre autorisé :

- `src/data/transitFeeds.js` — DEFERRED (C3.5) — `DEC-2026-003` ; condition de renversement non survenue.
- `src/data/transitFeeds.js` — réévalué (C3.17, 2026-11-09) : expansion de 6 groupes × +3
  (`transit-provider`, `transit-source`, `transit-standalone`, `transit-layer`, `transit-service`,
  `tools`) toujours jugée disproportionnaire pour un seul consommateur de données (wrapper + 1 call
  site interne) via l'entrée publique unique `odin/geo` — **décision RETENUE (non inversée)**.
- `voice/gevActions.js` — MIGRÉ (C3.16) — B-05 résolu (alias `carto-dark` + enum `set_map_stack`),
  migration vers `odin/geo` complétée ; coût limite zéro.

Plus aucun candidat READY WITH CONDITIONS ne subsiste. Toute exécution UNIQUEMENT sur
autorisation explicite. Ne pas confondre PENDING et COMPLETE.

## 8. Limite et incertitudes

- Les dépouillements C3.2 (4 tests) et C3.4 (15 tests) proviennent des rapports d'exécution
  précédents ; les diffs correspondants sont VERIFIED dans le repository vivant (imports + limite).
- L'inventaire initial C3.1 (17 consommateurs classés) a été ré-audité en C3.7 ; la liste exacte
  ci-dessus reflète l'état du dépôt vivant au 2026-11-09, y compris la migration C3.6 déjà réalisée.

## 9. Relations

- Référence d'architecture : `Knowledge/Architecture/ODIN_GEOSPATIAL_API.md`
- Décision : `DEC-2026-003` (report `transitFeeds.js`) — `Operational-Memory/DECISIONS.md`
- Blocage signal : `Operational-Memory/BLOCKERS.md` B-05
- État projet : `Operational-Memory/PROJECT_STATE.md`
- Tâches : `Operational-Memory/TASKS.md`
