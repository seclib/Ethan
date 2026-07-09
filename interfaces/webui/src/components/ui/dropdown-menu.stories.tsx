import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { DropdownMenu } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { MoreVertical, Edit, Trash, Copy, Share } from "lucide-react";

const meta: Meta<typeof DropdownMenu> = {
  title: "UI/DropdownMenu",
  component: DropdownMenu,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof DropdownMenu>;

const items = [
  { label: "Edit", icon: <Edit className="w-4 h-4" />, onClick: () => {} },
  { label: "Duplicate", icon: <Copy className="w-4 h-4" />, onClick: () => {} },
  { label: "separator" },
  { label: "Delete", icon: <Trash className="w-4 h-4" />, danger: true, onClick: () => {} },
];

export const Default: Story = {
  render: () => (
    <DropdownMenu
      trigger={<Button icon={<MoreVertical className="w-4 h-4" />} />}
      items={items}
    />
  ),
};

export const WithShortcuts: Story = {
  render: () => (
    <DropdownMenu
      trigger={<Button>Actions</Button>}
      items={[
        { label: "Copy", icon: <Copy className="w-4 h-4" />, shortcut: "⌘C", onClick: () => {} },
        { label: "Paste", icon: <Share className="w-4 h-4" />, shortcut: "⌘V", onClick: () => {} },
        { label: "separator" },
        { label: "Delete", icon: <Trash className="w-4 h-4" />, shortcut: "⌘⌫", danger: true, onClick: () => {} },
      ]}
    />
  ),
};