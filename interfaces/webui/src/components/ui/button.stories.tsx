import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";
import { Plus, Trash2, Settings } from "lucide-react";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "outline", "ghost", "destructive"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg", "icon"],
    },
    loading: { control: "boolean" },
    disabled: { control: "boolean" },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: "primary",
    children: "Click me",
  },
};

export const Secondary: Story = {
  args: {
    variant: "secondary",
    children: "Click me",
  },
};

export const Outline: Story = {
  args: {
    variant: "outline",
    children: "Click me",
  },
};

export const Ghost: Story = {
  args: {
    variant: "ghost",
    children: "Click me",
  },
};

export const Destructive: Story = {
  args: {
    variant: "destructive",
    children: "Delete",
  },
};

export const Small: Story = {
  args: {
    size: "sm",
    children: "Small",
  },
};

export const Large: Story = {
  args: {
    size: "lg",
    children: "Large",
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    children: "Loading",
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: "Disabled",
  },
};

export const WithIcon: Story = {
  args: {
    icon: <Plus />,
    children: "Add item",
  },
};

export const IconOnly: Story = {
  args: {
    size: "icon",
    icon: <Settings />,
    "aria-label": "Settings",
  },
};

export const WithIconRight: Story = {
  args: {
    iconRight: <Trash2 />,
    variant: "destructive",
    children: "Delete",
  },
};