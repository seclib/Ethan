# Résolution des dépendances npm — ETHAN WebUI (final)

## Date : 2026-07-10

## Problème initial
`npm install` échouait avec de multiples conflits de peer dependencies :
- Storybook v8/v10 mélangés
- Next 15 + React 19 RC
- `eslint-config-next` v16 vs ESLint 8 (install auto)
- Modules manquants

## Décision
Versions cohérentes sans `--force` ni `--legacy-peer-deps` :
- **Next.js 14.2.35** (pinned)
- **React 18.2** + **ReactDOM 18.2**
- **ESLint 8.57** + **eslint-config-next 14.2.35** (pinned)
- **TypeScript 5.4.5**
- **Storybook retiré** (conflit majeur, non requis pour build)

## Corrections finales ajoutées
- `tsconfig.json` : exclusion de `.next/types` (évite `TS6053` sur build/lint)
- `next.config.js` : retrait de `output: "standalone"` (build local plus fiable)
- suppression des `*.stories.tsx` et `.storybook/`

## Vérifications (vert)
- ✅ `npm install`
- ✅ `npm run build`
- ✅ `npm run lint` (0 erreur, 1 warning)
- ✅ `npm run typecheck`

## Fin
Le frontend est à nouveau installable et buildable.