# ODIN Geospatial API — Référence d'architecture (campagne C3)

Date : 2026-11-09
Statut : VERIFIED (contre le dépôt `examples/odin`, branche `main`, HEAD `57e0bb46ead5143ab37e91e374e1ef9a09168cb8`)
Nature : Knowledge technique / référence d'architecture
ID : `KNW-ARCH-ODIN-GEO-001`
Document campagne associé : `Engineering/Plans/ODIN_C3_GEOSPATIAL_CAMPAIGN.md`

---

## 1. Aperçu

Exemple ODIN : `/home/fatsio/AI/Ethan/examples/odin`.

L'ODIN Geospatial Core est l'implémentation canonique, indépendante du rendu, des primitives
géospatiales d'ODIN. Les consommateurs migrent progressivement d'une façade héritée vers le
point d'entrée public du package. Voir aussi les règles générales d'ETHAN dans la racine `AGENTS.md`.

## 2. Architecture des modules (VERIFIED dans le dépôt)

| Rôle | Fichier | Contenu |
|---|---|---|
| Point d'entrée public | `src/geo/index.js` | Ré-exporte l'API publique approuvée depuis `distance.js`, `crs.js`, `geometry.js` |
| Implémentation canonique | `src/geo/distance.js` | Haversine sur sphère, rayon IUGG `6371.0088` km ; entrées invalides, non finies ou hors plage → `Number.POSITIVE_INFINITY` ; pas d'habillage implicite des longitudes |
| CRS | `src/geo/crs.js` | `WGS84_GEOGRAPHIC`, `AXIS_ORDER_LAT_LON`, `AXIS_ORDER_LON_LAT`, `DATUM_WGS84`, `UNIT_DEGREE`, `wgs84Crs` |
| Géométrie | `src/geo/geometry.js` | `GeometryType`, `geoPointToGeoJsonCoordinates`, `geoJsonCoordinatesToGeoPoint` |
| Façade héritée | `src/geoDistance.js` | Ré-export pur de `./geo/distance.js` — conservé pendant la migration progressive |

### 2.1 Exports publics de `odin/geo` (VERIFIED)

`EARTH_RADIUS_KM`, `isGeoPoint`, `greatCircleKm`, `greatCircleMeters`, `wrapLongitude`,
`WGS84_GEOGRAPHIC`, `AXIS_ORDER_LAT_LON`, `AXIS_ORDER_LON_LAT`, `DATUM_WGS84`, `UNIT_DEGREE`,
`wgs84Crs`, `GeometryType`, `geoPointToGeoJsonCoordinates`, `geoJsonCoordinatesToGeoPoint`.

### 2.2 Exports du package (VERIFIED dans `package.json`)

`./geo` et `./geospatial` pointent tous deux vers `./src/geo/index.js` (alias historique conservé).
Interdiction : aucun sous-chemin de jeu d'autorisations plus étroit que `./geo` n'existe — importer
`odin/geo` réclame donc la possession totale du graphe de ré-export.

## 3. Contrat de distance canonique (VERIFIED)

- `greatCircleKm(from, to)` — kilomètres ; `{ lat, lon }` en degrés. Formule de Haversine avec
  bornage `min(1, max(0, h))` et `atan2`. `EARTH_RADIUS_KM = 6371.0088` (IUGG).
- `greatCircleMeters(from, to)` — mêmes contrats, en mètres (`* 1000`).
- `isGeoPoint(point)` — gardien : `Number.isFinite` + plage lat `[-90, 90]` / lon `[-180, 180]`.
- Tout point invalide -> `Infinity` : maintient les points invalides hors seuils et ramifications
  « plus proche ». Longitudes hors plage signifient un contrat d'appelant cassé (pas d'habillage).

## 4. Application des limites de package (VERIFIED dans `scripts/`)

- Checker : `scripts/check-package-boundaries.mjs` (porte `vite-build` `check-package-ownership` —
  tout module analysé dans le build d'un groupe doit appartenir au `modules` de ce groupe ;
  `treeshake: false` ; entrées = exports du groupe ; runtime `node` vs navigateur).
- Direction : `scripts/check-import-directions.mjs` (état actuel : `{"modules":1029,"portableEntries":80}`).
- Configuration : `scripts/package-boundaries.json` — chaque export du `package.json` est classé
  dans exactement un groupe (1:1, vérifié en tête de checker).

### 4.1 Règle du graphe à quatre modules

Du fait du graphe de ré-export de `src/geo/index.js`, un groupe qui autorise `import ... from 'odin/geo'`
doit posséder les quatre modules `src/geo/{index,distance,crs,geometry}.js` ensemble. Ajouter
uniquement `index.js` échoue avec
`"[check-package-ownership] Package boundary <group> imports an unowned module: src/geo/geometry.js"`
(leçon vérifiée en C3.4).

### 4.2 Implication architecturale et historique des coûts

Sans sous-chemin plus étroit, migrer un consommateur appartenant à des groupes pris séparément
élargit ces groupes à l'entièreté de la surface publique géo (CRS + géométrie), pas seulement au symbole
de distance. L'élargissement n'est justifiable que pour les vrais membres de l'écosystème géo,
pas uniquement pour prendre la fonction mathématique.

