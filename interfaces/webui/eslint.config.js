/**
 * ETHAN WebUI — ESLint flat config (ESLint 9+)
 *
 * eslint-config-next >= 15 expose nativement des configs flat.
 * Ne PAS passer par FlatCompat : eslint-config-next 16 retourne déjà un
 * tableau de configs flat, et FlatCompat (qui tente de le re-traiter comme
 * de l'eslintrc legacy) provoque l'erreur
 * « TypeError: Converting circular structure to JSON ».
 */
const nextCoreWebVitals = require("eslint-config-next/core-web-vitals");

module.exports = [
  {
    ignores: [
      ".next/**",
      "out/**",
      "node_modules/**",
      "storybook-static/**",
      "coverage/**",
    ],
  },
  ...nextCoreWebVitals,
  {
    files: ["**/*.{js,mjs,ts,tsx}"],
    rules: {
      // Éviter les erreurs sur les dépendances manquantes de Storybook
      "import/no-extraneous-dependencies": "off",

      // Règles React Compiler / react-hooks v6 (introduites par
      // eslint-config-next 16) : elles détectent de la débt préexistante
      // (setState dans useEffect, accès refs au render, mémoization
      // manuelle…). Rabaisssées en avertissement pour ne pas bloquer le
      // pipeline tout en gardant la visibilité — à traiter incrémentalement.
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/preserve-manual-memoization": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/refs": "warn",
      "react-hooks/static-components": "warn",
      "react-hooks/immutability": "warn",
    },
  },
];