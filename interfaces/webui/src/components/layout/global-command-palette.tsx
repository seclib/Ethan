"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/core/store/ui.store";
import { CommandPalette, CommandItem } from "@/components/ui/command-palette";
import {
  LayoutDashboard,
  MessageSquare,
  Network,
  Database,
  FileText,
  Map,
  Bot,
  Wrench,
  Puzzle,
  Cpu,
  Key,
  Terminal as TerminalIcon,
  ScrollText,
  Settings,
} from "lucide-react";

export function GlobalCommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, closeCommandPalette, toggleMissionControl } = useUIStore();

  const handleNavigate = (path: string) => {
    router.push(path);
  };

  const items: CommandItem[] = [
    {
      id: "nav-dashboard",
      label: "Go to Dashboard",
      category: "Navigation",
      icon: <LayoutDashboard />,
      shortcut: "G D",
      onSelect: () => handleNavigate("/"),
    },
    {
      id: "cmd-mission-control",
      label: "Launch Mission Control",
      category: "Commands",
      icon: <TerminalIcon />,
      shortcut: "⌘M",
      onSelect: () => {
        closeCommandPalette();
        toggleMissionControl();
      },
    },
    {
      id: "nav-assistant",
      label: "Go to Assistant",
      category: "Navigation",
      icon: <MessageSquare />,
      shortcut: "G A",
      onSelect: () => handleNavigate("/assistant"),
    },
    {
      id: "nav-memory",
      label: "Go to Memory",
      category: "Navigation",
      icon: <Network />,
      shortcut: "G M",
      onSelect: () => handleNavigate("/memory"),
    },
    {
      id: "nav-knowledge",
      label: "Go to Knowledge",
      category: "Navigation",
      icon: <Database />,
      shortcut: "G K",
      onSelect: () => handleNavigate("/knowledge"),
    },
    {
      id: "nav-documents",
      label: "Go to Documents",
      category: "Navigation",
      icon: <FileText />,
      shortcut: "G C",
      onSelect: () => handleNavigate("/documents"),
    },
    {
      id: "nav-planner",
      label: "Go to Planner",
      category: "Navigation",
      icon: <Map />,
      shortcut: "G P",
      onSelect: () => handleNavigate("/planner"),
    },
    {
      id: "nav-agents",
      label: "Go to Agents",
      category: "Navigation",
      icon: <Bot />,
      onSelect: () => handleNavigate("/agents"),
    },
    {
      id: "nav-tools",
      label: "Go to Tools",
      category: "Navigation",
      icon: <Wrench />,
      onSelect: () => handleNavigate("/tools"),
    },
    {
      id: "nav-plugins",
      label: "Go to Plugins",
      category: "Navigation",
      icon: <Puzzle />,
      onSelect: () => handleNavigate("/plugins"),
    },
    {
      id: "nav-models",
      label: "Go to Models",
      category: "Navigation",
      icon: <Cpu />,
      onSelect: () => handleNavigate("/models"),
    },
    {
      id: "nav-providers",
      label: "Go to Providers",
      category: "Navigation",
      icon: <Key />,
      onSelect: () => handleNavigate("/providers"),
    },
    {
      id: "nav-terminal",
      label: "Open Terminal",
      category: "Navigation",
      icon: <TerminalIcon />,
      shortcut: "⌘⇧T",
      onSelect: () => handleNavigate("/terminal"),
    },
    {
      id: "nav-logs",
      label: "Go to Logs",
      category: "Navigation",
      icon: <ScrollText />,
      shortcut: "G L",
      onSelect: () => handleNavigate("/logs"),
    },
    {
      id: "nav-settings",
      label: "Open Settings",
      category: "Navigation",
      icon: <Settings />,
      shortcut: "⌘,",
      onSelect: () => handleNavigate("/settings"),
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
