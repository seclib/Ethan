# ODIN P5.3-C.2 — Correction effective du contrat LOD adaptatif

Date : 2026-11-10
Auteur : Agent ECC
Statut : **IMPLEMENTED + TESTED** (validation runtime navigateur non effectuée)

## 1. Diagnostic préalable — anomalies confirmées

L'intervention a commencé par un diagnostic factuel de l'état réel du code. Six anomalies ont été confirmées par inspection du code source et exécution des tests.

### Anomalie 1 — `INFRA_LOD_ACTIVE_MIN` / `INFRA_LOD_ACTIVE_MAX` non définies

`src/performanceManager.js` référençait ces deux constantes **sans les importer** :

```js
// AVANT (lignes 535-537) — ReferenceError à l'exécution
const lodBudget = {
  activeLimit: INFRA_LOD_ACTIVE_MIN,   // undefined
  min: INFRA_LOD_ACTIVE_MIN,           // undefined
  max: INFRA_LOD_ACTIVE_MAX,           // undefined
};
```

**Preuve** : l'exécution de `getLODContract()` levait `ReferenceError: INFRA_LOD_ACTIVE_MIN is not defined`. Le contrat n'a jamais pu être produit.

**Origine** : les constantes existent et sont exportées par `src/data/localGeojsonLod.js` (`INFRA_LOD_ACTIVE_MIN = 80`, `INFRA_LOD_ACTIVE_MID = 200`, `INFRA_LOD_ACTIVE_MAX = 420`). Elles ont été réutilisées telles quelles, conformément à la consigne « réutiliser une constante existante si elle représente déjà cette limite ».

### Anomalie 2 — `changeId` était un compteur artificiel de lectures

```js
// AVANT (lignes 540-549)
let changeId = 0;
const history = this.getHistory();
if (history.length > 0) {
  const lastDecision = history[history.length - 1];
  if (lastDecision && lastDecision.changeId !== undefined) {
    changeId = lastDecision.changeId + 1;   // incrémenté à CHAQUE lecture
  } else {
    changeId = 1;
  }
}
```

Le compteur était dérivé de l'historique des décisions, pas de la politique LOD effective. Il ne distinguait pas « politique changée » de « contrat relu ».

### Anomalie 3 — `this.performanceManager` : ReferenceError qui cassait 8 tests

`src/data/localGeojsonCore.js` (lignes 971-973) lisait `this.performanceManager` à l'intérieur d'une **arrow function** imbriquée dans `createLocalGeoJsonLayer`. En ESM strict, `this` y vaut `undefined` :

```
TypeError [Error]: Cannot read properties of undefined (reading 'performanceManager')
    at src/data/localGeojsonCore.js:971:22
```

**Preuve** : `node --test src/data/localGeojson.test.mjs` échouait sur 8 tests (`globe-LOD caps live stems...`, `globe-LOD selection is stable...`, `getLodDiagnostics reports...`, `globe-LOD releases every stem...`, `globe-LOD re-selects during continuous motion...`, plus 3 tests de ground-sample).

### Anomalie 4 — variables mal nommées dans le bloc de consommation

Le bloc assignait `lastChangeId`, `lastMemoryPressure`, `lastActiveProfile`, `lastDecisionReason` — **jamais déclarés** (les variables déclarées sont `_lastChangeId`, `_lastMemoryPressure`, `_lastActiveProfile`, `_lastDecisionReason`). Ces affectations levaient un `ReferenceError`, **avalé silencieusement** par le `catch` qui se contente d'un `console.warn`. Le bloc n'était donc jamais exécuté complètement.

### Anomalie 5 — le budget n'atteignait jamais `selectInfraLod()`

Le contrat était lu **après** l'appel à `selectInfraLod()`, et le résultat n'était que mémorisé dans `_lastLodBudgetLimit`. La sélection elle-même ne recevait aucun budget : elle utilisait toujours `infraLodBudget(cameraHeightM)`.

### Anomalie 6 — chaîne runtime rompue

`src/standalone/catalog.js` ne transmettait pas `performanceManager` à `createApplicationCatalog()`, qui ne le transmettait pas à `createInfrastructureLayers()`. La couche recevait donc toujours `null`.

