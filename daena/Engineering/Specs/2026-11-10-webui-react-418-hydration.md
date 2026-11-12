# WebUI — Résolution React #418 (Hydration Mismatch)

> **Date** : 2026-11-10
> **Périmètre** : `interfaces/webui` uniquement — **aucune modification Core**
> **Statut** : terminé et validé (build Next.js + build Docker + vérification navigateur)

---

## 1. Symptôme

Build Docker de l'image `ui` en échec :

```text
useSearchParams() should be wrapped in a suspense boundary at page "/404"
Error occurred prerendering page "/_not-found"
```

Et, en production (image déjà construite), sur les routes `/login`, `/tools` et
la page 404 :

```text
Minified React error #418; visit https://react.dev/errors/418?args[]=text&args[]=
```

React #418 = « Hydration failed because the server rendered **text** didn't match
the client ». L'argument `text` désigne une divergence de **contenu textuel**
(sixième argument de l'URL React : le type d'élément divergant).

---

## 2. Cause racine (démontrée, pas supposée)

### 2.1 Un composant calculait `new Date()` pendant le rendu

`src/app/(auth)/login/components/top-bar.tsx` et
`src/app/(auth)/login/components/status-panel.tsx` initialisaient leur état
ainsi :

```tsx
const [utcTime, setUtcTime] = useState(formatUTC(new Date()));
```

`/login` est une route **prérendue statiquement** (`○ /login` dans la table de
build). Le serveur fige donc l'heure **au moment du build** dans le HTML, alors
que le client la recalcule **à l'hydratation** → divergence de texte.

Preuve directe dans le HTML prérendu produit par le build :

```text
$ node -e "console.log(require('fs').readFileSync('.next/server/app/login.html','utf8')
    .match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC/g))"
[ '2026-11-10 09:03:50 UTC', '2026-11-10 09:03:50 UTC',
  '2026-11-10 09:03:50 UTC', '2026-11-10 09:03:50 UTC' ]
```

L'horodatage correspond à l'instant du build (`BUILD_ID` : `13:03:50`).

### 2.2 Preuve causale par expérience contrôlée

En calant l'horloge du navigateur sur l'horodatage **exactement présent dans le
HTML servi**, l'erreur disparaît ; en la décalant, elle apparaît :

| Horloge client | `/login` | `/calendar` |
|---|---|---|
| réelle (≠ build) | ❌ #418 | ❌ #418 |
| calée sur le build | ✅ aucune erreur | ✅ aucune erreur |

Le contenu divergent a été localisé par diff **nœud de texte par nœud de texte**
entre le HTML serveur et le DOM hydraté :

```text
serveur : "2026-11-10 09:06:18 UTC"   @ …>header.fixed.top-0>…>time.text-[11px].font-mono
client  : "2026-11-10 09:22:39 UTC"   @ …>header.fixed.top-0>…>time.text-[11px].font-mono
```

### 2.3 Périmètre réel : `/tools` et la 404 n'étaient pas affectés

Le balayage des 38 routes principales (avec cookie authentifié) ne montre
d'erreur que sur `/login`. `/tools` et la 404 affichaient #418 **uniquement
parce que le middleware les redirige vers `/login`** quand la session est
absente : l'erreur observée était donc celle de `/login`, pas la leur.

### 2.4 Second cas de la même cause : le calendrier

`src/app/calendar/page.tsx` initialisait également `new Date()` pendant le
rendu (mois courant + jour « today »). `/calendar` est elle aussi prérendue
statique (`○ /calendar`) et figeait donc le mois **du build** :

```text
$ node -e "… '.next/server/app/calendar.html' …"
mois dans calendar.html (prérendu statique) : [ 'Novembre' ]
```

Le calendrier échouait donc lui aussi dès que la date de build différait de la
date de visite (bascule de mois) — défaut latent, non visible le jour du build.

### 2.5 Pistes écartées

| Piste | Verdict |
|---|---|
| Thème (light/dark/system) | Écarté : appliqué via `useLayoutEffect` sur `document.documentElement`, jamais dans le HTML. |
| i18n / langue | Écarté : `locale` initialisée à `"en"` côté serveur **et** client ; la détection navigateur n'intervient qu'après le montage. |
| Préférences utilisateur (Zustand `persist`) | Écarté : réhydratées après le montage. |
| `useSearchParams` (correction Phase 3-B) | Écarté : déjà encadré par une frontière `<Suspense>`. |
| Composants aléatoires (`Math.random()`) | Écarté : `dialog.tsx` / `popover.tsx` ne les placent que dans des `useRef` (non rendus). |

---

## 3. Correction appliquée

### 3.1 Module centralisé — `src/lib/hydration-safe-time.ts`

Point d'entrée unique de la WebUI pour toute valeur dépendante du temps :

| Export | Rôle |
|---|---|
| `formatUTC(date)` | formatage UTC lisible, déterministe. |
| `UTC_CLOCK_PLACEHOLDER` | placeholder rendu au premier passage (serveur + client). |
| `useUtcClock(intervalMs)` | horloge UTC : placeholder au premier rendu, heure réelle après le montage, rafraîchissement périodique. |
| `useHydrationSafeToday()` | date du jour : `null` au premier rendu, date réelle après le montage. |

Principe : **le premier rendu client doit être identique au HTML serveur**.
La valeur réelle n'est lue qu'**après le montage**, donc après l'hydratation.

### 3.2 Application

- `top-bar.tsx` / `status-panel.tsx` → `useUtcClock()` (suppression des deux
  `formatUTC(new Date())` dupliqués et de leurs intervalles locaux).
