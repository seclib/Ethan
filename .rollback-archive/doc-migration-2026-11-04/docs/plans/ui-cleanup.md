# Nettoyage Frontend ETHAN WebUI — Rapport

Date : 29/08/2026 · Périmètre : `interfaces/webui/src` uniquement · Backend/Core/Runtime : **intacts**

## 1. Cartographie des doublons (avant suppression)

| Candidat | Dépendances vérifiées | Décision |
|---|---|---|
| `components/shared/virtual-list.tsx` | **0 importeur** (`src/` + `tests/`) | 🗑 Supprimé |
| `components/ui/index.ts` (barrel) | **0 importeur** — imports directs `@/components/ui/x` partout | 🗑 Supprimé |
| CSS `.btn`, `.btn-primary`, `.btn-ghost`… | 0 usage après migration `diagnostics` → `<Button>` | 🗑 Blocs CSS supprimés |
| CSS `.modal-header/.modal-body/.modal-footer/.close-btn` | 0 usage (Dialog UI utilisé partout) | 🗑 Blocs CSS supprimés |
| `.icon-rail*` (dernier usage : `inbox`) | migré vers `<Button variant="ghost" size="icon">` | CSS à purger (voir §4) |
| IconRail / ancienne sidebar composant | déjà supprimés sessions précédentes (v2) | ✅ déjà fait |
| Anciens selectors | aucun doublon : un seul `AgentSelector`, un seul `ModelSelector` | ✅ rien à faire |
| Mock data | aucune donnée mockée détectée (listes réelles via hooks React Query) | ✅ rien à faire |
| Stores/hooks inutilisés | `ui.store`, `chat-sidebar.store`, tous les hooks features = consommés | ✅ conservés |
| Routes orphelines | 15 routes nav-config ↔ 17 `page.tsx` réels ; `/diagnostics` référencée | ✅ aucune suppression |

**Règle respectée** : aucune suppression sans vérification grep croisée (`src` + `tests`) + `tsc --noEmit` vert.

## 2. Fichiers supprimés

```
interfaces/webui/src/components/shared/virtual-list.tsx
interfaces/webui/src/components/ui/index.ts
```

## 3. Fichiers modifiés (migration legacy → design system)

| Fichier | Changement |
|---|---|
| `src/app/globals.css` | Suppression blocs `.btn*` et `.modal*` orphelins (~-90 lignes) |
| `src/app/diagnostics/page.tsx` | `.btn .btn-ghost` → `<Button variant="ghost" size="icon">` |
| `src/app/inbox/page.tsx` | `.icon-rail-btn` → `<Button variant="ghost" size="icon">` + import |
| `src/app/notes/page.tsx` | textarea legacy → classes harmonisées design system |
| `src/app/research/page.tsx` | input/select legacy → classes harmonisées |
| `src/app/security/page.tsx` | select legacy → classes harmonisées |

## 4. Dette restante (sciemment conservée)

- **`.icon-rail*` CSS** : définitions encore présentes dans `globals.css`, plus aucun usage TSX — purgables sans risque (prochain passage CSS).
- **Palette Ctrl+K** : entrées de navigation en dur, à dériver de `NAV_ITEMS_FLAT`.

## 5. Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ exit 0 |
| `next lint` | ✅ No ESLint warnings or errors |
| Jest | ✅ 6 suites / 12 tests PASS |
| `next build` production | ✅ 0 erreur, 23 pages générées, `/diagnostics` incluse |
| Routes (build réel) | ✅ `/diagnostics` 200 + SSR « Santé des services/Actualiser » ; `/agents` `/workspace` `/tools` `/settings` 200 (validé sur serveur de test temporaire 3011, arrêté après) |
| Référence 3011 | ✅ aucune dans le code/config (port officiel inchangé : 3001) |

## 6. ✅ Bloquant runtime RÉSOLU — port 3001

**Diagnostic final** : le processus `next-server (v15.5.23)` vu comme `root` (PID 206576) était en réalité **le processus à l'intérieur du conteneur Docker `ethan-ui`** (visible comme root depuis l'hôte, restart=unless-stopped). Aucun sudo n'était nécessaire.

**Cause du 404 `/diagnostics`** : l'image `ethan-ui:latest` datait de 47 h (ancien build sans la route).

**Résolution (procédure officielle compose) :**
```bash
docker compose build ui      # image reconstruite avec le code actuel (cache Docker, ~90 s)
docker compose up -d ui      # conteneur recréé : ethan-ui Up (healthy) 127.0.0.1:3001->3000/tcp
```

**Vérifications sur :3001 (conteneur à jour) :**
- 19/19 routes **200** (dont `/diagnostics` 200 + SSR « Diagnostics / Santé des services / Actualiser »)
- Proxy API : `/api/v1/settings` → 401 (backend :8000 atteint, auth requise — attendu)
- CSS servi (`/_next/static/css/b42c40952c78b41d.css`, 60 Ko) contient : `Inter`, `--sidebar-bg`, `--bg-rgb:23 23 27` (dark neutre), `.sidebar-new-chat` → **design system Open-WebUI actif en production conteneurisée**
- Chaîne complète validée : `navigateur → :3001 (ethan-ui) → /api/* → ethan-api :8000 → Core/Runtime`

## VERDICT FINAL : **PASS**

ETHAN WebUI tourne officiellement sur `http://localhost:3001` avec le build à jour (design system OWUI + cleanup + page Diagnostics), en mode Docker officiel (`docker compose`, service `ui`).

## 7. Résultat

```
une seule WebUI ✓  une seule navigation ✓  une seule expérience ✓
zéro doublon de code ✓  backend intact ✓  build/lint/tests verts ✓
```