Historique : C3.6–C3.10 zéro coût (groupes déjà géo-complets) ; C3.12 (+3 dans `cctv-layer`),
C3.13 (+3 dans `bikeshare-layer`) et C3.14 (+3 dans `traffic-layer`) = élargissements
d'échantillonnage limité, groupes navigateur, justifiés comme vrais membres de l'écosystème
carte/géo.

## 5. Stratégie de migration (VALIDÉE)

1. Un consommateur par étape de campagne ; jamais de remplacement en masse.
2. Modification du seul import (facade `'../geoDistance.js'` → `'odin/geo'`).
3. Préservation stricte du comportement : signatures, unités, gardiens de finitude,
   conventions de coordonnées, seuils, wrappers (y c. les `haversineKm` exposés généralement),
   commentaires/exports intacts. Aucun nettoyage opportuniste.
4. AUCUN élargissement d'autorisations de limites sans autorisation séparée.
5. Les tests ne migrent pas pendant que la façade reste un consommateur légitime ;
   `src/geo/distance.test.mjs` (test de parité) et `src/geoDistance.test.mjs` (contrat de façade)
   gardent leurs imports de façade de manière permanente.
6. Validation par étape : suite de tests directes du consommateur + `npm run check:boundaries` +
   `node scripts/check-import-directions.mjs` + `git diff --check` + résolution ESM `import('odin/geo')`.

## 6. Classification des consommateurs (état 2026-11-09, VERIFIED contre le dépôt)

### 6.1 Migrés vers `odin/geo` (diffs en cours de travail non committés)

| Fichier | Symbole migré | Étape |
|---|---|---|
| `src/cockpitCloudEffects.js` | `greatCircleMeters` | C3.2 |
| `src/data/naturalEarthRegions.js` | `EARTH_RADIUS_KM`, `greatCircleKm` | C3.4 |
| `src/data/analystEngine.js` | `greatCircleKm` | C3.6 |
| `src/hud.js` | `greatCircleKm` | C3.7 |
| `src/locations.js` | `greatCircleKm` | C3.8 |
| `src/annotations/annotationEngine.js` | `greatCircleMeters` | C3.9 |
| `src/annotations/drawMode.js` | `greatCircleMeters` | C3.10 |
| `src/layers/cctv/model.js` | `greatCircleKm` | C3.12 |
| `src/layers/bikeshare/model.js` | `greatCircleKm` | C3.13 |
| `src/data/trafficBounds.js` | `EARTH_RADIUS_KM`, `greatCircleKm`, `isGeoPoint` | C3.14 |
| `src/data/routePlausible.js` | `EARTH_RADIUS_KM`, `greatCircleKm`, `isGeoPoint` | C3.15 |
| `src/voice/gevActions.js` | `greatCircleKm` | C3.16 |

### 6.2 Candidats restants (état après C3.16 — VERIFIED 2026-11-09)

| Fichier | Symboles | Coût de limite | Qualification |
|---|---|---|---|
| `src/data/transitFeeds.js` | `greatCircleKm` | +3 dans 6 groupes (incl. node `transit-provider`) | DEFERRED — `DEC-2026-003` ; condition de renversement non survenue (`package.json` n'expose toujours que `./geo`/`./geospatial` → `src/geo/index.js`) |
| `src/voice/gevActions.js` | `greatCircleKm` | 0 | MIGRÉ (C3.16) — B-05 résolu (alias + enum), migration vers `odin/geo` complétée |

Consommateurs test (hors production, conservés) : `naturalEarthRegions.test.mjs`,
`trafficBounds.test.mjs`, `routePlausible.test.mjs` + les tests de contrat `src/geo/distance.test.mjs`
(parity) et `src/geoDistance.test.mjs`.

### 6.3 Non interchangeables — exclus de la consolidation

Implémentations indépendantes, sémantiquement différentes :

- `src/data/adminBoundaries.js` — Haversine local, rayon `6371`, coordonnées bornées.
- `src/tools/area.js` — géométrie d'aire, rayon local `6371.0088`.
- `src/data/satellitePass.js` — distance orbitale, rayon `6371.0`, contrôle d'éclipse.
- `src/layers/installations/model.js` — géodésiques couplées à Cesium.
- `src/geo/distance.test.mjs`, `src/geoDistance.test.mjs` — tests de contrats (imports de façade contractuels).

## 7. Commandes de validation

```bash
node --test <suite>.test.mjs        # suite directe du consommateur migré
npm run check:boundaries            # check-import-directions.mjs && check-package-boundaries.mjs
node scripts/check-import-directions.mjs
git diff --check                    # intégrité des diffs
```

## 8. Relations

- Campagne : `Engineering/Plans/ODIN_C3_GEOSPATIAL_CAMPAIGN.md`
- Décision de report : `DEC-2026-003` (`Operational-Memory/DECISIONS.md`)
- Blocage du signal de test : `Operational-Memory/BLOCKERS.md` B-05
- État provenant des valeurs : `Operational-Memory/PROJECT_STATE.md`
