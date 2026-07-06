"use client";

import { useEffect } from "react";
import type { AppPage } from "@/lib/store";

const SHORTCUT_MAP: Record<string, AppPage> = {
  "1": "dashboard",
  "2": "assistant",
  "3": "knowledge",
  "4": "memory",
  "5": "agents",
  "6": "planner",
  "7": "models",
  "8": "providers",
  "9": "plugins",
  "0": "tools",
  "-": "documents",
  ",": "settings",
  "l": "logs",
  "`": "terminal",
};

export function useKeyboardShortcuts(onNavigate: (page: AppPage) => void) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      // ⌘ or Ctrl
      if (!(e.metaKey || e.ctrlKey)) return;
      const key = e.key.toLowerCase();

      // ⌘B = toggle sidebar
      if (key === "b") {
        e.preventDefault();
        // dispatch a custom event so the store listener picks it up
        window.dispatchEvent(new CustomEvent("ethan:toggle-sidebar"));
        return;
      }

      // ⌘K = command palette (already exists)
      if (key === "k") return;

      const page = SHORTCUT_MAP[key];
      if (page) {
        e.preventDefault();
        onNavigate(page);
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onNavigate]);
}