**Note** : les anomalies 3 et 4 existaient déjà dans `HEAD` (`git show HEAD:src/data/localGeojsonCore.js` confirme les lignes 970 et 972). Elles n'ont été rendues visibles qu'à partir de l'activation runtime de P5.3-C.1.

## 2. Fichiers réellement modifiés

| Fichier | Modification |
|---|---|
| `src/performanceManager.js` | Import des constantes LOD ; nouvelle fonction exportée `lodBudgetForProfile(profile, cameraHeightM)` ; `getLODContract(cameraHeightM)` corrigé (6 champs, valeurs numériques valides, `changeId` = révision de politique effective) ; `_lodPolicyRevision` / `_lastLodPolicySignature` ajoutés ; `reset()` réinitialise la révision LOD. |
| `src/data/localGeojsonLod.js` | `selectInfraLod()` accepte un paramètre optionnel `activeLimit` : absent → bande caméra historique (identique) ; présent → budget transmis, borné entre `INFRA_LOD_ACTIVE_MIN` et `INFRA_LOD_ACTIVE_MAX` ; valeur inutilisable → repli sur la bande. Le budget appliqué est retourné dans `selection.budget`. Classement, tri déterministe et collapse des doublons préservés. |
| `src/data/localGeojsonCore.js` | Le bloc de consommation est **déplacé avant** `selectInfraLod()` ; il lit la variable de closure `performanceManager` (plus `this`) ; il utilise les variables `_last*` correctement déclarées ; il **transmet** `contract.lodBudget.activeLimit` au sélecteur. Ajout de `getLodPolicy()` exposant l'état de politique lu. |
| `src/app/constructCatalog.js` | `performanceManager` accepté en paramètre et transmis via `services` à `createInfrastructureLayers()`. |
| `src/data/infrastructure.js` | `performanceManager` propagé aux deux couches (datacenters, dams). |
| `src/standalone/catalog.js` | `performanceManager` accepté et transmis à `createApplicationCatalog()`. |
| `src/standalone/application.js` | La scène (propriétaire de l'instance unique) transmet `scene.performanceManager` au catalogue. |
| `src/data/localGeojsonLodContract.test.mjs` | **NOUVEAU** — 16 tests d'intégration ciblés. |

Aucun fichier supprimé. Aucun commit. Aucune commande Git destructive.

## 3. Correction de `INFRA_LOD_ACTIVE_MIN`

```js
// src/performanceManager.js
import {
  INFRA_LOD_ACTIVE_MIN,
  INFRA_LOD_ACTIVE_MID,
  INFRA_LOD_ACTIVE_MAX,
  infraLodBudget,
} from './data/localGeojsonLod.js';
```

`src/data/localGeojsonLod.js` est un **module pur** (aucun import) : aucun cycle d'import possible, vérifié par inspection. Le contrat expose désormais :

- `activeLimit` : toujours numérique, dans `[80, 420]`
- `min` : `INFRA_LOD_ACTIVE_MIN` (80)
- `max` : `INFRA_LOD_ACTIVE_MAX` (420)

Aucune valeur `undefined` n'est plus exposée.

## 4. Preuve que `activeLimit` atteint `selectInfraLod()`

### 4.1 Chaîne de code

```
performanceManager.getLODContract(cameraHeightM)   // contrat à 6 champs
        ↓  contract.lodBudget.activeLimit
localGeojsonCore.js : contratActiveLimit           // lu AVANT la sélection
        ↓
selectInfraLod(candidates, {
  cameraHeightM,
  incumbentIds: _activeLodIds,
  ...(contractActiveLimit !== null ? { activeLimit: contractActiveLimit } : {}),
})
        ↓
selection.budget.activeLimit → applyInfraEvictionGrace(activeLimit)
                              → _lastLodBudgetLimit
```

### 4.2 Preuve expérimentale (end-to-end, couche vivante)

Test `the contract budget bounds the entity selection of a live layer` :

- 600 entités materialized, caméra à 9 000 km, profil **Eco**
- Résultat : `budgetLimit = 80`, `active = 80`, `total = 600`

Test `switching the profile changes the applied budget of a live layer` (bande continentale, 1 000 km, 600 entités, **même caméra, même jeu de données, mêmes conditions de visibilité**) :

| Profil | `budgetLimit` observé | `active` observé | Attendu |
|---|---|---|---|
| Eco | 80 | 80 | 80 |
| Quality | 420 | 420 | 420 |
| Balanced (retour) | 200 | 200 | 200 |

**Les profils modifient réellement la sélection des entités GeoJSON.**

### 4.3 Distinction sélection / affichage

Le budget borne la **sélection** (`_activeLodIds`), pas la matérialisation. Le nombre d'entités **effectivement affichées** (`entity.show === true`) est un sous-ensemble de la sélection : l'occulteur sphérique éclipte ce qui est derrière le globe. Le test l'affirme explicitement : `assert.ok(env.shownCount() <= diagnostics.active)`. Les 600 entités restent materialized (le budget ne dégrade pas le DataSource).

## 5. Politique des profils (règles P5.3-B)

Aucun multiplicateur, aucun seuil inventé : la politique s'exprime en **crans de la bande existante** (80 / 200 / 420).

| Profil | Règle | Budget selon la bande caméra (globale / continentale / régionale) |
|---|---|---|
| **Eco** | budget réduit, plancher 80 | 80 / 80 / 200 |
| **Balanced** | `infraLodBudget(cameraHeightM)` | 80 / 200 / 420 |
| **Quality** | qualité renforcée, plafond 420 | 200 / 420 / 420 |
| **Automatic** | respecte les décisions effectives du Performance Manager | suit le profil concret décidé ; avant toute décision, comportement Balanced |

Vérifié par test sur les trois bandes : `eco <= balanced <= quality`, `eco >= 80`, `quality <= 420`.

**Limite signalée (conforme à la consigne)** : la politique LOD du mode `Automatic` n'est pas définie en propre dans le Performance Manager — celui-ci ne décide que du `maxScreenSpaceError` et bascule `_profile` vers un profil concret. Le mode Automatic applique donc la politique du profil concret décidé, et retombe sur Balanced tant qu'aucune décision n'est prise. Aucun seuil ni multiplicateur n'a été inventé pour combler ce vide.

## 6. `changeId`

Le `changeId` n'est plus dérivé de l'historique. Il compte les **changements de politique LOD effective**, via une signature `profil | niveau de qualité | budget actif` :

- signature identique → `changeId` inchangé (deux lectures rendues le même identifiant)
- profil, budget ou niveau de qualité modifié → `changeId` incrémenté

| Scénario | Résultat observé |
|---|---|
| 3 lectures consécutives sans changement | `changeId` identique |
| relecture sans changement | `changeId` identique |
| `setProfile('quality')` | `changeId` incrémenté |
| relecture après le changement | `changeId` stable |

## 7. Tests réellement exécutés

### 7.1 Nouveau fichier `src/data/localGeojsonLodContract.test.mjs` (16 tests)

```
ℹ tests 16
ℹ pass 16
ℹ fail 0
```

Couverture : budget transmis 80/200/420 sur le même jeu de données ; budget absent → bande historique ; bornage min/max ; valeur inutilisable → repli ; classement/doublons préservés ; contrat à 6 champs valides ; `changeId` stable ; `changeId` incrémenté ; politique par profil ; Eco ≤ Balanced ≤ Quality ≤ 420 ; Quality → Balanced ; **couche vivante** (budget appliqué, changement de profil, fallback sans PM, contrat cassé, contrat incomplet, contrat inchangé sans recalcul).

### 7.2 Tests ciblés existants

| Fichier | Résultat |
|---|---|
| `src/performanceManager.test.mjs` | 50/50 |
| `src/data/localGeojson.test.mjs` | 37/37 (les 8 échecs de l'anomalie 3 sont corrigés) |
| `src/data/localGeojsonLod.test.mjs` | 40/40 |
| `src/data/localGeojsonLifecycle.test.mjs` + `analyst` + `infrastructure` + `constructCatalog` + `application` + `standalone/startupChrome` | 25/25 |
| Total ciblé | **135/135** |

### 7.3 Suite complète

```
ℹ tests 7990    (7974 avant, +16 nouveaux)
ℹ pass  7981
ℹ fail  8
```

Les 8 échecs sont **identiques à ceux constatés avant l'intervention** et concernent des fichiers **non modifiés** :

| Échec | Cause | Fichier concerné | Modifié ? |
|---|---|---|---|
| no browser-built module imports a Node core module | `import('node:abortController')` présent dans un **commentaire JSDoc** | `src/tools/queries/near.js` | non |
| cable ground lines classify against exactly the active surface | mapping `carto-dark` absent | `src/data/telegeographySubmarineCables.js` | non |
| 6 échecs voice / tool schema | hashes de schéma épinglés | `src/voice/*` | non |

**Preuve** : `git status --short` sur ces chemins ne retourne aucune modification ; les échecs se reproduisent à l'identique en exécutant ces fichiers de test isolément, sans aucune modification de ma part.

### 7.4 Build et formatage

- `npx vite build` : **succès** (`✓ built in 8.86s`) — le nouvel import `performanceManager.js` → `data/localGeojsonLod.js` reste browser-safe (aucun `node:` dans les modules touchés).
- `node scripts/format.mjs --check` : mes 8 fichiers modifiés sont conformes. Les écarts de formatage restants concernent des fichiers **non modifiés** (`src/geo/*`, `src/maps/*`, `src/live/*`, `src/tools/*`) — écart préexistant, non corrigé (aucun formatage global).

## 8. Problèmes non résolus

1. **8 échecs de suite préexistants** — sans rapport avec le LOD, causes identifiées (§ 7.3). Non corrigés : hors périmètre de P5.3-C.2.
2. **Écart de formatage préexistant** dans ~20 fichiers non modifiés. Non corrigé : un formatage global est interdit par les contraintes.
3. **Validation runtime navigateur non effectuée** — les preuves sont des tests automatisés (node) sur une couche vivante avec Cesium et un viewport simulé. La validation en navigateur réel reste à faire.
4. **Politique LOD du mode `Automatic` non définie en propre** (§ 5) — comportement Balanced documenté en attendant une spécification de politique.
5. **`getLODContract()` a désormais une signature** `getLODContract(cameraHeightM)`. L'argument est optionnel ; sans lui, la bande globale (80) est retenue. Le seul appelant (`localGeojsonCore.js`) lui passe la hauteur de caméra courante.

## 9. Contraintes respectées

| Contrainte | État |
|---|---|
| JavaScript ESM conservé | ✅ imports/exports ESM, aucun `require` |
| CesiumJS conservé | ✅ aucune modification de l'API Cesium |
| Aucun nouveau moteur | ✅ politique exprimée en crans de la bande existante |
| Aucune dépendance supplémentaire | ✅ `prettier` déjà présent (dev), aucune dépendance runtime ajoutée |
| Aucun changement architectural | ✅ transmission par l'objet `services` existant, aucun nouvel objet global |
| Aucun commit | ✅ `git status` montre 7 modifiés + 1 nouveau, non commités |
| Aucune commande Git destructive | ✅ `git stash`, `git checkout`, `git reset`, `git worktree` non utilisés |
| Fichiers existants non supprimés | ✅ aucun `rm` de fichier source |
| Modifications existantes préservées | ✅ les 3 fichiers de P5.3-C.1 étendus, pas écrasés |
| Render Governor non modifié | ✅ responsabilité intacte |
| 3D Tiles non modifiés | ✅ `maxScreenSpaceError` inchangé |
| P5.4 non commencée | ✅ |

## 10. Verdict

**PASS — l'application effective du budget est démontrée par test.**

- ✅ `getLODContract()` ne produit plus de `ReferenceError` et retourne un contrat à 6 champs, tous valides et numériques.
- ✅ `changeId` est stable entre lectures identiques et évolue uniquement sur changement de politique effective.
- ✅ `lodBudget.activeLimit` **atteint réellement** `selectInfraLod()` : démontré end-to-end sur une couche vivante (80 → 200 → 420 puis retour à 200, avec caméra et données identiques).
- ✅ Sans Performance Manager, le comportement historique par bande caméra est intégralement conservé.
- ✅ Contrat absent, cassé ou incomplet → repli historique sans interrompre le rendu.
- ✅ La régression `this.performanceManager` qui cassait 8 tests est corrigée.
- ✅ 135/135 tests ciblés, +16 tests d'intégration, 7981/7990 sur la suite complète (8 échecs préexistants et sans rapport).
- ✅ Build de production réussi.

**Réserve** : la validation en navigateur réel n'a pas été effectuée ; les preuves reposent sur des tests automatisés. La politique LOD propre au mode `Automatic` reste à spécifier.
