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
| 6 | Gates Core assumés (docs précédentes) : `/automations`, `/channels`, `/prompts` — capacités réelles du Core (`routers/capabilities.py`) sans aucune surface WebUI | **Pages créées** : `/automations` (règles + déclenchement), `/channels` (canaux + messages), `/prompts` (CRUD). Clients minces (`lib/api/{automations,channels,prompts}.ts`) + workspaces FR, états vide/erreur explicites, filtres délégués au Core (`?enabled=`) |
| 7 | `POST /v1/channels/{id}/messages` **cassé côté gateway** : le contenu HTTP était passé en position `role` et un `metadata` non supporté par `ChannelStore.add_message` — tout appel réel levait `TypeError` (500) alors que l'endpoint était annoncé | Gateway réaligné sur la signature du Core (`role`/`content`) + test API dédié `interfaces/api/tests/test_channels_api.py` (5 tests, vrai ChannelStore sur store mémoire) |
| 8 | Skills Lab : test unitaire existant (dialog) mais `listSkillLabResults` (historique) **sans consommateur** | Page `/skills/lab` : formulaire candidat + sandbox Docker du Core + historique réel (le 503 Docker est affiché tel quel, aucun repli local) |

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
- `tests/unit/automations/automations-workspace.test.tsx` (10) : états vide/erreur,
  filtre `?enabled=` délégué au Core, rendu (état, compteur), déclenchement = POST
  Core, désactivation (`enabled: false`), suppression confirmée, création JSON
  parsée, JSON invalide → erreur locale sans appel Core.
- `tests/unit/channels/channels-workspace.test.tsx` (9) : états vide/erreur,
  messages du Core affichés, canal sans message, envoi (contenu + rôle), rôle
  choisi transmis, création puis sélection du canal créé, suppression confirmée.
- `tests/unit/prompts/prompts-workspace.test.tsx` (7) : états vide/erreur, rendu,
  filtre local (présentation seule — le Core n'est pas rappelé), création avec
  tags parsés, édition (PUT sur l'id), suppression confirmée.
- `tests/unit/skills/skills-lab-workspace.test.tsx` (5) : historique vide/affiché,
  erreur + « Réessayer », test sandboxé (code/nom/entrée/dépendances transmis,
  résultat affiché, historique rafraîchi), Docker absent → 503 affiché tel quel.
- `interfaces/api/tests/test_channels_api.py` (5, côté API) : mapping rôle/contenu
  verrouillé sur le vrai `ChannelStore` — contenu stocké dans `content`, rôle par
  défaut `user`, fil par canal, 404 pour un canal inconnu.

## Preuves

| Vérification | Résultat |
|---|---|
| `npm run validate` | **EXIT 0** — 39 suites / 233 tests (avant : 36 / 217) |
| `npm run build` | **EXIT 0** — route `○ /library` compilée |
| `npx playwright test` | **EXIT 0** — 3 passed / 11 skipped (specs authentifiées) |

## Gates levés (capacités Core désormais révélées)

Les pages créées exposent des capacités **réellement servies par le Core** ; la
WebUI ne fait que présenter et transmettre les actions (jamais de logique
métier, AGENTS.md) :

| Route | Capacité Core | Endpoints |
|---|---|---|
| `/automations` | `AutomationManager` (`core/scheduler/automations.py`) | `GET/POST /v1/automations`, `PUT/DELETE /v1/automations/{id}`, `POST /v1/automations/{id}/trigger` |
| `/channels` | `ChannelStore` (`core/state/channels.py`) | `GET/POST /v1/channels`, `DELETE /v1/channels/{id}`, `GET/POST /v1/channels/{id}/messages` |
| `/prompts` | `PromptManager` (`core/config/prompts.py`) | `GET/POST /v1/prompts`, `PUT/DELETE /v1/prompts/{id}` |
| `/skills/lab` | `SkillLab` (`core/skills/lab.py`) | `POST /v1/skills/lab/test`, `GET /v1/skills/lab/results` |

Navigation : Automation (Pilotage), Skills Lab + Prompts (Skills & Integrations),
Channels (nouvelle section Collaboration), les quatre également dans Ctrl+K.
Aucun raccourci « G x » ajouté (les 10 séquences existantes suffisent).

### Décision Library

`/library` reste dans la taxinomie **Knowledge** (et non dans la sidebar
quotidienne) : la vue unifie documents RAG, Knowledge, collections et images,
tandis que `/knowledge` porte la taxinomie/ingestion. Doubler l'entrée quotidienne
créerait la confusion que la règle anti-doublon cherche à éviter ; l'accès reste
direct (Knowledge, `G L`, palette Ctrl+K).

## Hors périmètre

- E2E authentifié (identifiants requis) : les specs skippent proprement.
- Enforcement MCP `SecureToolEnforcer` / RBAC API : chantier Core committé
  séparément (`chore(security)` — permissions API, politique des serveurs MCP,
  garde-fous d'extension).
- `examples/jarvis-os` (gitlink sans `.gitmodules`) : volontairement non committé.
