# Cartographie WebUI → API → Core (préalable obligatoire à la refonte UX)

**Date** : 30/09/2026 · **Périmètre** : `interfaces/webui` · **Core** : inchangé
· **Statut** : arbitré et livré (§6)

> Pourquoi ce document existe. La consigne « consolider les menus / éviter les
> menus redondants » ne peut pas être exécutée sans savoir **ce qui est
> réellement la même chose**. Supprimer ou fusionner sur une intuition, c'est
> casser une capacité. Toute fusion proposée ici est donc adossée à des
> endpoints partagés, pas à des noms d'écran.

## 1. Méthode (reproductible)

Deux lectures croisées, sans serveur ni NATS (import de `app` **sans**
lifespan) :

- **statique** : parsing des modules `src/lib/api/*.ts` (chemins réellement
  appelés par l'interface) ;
- **dynamique** : surface déclarée par `interfaces.api.main.app` (307 routes).

Le rapprochement est désormais **figé par un test** :
`tests/interfaces/test_webui_api_contract.py`. Toute régression de contrat
(route inexistante, préfixe proxy modifié) échoue à l'exécution, avec le module
fautif nommé.

## 2. Convention de transport (à ne pas casser)

`src/app/api/[...path]/route.ts` retire **exactement** `/api` et **rien d'autre** :
le chemin JS est donc le chemin backend.

```
WebUI : apiFetch('/models')  →  proxy /api/models  →  API : GET /models
WebUI : apiFetch('/v1/message') → API : POST /v1/message
```

Il n'y a **pas** de `/v1` automatique : c'est la raison pour laquelle un seul
préfixe erroné casse toute une page en silence (c'est exactement la panne du
Shell : `POST /message` au lieu de `/v1/message`). Le test
`TestProxyContract` verrouille cette règle.

## 3. Résultat de l'audit

| Mesure | Valeur |
|---|---|
| Routes App Router | 42 |
| Routes API déclarées | 307 |
| Chemins appelés par le WebUI | 202 |
| **Chemins fantômes (appelés, inexistants)** | **0** |
| Modules `lib/api` sans aucun appel | 0 |

**Le WebUI n'appelle aucune route inexistante.** Aucune correction d'API n'est
justifiée par cette cartographie : la dette n'est pas là.

## 4. Ce qui est déjà conforme (à ne pas refaire)

Points du cahier des charges **déjà livrés** — les « refaire » serait du bruit :

- **Arborescence Settings** : déjà 8 groupes / 21 sections conformes à la cible
  (`settings-nav.ts`), avec écrans fantômes historiques déjà supprimés
  (cf. `2026-09-30-webui-settings-honesty.md`).
- **Doublon « Models / AI Models / LLM / Model Configuration » : inexistant.**
  Il n'existe que `/providers` et `/models`, distincts et non redondants :
  un provider est un *service* (endpoint, clé, état), un modèle est un *modèle
  servi par* ce service. Les séparer est correct, pas redondant.
- **Projet** : le cahier des charges est **déjà couvert par le Core**
  (`interfaces/api/routers/projects.py` + `core/projects/`) : `instructions`,
  fichiers (`/v1/projects/{id}/documents`), knowledge/collections,
  skills/tools, `agent_id`/`provider_id`/`model` par défaut, et contexte
  d'exécution (`GET /v1/projects/{id}/context`). Rien à ajouter au Core.

## 5. Les deux recouvrements réels (arbitrés : tout consolider)

Recouvrement = **même endpoint Core appelé par deux écrans**. C'est la preuve
de doublon, pas l'intuition.

### 5.1 Knowledge ↔ Library — 5 endpoints partagés

| Endpoint | Knowledge | Library |
|---|---|---|
| `/v1/knowledge` | ✓ | ✓ |
| `/v1/knowledge/collections` | ✓ | ✓ |
| `/v1/rag/documents` | ✓ | ✓ |
| `/v1/projects/{id}/documents` | ✓ | ✓ |
| `/files` (via `files.ts`) | ✓ | ✓ |

`LibraryWorkspace` est explicitement une « vue unifiée » des mêmes APIs que
`KnowledgeHub` : deux surfaces, un seul jeu de données.

### 5.2 Tools ↔ MCP — 2 endpoints partagés

| Endpoint | tools.ts | mcp.ts |
|---|---|---|
| `/v1/tools/servers` | ✓ | ✓ |
| `/v1/tools/servers/{id}` | ✓ | ✓ |
`ToolsWorkspace` et `McpServersWorkspace` sont deux UI sur **la même ressource
Core** (même chemin de code, mêmes appels). La séparation était documentée comme
délibérée dans `nav-config.ts` (« séparation capacités / infrastructure ») :
l'arbitrage l'a réexaminée et a conclu que la distinction utile est celle
entre **l'inventaire des capacités (outils invocables)** et **la configuration
des serveurs qui les fournissent** — les deux restent lisibles, mais dans un
seul écran.

## 6. Arbitrage retenu — « tout consolider »

**Décision produit : on consolide.** Les deux paires partagent des endpoints
Core, donc deux menus pour un seul jeu de données. Principe :

> **une ressource Core → une route canonique ; les anciennes URLs restent
> valides et redirigent.**

Concrètement :

| Avant (2 menus, 2 surfaces) | Après (1 menu, 1 surface, 1 route canonique) |
|---|---|
| `/knowledge` + `/library` | onglet **Library** dans `/knowledge` |
| `/tools` + `/mcp` | onglets **Outils / Serveurs MCP** dans `/tools` |

- `KnowledgeHub` gagne un onglet `Library` ; `ToolsHub` gagne un onglet
  `Serveurs MCP` ;
- l'onglet s'ouvre par query param : `/knowledge?view=library` et
  `/tools?view=mcp`. C'est ce qui permet aux anciennes URLs d'y conduire ;
- `/library` et `/mcp` restent des routes servies (App Router : 42 routes
  maintenues) et **redirigent** vers la surface canonique — aucun signet ni
  lien externe ne casse, et la redirection est visible par le client ;
- sidebar, palette de commandes, raccourcis clavier et lien Settings ne pointent
  plus que vers les routes canoniques ;
- **aucun changement Core** : il ne s'agit que de navigation et de
  présentation, ce qu'AGENTS.md autorise explicitement pour une interface.

## 7. Preuves de la consolidation

| Preuve | Emplacement |
|---|---|
| Contrat WebUI ↔ API (route inexistante, préfixe proxy) | `tests/interfaces/test_webui_api_contract.py` |
| Onglets, `?view=`, et redirections `/library` `/mcp` | `interfaces/webui/tests/unit/mcp/mcp-servers-workspace.test.tsx` |
| Pas de doublon de destination ni de libellé de menu | `interfaces/webui/tests/unit/ui/nav-dedup.test.ts` |
| Redirections réelles + onglet ouvert (navigateur) | `interfaces/webui/probe-e2e.mjs` §6 |

Les tests d'onglets sont **mutation-testés** : neutraliser `aria-current` sur
les onglets ou la cible de `redirect()` fait échouer la suite — ils ne passent
pas par hasard.

État de la validation : **306 tests Jest verts**, `tsc --noEmit` propre,
`npm run lint` sans erreur (61 warnings préexistants), contrat Python
`17 passed`, et `probe-e2e.mjs` en conditions réelles (stack WebUI + API up,
Chromium headless) : **34 OK / 0 échec** — dont la vérification que
`/library` atterrit bien sur `/knowledge?view=library` **avec** l'onglet
« Library » actif, et `/mcp` sur `/tools?view=mcp` avec « Serveurs MCP ».
