# WebUI — Refonte Settings « honnête » (anti-fantôme)

> **Date** : 2026-09-30
> **Rôle** : Lead Product Architect + Senior UX Engineer
> **Périmètre** : `interfaces/webui` uniquement — **aucune modification Core**
> **Règle appliquée** : AGENTS.md — « Les interfaces révèlent ETHAN ; elles ne le
> définissent pas » ; une capacité existe dans Core/Runtime **avant** d’être exposée.

---

## 1. Problème constaté (preuves)

L’audit route ↔ composant ↔ API ↔ Core a mis en évidence des **écrans fantômes**
dans Settings : des formulaires qui *ressemblent* à de la configuration mais qui
n’écrivent rien de consommé par le système.

Preuves :

1. `settings-sections.tsx` contenait des contrôles purement locaux :
   - Chat : « Default Chat Mode » (`Standard/Creative/Precise` — **n’existent pas**
     dans le Core, qui connaît `plan/act/debug`), « Message History », « Auto-save Drafts » ;
   - AI : « Default Model » (`gpt-4`, `claude-3`, `llama-3` — valeurs inventées),
     « Temperature », « Max Tokens », « Streaming » ;
   - Search / Library / Reminders / System / Security / Advanced : mêmes patterns
     (selects statiques, toggles locaux) — dont « Two-Factor Authentication »,
     « API Key Rotation » (**fausse sécurité côté UI**), « Telemetry », « Custom CSS ».
2. `GeneralSection` éditait `GET/PUT /v1/settings`… dont la réponse n’est consommée
   par **aucun** sous-système Core (le router `interfaces/api/routers/v1.py` est le
   seul consommateur de `get_settings`/`update_settings`).
3. Les libs `lib/api/search.ts` (`/v1/search`) et `lib/api/reminders.ts` (`/reminders`)
   étaient **orphelines** : le Core expose ces capacités réelles, l’UI ne les utilisait pas.
4. `settings-nav` exposait 24 sections dont 3 sans capacité réelle derrière
   (`general`, `ai`, `advanced`) — d’où un menu redondant « Models / AI Models / LLM ».

---

## 2. Décisions (une source de vérité par capacité)

| Section | Avant | Après |
|---|---|---|
| **general** (Preferences) | Éditeur brut du record `system`/`llm` d’un store Core non consommé | **Supprimée** (aucun objectif utilisateur réel) |
| **ai** (Advanced) | Faux Default Model / Temperature / Max Tokens / Streaming | **Supprimée** (doublon de Providers/Models ; rien à brancher) |
| **advanced** (Experimental) | Experimental / Debug Mode / Custom CSS | **Supprimée** (aucune capacité réelle) |
| **chat** | Modes inventés + faux réglages | **Rebranchée** : store `chat-mode` réel (Plan/Act/Debug + effort de raisonnement), déjà envoyé au Core dans le payload chat (`mode`, `reasoning_effort`) |
| **search** | Faux Default Type / Limit / Fuzzy | **Rebranchée** : console réelle `/v1/search` + types `/v1/search/types`, états explicites |
| **reminders** | Faux Timezone / Sound / Auto-dismiss | **Rebranchée** : CRUD réel `/reminders` (liste, créer, activer/désactiver, supprimer), fuseau navigateur affiché, planification 100 % Core |
| **library** | Faux Default View / Auto-refresh / Preview | **Rebranchée** : préférence d’affichage **persistée et consommée** par `/library` (`library.store`) + lien workspace |
| **system** | Faux Log Level / Max Workers / Telemetry | **Rebranchée** : santé réelle `/health/detailed` + diagnostics + liens Diagnostics/Monitoring/Logs ; note explicite « paramètres de déploiement (env Core), jamais à chaud » |
| **security** | Faux toggles 2FA / Session Timeout / API Key Rotation | **Rebranchée** : statut réel 2FA (`/auth/2fa/status`) + résumé `/security/status` + lien vers le workspace `/security` (qui possède déjà tous les flux) |

