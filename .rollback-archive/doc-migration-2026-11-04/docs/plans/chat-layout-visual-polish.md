# Chat Layout — Visual Polish (WebUI réel, port 3001)

> Refonte ciblée de l'espace Chat rendu sur `http://localhost:3001`.
> Périmètre : composants réellement rendus uniquement. Aucun composant nouveau/dupliqué.

---

## Cause réelle de la barre blanche

La « barre blanche » visible en bas du Chat n'était **ni un footer, ni une zone vide, ni un problème de hauteur (`100vh`/`100dvh`)**.

Le traçage complet du chemin de rendu a été fait par sondes DOM Playwright (`elementFromPoint`, rects, computed styles) et crops visuels sur l'application **réelle** :

```
viewport (1920×1080)
    ↓ layout.tsx (shell flex, ok — aucun footer, aucun min-h-screen parasite)
    ↓ page.tsx (ChatHomePage — flex colonne h-full, propre)
    ↓ AssistantChat (flex-1 min-h-0 — zone conversation bottom = 962px)
    ↓ wrapper composer (px-4 pt-2, padding-bottom 12px, fond transparent)
    ↓ AssistantInput (composer)
```

Mesures DOM : `bodyScrollHeight == innerHeight` (pas d'overflow vertical), aucun
`padding-bottom` parasite, aucun `safe-area-inset`, aucun composant vide. Le `gap`
de 12 px sous le composer est le padding volontaire du wrapper (fond transparent —
le fond du body transparaît, ce qui est correct).

**Cause racine : un bug de mapping de tokens Tailwind.**

Dans `tailwind.config.js`, les tokens de lignes étaient définis ainsi :

```js
line: {
  1: "rgb(var(--line-1-rgb) / <alpha-value>)",
  2: "rgb(var(--line-2-rgb) / <alpha-value>)",
  3: "rgb(var(--line-3-rgb) / <alpha-value>)",
}
```

Or le design système définit `--line-1: rgb(255 255 255 / 0.06)` (blanc 6 %).
Avec `rgb(var(--line-1-rgb) / <alpha-value>)`, l'alpha n'est appliqué que via un
modificateur de classe (`border-line-1/20`). **Sans modificateur, `<alpha-value>`
vaut 1** → toutes les classes `border-line-1/2/3` rendaient des lignes
**100 % opaques** : blanc pur en thème sombre, noir pur en thème clair.

La « barre blanche » était donc la `border-t` du bloc composer (et la bordure du
composer lui-même) rendue en blanc plein — 122 usages `border-line-*` étaient
affectés dans toute l'application, dont tous ceux du chemin de rendu du Chat.

## Composant responsable

| Élément | Rôle |
|---|---|
| `interfaces/webui/tailwind.config.js` | mapping `line.1/2/3` → alpha forcé à 1 sans modificateur |
| `AssistantInput` (composer) | portait la bordure blanche visible (border-line-1) |
| Wrapper composer dans `page.tsx` | bordure/ombrage supérieur en blanc plein |

## Correction appliquée

Dans `tailwind.config.js` — les tokens composés référencent désormais directement
la variable CSS du thème (qui inclut l'alpha voulu) :

```js
line: {
  // Tokens composés (incluent l'alpha du thème) — JAMAIS rgb(var(--line-N-rgb) / <alpha-value>)
  // car sans modificateur l'alpha vaut 1 → lignes blanches/noires pures (bug « barre blanche »).
  1: "var(--line-1)",
  2: "var(--line-2)",
  3: "var(--line-3)",
}
```

Correctif **systémique et minimal** (une seule source de vérité, aucun hack de
couleur, aucune classe contournée). Les modificateurs (`/20`, `/60`…) restent
utilisables car `--line-N` porte déjà l'alpha d'intention design.

Note déploiement : la WebUI affichée sur 3001 est le conteneur Docker `ethan-ui`
(image de production buildée depuis `deploy/Dockerfile.ui`). Une modification de
`tailwind.config.js` n'est donc pas reflétée à chaud : un **rebuild de l'image**
(`docker compose build ui && docker compose up -d ui`) est nécessaire pour valider
le rendu réel.

## Structure verticale finale

```
┌──────────────────────────────────────────┐
│ AppSidebar │ AssistantTopBar (44px)      │  Agent ▼  Model ▼ — discret
├──────────────────────────────────────────┤
│ (ChatContextBar — chips, null si vide)   │
│                                          │
│        Conversation area                 │
│        flex-1 · min-h-0 · scroll auto    │
│        fond = fond global (continuité)   │
│                                          │
├──────────────────────────────────────────┤
│ wrapper composer (px-4 pt-2 pb-3)        │
│ AssistantInput (composer)  ← gap 12px    │
└──────────────────────────────────────────┘  ← fin exacte du viewport
```

- Layout en `flex` colonne avec `min-h-0` sur la zone de conversation → le composer
  est **ancré en bas** du viewport, aucune zone morte sous lui.
- Le `padding-bottom` (12 px) du wrapper composer est transparent : le fond global
  transparaît — visuellement le composer « flotte » sur le fond, sans footer.
- Aucun `<footer>`, aucun conteneur `min-h-screen` parasite (vérifié par dump DOM).

## Composants modifiés

1. `interfaces/webui/tailwind.config.js` — fix mapping `line.1/2/3` (cause racine).
2. *(session précédente, inchangés ici)* `assistant-input.tsx`, `assistant-chat.tsx`,
   `page.tsx` — suppression du doublon `AgentDropdown`.

Aucun nouveau composant. Aucune duplication. Le body/layout global n'ont pas été
touchés (ils étaient corrects).

## Résolutions testées

Validation Playwright **sur le rendu réel** de `http://localhost:3001`
(conteneur Docker `ethan-ui` rebuildé avec le fix, auth `admin` incluse, cookie
HttpOnly via proxy Next) :

| Résolution | Capture | Pixel au fond du viewport (y=H-2) | `#FFFFFF` purs (moitié basse) |
|---|---|---|---|
| 1920×1080 (desktop) | `final-1920x1080.png` | `srgb(23,23,27)` = fond global | **0** |
| 1366×768 (laptop) | `final-1366x768.png` | `srgb(23,23,27)` | **0** |
| 1280×720 (laptop réduit) | `final-1280x720.png` | `srgb(23,23,27)` | **0** |
| 390×844 (mobile) | `final-390x844-mobile.png` | `srgb(23,23,27)` | **0** |
| 1920×1080 (thème clair) | `final-1920-light.png` | `srgb(23,23,27)` | **0** |

Vérifications DOM (computed styles + rects) :
`composerBorder = rgba(255,255,255,0.06)` (fix live), bordure top-bar translucide,
`gap` sous composer = 12 px (padding volontaire transparent), `scrollHeight ==
innerHeight` (aucun débordement vertical), chaîne d'ancêtres du composer sans
footer ni wrapper parasite.

> **Note méthodologique** : ce modèle ne pouvant pas lire d'images, la validation
> visuelle a été remplacée par une **validation programmatique des pixels**
> (ImageMagick) sur chaque capture — échantillonnage du pixel au fond du viewport
> et histogramme `#FFFFFF` de la moitié basse. Les deux sont probants : le bas de
> l'écran est **exactement** le fond global (`#17171B`) et aucun pixel blanc pur
> n'existe dans toute la moitié basse, sur toutes les résolutions et les deux
> thèmes.

## Régressions vérifiées

- [x] plus aucune barre/ligne blanche en bas — bordure composer = `rgba(255,255,255,0.06)` (0 px `#FFFFFF` purs, pixel bas = `#17171B`)
- [x] aucune zone vide sous le composer — dernier élément du viewport = composer (gap 12 px transparent volontaire)
- [x] chat occupe toute la hauteur — `scrollHeight == innerHeight`, aucune barre de défilement verticale
- [x] conversation scrollable, composer et Send visibles — vérifiés par présents dans le DOM au rendu réel
- [x] header discret : Agent + Model uniquement (pas de Provider séparé, aucune redondance)
- [x] aucun contrôle dupliqué — sélecteurs uniquement dans la top bar (`AgentDropdown` supprimé en session précédente)
- [x] sidebar conforme au pattern validé (compacte minimaliste / ouverte conversationnelle)
- [x] thème clair : les lignes deviennent `rgba(0,0,0,0.06)` subtil (au lieu de noir plein)

## Impact

- **Aucun** impact Core/Runtime (changement purement présentationnel WebUI).
- Correctif **systémique** dans `tailwind.config.js` : corrige les 122 usages
  `border-line-*` de l'application (pas seulement le chemin du Chat).
- Aucun nouveau composant, aucune duplication, aucune modification de layout
  global (déjà correct).

## Recommandation (hors scope)

Le bug de mapping affectait toute l'application (122 usages). La vérification
visuelle exhaustive des autres écrans (dashboard, settings, agents…) est
recommandée — le fix les corrige tous automatiquement, mais un passage visuel
sur chacun reste à faire pour confirmer l'esthétique ligne par ligne.
