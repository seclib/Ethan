# ETHAN WebUI — Refonte des pages vers les patterns Open-WebUI

## Objectif

Uniformiser les 8 pages de gestion (Agents, Models, Providers, Knowledge, Skills,
Tools, MCP, Settings) autour du pattern de liste Open-WebUI :

```
Header (titre + description + compteur + action principale)
Recherche / filtres
Liste / grille de cartes
Detail (drawer / dialog quand pertinent)
Actions contextuelles
```

Le backend ETHAN (Core/Runtime/API) et tous les clients API existants sont
**conservés à l'identique** : cette étape ne touche que la couche présentation.

---

## Composant réutilisable créé

`src/components/shared/page-header.tsx` — `PageHeader`

```tsx
<PageHeader
  title="Agents"
  description="…"
  icon={<Bot className="h-5 w-5" />}
  count={agents.length}
  actions={<Button>Nouvel agent</Button>}
/>
```

- Titre + compteur pastille + description
- Section actions à droite (bouton principal)
- Uniformise le haut de toutes les pages refondues

---

## Migration par page

### 1. Agents — `agents-workspace.tsx`
- **Déjà refondu** en grille de cartes (session antérieure) : cartes avec statut,
  provider·model, compteurs capabilities, menu contextuel, actions rapides.
- **Ajout** : `PageHeader` (titre + description + compteur + action « Nouvel agent »)
  au-dessus de la barre de recherche.
- Hooks/data : `useAgents`, `useUpdateAgent`, `useDeleteAgent`, `useExecuteAgent`,
  `useCreateAgent` — inchangés.

### 2. Models — `models-workspace.tsx`
- **Déjà refondu** en grille de cartes avec badges Local/Provider, capabilities,
  disponibilité, menu ⋮, épinglage.
- **Ajout** :
  - `PageHeader` avec compteur + filtre **Favoris** en action ;
  - **correction de cohérence** : le early-return `isLoading` (qui masquait le
    header pendant le chargement) est supprimé — le `PageHeader` est désormais
    toujours visible, avec un loading inline dans la zone de contenu ;
  - recherche `max-w-md` rebassée sous le header.
- Hooks/data : `useModels` (`searchModels`, `pinModel`, `unpinModel`, `isPinned`) — inchangés.

### 3. Providers — `providers-workspace.tsx`
- **Nouveautés** :
  - `PageHeader` avec compteur + action « Ajouter un provider » ;
  - **recherche** (nom, type, URL) — était absente ;
  - **filtres de statut** : Tous / Connectés / Hors ligne ;
  - **empty states** distincts (« aucun provider » vs « aucun résultat »).
- Hooks/data : `useProviders` (CRUD, test connexion, toggle, default) — inchangés ;
  `ProviderFormDialog` conservé.

### 4. Skills — `skills-workspace.tsx`
- **Déjà refondu** en grille de cartes avec recherche, badges, actions
  (toggle/edit/delete/execute), `SkillDialog`/`ExecuteSkillDialog`.
- **Ajout** : `PageHeader` avec compteur + action « Nouveau skill » (remplace le
  `<h1>` isolé).
### 5. Knowledge — `knowledge-workspace.tsx`
- Layout **master-detail** (collections à gauche, documents/détails à droite) :
  adapté au modèle RAG (collection → documents) — conservé.
- Éléments OWUI déjà présents : recherche dans la liste, panneau de détail,
  dialogs (création, renommage, ingestion, moteur RAG).
- **Aucune modification de la logique** — la cohérence du haut de page est
  assurée par le `PageHeader` appliqué aux autres pages.

### 6. Tools — `tools-workspace.tsx`
- Layout **master-detail** avec sections **Available / Configured / MCP** :
  adapté au catalogue d'outils + serveurs MCP.
- Hash URL `#mcp` → ouverture directe depuis la sidebar (déjà en place).
- **MCP est une section de /tools** (pas de page dédiée) ; les serveurs MCP
  sont gérés dans le panneau MCP avec dialogs d'ajout/édition.
- **Aucune modification** nécessaire à cette étape (déjà conforme OWUI).

### 7. MCP
- Absorbé dans **Tools** (`#mcp`) conformément au plan de navigation (pas de
  route fictive `/mcp`). Aucune réimplémentation.

### 8. Settings — `settings-workspace.tsx`
- Layout **navigation par sections** (General, Appearance, Models, Providers,
  Knowledge, RAG, Skills, Agents, Tools, MCP) + panneau de contenu.
