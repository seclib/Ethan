import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Avatar } from "@/components/ui/avatar";

const meta: Meta<typeof Avatar> = {
  title: "UI/Avatar",
  component: Avatar,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Avatar>;

export const Default: Story = {
  render: () => <Avatar fallback="JD" />,
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-end gap-4">
      <Avatar size="sm" fallback="SM" />
      <Avatar size="md" fallback="MD" />
      <Avatar size="lg" fallback="LG" />
      <Avatar size="xl" fallback="XL" />
    </div>
  ),
};

export const WithImage: Story = {
  render: () => (
    <Avatar
      src="https://github.com/shadcn.png"
      alt="User"
      fallback="JD"
      size="lg"
    />
  ),
};

export const Initials: Story = {
  render: () => (
    <div className="flex gap-4">
      <Avatar fallback="John Doe" />
      <Avatar fallback="Marie Curie" />
      <Avatar fallback="A" />
      <Avatar />
    </div>
  ),
};