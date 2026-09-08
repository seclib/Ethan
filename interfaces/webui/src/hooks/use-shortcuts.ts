/**
 * ETHAN WebUI — Keyboard shortcuts
 *
 * UI shortcuts are separate from Runtime commands.
 * They only trigger navigation or UI actions.
 *
 * Shortcuts:
 *   n         → New Chat
 *   p         → New Project
 *   / or Ctrl+K → Search (Command Palette)
 *   l         → Library
 *   ,         → Settings
 *   ?         → Show shortcuts help
 */

"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

export interface ShortcutMap {
  [key: string]: {
    action: () => void;
    description: string;
    category: "navigation" | "action";
  };
}

export function useShortcuts(customShortcuts?: ShortcutMap) {
  const router = useRouter();

  const defaultShortcuts: ShortcutMap = {
    n: {
      action: () => router.push("/chat/new"),
      description: "New Chat",
      category: "navigation",
    },
    p: {
      action: () => router.push("/projects/new"),
      description: "New Project",
      category: "navigation",
    },
    "/": {
      action: () => {
        const event = new CustomEvent("ethan:open-search");
        window.dispatchEvent(event);
      },
      description: "Search",
      category: "action",
    },
    l: {
      action: () => router.push("/library"),
      description: "Library",
      category: "navigation",
    },
    ",": {
      action: () => router.push("/settings"),
      description: "Settings",
      category: "navigation",
    },
    "?": {
      action: () => {
        const event = new CustomEvent("ethan:show-shortcuts");
        window.dispatchEvent(event);
      },
      description: "Show shortcuts",
      category: "action",
    },
  };

  const shortcuts = { ...defaultShortcuts, ...customShortcuts };

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      // Handle Ctrl+K for search
      if (event.key === "k" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        shortcuts["/"]?.action();
        return;
      }

      const shortcut = shortcuts[event.key];
      if (shortcut) {
        event.preventDefault();
        shortcut.action();
      }
    },
    [shortcuts],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return { shortcuts };
}

/**
 * Hook to listen for custom shortcut events (open search, show shortcuts).
 */
export function useShortcutEvents(
  onOpenSearch?: () => void,
  onShowShortcuts?: () => void,
) {
  useEffect(() => {
    const handleOpenSearch = () => onOpenSearch?.();
    const handleShowShortcuts = () => onShowShortcuts?.();

    window.addEventListener("ethan:open-search", handleOpenSearch);
    window.addEventListener("ethan:show-shortcuts", handleShowShortcuts);

    return () => {
      window.removeEventListener("ethan:open-search", handleOpenSearch);
      window.removeEventListener("ethan:show-shortcuts", handleShowShortcuts);
    };
  }, [onOpenSearch, onShowShortcuts]);
}
