import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { CommandPalette } from "@/components/ui/command-palette";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Plus, Settings, Search } from "lucide-react";

const meta: Meta<typeof CommandPalette> = {
  title: "UI/CommandPalette",
  component: CommandPalette,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof CommandPalette>;

const items = [
  { id: "1", label: "Dashboard", category: "Navigate", icon: <LayoutDashboard className="w-4 h-4" />, onSelect: () => {} },
  { id: "2", label: "New Mission", category: "Actions", icon: <Plus className="w-4 h-4" />, shortcut: "⌘N", onSelect: () => {} },
  { id: "3", label: "Settings", category: "Navigate", icon: <Settings className="w-4 h-4" />, onSelect: () => {} },
  { id: "4", label: "Search", category: "Actions", icon: <Search className="w-4 h-4" />, shortcut: "⌘K", onSelect: () => {} },
];

export const Default: Story = {
  render: () => {
    const [open, setOpen] = React.useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open Command Palette</Button>
        <CommandPalette
          open={open}
          onClose={() => setOpen(false)}
          items={items}
        />
      </>
    );
  },
};

export const WithRecent: Story = {
  render: () => {
    const [open, setOpen] = React.useState(false);
    const recent = [items[0], items[2]];
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open with Recent</Button>
        <CommandPalette
          open={open}
          onClose={() => setOpen(false)}
          items={items}
          recent={recent}
        />
      </>
    );
  },
};