# WebUI — Audit de cohérence « anti-fantôme »

**Date** : 2026-09 · **Périmètre** : `interfaces/webui` (aucune modification Core)
**Principe directeur** : l'interface révèle ETHAN — elle n'annonce jamais une
capacité que le Core (ou l'App Router) ne sert pas réellement.

## Méthode

1. **Garde-fou statique** (nouveau) : scan de tous les `href` / `router.push` /
   `redirect` du source, confronté à l'arbre de routes réel (groupes de routes,
   segments dynamiques, templates, assets `public/`).
2. **Recensement des modules orphelins** : composant / client API / hook sans
   page ni consommateur.
3. **Vérification des endpoints Core** appelés par chaque client WebUI
   (`interfaces/api/routers/{v1,domains,capabilities}.py`).

## Constats & correctifs

| # | Constat | Correctif |
|---|---------|-----------|
| 1 | `src/hooks/use-shortcuts.ts` : doublon **orphelin** (0 appelant) du système réel `global-shortcuts.tsx`, avec 3 cibles invalides — `n → /chat/new` (inexistant), `l → /library` (inexistant alors), `p → /projects/new` (fantôme *masqué* : la route dynamique `/projects/:id` le validait à tort) | Hook supprimé ; le système monté (`layout.tsx`) reste la seule implémentation |
| 2 | Séquences « g puis x » dispersées : handler (7 clés), indicateur visuel (libellés en dur), palette Ctrl+K (`G P`, `G N` annoncés **mais non résolus** ; `G T` résolu mais **non annoncé**) | `G_SEQUENCE_ROUTES` (nav-config) = source unique ; handler, indicateur **et** palette en dérivent (`formatGSequence`) |
| 3 | `components/features/library/library-workspace.tsx` + `lib/api/library.ts` orphelins : aucune route `/library`, alors que le raccourci `l` la visait | Page `/library` créée (présentation seule), taxinomie **Knowledge**, entrée palette « Go to Library », textes FR cohérents |
| 4 | Endpoints du client Library non re-vérifiés depuis l'orphelinat | Vérifiés : `/v1/rag/documents`, `/v1/knowledge`, `/v1/knowledge/collections` (routers/v1.py) et `/files` (routers/domains.py) — aucune donnée simulée, états vide/erreur explicites |
| 5 | Nav : 29 entrées à re-valider après la refonte | 29/29 résolues vers une route réelle (seul artefact : `//login` dans l'outillage de test, corrigé) |

## Garde-fou ajouté

`tests/unit/ui/internal-links.test.ts` (2 tests) :

- découverte de l'arbre App Router (39 routes ; `/`, `/library`, `/projects/:id`…) ;
- **chaque lien interne du source pointe une route réelle**, tolérance zéro, avec
  auto-vérification (≥ 30 liens inspectés) pour empêcher un faux vert si les
  regex cessent de matcher.

## Tests ajoutés

- `tests/unit/ui/global-shortcuts.test.tsx` (7) : invariants de la source unique,
  résolution des 10 séquences par le handler, indicateur complet (aucune dérive),
  séquence inconnue inerte, palette n'annonçant que des raccourcis résolubles,
  navigation vers Library.
- `tests/unit/library/library-workspace.test.tsx` (7) : état vide nommant les
  sources Core, erreur + « Réessayer », compteur singulier/pluriel, détail
  (contenu / métadonnées réels), filtres type et recherche **délégués au Core**.

## Preuves

| Vérification | Résultat |
|---|---|
| `npm run validate` | **EXIT 0** — 39 suites / 233 tests (avant : 36 / 217) |
| `npm run build` | **EXIT 0** — route `○ /library` compilée |
| `npx playwright test` | **EXIT 0** — 3 passed / 11 skipped (specs authentifiées) |

## Gates restants (assumés — aucun lien fantôme)

Capacités **exposées par le Core** mais sans surface WebUI ; aucune entrée de
nav, de palette ou de raccourci ne les référence (créer leurs pages est une
décision produit, pas une dette de cohérence) :

- `/automations` — `routers/capabilities.py:84-146`
- `/channels` — `routers/capabilities.py:366-436`
- `/prompts`

## Hors périmètre

- E2E authentifié (identifiants requis) : les specs skippent proprement.
- Enforcement MCP `SecureToolEnforcer` : sujet Core, non opposable runtime.
- `core/capability_manager/` : WIP non suivi git.
