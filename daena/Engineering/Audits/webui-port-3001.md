# Migration WebUI ETHAN → port 3001

> **Portée** : changement de port d'exposition de la WebUI (interface Next.js) de 3000 → 3001 uniquement. Aucune modification de Core/Runtime/API.

## Contexte

- Le WebUI est une interface Next.js 15 → le backend ETHAN (FastAPI) tourne sur **8000**.
- En mode **Docker (production)**, le compose racine mappait déjà `127.0.0.1:3001:3000` : le port 3001 était donc la vraie cible, mais la **cohérence** (dev local / scripts / docs / tests / Grafana) était rompue.
- **Conflit détecté & résolu** : Grafana utilisait `GRAFANA_PORT:-3001` → **déplacé sur 3002** pour libérer 3001 à la WebUI.

## Architecture réseau (confirmée)

```
Browser http://localhost:3001
   ↓  (fetch /api/* + cookie HttpOnly)
Next.js dev|prod  ── proxy route.ts ──→  FastAPI localhost:8000 (Core/Runtime)
   ↓
(WebSocket ws://localhost:8000/api/v1/ws — inchangé)
```

→ **Le port 3001 ne touche QUE l'interface**. L'API Core/Runtime reste sur **8000**.

## Fichiers modifiés

| # | Fichier | Modification |
|---|---|---|
| dev | `scripts/cmd-webui.sh` | `PORT="${PORT:-3000}"` → `:-3001` |
| dev | `interfaces/webui/webui.sh` | port 3000 → 3001 (dev + start) |
| docker | `interfaces/webui/docker-compose.yml` | `3000:3000` → `3001:3000` ; healthcheck `:3000` → `:3001` |
| tests | `interfaces/webui/playwright.config.ts` | baseURL 3000 → 3001 (×2) |
| diag | `scripts/cmd-doctor.sh` | `WebUI:3000` → `:3001` + `PORT:-3000` → `:-3001` |
| boot | `tests/test_boot.sh` | `PORTS="…3000…"` → `…3001…` |
| status | `scripts/cmd-status.sh` | URL check 3000 → 3001 (×2) |
| up | `scripts/cmd-up.sh` | proxy check 3000 → 3001 |
| docs | `Obsidian/Engineering/Audits/ethan-launcher.md` | `--port=3000` + `localhost:3000` → 3001 |
| docs | `Obsidian/Engineering/Audits/service-orchestration.md` | « WebUI (port 3000) » → 3001 |
| docs | `Obsidian/Engineering/Audits/auth_flow_audit.md` | `localhost:3000` → 3001 |
| docs | `README.md` | `localhost:3000` → 3001 |
| clash | `docker-compose.observability.yml` | `GRAFANA_PORT:-3001` → `:-3002` |
| ports | `port_registry.json` | grafana `3001`→`3002` ; entrée WebUI `host 3001` |
| code | `interfaces/webui/src/app/api/[...path]/route.ts` | commentaire `:3001` (info cookie) |

**Inchangés (conscients) :**
- `interfaces/webui/Dockerfile` & `deploy/Dockerfile.ui` → `EXPOSE 3000`/`ENV PORT 3000` : **port interne du conteneur**, mappé → 3001 par le compose. Correct.
- `docker-compose.yml` racine → `api` sur **8000** (backend, non déplacé).

## Résultats de validation (act)

| Check | Résultat |
|---|---|
| `npx tsc --noEmit` | exit 0 |
| `npx next lint` | ✔ No ESLint warnings or errors |
| `npx next build` | exit 0 (toutes routes prérendues) |
| Serveur dev écoute | **3001** (307 = redir vers `/login` sur routes protégées ✓) |
| `/login` → SSR | 200 |
| Port 3000 | **libre** (plus utilisé par la WebUI) |
| Proxy API | `/api/v1/*` → FastAPI :8000 ✓ |
| WebSocket | `NEXT_PUBLIC_WS_URL=http://localhost:8000` (inchangé) ✓ |

## Recommandation

`http://localhost:3001` est **le port canonique de la WebUI ETHAN**.

## Refonte du composer (validée en parallèle)

Chaque `QuickAction` (Skills/Tools/Knowledge/Agent) gère désormais son propre
popper via `children` (élimination du popper global `menuRef`/`menuButtonRefs`).

Corrections appliquées sur le chemin des props :
- `page.tsx` : bloc de props du composer (corrompu par une fausse manip regex) → réindenté proprement.
- `assistant-chat.tsx` : ajout au destructuring de `selectedAgentName`, `activeProvider`,
  `activeModel`, `onOpenModelSelector` (étaient déclarées dans l'interface et passées au
  rendu mais absentes de la signature → TS2552/TS2304) + indentation corrigée.

Validation finale de cette étape :
| Check | Résultat |
|---|---|
| `tsc --noEmit` | exit 0 |
| `next lint` | ✔ No ESLint warnings or errors |
| Jest | 6 suites / **12 tests PASS** |
| Serveur **3001** | toutes routes 200 |
| Shell `/` | sidebar + sélecteur Agent rendus |
