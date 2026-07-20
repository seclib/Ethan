import type { StorybookConfig } from "@storybook/react";

const config: StorybookConfig = {
  stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|ts|tsx)"],
  addons: [],
  framework: {
    name: "@storybook/react",
    options: {},
  },
  docs: {
    autodocs: true,
  },
};

export default config;
