import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Tabs } from "@/components/ui/tabs";

const meta: Meta<typeof Tabs> = {
  title: "UI/Tabs",
  component: Tabs,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Tabs>;

const lineItems = [
  { value: "tab1", label: "Account", content: <p className="text-sm text-foreground-secondary">Account settings content.</p> },
  { value: "tab2", label: "Password", content: <p className="text-sm text-foreground-secondary">Password settings content.</p> },
  { value: "tab3", label: "Settings", content: <p className="text-sm text-foreground-secondary">General settings content.</p> },
];

const pillItems = [
  { value: "tab1", label: "Home", content: <p className="text-sm text-foreground-secondary">Home content.</p> },
  { value: "tab2", label: "Profile", content: <p className="text-sm text-foreground-secondary">Profile content.</p> },
  { value: "tab3", label: "Settings", content: <p className="text-sm text-foreground-secondary">Settings content.</p> },
];

export const Default: Story = {
  render: () => <Tabs items={lineItems} defaultValue="tab1" className="w-80" variant="line" />,
};

export const Pill: Story = {
  render: () => <Tabs items={pillItems} defaultValue="tab1" className="w-80" variant="pill" />,
};
