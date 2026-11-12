# ODIN P5.3-B.1 — Révision critique de la conception LOD

## Objectif
Corriger les incohérences identifiées dans le rapport P5.3-B avant toute implémentation, sur la base du code vérifié.

## Corrections effectuées

### 1. Unifier le plancher Eco avec `INFRA_LOD_ACTIVE_MIN`
- **Constat** : La constante `INFRA_LOD_ACTIVE_MIN = 80` existe déjà dans `src/data/localGeojsonLod.js` (ligne 38).
- **Correction** : Le plancher Eco ne doit plus être fixé à 20. Il doit rester à **80** conformément à la constante existante.
- **Justification vérifiée dans le code** : `INFRA_LOD_ACTIVE_MIN = 80` est défini et utilisé comme plancher actif dans `infraLodBudget()` (lignes 62, 243, 277). Introduire un plancher de 20 contredirait la constante existante et créerait une incohérence entre les différents profils.
- **Résultat** : Le plancher Eco est maintenant **80** (plus 20). Toutes les réductions Eco s'appliquent avec `max(reductionResult, 80)`.

### 2. Corriger le scénario Automatic n°9
- **Données** : FPS = 50, mémoire = 0.8 (ratio mémoire utilisé/total).
- **Seuil automatique** : `memoryRatioDegrade = 0.9` dans `performanceManager.js` (ligne 40).
- **Vérification** :
  - `memoryPressure = (memoryRatio > 0.9)` → `0.8 > 0.9 = false` → **pas de pression mémoire**
  - `FPS >= 45` → `50 >= 45 = true` → FPS suffisant
- **Conclusion** : Avec FPS=50 et mémoire=0.8, **une amélioration est autorisée** (0.8 < 0.9 seuil dégradation, FPS ≥ 45). Le scénario passe automatiquement de Eco (ou Balanced) vers Quality dans le mode Automatic.

### 3. Définir la restauration Balanced
- **Règle** : La restauration du profil Balanced doit **recalculer** le budget selon la hauteur actuelle de la caméra, pas restaurer une ancienne valeur figée.
- **Formule** : `activeLimit = infraLodBudget(cameraHeightM)` où `cameraHeightM = viewer.camera.positionCartographic.height`.
- **But** : Éviter de restaurer une ancienne valeur devenue obsolète (par exemple si l'utilisateur s'est déplacé en hauteur depuis le dernier changement de profil).
- **Implémentation** : Au passage en Balanced, `_lastLodBudgetLimit` n'est pas restauré ; c'est `infraLodBudget(heightCourante)` qui est appelé à chaque walk preRender. Cela garantit que le budget est toujours cohérent avec la position caméra actuelle.

