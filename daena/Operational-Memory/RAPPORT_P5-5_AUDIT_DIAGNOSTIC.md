# ODIN P5.5 — Audit contradictoire et validation du diagnostic de rendu

Date : 2026-11-10
Auteur : Agent ECC
Statut : **MISSION D'AUDIT — aucune optimisation fonctionnelle réalisée**
Verdict : **PARTIAL** (le diagnostic P5.5 antérieur, tel que livré, était **FAIL** ; le diagnostic corrigé et revalidé est reproductible, à l'exception de la métrique GPU qui reste inaccessible)

## 1. Périmètre réellement touché

| Fichier | État |
|---|---|
| `scripts/qa-render-pipeline.mjs` | **seul fichier modifié** — dispositif de mesure corrigé et revalidé |
| Tous les fichiers `src/` | **inchangés** (horodatage vérifié : le plus récent est `src/maps/google3d.js` à 13:04, l'audit a commencé après) |
| `scripts/qa-zoom-refine.mjs` | inchangé (appartient à P5.4) |

`git status --short` ne montre aucune modification applicative nouvelle ; les 10 fichiers `src/` modifiés sont le travail **non commité** de P5.3-C.1/C.2 et P5.4, intégralement préservé. Aucun commit, aucune commande Git destructive, aucun fichier supprimé.

## 2. Anomalies trouvées dans le dispositif de mesure

Le diagnostic P5.5 précédent s'appuyait sur `scripts/qa-render-pipeline.mjs` et sur des scripts temporaires (`listeners.tmp.mjs`, `withlayers.tmp.mjs`, `probe*.tmp.mjs`, `msaa.tmp.mjs`, `framecost.tmp.mjs`, `fc2.tmp.mjs`, `smoke.tmp.mjs`, `fmt.tmp.mjs` — tous supprimés après usage, vérifié).

### 2.1 Défauts bloquants

**A1 — Inventaire lu dans la mauvaise collection.** L'inventaire comptait `entities` et `dataSources` en itérant `scene.primitives`. Or les DataSources de l'application vivent dans `viewer.dataSources` (collection de Cesium), **pas** dans `scene.primitives` (qui contient le tileset et un `PrimitiveCollection`). Conséquence : le diagnostic annonçait « entities: 0, dataSources: 0 » alors que la scène réelle, couches activées, contient **5 DataSources et 5081 entités**.

**A2 — `postProcessStages` itéré comme itérable.** `PostProcessStageCollection` (Cesium 1.138) n'a **ni `Symbol.iterator` ni indexeur** : seulement `length` (public) et `_stages` (tableau interne). Le `for (const stage of scene.postProcessStages)` levait `TypeError: scene.postProcessStages is not iterable` et **interrompait la sortie** avant l'écriture de l'inventaire.

**A3 — La phase « coût des listeners » ne mesurait rien.** Elle enregistrait un **nouveau** listener dont la « durée » était mesurée via `queueMicrotask` : la microtâche s'exécute **après** le retour du listener, elle mesure donc la latence de planification d'une microtâche, pas le travail de l'application. La phase renvoyait `note: 'probe counts listeners per hook'` et aucun chiffre, alors que l'en-tête du script annonçait la mesure des listeners applicatifs.

**A4 — Le probe temporaire des listeners était destructif.** Il faisait `removeEventListener(listener)` puis `addEventListener(wrapped)` : la clé de la `Map` de Cesium change, donc un `removeEventListener(original)` ultérieur de l'application devient un **no-op**, et les listeners d'origine étaient ré-enregistrés à la fin. Il a aussi rendu `frames: 0` dans la scène au repos, donc ses chiffres étaient vides.

### 2.2 Défauts de méthode

**A5 — Durée codée en dur.** `renderCallHz` et `actualFps` divisaient par un littéral `/ 12` au lieu de la fenêtre mesurée : faux dès que la fenêtre diffère.

**A6 — Situation A inexistante.** La phase « idle » s'exécutait **après** le mouvement de caméra : elle mesurait « après stabilisation », pas « scène au repos ». La mission exige deux situations **distinctes**.

**A7 — Aucune répétition.** Un seul passage par configuration : impossible de statuer la reproductibilité.

**A8 — Aucun contrôle de perturbation.** Rien ne quantifiait le coût de l'instrumentation elle-même sur les mesures.

**A9 — `viewer.entities.length` inexploitable.** Retourne `undefined` ; le compte d'entités doit venir des DataSources.

**A10 — Confusion CPU / GPU.** `medianRenderedCostMs` était présenté comme un coût de frame. C'est le **temps CPU** passé dans `scene.render()` (JS + soumission des commandes). Le coût GPU n'est observable qu'à travers l'écart entre la fin d'une frame et le début de la suivante. **Cesium n'expose aucune timer query publique.**

## 3. Corrections apportées au seul dispositif de mesure

`scripts/qa-render-pipeline.mjs` réécrit (device de mesure uniquement, aucun code applicatif).

| Correction | Méthode retenue |
|---|---|
| Comptage des événements **sans toucher aux listeners** | Substitution de `Event.raiseEvent` **sur l'instance de l'événement** : les listeners ne sont ni retirés ni remplacés, et l'on obtient à la fois le nombre de raised et le CPU total des listeners du hook |
| Séparation tick / frame | `scene.render` enveloppé → **ticks** (appels) ; `postRender.raiseEvent` estampé → **frames** effectivement dessinées |
| Séparation CPU / GPU | `cpuSubmitMedianMs` (CPU) et `framePeriodMedianMs` (période totale observable, GPU inclus) sont deux métriques distinctes ; le GPU est explicitement déclaré **non mesurable** |
| Inventaire | `viewer.dataSources` + `viewer.entities.values` + `scene.primitives` + comptage des tilesets + étapes post-process **activées** (via `collection.length` et `collection._stages`) |
| Situation A / B | A : au repos **avant** tout mouvement ; B : couches réelles activées puis **présence vérifiée dans la scène**, mouvement reproductible, puis fenêtre post-stabilisation |
| Fenêtres | Durées mesurées, plus aucune division codée en dur |
| Perturbation | Mesure comparée : overrides `raiseEvent` vs simple compteur `scene.render` |
| Ids de couches | `local-datacenters` et `local-dams`, **lus dans `src/data/layerState.js`** (registre `LAYER_STATE_REGISTRY`, tokens `d` et `q`), jamais inventés |

## 4. État initial vérifié

| Élément | Valeur vérifiée | Source |
|---|---|---|
| `scene.primitives` | 2 (`Cesium3DTileset`, `PrimitiveCollection`) | mesuré |
| tilesets | **1** | mesuré |
| `viewer.dataSources` | **5** : `gev-annotations` (0), `gev-draw-preview` (1), `gev-recent-imagery-box-preview` (2), **Datacenters (4362)**, **Dams (716)** | mesuré |
| entités (dans les DataSources) | **5081** | mesuré |
| `viewer.entities` | collection vide (`values.length = 0`) | mesuré |
| post-process : longueur de collection | **7** — ce sont les étapes **de l'application** (`godsEyeView_retro`, `_surveillance`, `_thermal`, `_anime`, `_noir`, `_snow`, `_sharpen`) | mesuré |
| post-process : étapes **activées** | **1** : `godsEyeView_sharpen` (intensité par défaut `0.49` → `enabled = value > 0.001`) | mesuré + code |
| FXAA de Cesium | activé (P5.4) — **hors** de la collection ci-dessus | mesuré |
| `msaaSamples` / `fxaa` | 1 / true | mesuré |
| `requestRenderMode` / `targetFrameRate` | true / 60 | mesuré |
| globe / skyAtmosphere / sun / moon / skyBox | false / true / true / true / true | mesuré |
| Render Governor | installé, mode **idle**, `holds: []` | mesuré |
| `tileset.maximumScreenSpaceError` | **16** = défaut Cesium → **aucun profil statique n'a jamais été appliqué** | mesuré |
| mémoire JS | 219 MB au repos → **427-448 MB** avec les couches GeoJSON | mesuré |

## 5. Comportements réels vérifiés

### 5.1 Performance Monitor — jamais démarré

**Preuve statique** : `performanceManager.start()`, `.setProfile()` et `.decide()` ne sont **appelés nulle part** dans l'application (`grep` sur `src/`, hors module et hors tests).

**Preuve comportementale** :

- le listener `postRender` du monitor est **absent** (les 6 listeners `postRender` identifiés ne sont pas les siens) ;
- `tileset.maximumScreenSpaceError` est resté à 16 — un profil Eco (32) ou Quality (4) l'aurait réécrit ;
- `_applyStaticProfile()` n'a donc jamais été appelé.

**Conséquence** : les profils Eco / Balanced / Quality / Automatic sont **inertes** dans ODIN. Seul `getLODContract()` (lu par les couches GeoJSON depuis P5.3-C.2) et `attachTileset()` sont réellement utilisés ; le profil effectif est toujours `balanced`.

**Anomalie connexe** (signalée, non corrigée — hors périmètre d'un audit) : `src/performanceMonitor.js` se termine par deux commentaires de vestige incohérents avec le fichier (`// <-- This is line 314, ...` alors que le fichier en compte 292, et `// <-- This closes the function` après la fermeture).

### 5.2 Sémantique réelle des événements Cesium (source installée)

| Événement | Déclenchement | Mesuré (au repos) |
|---|---|---|
| `preUpdate` / `postUpdate` | **à chaque appel** de `scene.render()` (`Scene.js:4375` et `:4437`) | 219 / 224 / 210 raises |
| `preRender` / `postRender` | **uniquement quand une frame est dessinée** (`Scene.js:4440` et `:4457`) | **0** raise |

### 5.3 Render Governor — comportement correct

Au repos : mode `idle`, `holds: []`, et **0 frame rendue en 10 s** sur 4 exécutions. Aucune fuite, retour au mode idle après les chargements (`recentRequests` : `visibility-restore`, `layer-visibility`). Le gouverneur fait ce qu'il annonce.

### 5.4 Compatibilité des API (Cesium 1.138 installée)

| API utilisée | Vérification |
|---|---|
| `RequestScheduler.requestsByServer` | présent (objet), `maximumRequests = 50`, `maximumRequestsPerServer = 18` |
| `RequestScheduler.maximumRequestsPerServer` | 18 (défaut) |
| `Cesium3DTileset.foveatedTimeDelay` | présent |
| `Cesium3DTileset.loadProgress` | présent (`new Event()`) |
| `Cesium3DTileset.maximumScreenSpaceError` | présent (défaut 16) |
| `scene.postProcessStages.fxaa` | présent et activable |
| `scene.postProcessStages` | **ni itérable ni indexeur** — défaut du harnais, voir A2 |
| `EntityCollection.values` | présent (`length = 0` pour `viewer.entities`) |

## 6. Résultats — Situation A (scène au repos)

Globe chargé, tilesets stabilisés, caméra immobile, governor en mode normal (`idle`). 4 exécutions.

| run | ticks | frames | tickHz | frameHz | CPU soumission médiane | CPU soumission totale | préUpdate/raise | postUpdate/raise |
|---|---|---|---|---|---|---|---|---|
| 1 | 219 | **0** | 21,9 | **0** | 4 ms | 1016 ms | 0,010 ms | 0,063 ms |
| 2 | 224 | **0** | 22,4 | **0** | 4 ms | 966 ms | 0,006 ms | 0,060 ms |
| 3 | 210 | **0** | 21,0 | **0** | 4 ms | 911 ms | 0,005 ms | 0,071 ms |
| 4 | 218 | **0** | 21,8 | **0** | 4 ms | — | — | — |

- **Zéro frame rendue** : le Render Governor et le `requestRenderMode` de Cesium fonctionnent comme annoncé.
- Coût CPU par tick : **≈ 4,6 ms**, dont **≈ 0,07 ms** pour les listeners applicatifs (`postUpdate` cyber-sonar) et **≈ 0,01 ms** (`preUpdate`).
- **Le coût applicatif par tick est négligeable** : ≈ 15 ms sur 10 s de tick continu (≈ 0,15 % d'une seconde de CPU).
- Le coût de tick restant (≈ 4,5 ms) est celui de la mise à jour de scène de Cesium (traversée des tuiles, pass DEFER_CHECK) — **pas** du code de l'application.

## 7. Résultats — Situation B (scène active)

Couches GeoJSON réelles activées (`local-datacenters` 4362 entités, `local-dams` 716 entités — **présence vérifiée dans `viewer.dataSources`**), mouvement de caméra reproductible (100 pas de 0,02° de longitude, ~120 ms).

### 7.1 Pendant le mouvement

| run | ticks | frames | frameHz | CPU médiane | CPU totale | période de frame médiane | **preRender** | postRender | preUpdate | postUpdate |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 145 | 126 | 10,50 | 7 ms | 21 015 ms | 495 ms | **762 ms** (6,05 ms/frame) | 29,6 ms | 2,5 ms | 8,6 ms |
| 2 | 147 | 122 | 10,17 | 7 ms | 22 767 ms | 510 ms | **4982 ms** (40,84 ms/frame) | 27,0 ms | 2,7 ms | 9,2 ms |
| 3 | 159 | 136 | 11,33 | 9 ms | 29 882 ms | 562 ms | **4289 ms** (31,53 ms/frame) | 60,3 ms | 2,9 ms | 13,7 ms |
| 4 | 149 | 115 | 9,58 | — | — | — | **34,36 ms/frame** | — | — | — |

### 7.2 Après stabilisation

| run | ticks | frames | frameHz | CPU totale | preRender | postRender |
|---|---|---|---|---|---|---|
| 1 | 27 | 18 | 1,8 | 3351 ms | 18,0 ms (1,00 ms/frame) | 3,5 ms |
| 2 | 23 | 16 | 1,6 | 2796 ms | 23,2 ms (1,45 ms/frame) | 3,8 ms |
| 3 | 20 | 18 | 1,8 | 2756 ms | 20,1 ms (1,12 ms/frame) | 5,7 ms |

### 7.3 Ce que ces chiffres disent

1. **Le hook `preRender` est le poste applicatif dominant** : 6 à 41 ms par frame pendant le mouvement, contre 0,2-0,4 ms en `postRender`. C'est le walk LOD GeoJSON (P5.3) sur 5081 entités — le système que la mission interdit de modifier inutilement.
2. **Mais le coût de frame n'est pas CPU** : la période de frame médiane est de 495-562 ms alors que la soumission CPU ne coûte que 7-9 ms de médiane. L'écart est de la **rastérisation logicielle** (SwiftShader). Le CPU applicatif ne représente donc qu'une fraction marginale du coût de frame dans cet environnement.
3. **Les hooks par tick sont hors de proportion avec les hooks par frame** : `preUpdate`/`postUpdate` sont levés 145-159 fois pendant le mouvement, pour un coût de 0,02-0,09 ms ; `preRender`/`postRender` 115-136 fois pour 6-41 ms. Confirme la sémantique Cesium.
4. **La dispersion du `preRender` (6 / 41 / 32 / 34 ms par frame) est réelle et forte** : le walk LOD dépend du nombre d'enregistrements visibles et de la distance caméra. Les 4 exécutions ne se recouvrent pas, mais le même ordre de grandeur se répète.

## 8. Effets de l'instrumentation sur les mesures

| Configuration | Cadence des ticks (8 s) |
|---|---|
| avec les 4 overrides `raiseEvent` | 23,0 Hz puis 19,5 Hz |
| compteur `scene.render` seul | 19,6 Hz puis 20,4 Hz |

**Perturbation non mesurable** : l'étalement intra-groupe (19,5-23,0 Hz) dépasse l'écart inter-groupes. La substitution de `raiseEvent` sur l'instance n'affecte pas la cadence mesurée. La méthode (ne jamais retirer les listeners) est donc sûre.

## 9. Comparaison des répétitions

| Métrique | run 1 | run 2 | run 3 | run 4 | Reproductibilité |
|---|---|---|---|---|---|
| A : frames au repos | 0 | 0 | 0 | 0 | **parfaite** |
| A : tickHz | 21,9 | 22,4 | 21,0 | 21,8 | **excellente (±3 %)** |
| B : frameHz (mouvement) | 10,50 | 10,17 | 11,33 | 9,58 | bonne (±9 %) |
| B : preRender ms/frame | 6,05 | 40,84 | 31,53 | 34,36 | **mauvaise** (ordre de grandeur 6-41 ms) |
| B : période de frame médiane | 495 | 510 | 562 | — | bonne (±7 %) |
| B : frames après stabilisation | 18 | 16 | 18 | 19 | bonne |
| Entités / DataSources / tilesets | 5081 / 5 / 1 | idem | idem | idem | **parfaite** |
| Erreurs de page | 0 | 0 | 0 | 0 | **parfaite** |

**Les mesures de structure et de cadence sont reproductibles ; la répartition du coût `preRender` ne l'est pas.** C'est la métrique la plus incertaine de cet audit.

## 10. Limites techniques

1. **Pas de GPU matériel.** Le rendu est SwiftShader (ANGLE/Vulkan logiciel). Toute valeur de « coût de frame » est une **figure de rastérisation logicielle**, jamais une performance GPU réelle.
2. **Le temps GPU n'est pas mesurable** : Cesium n'expose pas de timer query publique. Seul l'écart entre frames est observable, et il mêle CPU, synchronisation et rastérisation. L'audit ne présente donc **aucune** estimation GPU comme une mesure.
3. **La cadence de tick au repos (21-22 Hz) reste inexpliquée** : une page vide dans le même navigateur tourne à **58,8 Hz** (médiane 17 ms). L'écart n'est donc **pas** le plafond rAF du navigateur. Il peut venir du compositeur headless sous `requestRenderMode` (production de frames à la demande) ou du chemin de mise à jour de scène de Cesium ; l'instrumentation actuelle ne permet pas de trancher. **Point ouvert.**
4. **Le coût `preRender` n'est pas attribué par listener** : la mesure est agrégée par hook. Identifier le listener fautif exigerait de ré-envelopper les listeners un par un, méthode destructive écartée en A4. L'imputation au walk LOD GeoJSON repose sur le nombre de listeners (3 → 5 quand les couches GeoJSON sont activées) et sur le périmètre de la mission, pas sur une attribution directe.
5. **Une seule configuration mesurée.** L'audit valide la fiabilité du dispositif, pas une comparaison avant/après d'optimisation : c'était hors périmètre.
6. **Les mesures sont dépendantes de la position caméra** : la fenêtre de mouvement part de la position de démarrage de l'application. Les positions finales diffèrent légèrement d'un run à l'autre, ce qui explique une partie de la dispersion du `preRender`.

## 11. Conclusion sur la fiabilité du diagnostic

### Sur le diagnostic P5.5 antérieur — **FAIL**

Il ne satisfait pas les critères de validation :

| Critère | Verdict |
|---|---|
| Compteurs correspondant aux événements réellement observés | **ÉCHEC** — inventaire lu dans `scene.primitives` au lieu de `viewer.dataSources` (A1) ; itération de `postProcessStages` qui plante (A2) |
| Mesures cohérentes entre répétitions | **ÉCHEC** — une seule exécution, durée codée en dur (A5, A7) |
| Tests au repos et en mouvement distincts | **ÉCHEC** — le « idle » était mesuré après le mouvement (A6) |
| Couches activées réellement présentes dans la scène | **ÉCHEC** — non activées, et comptées dans la mauvaise collection (A1) |
| Limites de SwiftShader clairement documentées | **ÉCHEC** — `medianRenderedCostMs` était présenté comme un coût de frame (A10) |
| Conclusions soutenues par des mesures vérifiables | **ÉCHEC** — la phase « coût des listeners » ne mesurait rien (A3, A4) |

Deux affirmations du diagnostic antérieur sont en outre **factuellement fausses** et doivent être abandonnées :

- **« postProcessStages: 7 »** → 7 est le nombre d'étapes **de l'application** dans la collection ; **une seule** est active (`godsEyeView_sharpen`, par défaut). Le FXAA de Cesium est une étape séparée, hors collection. Le pipeline post-process réel comporte **deux** passes plein écran (sharpen + FXAA).
- **« entities: 0, dataSources: 0 »** → artefact de la collection lue et de l'état par défaut ; la scène réelle tient **5081 entités** dans **5 DataSources**.

L'erreur « 7 post-process » a été propagée dans le rapport P5.4 : elle doit y être corrigée.

### Sur le diagnostic corrigé et revalidé — **PARTIAL**

| Critère | Verdict |
|---|---|
| Compteurs correspondant aux événements réellement observés | **OK** — ticks / frames / updates mesurés séparément, via des seams non destructives ; inventory sur les bonnes collections |
| Mesures cohérentes entre répétitions | **OK** pour la structure et la cadence ; **incertain** pour la répartition du coût `preRender` (6-41 ms/frame) |
| Tests au repos et en mouvement distincts | **OK** — Situation A (0 frame en 10 s) et Situation B distinctes et documentées |
| Couches activées réellement présentes | **OK** — 4362 + 716 entités retrouvées dans `viewer.dataSources` après activation, ids lus dans le registre |
| Limites de SwiftShader documentées | **OK** — GPU déclaré non mesurable, coût de frame qualifié de logiciel |
| Conclusions soutenues par des mesures vérifiables | **PARTIEL** — le coût GPU et l'origine de la cadence de repos restent non établis |

### Ce que l'audit a authentifié sur le fond

- Le Render Governor et le `requestRenderMode` de Cesium **fonctionnent** : zéro frame au repos, retour au mode idle.
- Le **coût applicatif par tick est négligeable** (≈ 0,07 ms) ; le coût par tick de ≈ 4,6 ms appartient à Cesium.
- Le **coût applicatif par frame** se concentre dans `preRender` (6-41 ms) — le walk LOD GeoJSON.
- Le **coût de frame est dominé par la rastérisation logicielle**, pas par le CPU de l'application.
- Les **profils de performance sont inertes** dans ODIN : jamais activés, jamais appliqués.

## 12. Verdict

**PARTIEL** — le diagnostic P5.5 antérieur était **non fiable** (inventaire erroné, plantage sur les post-process, mesure de listeners vide, confusion CPU/GPU, absence de répétitions et de situation au repos) ; il est **invalidé**. Le diagnostic corrigé et revalidé par ce rapport est **cohérent et reproductible** pour la structure de la scène, la cadence de rendu, la sémantique des événements et le comportement du Render Governor ; **deux métriques restent incertaines** : le coût GPU (non mesurable sans GPU matériel ni timer query publique) et la dispersion du coût `preRender` (6-41 ms/frame).

**L'optimisation P5.5 n'a pas été commencée**, conformément à la consigne d'attendre la validation du diagnostic. Le point ouvert le plus important avant de reprendre l'optimisation est la cadence de repos (21 Hz dans l'application contre 59 Hz sur une page vide) : tant qu'il n'est pas expliqué, on ne peut pas affirmer que le tick au repos est optimisable sans risquer de casser le réveil des tuiles (mécanisme P5.4).

## 13. Suite proposée

1. Mesurer le coût GPU sur une machine avec GPU (le rapport P5.5 doit alors distinguer coût GPU et coût CPU sur données réelles).
2. Expliquer la cadence de repos (21 Hz contre 59 Hz) — dérocher le compositeur headless ou instrumenter le `DEFER_CHECK`.
3. Attribuer le coût `preRender` listener par listener avec une méthode non destructive (par exemple en instrumentant `Event.raiseEvent` avec identification de l'appelant).
4. Ne corriger le rapport P5.4 que sur le point factuellement faux (« 7 post-process stages »).

## 14. Annexe — fichiers et commandes

| Élément | Détail |
|---|---|
| Dispositif de mesure | `scripts/qa-render-pipeline.mjs` (réécrit et revalidé) |
| Commande | `QA_BASE_URL=http://127.0.0.1:4180/ QA_LABEL=run<N> node scripts/qa-render-pipeline.mjs` |
| Sorties | `qa-shots/render-pipeline/pipeline-run<N>.json` |
| Navigateur | Chrome 157 headless, SwiftShader, 1280×800, `--use-angle=swiftshader` |
| Serveur | `npx vite --port 4180 --host 127.0.0.1` |
| Credentials | `CESIUM_ION_TOKEN` du `.env` local (route `google-ion`) |
| Suite unitaire | `node scripts/run-unit-tests.mjs` → **7998 tests, 7989 pass, 8 fail** (les 8 échecs préexistants, fichiers non modifiés) |
| Build | non rejoué (aucun changement de code applicatif pendant l'audit) |
