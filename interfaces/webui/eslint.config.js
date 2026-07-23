const { FlatCompat } = require("@eslint/eslintrc");
const path = require("path");

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

module.exports = [
  ...compat.extends("next/core-web-vitals"),
  {
    rules: {
      // Éviter les erreurs sur les dépendances manquantes de Storybook
      "import/no-extraneous-dependencies": "off",
    },
  },
];