- `calendar/page.tsx` → `useHydrationSafeToday()` ; avant le montage, la page
  rend une grille **vide de structure fixe** (42 cellules) et un libellé de
  mois neutre (`—`) ; navigation entre mois conservée.

### 3.3 Ce qui n'a PAS été fait (conformément au périmètre)

- Aucun `suppressHydrationWarning` ajouté.
- Aucun `force-dynamic` : `/login` et `/calendar` restent **prérendues
  statiquement** (`compute: "static"` dans `prerender-manifest.json`).
- Aucune désactivation de l'hydratation.
- Aucun placeholder arbitraire à la place d'un composant fonctionnel.
- Aucune conversion de layout en composant client.
- Aucune modification des dépendances Next.js / React.
- Hors périmètre et non traités : `window.location.href` (sidebar), `setState`
  en effet, migration middleware → proxy, avertissements de configuration Next.js.

---

## 4. Vérifications

| Contrôle | Commande | Résultat |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | exit 0 |
| Tests ciblés | `npx jest tests/unit/auth --runInBand` | 3 suites / 17 tests ✅ |
| Suite complète | `npx jest --runInBand` | **72 suites / 421 tests ✅** |
| ESLint (fichiers modifiés) | `npx eslint src/lib/hydration-safe-time.ts …` | 0 erreur, 0 warning |
| Build Next.js | `npm run build` | `✓ Generating static pages (61/61)`, **EXIT=0** |
| Build Docker | `docker compose build --progress=plain ui` | `Image ethan-ui Built`, **EXIT=0** |
| Vérification navigateur | Playwright + Chrome, image Docker reconstruite | **0 erreur #418** sur `/login`, `/tools`, `/calendar`, 404, `/` |

### 4.1 HTML prérendu après correction

```text
login.html    → horodatages figés : AUCUN ✅ | placeholders --:--:-- UTC : 4
calendar.html → horodatages figés : AUCUN ✅ | mois figé : AUCUN ✅
```

### 4.2 Comportement fonctionnel préservé (navigateur réel)

```text
/login  → horloges affichées : ["2026-11-10 09:51:11 UTC", "2026-11-10 09:51:11 UTC"]
          <html class="dark"> | lang="fr"
/tools  → thème persisté "light" : class="light", data-theme="light"
          locale persistée "fr" : lang="fr" / dir="ltr"
          libellés nav : ["Agents","Projets","Missions","Calendrier"]
/calendar → mois affiché : "Novembre 2026" | surbrillance "today" : 1
```

### 4.3 Robustesse (horloge client volontairement décalée)

| Horloge client simulée | `/login` | `/calendar` | `/tools` | 404 |
|---|---|---|---|---|
| réelle | ✅ | ✅ | ✅ | ✅ |
| +1 an (`2027-11-10T23:59:59Z`) | ✅ | ✅ | ✅ | ✅ |
| calée sur le build | ✅ | ✅ | — | — |

La correction est donc **insensible à l'écart entre la date de build et la
date de visite** — c'était précisément la cause racine.

---

## 5. Tests de non-régression ajoutés

| Fichier | Couverture |
|---|---|
| `tests/unit/auth/utc-clock-hydration.test.tsx` (12 tests) | rendu serveur == premier rendu client ; pas d'horodatage figé avant montage ; heure réelle après montage ; mise à jour périodique ; nettoyage de l'intervalle ; format UTC stable ; `TopBar` et `StatusPanel` sur le placeholder commun. |
| `tests/unit/auth/calendar-hydration.test.tsx` (4 tests) | pas de mois figé dans le HTML prérendu ; premier rendu client identique au serveur ; mois courant et cellules remplies après montage. |

Les tests utilisent `react-dom/server.node` (build **serveur** de React, celle
qui génère le HTML prérendu) et non une assertion d'absence de message
d'erreur : ils démontrent le comportement attendu.

---

## 6. Limites et risques restants

- **Limite** : la valeur « now » n'est plus disponible dans le HTML statique
  avant l'hydratation. Pour l'horloge c'est invisible (placeholder de largeur
  stable) ; pour le calendrier, la grille est vide pendant la fraction de
  seconde qui précède l'hydratation. C'est le compromis standard entre
  prérendu statique et contenu dépendant du temps.
- **Limite** : le mécanisme `setState` dans un effet est pattern React
  documenté pour ce cas, mais ESLint le signale (`react-hooks/set-state-in-effect`)
  — désactivé **localement et avec justification écrite** dans le fichier.
- **Dette préexistante non traitée** (hors périmètre) : `window.location.href`
  dans la sidebar, deux `setState` en effet, `middleware` déprécié au profit de
  `proxy`, avertissements de configuration Next.js.
- **Origine des autres `console.error` observés** : WebSocket vers l'API
  (`ws://localhost:8000/v1/ws` → 403 sans API) et appels `/api/*` en échec
  faute de backend démarré. Sans rapport avec l'hydratation.

---

## 7. Note de traçabilité

Cette mission a été menée **en parallèle d'une autre session** modifiant la
WebUI (feature « Observatory »). Deux corrections hors périmètre issues de
cette session concurrente ont été nécessaires pour débloquer la validation :

- `src/components/layout/nav-config.ts` : `BookOpen` importé **deux fois**
  (lignes 27 et 32) → erreur TS2300 « Duplicate identifier », bloquante pour
  `tsc`, le build et Jest. Doublon supprimé (l'icône est déjà importée ligne 27).

Aucune modification fonctionnelle de la feature Observatory n'a été touched.
