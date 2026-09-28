"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/store/ui.store";
import { CommandPalette, CommandItem } from "@/components/ui/command-palette";
import {
  LayoutDashboard,
  MessageSquare,
  Network,
  Database,
  Bot,
  Wrench,
  Terminal as TerminalIcon,
  Settings,
  Layers,
  Cpu,
  Library,
  Workflow,
  FlaskConical,
  ScrollText,
  MessagesSquare,
} from "lucide-react";
import { formatGSequence } from "./nav-config";

export function GlobalCommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, closeCommandPalette } = useUIStore();

  const handleNavigate = (path: string) => {
    router.push(path);
  };

  const items: CommandItem[] = [
    {
      id: "nav-dashboard",
      label: "Go to Assistant",
      category: "Navigation",
      icon: <MessageSquare />,
      shortcut: formatGSequence("a"),
      onSelect: () => handleNavigate("/"),
    },
    {
      id: "nav-workspace",
      label: "Go to Workspace",
      category: "Navigation",
      icon: <LayoutDashboard />,
      shortcut: formatGSequence("d"),
      onSelect: () => handleNavigate("/workspace"),
    },
    {
      id: "nav-knowledge",
      label: "Go to Knowledge",
      category: "Navigation",
      icon: <Database />,
      shortcut: formatGSequence("k"),
      onSelect: () => handleNavigate("/knowledge"),
    },
    {
      id: "nav-agents",
      label: "Go to Agents",
      category: "Navigation",
      icon: <Bot />,
      shortcut: formatGSequence("e"),
      onSelect: () => handleNavigate("/agents"),
    },
            {
      id: "nav-tools",
      label: "Go to Tools",
      category: "Navigation",
      icon: <Wrench className="h-4 w-4" />,
      shortcut: formatGSequence("t"),
      onSelect: () => handleNavigate("/tools"),
    },
    {
      id: "nav-providers",
      label: "Go to Providers",
      category: "Navigation",
      icon: <Layers className="h-4 w-4" />,
      shortcut: formatGSequence("p"),
      onSelect: () => handleNavigate("/providers"),
    },
    {
      id: "nav-models",
      label: "Go to Models",
      category: "Navigation",
      icon: <Cpu className="h-4 w-4" />,
      shortcut: formatGSequence("n"),
      onSelect: () => handleNavigate("/models"),
    },
    {
      id: "nav-missions",
      label: "Go to Missions",
      category: "Navigation",
      icon: <Network />,
      shortcut: formatGSequence("m"),
      onSelect: () => handleNavigate("/missions"),
    },
    {
      id: "nav-library",
      label: "Go to Library",
      category: "Navigation",
      icon: <Library className="h-4 w-4" />,
      shortcut: formatGSequence("l"),
      onSelect: () => handleNavigate("/library"),
    },
    {
      id: "nav-settings",
      label: "Open Settings",
      category: "Navigation",
      icon: <Settings />,
      shortcut: "⌘,",
      onSelect: () => handleNavigate("/settings"),
    },
    {
      id: "nav-automations",
      label: "Go to Automations",
      category: "Navigation",
      icon: <Workflow className="h-4 w-4" />,
      onSelect: () => handleNavigate("/automations"),
    },
    {
      id: "nav-skills-lab",
      label: "Open Skill Lab",
      category: "Navigation",
      icon: <FlaskConical className="h-4 w-4" />,
      onSelect: () => handleNavigate("/skills/lab"),
    },
    {
      id: "nav-prompts",
      label: "Go to Prompts",
      category: "Navigation",
      icon: <ScrollText className="h-4 w-4" />,
      onSelect: () => handleNavigate("/prompts"),
    },
    {
      id: "nav-channels",
      label: "Go to Channels",
      category: "Navigation",
      icon: <MessagesSquare className="h-4 w-4" />,
      onSelect: () => handleNavigate("/channels"),
    },
    {
      id: "cmd-mission-workspace",
      label: "Open Mission workspace",
      category: "Commands",
      icon: <TerminalIcon />,
      shortcut: "⌘M",
      onSelect: () => {
        closeCommandPalette();
        handleNavigate("/missions");
      },
    },
  ];

  return (
    <CommandPalette
      open={commandPaletteOpen}
      onClose={closeCommandPalette}
      items={items}
      placeholder="Type a command or search..."
    />
  );
}