Sections **conservées telles quelles** (déjà réelles et Core-backed) :
`providers`, `models`, `routers`, `speech`, `knowledge`, `rag`, `embedding`,
`vector-db`, `chunking`, `reranking`, `skills`, `integrations`, `capabilities`,
`appearance` (thème/accents), `shortcuts` (registre UI réel).

### Arborescence Settings validée (21 sections, 8 groupes)

```
General       chat · reminders · shortcuts · library
AI            providers · models · routers · speech
Knowledge     knowledge · rag · embedding · vector-db · chunking · reranking · search
Skills        skills
Integrations  integrations
Security      security
Appearance    appearance
Advanced      system · capabilities
```

Aucun libellé redondant (Models / AI Models / LLM / Model Configuration) :
`Models` reste la source unique ; l’ancien « LLM » disparaît avec `general`/`ai`.

---

## 3. Règles UX appliquées

- **Objectif clair** par écran : chaque section énonce ce qu’elle révèle ou règle.
- **États explicites** : chargement, vide, erreur, dégradé — jamais de valeur simulée.
- **Une seule source de vérité** : les surfaces gérées dans un workspace dédié
  (providers, models, 2FA, utilisateurs, audit…) sont **révélées + liées**, jamais dupliquées.
- **Pas de logique métier frontend** : les mutations passent par les endpoints Core existants.
- **Pas de fausse sécurité UI** : la section Security ne propose plus aucun toggle ;
  elle affiche l’état réel et délègue la gestion au workspace `/security`.
- **Port 3001 maintenu** : `dev`/`start` (`package.json`), `playwright.config.ts`.

---

## 4. Scénarios de validation (1 → 10)

| # | Scénario | Couverture |
|---|---|---|
| 1–2 | Créer un Project → le retrouver comme contexte du chat | E2E `scenarios.spec.ts` (écriture réelle Core **auto-nettoyée** : `DELETE /v1/projects/{id}`) |
| 3 | Changer de modèle depuis le chat | E2E `scénario 3` (ModelSelector compact) |
| 4 | Changer d’agent depuis le chat | E2E `scénario 4` (AgentSelector header, skip propre si le Core n’expose aucun agent) |
| 5 | Ajouter un fichier (upload Core) | E2E `scénario 5` (`data-testid="chat-file-input"`) |
| 6 | Rechercher dans Knowledge | E2E `scénario 6` + section Search (tests unitaires) |
| 7 | Configurer un provider | E2E `scénario 7` + `settings-providers-reveal-only.test.tsx` |
| 8 | Connecter une intégration | E2E `scénario 8` (Settings → Integrations) |
| 9 | Gérer un skill | E2E `scénario 9` |
| 10 | Revenir au chat | E2E `chat.spec.ts` (lien « Retour au chat ») |

Les specs E2E sont **skippées proprement** sans `ETHAN_E2E_EMAIL`/`ETHAN_E2E_PASSWORD`
et nécessitent la stack Core + WebUI sur 3001.

**Campagne réelle exécutée le 2026-09-30** (compte dédié créé via `POST /auth/register`,
stack Docker + WebUI dev) : **19 passed / 1 skipped / 0 failed** — le skip est le
scénario 4, légitime (`GET /v1/agents` → `[]` sur le Core de dev). Le scénario 3
(modèle) passe avec les 479 modèles exposés par le Core ; le projet créé par le
scénario 1–2 est supprimé en fin de test (vérifié : `GET /v1/projects` → `[]`).

---

## 5. Périmètre vérifié (déjà livré, non modifié)

- **Chat-centré** (`app/page.tsx`) : nouveau chat (sidebar), sélection Project
  (`ProjectSelector`), modèle (`ModelSelector` compact), agent (`AgentSelector`),
  mode Plan/Act/Debug + effort de raisonnement (`ChatModeToggle`), pièces jointes
  (upload Core `/files/upload`, `file_ids`), contexte des capacités
  (`ChatContextBar` : tools/skills/knowledge/plugins/mémoire).
