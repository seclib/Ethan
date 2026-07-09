import type { Meta, StoryObj } from "@storybook/react";
import { Badge } from "./badge";

const meta: Meta<typeof Badge> = {
  title: "UI/Badge",
  component: Badge,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "primary", "success", "warning", "error", "info", "dim"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    dot: { control: "boolean" },
  },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
  args: {
    variant: "default",
    children: "default",
  },
};

export const Primary: Story = {
  args: {
    variant: "primary",
    children: "primary",
  },
};

export const Success: Story = {
  args: {
    variant: "success",
    children: "success",
  },
};

export const Warning: Story = {
  args: {
    variant: "warning",
    children: "warning",
  },
};

export const Error: Story = {
  args: {
    variant: "error",
    children: "error",
  },
};

export const Info: Story = {
  args: {
    variant: "info",
    children: "info",
  },
};

export const Dim: Story = {
  args: {
    variant: "dim",
    children: "dim",
  },
};

export const WithDot: Story = {
  args: {
    variant: "success",
    dot: true,
    children: "Running",
  },
};

export const AllVariants = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="default">default</Badge>
      <Badge variant="primary">primary</Badge>
      <Badge variant="success" dot>success</Badge>
      <Badge variant="warning" dot>warning</Badge>
      <Badge variant="error" dot>error</Badge>
      <Badge variant="info">info</Badge>
      <Badge variant="dim">dim</Badge>
    </div>
  ),
};