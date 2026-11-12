const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  transformIgnorePatterns: ["node_modules/(?!(react-markdown|vfile|unist|micromark|mdast|lowlight|highlight.js|comma-separated-tokens|html-url-attributes|property-information|space-separated-tokens|hast|devlop|zwitch|trim-lines|decode-named-character-reference|character-entities|micromark-.*|remark-.*|rehype-.*|unified|bail|is-plain-obj|trough|xdm|estree-.*|estree-util-.*).*)"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testPathIgnorePatterns: ["<rootDir>/node_modules/", "<rootDir>/.next/", "<rootDir>/tests/e2e/"],
  testMatch: [
    "**/__tests__/**/*.test.ts",
    "**/tests/unit/**/*.test.ts",
    "**/tests/unit/**/*.test.tsx",
  ],
};

module.exports = createJestConfig(customJestConfig);