- **Project** (`project-workspace.tsx`) : Instructions, Fichiers (RAG Core),
  Conversations (ChatStore, scope `project_id`), Configuration (provider, model,
  agent, knowledge, skills, tools) — défauts appliqués par le Core.
- **Navigation** : sidebar conversation-first (`nav-config`), taxinomie secondaire
  Settings, palette Ctrl+K, zéro href dupliqué (testé).

---

## 6. Fichiers modifiés

**Ajoutés**
- `interfaces/webui/src/store/library.store.ts`
- `interfaces/webui/tests/unit/settings/settings-chat-defaults.test.tsx`
- `interfaces/webui/tests/unit/settings/settings-reminders.test.tsx`
- `interfaces/webui/tests/unit/settings/settings-search-console.test.tsx`
- `interfaces/webui/tests/unit/settings/settings-system-security.test.tsx`
- `interfaces/webui/tests/unit/settings/settings-library-pref.test.tsx`
- `interfaces/webui/tests/unit/library/library-view-preference.test.tsx`

**Modifiés**
- `settings-nav.ts` (3 ids fantômes retirés), `settings-workspace.tsx`
  (SECTIONS/dispatch, `GeneralSection` supprimée, défaut = Chat)
- `settings-sections.tsx` (**réécrit** : sections réelles uniquement)
- `library-workspace.tsx` (préférence partagée + `aria-pressed`)
- `lib/api/diagnostics.ts` (`fetchDetailedHealth` — le 503 dégradé reste lisible)
- `tests/e2e/scenarios.spec.ts` (scénarios 3 → 9)
- tests settings existants (mocks `use-settings` retirés)

**Supprimés** (orphelins)
- `components/features/settings/hooks/use-settings.ts`
- `lib/api/settings.ts`

---

## 7. Validation

```bash
cd interfaces/webui
npx tsc --noEmit     # exit 0
npx jest             # 49 suites / 292 tests ✅
npx eslint src       # 0 erreur (warnings préexistantes non liées)
npx playwright test --list tests/e2e/scenarios.spec.ts   # 8 tests listés

# Campagne E2E réelle (stack Docker + WebUI dev) :
ETHAN_E2E_EMAIL=… ETHAN_E2E_PASSWORD=… npx playwright test   # 19 passed / 1 skipped
```

**Durcissements issus de l’exécution réelle (2026-09-30)** :
- course d’hydratation React en mode dev (le premier `fill`/`Ctrl+K` pouvait
  précéder le montage : champs contrôlés réinitialisés, aucun POST
  `/auth/login`) → helper `fillStable()` (`support/auth.ts`) + retry clavier
  Ctrl+K (`app.spec.ts`) ;
- attente des listes Core asynchrones avant comptage (modèles/agents) : le
  scénario 3 ne se « skippe » plus à tort pendant le chargement ;
- budget `expect` global porté à 10 s (`playwright.config.ts`) pour absorber la
  compilation Next à froid en dev (sans masquer les régressions) ;
- scénario 1–2 auto-nettoyé (suppression par id, repli par nom si l’échec
  survient avant la navigation) — plus aucun résidu dans le Core de dev.

**Note d’exploitation (stack)** : le bus NATS exige `NATS_TOKEN` et les images
`api`/`kernel` embarquent le code — après un changement de `core/bus/`, il faut
`docker compose build api kernel && docker compose up -d api kernel`, sinon
l’API boucle en `nats: Authorization Violation` (image périmée sans
`nats_connect_options`).

Limites connues :
- le record Core `/v1/settings` (store historique) n’est **plus éditable depuis
  l’UI** ; il est désormais **déprécié côté Core** (`deprecated=True` + ADR-3007)
  et sa suppression est tracée par une RFC dédiée (rupture de contrat ADR-3006) ;
- les E2E interactifs (3/4/5) restent conditionnés au Core réel : skip documenté
  quand le Core n’expose ni modèle alternatif ni agent (ex. scénario 4 sur le
  Core de dev, `GET /v1/agents` → `[]`).