- Hash URL `#section` → ouverture directe depuis la sidebar.
- **Conservé tel quel** : la structure correspond au pattern OWUI « admin
  settings », avec sections réelles branchées sur les APIs vivantes.

---

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `src/components/shared/page-header.tsx` | **nouveau** — header de page réutilisable |
| `src/components/features/agents/components/agents-workspace.tsx` | `PageHeader` + description |
| `src/components/features/providers/components/models-workspace.tsx` | `PageHeader` + correction loading |
| `src/components/features/providers/components/providers-workspace.tsx` | `PageHeader` + recherche + filtres statut + empty states |
| `src/components/features/skills/components/skills-workspace.tsx` | `PageHeader` + description |

**Non modifiés** (déjà conformes OWUI) : `knowledge-workspace.tsx`,
`tools-workspace.tsx`, `settings-workspace.tsx`.

---
## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ exit 0 |
| `next lint` | ✅ No ESLint warnings or errors |
| Jest | ✅ 6 suites / 12 tests PASS |
| Routes (10) : `/`, `/agents`, `/models`, `/skills`, `/providers`, `/knowledge`, `/tools`, `/settings`, `/workspace`, `/diagnostics` | ✅ 200 |
| SSR Agents | ✅ `PageHeader` (« Agents ETHAN — personnalités… ») rendu |
| SSR Models | ✅ « Catalogue des modèles LLM », « Favoris », « Rechercher un modèle » rendus |
| SSR Skills | ✅ « instructions structurées », « Nouveau skill » rendus |
| SSR Providers | ✅ « Connexions aux moteurs LLM », « Rechercher un provider », « Connectés », « Hors ligne » rendus |
| Chat `/` | ✅ sélecteur Modèle intact (« Changer de modèle ») |

**Note infra** : le serveur dev (PID antérieur, `next-server` du container
Docker `ethan-ui`) servait un **build figé** sur 3001 ; il a été arrêté via
`docker stop ethan-ui` puis remplacé par le dev server hôte `./ethan webui`
(le container reste en `Exited (0)`, récupérable via `./ethan up`).

---

## Règles respectées

- Aucune modification Core/Runtime/API/backend.
- Aucune réimplémentation métier ; tous les hooks et clients API existants sont réutilisés.
- Aucune route fictive ; MCP reste dans `/tools#mcp`.
- `docs/plans/*` est git-ignoré (ce document n'est pas versionné par défaut).
## Migration v2 — Knowledge & Tools & MCP (PageHeader unifié)

### Knowledge (`knowledge-workspace.tsx`)
- Ancien en-tête local (`<h1>` + actions dispersées) remplacé par `PageHeader` :
  - `title="Knowledge"`, `description="Bases de connaissances, documents et moteur RAG"`
  - `icon=<Database>`, `count={collections.length}`
  - Actions regroupées à droite : bouton **Moteur RAG** (secondary, ouvre le panneau RAG existant) + bouton **Nouvelle** collection (primary, dialog existant)
- Le master-detail collections→documents et tous les dialogs sont inchangés.

### Tools & MCP (`tools-workspace.tsx`)
- En-tête remplacé par `PageHeader` :
  - `title="Tools & MCP"`, `description="Outils du noyau, serveurs MCP et test des capacités"`
  - `icon=<Wrench>`, `count={tools.length + servers.length}`
  - Action **Serveur MCP** (primary, dialog d'ajout existant) déplacée dans le header
- Master-detail (outils builtin / configurés / serveurs MCP) inchangé, hash `#mcp` conservé.

### Validation v2 (exécutée)
| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | exit 0 |
| `next lint` | No ESLint warnings or errors |
| Jest | 6 suites / 12 tests PASS |
| Build Docker `ui` reconstruit | 0 erreur |
| SSR `:3001/knowledge` | 200 — « Knowledge » ×2, « Bases de connaissances, documents et moteur RAG » ✓ |
| SSR `:3001/tools` | 200 — « Outils du noyau, serveurs MCP et test des capacités », « Serveur MCP » ✓ |
| 19 routes | toutes 200 |

Méthode de preuve : chaînes des nouveaux `PageHeader` retrouvées dans `.next/server/app/{knowledge,tools}/page.js` du conteneur reconstruit **et** dans le HTML servi — le build servi sur 3001 est bien le code à jour.

- Hooks/data : `useSkills` — inchangés.