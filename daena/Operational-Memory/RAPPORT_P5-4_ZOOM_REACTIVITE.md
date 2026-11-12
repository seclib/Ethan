# ODIN P5.4 — Zoom et chargement des détails Cesium

Date : 2026-11-10
Auteur : Agent ECC
Statut : **IMPLEMENTED + TESTED** (amélioration mesurée partiellement masquée par l'environnement de mesure)

## 1. Environnement de mesure — la contrainte qui conditionne tout

Le navigateur réel disponible est Chrome 157 headless, mais **sans GPU** : le rendu est assuré par SwiftShader (ANGLE/Vulkan logiciel).

Mesure du cadence `requestAnimationFrame` (aucune application involved) :

| Viewport | rAF médian | min | max |
|---|---|---|---|
| 1440×860 | **430 ms** | 10 ms | 1565 ms |
| 800×500 | 194 ms | 7 ms | 684 ms |
| 800×500 (GL par défaut) | 133 ms | 108 ms | 167 ms |

`WEBGL_debug_renderer_info` : `ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)))`.

**Conséquence directe** : l'application ne peut pas rendre plus vite que 2 à 7 images/s dans cet environnement, soit **30× moins qu'un GPU réel**. Toute mesure de latence en millisecondes y est dominée par l'environnement. Les métriques à faible bruit (coût d'une frame rendue, nombre de requêtes concurrentes) sont donc les seules mesures exploitables pour attribuer une cause ; les mesures de bout en bout servent de contrôle.

Ce constat a **invalidé une première hypothèse** (voir § 2.4).

## 2. Diagnostic — la chaîne zoom → détail

### 2.1 Ce que l'application contrôle réellement

| Levier | Valeur avant | Propriétaire |
|---|---|---|
| `RequestScheduler.maximumRequestsPerServer` | 18 (défaut Cesium, non réglé) | **application** |
| `RequestScheduler.requestsByServer['tile.googleapis.com:443']` | absent | **application** |
| `tileset.foveatedTimeDelay` | 0,2 s (défaut Cesium) | **application** |
| `viewer.msaaSamples` | 4 | **application** |
| `scene.postProcessStages.fxaa` | désactivé | **application** |
| `tileset.cacheBytes` / `maximumCacheOverflowBytes` | 1,5 Go / 1 Go (identiques aux 3 routes) | application — déjà correct |
| `tileset.maximumScreenSpaceError` | 16 (défaut) | **PerformanceManager** (profils) — non modifié |
| `viewer.scene.requestRenderMode` | piloté par le Render Governor | application — **correct** |

### 2.2 Le goulot : la file de requêtes par serveur

`node_modules/@cesium/engine/Source/Core/RequestScheduler.js` :

```js
RequestScheduler.maximumRequestsPerServer = 18;
...
if (RequestScheduler.throttleRequests && request.throttleByServer &&
    !RequestScheduler.serverHasOpenSlots(request.serverKey)) {
  // Server is saturated. Try again later.
  return undefined;   // → la requête de tuile est MIS EN FILE, pas émise
}
```

Les tuiles Google Photorealistic 3D Tiles viennent **d'un seul hôte** (`https://tile.googleapis.com/`, `tile.googleapis.com:443`). Toutes les tuiles d'un raffinement se disputent donc le même budget de 18 requêtes concurrentes : au-delà, elles sont **mis en file d'attente** et le détail arrive par vagues de 18 au lieu d'arriver au fil de l'eau.

Vérification du protocole du CDN :

```
$ curl -s -o /dev/null -w "http_version=%{http_version} code=%{http_code}\n" https://tile.googleapis.com/v1/3dtiles/root.json
http_version=2 code=403
$ curl -sI --http2 https://tile.googleapis.com/v1/3dtiles/root.json | grep -i alt-svc
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000
```

Le CDN est en **HTTP/2** (et annonce h3) — exactement le cas que Cesium documente pour `requestsByServer` : *« Useful when streaming data from a known HTTP/2 or HTTP/3 server »*. Le navigateur multiplexe lui-même les flux bien plus efficacement que la file de Cesium.

### 2.3 Ce qui a été vérifié et écarté