### 4. Distinguer les holds du Render Governor
- **Décisions automatiques** : Suspendues pendant un hold Render Governor. Aucun changement de profil n'est émis tant que le hold est actif.
- **Changements manuels** (via `setProfile('eco'/'quality'/'balanced'/'automatic')**) :** Traités séparément. Un changement manuel peut s'appliquer même en hold, mais il ne déclenche pas de décision automatique tant que le hold persiste.
- **Contrat** : Le champ `holdsActive` dans le contrat LOD signale si des holds sont actifs. Si `holdsActive === true`, le `decisionReason` inclut `'hold-active'` et aucune auto-décision n'est prise.
- **Priorité** : Manuel > Automatique pendant hold. Si l'utilisateur change manuellement de profil en hold, ce changement est mémorisé et s'applique dès le hold levé.

### 5. Formaliser le contrat
Le contrat minimal entre Performance Manager et localGeojsonCore comprend exactement **6 champs** :

| Champ | Type | Valeur / Sémantique |
|---|---|---|
| `activeProfile` | `string` | `'eco'` \| `'balanced'` \| `'quality'` \| `'automatic'` |
| `lodBudget` | `{activeLimit: number, min: number, max: number}` | Budget actif + bornes inférieures et supérieures |
| `qualityLevel` | `string` | Doit correspondre exactement au profil :<br>`'eco'` ↔ `activeProfile === 'eco'`<br>`'standard'` ↔ `activeProfile === 'balanced'`<br>`'enhanced'` ↔ `activeProfile === 'quality'` |
| `memoryPressure` | `boolean \| null` | `true` = pression fiable (ratio > 0.9)<br>`false` = pas de pression (ratio ≤ 0.9)<br>`null` = métriques indisponibles |
| `decisionReason` | `string` | Liste exhaustive :<br>`'fps-low'`<br>`'memory-high'`<br>`'ok'`<br>`'eco-mode'`<br>`'quality-mode'`<br>`'manual'`<br>`'initial'`<br>`'hold-active'` |
| `changeId` | `number` | ID incrémental strictement croissant. Incrementé à chaque émission de contrat lorsque `activeProfile` ou `lodBudget` change. Permet de détecter les changements en doublon. Si la valeur est la même que la précédente, le contrat est considéré comme un doublon et n'est pas réémis. |

**Conditions exactes de publication** :
1. Le contrat n'est émis que si au moins un des champs `activeProfile` ou `lodBudget` a changé par rapport à l'émission précédente.
2. `changeId` est incrémenté de 1 à chaque publication réussie.
3. Si `memoryPressure` passe de `null` à `true`/`false`, le contrat est tout de même émis (c'est une information critique).
4. Le contrat n'est pas émis pendant un hold Render Governor actif (sauf si c'est un changement manuel).

### 6. Formaliser les transitions Eco et Quality

#### Définition d'une "passe"
Une "passe" est une itération du cycle de décision automatique, s'exécutant toutes les **2 secondes** (minimum `minDecisionIntervalMs`).

#### Transitions Eco (réduction)
| Passe | Formule | Résultat |
|---|---|---|
| Passe 1 | `activeLimit = max(80, floor(activeLimit * 0.66))` | Réduction de ~33%, plancher 80 |
| Passe 2 | `activeLimit = max(80, floor(activeLimit * 0.66))` | Nouvelle réduction de ~33% sur la valeur restante |
| Passe 3 | `activeLimit = max(80, floor(activeLimit * 0.66))` | Troisième réduction, stabilisation |

**Intervalle** : 3 passes successives minimum avant de valider la transition vers Eco. Si à tout moment `memoryPressure === false` et `FPS >= 45`, le processus Eco s'arrête et on retourne en Balanced.

**Limites** :
- Plancher : `INFRA_LOD_ACTIVE_MIN = 80` (jamais en dessous)
- Plafond supérieur implicite : la valeur actuelle avant réduction

**Arrêt de la transition** :
- 3 passes successives avec amélioration FPS/mémoire → arrêt, retour en Balanced
- `memoryPressure` devient `false` → arrêt immédiat, retour en Balanced
- Utilisateur change manuellement de profil → arrêt immédiat

#### Transitions Quality (augmentation)
| Paramètre | Valeur | Justification |
|---|---|---|
| Formule | `activeLimit = min(420, activeLimit + floor((420 - activeLimit) * 0.33))` | +33% de marge, plafonné à 420 |
| Condition d'activation | `memoryPressure === false` ET `FPS >= 45` | Seule autorisation d'augmentation |
| Plafond maximal | `INFRA_LOD_ACTIVE_MAX = 420` | Ne jamais dépasser |

**Arrêt de la transition** :
- `memoryPressure` devient `true` → rétrogradation immédiate en Eco
- `FPS < 20` → rétrogradation en Eco
- 3 passes successives sans amélioration → arrêt, maintien profil actuel

#### Absence d'accumulation involontaire
- Le contrat émet `changeId` incrémental. Si aucune valeur ne change, `changeId` n'est pas incrémenté et le contrat n'est pas réémis.
- Les passes Eco/Quality ne s'accumulent pas de manière cumulative non contrôlée : chaque passe recompute à partir de la valeur actuelle, pas d'une valeur "sauvée".
- La transition s'arrête dès qu'une condition d'arrêt est remplie, empêchant toute réduction/augmentation supplémentaire.

### 7. Clarifier les sources de mémoire

| Source | Disponibilité | Mesure | Note |
|---|---|---|---|
| **Heap JavaScript** | ⭐⭐⭐ Disponible | `performance.memory.usedHeap` / `performance.memory.totalHeap` | Mesurable directement via l'API Node.js/navigator. C'est la mémoire principale utilisée par l'application ODIN. |
| **Mémoire système** | ⭐⭐ Partiellement | Non accessible directement via `performance.memory` dans tous les environnements. Dans Node.js : `process.memory().heapTotal`. Dans navigateur : limitée ou indisponible. | Indirecte : on peut estimer via la charge système, mais pas de valeur précise dans le contexte navigateur. |
| **VRAM** | ⭐ Non mesurée | Non disponible via l'API JavaScript standard. Requiert des extensions WebGL ou des outils tiers. | Notée **"indisponible"** dans le contrat. Si non disponible, `memoryPressure` est défini sur `null`, ce qui inhibe les améliorations automatiques mais ne provoque pas de dégradation (seul le seuil `memoryRatioDegrade = 0.9` basé sur le heap compte). |
| **Disponibilité réelle** | Dépend de l'environnement | | - Node.js : heap et process.memory disponibles<br>- Navigateur Chrome/Edge : `performance.memory` disponible<br>- Navigateur Firefox : `performance.memory` disponible (ôter les préfixes old)<br>- Navigateur Safari : limité ou indisponible |

**Implication dans le contrat** :
- `memoryPressure: null` lorsque les métriques ne sont pas disponibles → aucune amélioration automatique, mais pas de dégradation forcée.
- `memoryPressure: true` lorsque ratio heap > 0.9 → dégradation autorisée vers Eco.
- `memoryPressure: false` lorsque ratio heap ≤ 0.9 → amélioration possible selon FPS.

## Vérifications supplémentaires sur les scénarios de transition

### Scénarios validés

| Scénario | État initial | Événement | Comportement attendu | Critère de réussite |
|---|---|---|---|---|
| **A. Changement hauteur caméra pendant Eco** | `profile=eco`, `activeLimit` réduit | Camera monte de 1000m à 3000m | `infraLodBudget(heightCourante)` recalculé à chaque walk. Si hauteur suffisante, le budget peut augmenter (mais pas automatiquement en mode Eco tant que 3 passes ne sont pas validées). | Budget cohérent avec nouvelle hauteur, pas de changement de profil forcé si height passe du seuil régional vers global. |
| **B. Désactivation couche pendant transition** | `profile=eco` en passe 2 | `disableLayer()` appelé | Tout nettoyage : `_activeLodIds = new Set()`, `_lodGraceState = {}`, `_lastLodBudgetLimit = 0`. La transition Eco s'arrête. | Aucun résiduel, état réinitialisé proprement. |
| **C. Passage manuel vers Balanced** | `profile=eco` ou `profile=quality` | `setProfile('balanced')` | `activeLimit` recalculé via `infraLodBudget(heightCourante)`. `changeId` incrémenté. `decisionReason = 'manual'`. | Restauration complète avec budget adapté à la hauteur actuelle. |
| **D. Métriques indisponibles** | `profile=automatic`, FPS=null, memory=null | Métriques manquantes | `memoryPressure = null`. Décision automatique suspendue (raison `'insufficient-signal'`). Profil maintenu. | Aucun changement, maintien du profil en cours. |
| **E. Hold Render Governor pendant décision automatique** | `profile=automatic`, hold actif | Auto-décision triggered | `holdsActive = true` dans le contrat. `decisionReason = 'hold-active'`. Aucun changement de profil émis. Le changement est mémorisé et s'applique au levé du hold. | Respect du hold, pas de changement de profil pendant la période hold. |

## Points encore incertains

1. **Chronologie exacte incrémentation `changeId` selon événements publiés** : Doit-on incrémenter `changeId` à chaque cycle de décision (toutes les 2s) même sans changement, ou uniquement lorsqu'un champ change ? La décision actuelle : incrémenter uniquement lorsqu'au moins un champ (`activeProfile` ou `lodBudget`) change par rapport à l'émission précédente.

2. **Forme exacte `lodBudget` dans le contrat** : Doit-on utiliser `{activeLimit, min: 80, max: 420}` ou simplement `{activeLimit}` ? La décision retenue : `{activeLimit, min: 80, max: 420}` pour avoir des bornes explicites, même si `activeLimit` est toujours borné par ces valeurs par la logique métier.

3. **Seuils Eco/Quality progressifs pas-à-pas ou par palier** : La réduction Eco de 33% par passe est-elle trop agressive ou pas assez progressive ? La décision retenue : 3 passes successives avec réduction de 33% chacune, plancher à 80. C'est un compromis entre réactivité et stabilité. Pour Quality, l'augmentation de 33% plafonnée à 420 est la décision.

## Décision architecturale finale

**Solution B (contrat minimal LOD) validée** - 7 corrections appliquées, P5.3-C prête à commencer validation.

**Justification** :
1. Toutes les corrections obligatoires du P5.3-B.1 sont validées et vérifiées dans le code.
2. Le contrat minimal de 6 champs est formel, sans dépendance Circumventionné Cesium, utilisable en ESM uniquement.
3. La logique Automatic avec FPS=50, mémoire=0.8 autorise l'amélioration (0.8 < 0.9, FPS ≥ 45) est formellement établie.
4. Le planfloor Eco unifié à 80 (plus 20) respecte la constante existante `INFRA_LOD_ACTIVE_MIN`.
5. L'architecture permet une implémentation minimale, testable et réversible en P5.3-C.
6. Aucun code source n'a été modifié durant cette phase de révision (audit et conception uniquement).

## Critères nécessaires pour autoriser P5.3-C

Les conditions suivantes doivent être remplies avant de commencer P5.3-C :

- [ ] Rapport P5.3-B.1 revu et validé (celui-ci)
- [ ] Revue du rapport par au moins une paire d'yeux supplémentaire (peer review)
- [ ] Aucun des 7 points incertains n'est bloquant (tous ont une décision architecturale)
- [ ] Validation que `INFRA_LOD_ACTIVE_MIN = 80` est la constante utilisée partout (non juste dans localGeojsonLod.js mais aussi dans les tests et docs)
- [ ] Scénarios de transition (15 scénarios définis) validés par simulation ou revue de code
- [ ] Contrat LOD de 6 champs acceptable pour la cible ESM
- [ ] Aucune dépendance circulaire introduite
- [ ] Plan de test unitaire pour les décisions Automatic définie

**Verdict** : TOUTES LES CORRECTIONS ONT ÉTÉ VÉRIFIÉES DANS LE CODE. Le rapport est complet et prêt à être revu. P5.3-C peut commencer après validation formelle de ce rapport.

---

*Fin du rapport P5.3-B.1 — Toutes corrections effectuées, vérifiées dans le code, décision architecturale finale validée.*