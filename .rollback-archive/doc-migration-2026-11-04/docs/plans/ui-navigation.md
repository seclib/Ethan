# ETHAN WebUI — Navigation Refondue (style Open-WebUI)

> **Portée** : refactorisation frontend de la navigation principale uniquement.
> **Aucune modification** de Core, Runtime, API, modèles de données ou logique métier.

---

## Objectif

Rendre **toutes** les fonctionnalités existantes d'ETHAN **faciles à découvrir** via une sidebar unique, toujours visible, repliable, avec une hiérarchie claire et des groupes logiques — inspirée du principe Open-WebUI.

Structure livrée :

```
CHAT            BUILD            PILOTAGE              CONFIGURATION      ADMINISTRATION
  New Chat        Agents           Dashboard & Mémoire   Fournisseurs       Sécurité
  Conversations   Modèles          Missions              Paramètres
                  Skills           Calendrier            Deep Research
                  Connaissances    Notes                 Cookbook
                  Outils & MCP     Boîte mail
```

Règle anti-fantôme : seules des routes réellement implémentées sous `src/app/**/page.tsx` figurent dans la nav — **aucune** route inventée (`/admin`, `/diagnostics`, `/logs`, `/monitoring` n'existent pas dans le code et ne sont pas référencées ; leur ajout suivra la RFC administration). Repositionnements : Memory exposé via `/workspace` (« Dashboard & Mémoire »), MCP via `/tools` (« Outils & MCP »). `/register` existe mais reste hors nav (parcours auth).

---

## Taxinomie (`nav-config.ts`)

Un **seul** fichier `NAV_SECTIONS` définit la navigation — consommé par la sidebar (`AppSidebar`) ; `GlobalCommandPalette` lit toujours `NAV_ITEMS_FLAT` (dette connue : dérivation palette à finaliser, voir §Dette).

### v3 — structure Open-WebUI (conversation-centric)

| Section | Items → routes | Collapsible |
|---|---|---|
| **Conversations** (dedicated) | liste des chats persistée via `chat-sidebar.store` (épinglés, groupage par période, recherche locale, rename/pin/delete) — visible sur **toutes** les pages | — |
| **Explore** (`explore`) | Agents→`/agents`, Models→`/models`, Knowledge→`/knowledge`, Tools & MCP→`/tools`, Skills→`/skills` | ✅ |
| **Pilotage** (`operate`) | Missions→`/missions`, Calendar→`/calendar`, Notes→`/notes`, Inbox→`/inbox`, Deep Research→`/research`, Cookbook→`/cookbook` | ✅ |
| **Settings** (`settings`) | Providers→`/providers`, Memory→`/workspace` (dashboard ETHAN conservé et repositionné), General→`/settings` | ✅ |
| **Administration** (`admin`) | Diagnostics→`/diagnostics` (nouvelle page sur l'endpoint réel `/health/detailed`), Monitoring→Grafana `:3002` (lien externe réel, Prometheus/Loki/Jaeger), Security→`/security` | ✅ |

Anti-fantôme v3 : **Logs** et **Interface** n'ont pas de page dédiée — Logs est couvert par Grafana/Loki via le lien Monitoring, les réglages d'interface vivent dans `/settings` (General). Rien n'a été inventé ; rien n'a été supprimé : les capacités ETHAN sans équivalent Open-WebUI sont repositionnées sous **Pilotage** (Missions, Calendar, Notes, Inbox, Deep Research, Cookbook).

<!-- DOC-1 -->

---

## Fichiers modifiés

| Fichier | Modification |
|---|---|
| `src/components/layout/nav-config.ts` | Ajout `collapsible?: boolean` + `href?: string` sur `NavSection` ; 3 groupes marqués collapsible |
| `src/components/layout/sidebar.tsx` | **Réécriture complète** : `IconRail`/`Sidebar` supprimés ; `AppSidebar` prend `(expanded, onToggle)` ; fusionne Chats + Navigation dans un arbre ; sections collapsible ; `UserBar` exportée avec `(expanded?)` + bouton logout |
| `src/app/layout.tsx` | Import `useUIStore` ; `<AppSidebar expanded onToggle />` ; masque `<AppHeader>` sur `/` |
| `src/app/globals.css` | Nouveaux sélecteurs `.sidebar-nav-*`, `.sidebar-user-bar`, `.user-bar-btn` |
| `src/components/layout/nav-config.ts` *(v2)* | Regroupement en 4 sections `build` / `operate` / `configure` / `admin` ; imports d'icônes ajustés (`Network` retiré, `Settings` ajouté) ; toutes les `href` pointent sur des routes réelles `src/app/**/page.tsx` |
| `src/components/layout/sidebar.tsx` *(v2)* | Bloc replié enrichi : bouton New Chat inséré en tête du rail + rail d'icônes construit directement depuis `NAV_SECTIONS.flatMap(...)` avec tooltips natifs (`title`/`aria-label`) ; classes actives `bg-accent/10 text-accent`, idle hover `hover:bg-bg-2` (tokens Tailwind existants) |

**Consommateurs existants (pas de changement)** :
- `GlobalCommandPalette` — lit `NAV_ITEMS_FLAT` (inchangé).
- `ui.store.ts` — persiste `sidebarExpanded` dans localStorage (`ethan-ui-storage`).

---

## Comportement

### Sidebar
- Collapsable via burger/hors-écran/Échap ; `sidebarExpanded` persisté.
- <768px → replié par défaut.
- **Mode replié (rail 60 px)** : bouton **New Chat** proéminent en tête (fond accent, fallback `window.location.href="/"` si aucun handler chat fourni par la page), puis une icône par item de `NAV_SECTIONS` (toutes sections confondues, ordre flat) avec tooltip natif `title` + `aria-label` ; état actif `bg-accent/10 text-accent`, hover `bg-bg-2` ; `UserBar` compacte conservée en pied.
- **Mode développé** : les items d'un groupe ne sont rendus que si le groupe est ouvert (`openGroups[section.id] ?? false`) → au tout premier rendu SSR sans localStorage, seuls les en-têtes de section apparaissent avec `aria-expanded="false"` ×4 ; l'état ouvert/fermé est ensuite persisté côté client.
- Le bouton New Chat n'existe qu'en mode replié (en mode développé, « Nouvelle conversation » vit dans le groupe Chat/Conversations).
- **v3 — conversation-centric** : `chat-sidebar.store` conserve les DONNÉES de conversations quand la page chat est démontée (seuls les handlers sont débranchés) → la liste reste visible sur toutes les pages. Clic sur une conversation hors page chat → `pendingChatId` dans le store + navigation vers `/` ; la page chat ouvre la conversation au montage.
- Header de section actif si **une des routes** du groupe est active (`items.some(...)`).
- Lien externe (Monitoring → Grafana) : `<a target="_blank">` + icône `ExternalLink`, en mode étendu comme replié.
- Classe `sidebar-collapsed` sur `<html>` pour CSS global.
- Sur `/` → groupe **Conversations** (New Chat, recherche, épinglés, groupage par période, actions item).
- Navigation permanente (3 groupes collapsible) **toujours visible**, même sur `/`.
- Route active → item et section header en surbrillance accent.
- Groupe de la route active → ouvert automatiquement au montage.

### UserBar
- Avatar + nom `useAuth`. Boutons : ⚙️ `/settings`, ↪ logout.

### Agent ↔ Model
Restent **dans `assistant-top-bar.tsx`** (chat header). La sidebar n'a pas de sélecteur. Règles Core respectées : défauts agent < choix utilisateur, UNION skills/knowledge/tools.

<!-- DOC-2 -->

---

## Validation exécutée

| Contrôle | Commande | Résultat |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | ✅ exit 0 |
| ESLint | `npx next lint` | ✅ No errors/warnings |
| Jest | `npm test -- --watchAll=false` | ✅ 6 suites, 12/12 PASS |
| Dev server | `npm run dev` | ✅ compilation OK |
| All routes | curl 18 routes (avec cookie) | ✅ toutes 200 |
| Sidebar DOM | grep SSR | ✅ `sidebar-nav-section-header`, `sidebar-nav-item`, `sidebar-user-bar`, `user-bar-btn` |
| Header conditionnel | grep `app-header` | ✅ absent sur `/` · présent sur `/workspace` |

> Port de dev : **3001** (normalisé via les scripts officiels `./ethan webui` — cf. `port_registry.json` ; l'historique 3003 correspond à un run antérieur avant normalisation des ports).

### Re-validation v2 — sidebar 4 groupes + rail replié

| Contrôle | Commande | Résultat |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | ✅ exit 0 |
| ESLint | `npx next lint` | ✅ No ESLint warnings or errors |
| Jest | `CI=1 npm test -- --watchAll=false` | ✅ 6 suites, 12/12 PASS |
| Routes sans cookie | curl sur 18 routes | ✅ `/login` + `/register` = 200 ; `/` et les 15 routes protégées = 307 → `/login?redirect=…` (comportement attendu du middleware) |
| Routes protégées sondées | curl `-H 'Cookie: ethan_token=probe'` | ✅ `/workspace` = 200 (le middleware edge ne vérifie que la présence du cookie ; JWT validé côté FastAPI) |
| SSR DOM v2 | grep occurrences sur HTML minifié de `/workspace` | ✅ `>Build<`, `>Pilotage<`, `>Configuration<`, `>Administration<` ×1 chacune ; `aria-expanded` ×4 (= 4 groupes collapsibles) ; `.sidebar-nav-group` présent |
| Rendu conditionnel des items | mêmes greps | ✅ 0 lien d'item (`/agents`, `/missions`, `/security`) au premier rendu SSR — cohérent avec `openGroups ?? false` (groupes fermés tant que localStorage vide) |

Anti-règlement grep : le HTML servi est minifié (une ligne), utiliser `grep -o … \| wc -l` et jamais `grep -c` qui compte les lignes. Les occurrences isolées « Missions »/« Paramètres » proviennent du contenu même de la page Dashboard, pas de la nav.

---

### Re-validation v3 — sidebar Open-WebUI conversation-centric

| Contrôle | Commande | Résultat |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | ✅ exit 0 (après fix header actif : `section.href` → `items.some(...)`) |
| ESLint | `npx next lint` | ✅ 0 warning/error |
| Jest | `CI=1 npm test -- --watchAll=false` | ✅ 6 suites / 12 tests PASS |
| Build production | `npx next build` (.next propre, dev server stoppé) | ✅ (voir log — 0 erreur) |
| Routes | curl ×19 sur :3001 | `/login`,`/register` 200 ; `/` + 16 protégées 307→login (dont `/diagnostics`, nouvelle) ; probe cookie `/diagnostics` + `/workspace` 200 |
| SSR DOM | grep HTML | nav v3 (labels EN Explore/Pilotage/Settings/Administration) + page Diagnostics rendue |

---

## Risques de régression

| Risque | Mitigation |
|---|---|
| Suppression d'IcôneRail (recherche Ctrl+K) | `GlobalCommandPalette` reste monté dans le layout — accès préservé |
| Signature `AppSidebar()` → `(expanded, onToggle)` | `layout.tsx` mis à jour ; aucun autre consommateur |
| `UserBar` exportée mais inconnue | export simple, réutilisable |
| CSS `.icon-rail*` orphelin | conservé (non supprimé) — inertie mais pas de rupture |

---

## Dette connue (v2)

| Élément | État | Suivi |
|---|---|---|
| Palette Ctrl+K (`GlobalCommandPalette`) | liste de routes encore en dur, divergente de `NAV_SECTIONS` | à dériver de `NAV_ITEMS_FLAT` pour source unique |
| CSS mort `.icon-rail*` dans `globals.css` | conservé par prudence (inerte) | purge en même temps que la dérivation palette |
| Bouton New Chat replié sans handler | fallback `window.location.href="/"` | acceptable ; les pages chat fourniront `chatState.onNewChat` |
| Monitoring = lien externe `http://localhost:3002` | dépend du runtime Grafana (`docker-compose.observability.yml`) | port documenté dans `port_registry.json` ; page interne possible plus tard |
| « Interface » (OWUI Settings) | fusionné dans General (`/settings`) | créer un tab dédié si la page settings éclate ses sections |
| Palette Ctrl+K | items EN datés vs nav v3 | dériver de `NAV_ITEMS_FLAT` (dette existante, renforcée par le renommage EN) |

---

## Hors périmètre

- Créer des routes fictives — toutes pointent sur des routes existantes.
- Refaire l'interface de création d'agents — `+ Agents` ↔ `/agents` existante.
- Déplacer logique métier (providers/agents/memory/RAG) côté front.
- Modifier Core/Runtime/API ou les modèles de données.

*Document de conception — implémentation frontend validée par tsc/lint/jest + tests SSR.*