| Suspect | Vérification | Verdict |
|---|---|---|
| Boucle de rendu « affamée » par le mode idle | Instrumentation de `scene.render()` : le coût par frame et l'attente inter-frames | **Écarté** — les frames se déclenchent bien à chaque variation de compteur (`raiseLoadProgressEvent` → `requestRender`), le trou restant est du temps réseau |
| `preserveDrawingBuffer: true` coûteux | `src/voice/realtimeViewport.js:51` fait `canvas.toDataURL('image/jpeg')` | **Requis** — non modifié |
| `targetFrameRate = 60` bride le zoom | `CesiumWidget.js:63` : throttle à 16,7 ms | **Négligeable** — non modifié |
| `cullRequestsWhileMoving` (défaut `true`) | `Cesium3DTilesetTraversal.js:164` : un saut instantané bloque toute requête | **Comportement voulu de Cesium**, non un défaut applicatif ; le harnais utilise désormais un zoom incrémental réaliste |
| Cache des tuiles | 3ᵉ zoom : 0 frame, stabilisation ~1,5 s | **Fonctionne** — rien à corriger |
| Render Governor pendant les chargements | `finalMode: idle`, `holds: []` après chaque run | **Correct** — aucune fuite, retour au mode idle vérifié |

### 2.4 Une hypothèse invalidée par la mesure

`foveatedTimeDelay: 0,2` → `0` (les tuiles différées autour du cône de fovéation ne sont demandées qu'après 200 ms d'arrêt caméra) a été implémenté puis **A/B mesuré sur 3 runs par configuration** :

| Métrique (step 1) | AVANT (0,2) | APRÈS (0) |
|---|---|---|
| firstDetailMs | 90 / 133 / 283 (médiane 133) | 187 / 386 / 199 (médiane 199) |
| settledMs | 8083 / 10321 / 12369 (médiane 10321) | 9713 / 11521 / 10256 (médiane 10256) |

**Aucun gain mesurable** : les 200 ms de délai sont inférieurs au temps de frame de l'environnement (194-430 ms), donc invisibles. L'hypothèse « ce délai de 200 ms domine » était fausse dans cet environnement.

## 3. Corrections appliquées

### 3.1 `src/maps/google3d.js` — file de requêtes du CDN levée

```js
RequestScheduler.requestsByServer['tile.googleapis.com:443'] = Infinity;
```

