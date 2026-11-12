# Audit UX / Polish — WebUI ETHAN (phase TEST · CORRECTION · POLISH)

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001` (conteneur `ethan-ui`)
**Méthode** : lecture du code, curl SSR (`Cookie: ethan_token=probe`), grep structurel des mutations, validation `tsc`/`build`/`lint`/`jest`, rebuild Docker et re-test.
**Périmètre respecté** : aucune refonte d'architecture, aucun changement de thème, aucune suppression de fonctionnalité.

---

## Bugs corrigés

| # | Bug | Cause racine | Correction | Fichier |
|---|---|---|---|---|
| 1 | Scroll impossible sur Providers LLM et Skills | Conteneur racine `flex h-full` **sans** `min-h-0` ni `overflow-y-auto` dans une hiérarchie flex `100dvh` dont l'ancêtre porte `overflow: hidden` (`layout.tsx` l.42) — le contenu débordait masqué, inaccessible | `min-h-0 overflow-y-auto` sur le workspace + `overflow: auto` sur le `<main>` global (`layout.tsx` l.54) : sidebar fixe, contenu principal scrollable | `providers-workspace.tsx`, `skills-workspace.tsx`, `layout.tsx` |
| 2 | Faux switch sur les modèles découverts (Settings → Models) | `POST /models/{id}/toggle` n'agit que sur `is_active` des fiches **custom** (`core/llm/model_store.py` l.106-111) ; sur un modèle découvert il renvoyait 404 | Toggle affiché **uniquement** pour les modèles custom ; les modèles découverts affichent leur nature réelle | `settings-workspace.tsx` |
| 3 | État des modèles illisible | Aucun libellé d'état, `ToggleRight` identique actif/inactif, point de statut seul pour les découverts | Libellés « Activé »/« Désactivé », `ToggleRight` coloré `text-accent` si actif, tooltip d'action, badge `decouvert`, état « Disponible » / « Provider hors ligne » (ambre) avec tooltip pédagogique | `settings-workspace.tsx` |
| 4 | Section General peu instructive | Groupes de config rendus bruts (`system`, `llm` minuscules, sans explication) | Titres « System » / « LLM » + description d'une ligne par groupe | `settings-workspace.tsx` |
| 5 | Incohérence linguistique Settings | Description General en anglais, toutes les autres en français | « Configuration générale et gouvernance du système » | `settings-workspace.tsx` |

## Problèmes de scroll

| Page | État après correction |
|---|---|
| `/providers`, `/skills` | ✅ corrigés (`min-h-0 overflow-y-auto` sur le workspace) |
| `/missions`, `/workspace` | ✅ `overflow-y-auto` présent nativement |
| `/models`, `/settings`, `/agents`, `/knowledge`, `/tools` | ✅ scroll via `<main>` global (`overflow: auto`) |
| `/calendar`, `/notes`, `/inbox`, `/research`, `/cookbook`, `/security` | ✅ couverts par `<main>` global — décision : pas d'overflow redondant |
| Sidebar | ✅ indépendante (rail fixe, zone chat scrollable) |
| Modals / drawers | ✅ Dialog design-system (portal, overlay, focus trap, Escape) — non impactés |

**Comportement atteint** : sidebar indépendante, contenu principal scrollable verticalement, aucune zone inaccessible ; pas de scroll horizontal (body `overflowX: hidden`).

## Settings améliorés

Inventaire audité (toutes les données sont réelles) :

| Section | Rôle affiché | État |
|---|---|---|
| General | « Configuration générale et gouvernance du système » + groupes System (« Comportement général d'ETHAN ») / LLM (« Paramètres par défaut des modèles ») | ✅ Édition réelle, Enregistrer avec dirty check |
| Appearance | « Thème, couleur d'accent et préférences d'interface » | ✅ dark/light/system/OLED/high-contrast + accents persistés |
| Models | « Catalogue de modèles découverts et personnalisés » | ✅ états clarifiés (cf. ci-dessous) |

## Models clarifiés

**Comportement réel d'ETHAN** (déterminé avant toute modification d'UI) :

- **A. « Actif »** = pour une fiche **custom**, le champ `is_active` (aliasé `is_available` dans le payload API) — toggleable.
- **B. Notions backend existantes** : `is_available` (provider joignable pour les modèles découverts ; `is_active` pour les custom), `is_custom` / `source: discovered|custom`, `is_local`, `is_private`, `quality_score`. **Pas** de notion `default` par modèle — le défaut se règle au niveau provider (`setDefaultProvider`).
- **C. API** : `GET /models`, `POST /models/{id}/toggle` (`interfaces/api/routers/models.py`, `core/llm/model_store.py`).

**Rendu final** :

```
● llama3.1:8b                 Géré par ollama · Disponible      (découvert — aucun switch)
● mon-preset  [custom]        Activé      [toggle actif]        (custom — action réelle)
○ mon-preset-2 [custom]       Désactivé   [toggle inactif]      (custom — action réelle)
⚠ …                           … · Provider hors ligne           (découvert, provider down — ambre)
```

Aucun faux switch : le contrôle n'existe que là où la capacité backend existe.

## Administration

| Élément | Backend réel | Verdict |
|---|---|---|
| Diagnostics (`/diagnostics`) | `GET /health/detailed` FastAPI, proxy JWT, `no-store` | **Fonctionnelle** |
| Logs (Grafana Explore `:3002/explore`) | Loki via Grafana, lien externe marqué `external` | **Fonctionnelle** (honnête : externe, pas de fausse page) |
| Monitoring (Grafana `:3002`) | Prometheus/Loki/Jaeger réels | **Fonctionnelle** (externe) |
| Security (`/security`) | Données backend | **Fonctionnelle** |

**Choix : option A** — Administration est réellement fonctionnelle. Aucun élément mock, aucune route fantôme, aucune page conservée « au cas où » ; les liens externes sont explicites.

## Test des actions

| Élément testé | Résultat |
|---|---|
| Mutations Providers+Models (9), Skills (7), Knowledge (9), Agents (5) | ✅ réelles, toast + `invalidateQueries` |
| Tools & MCP : toggle/édition/sync serveur | ✅ `updateToolServer`, `POST /v1/tools/servers/{id}/sync` |
| Notes (échantillon Pilotage) : CRUD + recherche | ✅ API réelle |
| Dialogs : Escape, focus trap, tab cycling, close | ✅ `src/components/ui/dialog.tsx` |
| Sidebar : replier/déplier, New Chat, Ctrl+K, tooltips | ✅ aria-labels complets |
| Settings : toggles booleans, inputs, save | ✅ dirty check + toasts |
| Mock data | ✅ 0 (seul hit : commentaire « Pas de mock ») |

## Éléments volontairement conservés

- Warning lint `no-img-element` sur le logo ANFSI (overlay de transition, `<img>` volontaire).
- Pages Pilotage sans overflow propre (scroll global suffisant, layouts flex internes préservés).
- Onglet MCP accessible depuis deux entrées (`/tools#mcp` et nav) — hash URL supporté.

## Éléments masqués ou retirés

- **Switch sur les modèles découverts** (Settings → Models) — retiré car sans capacité backend (404) ; remplacé par « Géré par {provider} · état ».
- Aucune fonctionnalité supprimée, aucune page masquée : tout le menu correspond à des capacités réelles.

## Dette UX restante

1. Intégrer les migrations PostgreSQL 003/006 dans `init.sql` (dette infra, hors WebUI).
2. Une future vue « Logs ETHAN natifs » devra être une capacité Runtime exposée via API, pas un scrape Grafana côté WebUI.
3. Clés de config General en `font-mono` brut sans labels humains — acceptable en vue admin, à enrichir pour des non-techniciens.

---

## Verdict : **PASS**

Les problèmes réellement identifiés (scroll Providers/Skills, faux switch Models, états illisibles, labels General) ont été corrigés, validés (`tsc` 0 erreur, build OK, 6 suites/12 tests, 18/18 routes 200) et déployés sur le conteneur `ethan-ui:3001`.

| Providers | État par provider (`{type} · {status}`) | ✅ |
| Knowledge / RAG / Skills / Agents / Tools / MCP | Descriptions FR en place | ✅ état live + lien vers le workspace dédié (pas de duplication Core) |
