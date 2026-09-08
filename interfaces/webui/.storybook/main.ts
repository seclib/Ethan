import type { StorybookConfig } from "@storybook/types";

const config: StorybookConfig = {
  stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
  // NB: en Storybook ≥ 9, addon-essentials / addon-interactions / addon-links
  // sont intégrés au package `storybook` ; seul addon-links est encore publié
  // séparément en v10 et doit être listé ici.
  addons: [
    "@storybook/addon-links",
  ],
  framework: {
    name: "@storybook/nextjs",
    options: {},
  },
  docs: {
    autodocs: true,
  },
  staticDirs: ["../public"],
};

export default config;