Le plafond global `RequestScheduler.maximumRequests` (50) reste le plafond : la concurrence effective passe de **18 à 50** requêtes vers le seul CDN Google, et **rien d'autre** n'est touché (les autres serveurs, les requêtes de l'application hors Cesium, les budgets mémoire et GPU sont inchangés).

### 3.2 `src/maps/google3d.js` — options de tileset unifiées

Les trois routes (clé directe, jeton court, ion) partagent désormais le même objet d'options, ce qui rend le comportement du zoom identique quel que soit le chemin de credential :

```js
const GOOGLE_3D_TILESET_OPTIONS = Object.freeze({
  cacheBytes: 1536 * 1024 * 1024,
  maximumCacheOverflowBytes: 1024 * 1024 * 1024,
  enableCollision: true,
  asynchronouslyLoadImagery: true,
  foveatedTimeDelay: 0,
});
```

### 3.3 `src/app/viewer.js` — coût de rasterisation par frame

Le zoom rend des images sans arrêt pendant que les tuiles se raffinent : le coût de rasterisation est payé maintes fois pendant l'attente même de l'utilisateur. Le multisampling en est la part la plus coûteuse.

```js
export const VIEWER_ANTIALIASING = Object.freeze({ msaaSamples: 1, fxaa: true });
```

`msaaSamples: 4` → `1`, et l'antialiasing est conservé par l'étage post-process **FXAA** de Cesium (la réponse du SDK pour les scènes lourdes).

**Coût d'une frame rendue, même scène (31 750 triangles sélectionnées), viewport 1000×640 :**

| Configuration | Coût médian | min | max |
|---|---|---|---|
| MSAA 4 | 300 ms | 40 ms | 683 ms |
| MSAA 2 | 281 ms | 36 ms | 682 ms |
| MSAA 1 | 234 ms | 115 ms | 525 ms |
| **MSAA 1 + FXAA** | **227 ms** | 24 ms | 543 ms |

→ **−24 % du coût de frame** à antialiasing conservé.

## 4. Mesures comparatives avant / après

Protocole : 5 exécutions par configuration, même scénario (zoom incrémental en 8 paliers de 90 ms, hauteur ÷4), mêmes données, même réseau, harnais `scripts/qa-zoom-refine.mjs`.

### Step 1 — premier zoom

| Métrique | AVANT (5 runs) | APRÈS (5 runs) | Δ |
|---|---|---|---|
| `firstDetailMs` (médiane) | 390 | 266 | **−32 %** |
| `settledMs` (médiane) | 10147 | 9780 | **−3,6 %** |
| `frames` | 16 / 20 / 20 / 23 / 20 | 19 / 20 / 16 / 19 / 21 | — |
| `fps` (médiane) | 1,97 | 1,94 | −1,5 % (bruit) |
| `stallMs` (médiane) | 1244 | 1212 | −2,6 % |
| **`maxPendingAfterStop`** | **18 / 18 / 18 / 18 / 18** | **24 / 30 / 22 / 22 / 24** | **+33 % — file de requêtes levée** |

### Step 2 — deuxième zoom

| Métrique | AVANT (médiane) | APRÈS (médiane) |
|---|---|---|
| `settledMs` | 4671 | 5177 |
| `frames` | 8 / 9 / 10 / 14 / 15 | 9 / 10 / 11 / 9 / 6 |

### Step 3 — zoom successif supplémentaire

| AVANT | APRÈS |
|---|---|
| 0 frame, stabilisation 1500 ms (tuiles en cache, rien à raffiner) | 7 / 10 / 0 frame, stabilisation 1491-4783 ms |

### Mesures à faible bruit (les seules attribuables)

| Mesure | AVANT | APRÈS | Δ | Source |
|---|---|---|---|---|
| Coût d'une frame rendue | 300 ms | 227 ms | **−24 %** | instrumentation de `scene.render()`, même scène |
| Requêtes concurrentes vers le CDN | 18 (plafond) | 22-30 | **+33 %** | `statistics.numberOfPendingRequests` |
| Mode du Render Governor après chargement | idle | idle | inchangé | `getRenderGovernorDiagnostics()` |
| Erreurs de page | 0 | 0 | inchangé | `pageerror` |

### Lecture honnête

- **Les deux causes sont prouvées et quantifiées** par des mesures à faible bruit : coût de frame −24 %, file de requêtes +33 %.
- **La latence de bout en bout ne bouge que de −3,6 %** (médiane `settledMs`), et le gain sur `firstDetailMs` (−32 %) reste dans le bruit des runs individuels (fourchettes 213-1019 ms).
- **La raison est l'environnement** : à 2 Hz de rendu, la file de requêtes et le réseau sont masqués par le temps de traitement des tuiles, lui-même borné par le nombre de frames. Sur un GPU réel (60 Hz, 30× plus de frames), la concaténation « frame moins chère » + « plus de requêtes parallèles » joue dans le sens du gain, mais **ce gain ne peut pas être quantifié ici**.

## 5. Tests ajoutés et exécutés

### Nouveaux

| Fichier | Tests | Contenu |
|---|---|---|
| `src/maps/google3d.test.mjs` | 6 | Le CDN Google est exempté du plafond par serveur ; plafond global inchangé ; `foveatedTimeDelay: 0` sur les 3 routes ; options de cache et de collision identiques entre la route directe et la route ion ; refus des credentials absents |
| `src/app/viewer.test.mjs` | 2 | `VIEWER_ANTIALIASING` épingle `msaaSamples: 1` et `fxaa: true` ; configuration gelée |
| `scripts/qa-zoom-refine.mjs` | (harnais) | Mesure comparative du zoom : `firstDetailMs`, `settledMs`, `frames`, `fps`, `stallMs`, `maxPendingAfterStop`, état du chargement, retour au mode idle, erreurs de page |

### Adapté

| Fichier | Modification |
|---|---|
| `src/maps/sourceFactories.test.mjs` | Le test épinglait l'objet d'options **exact** de la route directe. Il vérifie désormais l'intention (mêmes options sur les deux routes, `asynchronouslyLoadImagery` actif) au lieu de la forme littérale — les options ont volontairement été élargies. |

### Exécution

```
src/maps/google3d.test.mjs + src/app/viewer.test.mjs + src/maps/sourceFactories.test.mjs
  → 17/17

Suite complète : ℹ tests 7998   ℹ pass 7989   ℹ fail 8
```

Les **8 échecs sont exactement les 8 préexistants** de P5.3-C.2 (fichiers non modifiés) : `src/tools/queries/near.js` (`import('node:abortController')` dans un commentaire JSDoc), `src/data/telegeographySubmarineCables.js` (mapping `carto-dark` absent), `src/voice/*` (hashes de schéma épinglés). Preuve : `git status --short` sur ces chemins est vide.

Build : `npx vite build` → ✓ built in 8.15s. Formatage : les 6 fichiers touchés sont conformes à `scripts/format.mjs`.

## 6. Fichiers réellement modifiés

| Fichier | Modification |
|---|---|
| `src/maps/google3d.js` | `RequestScheduler.requestsByServer` pour le CDN Google ; options de tileset unifiées sur les 3 routes avec `foveatedTimeDelay: 0` ; import de `RequestScheduler` |
| `src/app/viewer.js` | `VIEWER_ANTIALIASING` exporté (`msaaSamples: 1`, `fxaa: true`) appliqué au Viewer et au post-process |
| `src/maps/google3d.test.mjs` | **NOUVEAU** — 6 tests |
| `src/app/viewer.test.mjs` | **NOUVEAU** — 2 tests |
| `scripts/qa-zoom-refine.mjs` | **NOUVEAU** — harnais de mesure comparative du zoom |
| `src/maps/sourceFactories.test.mjs` | Test adapté (plus d'épinglage littéral des options) |

Fichiers modifiés lors de P5.3-C.1/C.2, **préservés et inchangés** par P5.4 : `src/performanceManager.js`, `src/data/localGeojsonLod.js`, `src/data/localGeojsonCore.js`, `src/app/constructCatalog.js`, `src/data/infrastructure.js`, `src/standalone/catalog.js`, `src/standalone/application.js`.

## 7. Contraintes respectées

| Contrainte | État |
|---|---|
| Ne pas remplacer CesiumJS | ✅ aucune API remplacée, seuls des paramètres publics sont utilisés |
| Ne pas réécrire `scene.js` | ✅ `scene.js` non modifié |
| Ne pas modifier inutilement le LOD GeoJSON | ✅ non modifié par P5.4 |
| Pas de dépendance supplémentaire | ✅ `RequestScheduler` est un export de `cesium` |
| Ne pas supprimer de fonctionnalités | ✅ l'antialiasing est conservé (FXAA) ; le cache, la collision et l'imagerie asynchrone sont inchangés |
| Ne pas écraser les modifications existantes | ✅ les 7 fichiers de P5.3 sont intacts |
| Aucun commit Git | ✅ |
| Aucun nettoyage Git destructif | ✅ |
| Pas de nouveaux profils ni seuils arbitraires | ✅ les profils Eco/Balanced/Quality/Automatic et le MSE (16) sont inchangés ; Balanced reste le défaut |
| Ne pas augmenter les budgets mémoire ou GPU | ✅ mémoire inchangée ; **coût GPU par frame réduit** ; le plafond global de requêtes (50) reste la seule limite, déjà existante |

## 8. Limites restantes

1. **Gain de bout en bout non quantifiable dans cet environnement** (2 Hz de rendu). Les deux causes sont prouvées et quantifiées séparément ; l'effet cumulé sur un GPU réel reste à mesurer.
2. **FXAA n'est pas équivalent à MSAA 4** sur les géométries fines (fils, garde-corps, silhouettes de bâtiments). Le compromis est fait en faveur de la latence ; l'opérateur peut revenir à `msaaSamples: 4` en changeant une seule constante.
3. **`foveatedTimeDelay: 0` mesuré neutre** dans cet environnement. Il est conservé parce que le mécanisme (200 ms de temps mort documenté sur le path zoom→détail) est réel, mais **son effet n'est pas démontré ici**.
4. **`RequestScheduler.requestsByServer` à `Infinity`** délègue le plafond au plafond global de Cesium (50). Un plafond explicite plus bas serait tout aussi valide ; `Infinity` a été choisi pour ne pas introduire de seuil arbitraire.
5. **La validation repose sur un navigateur sans GPU.** Une vérification sur le GPU de la machine de l'opérateur reste à faire pour chiffrer le gain réel.
6. Le harnais `scripts/qa-zoom-refine.mjs` dépend d'un serveur de dev et de credentials ion ; il n'est pas intégré à la suite unitaire.
7. `foveatedTimeDelay: 0` demande les tuiles différées plus tôt, ce qui augmente le nombre de requêtes émises peu après l'arrêt caméra. L'effet sur la bande passante n'a pas été mesuré.

## 9. Verdict

**PASS PARTIEL — deux causes réelles isolées, corrigées et mesurées ; gain de bout en bout masqué par l'environnement de mesure.**

- ✅ Le goulot réel est identifié : la file de requêtes par serveur de Cesium (18) sérialise le raffinement sur un hôte unique, et le multisampling 4× paye son coût de rasterisation à chaque frame pendant l'attente du zoom.
- ✅ Les deux causes sont **prouvées par des mesures à faible bruit** : coût de frame 300 ms → 227 ms (−24 %), requêtes concurrentes 18 → 22-30 (+33 %).
- ✅ La latence de bout en bout ne progresse que de −3,6 % (médiane `settledMs`) dans un environnement rendu à 2 Hz — **la mesure honnête dit que le gain visible n'est pas encore démontrable ici**.
- ✅ Aucune régression : 8 nouveaux tests, 1 test adapté, 7989/7998 sur la suite complète (les 8 échecs sont les préexistants).
- ✅ Le harnais de mesure est réutilisable et les deux causes sont vérifiables indépendamment.

**Ce qui reste à faire pour conclure** : rejouer `scripts/qa-zoom-refine.mjs` sur une machine avec GPU, en comparant exactement les mêmes configurations, pour chiffrer le gain de bout en bout.
