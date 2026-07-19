"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/core/store/ui.store";

export function GlobalShortcuts() {
  const router = useRouter();
  const { toggleSidebar, commandPaletteOpen, openCommandPalette, closeCommandPalette } = useUIStore();
  
  // Track sequence for "g" commands
  const [keySequence, setKeySequence] = React.useState<string[]>([]);

  React.useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA" ||
        (document.activeElement as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const isCmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;
      const key = e.key.toLowerCase();

      // ⌘ + K = Command Palette
      if (isCmdOrCtrl && key === "k") {
        e.preventDefault();
        if (commandPaletteOpen) {
          closeCommandPalette();
        } else {
          openCommandPalette();
        }
        return;
      }

      // ⌘ + Shift + L = Toggle Sidebar
      if (isCmdOrCtrl && e.shiftKey && key === "l") {
        e.preventDefault();
        toggleSidebar();
        return;
      }

      // ⌘ + Shift + T = Terminal
      if (isCmdOrCtrl && e.shiftKey && key === "t") {
        e.preventDefault();
        router.push("/terminal");
        return;
      }

      // ⌘ + , = Settings
      if (isCmdOrCtrl && key === ",") {
        e.preventDefault();
        router.push("/settings");
        return;
      }

      // Sequence: g then [key]
      if (keySequence.length === 0 && key === "g") {
        setKeySequence(["g"]);
        // Clear sequence after 1 second if not completed
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => setKeySequence([]), 1000);
        return;
      }

      if (keySequence[0] === "g") {
        const routes: Record<string, string> = {
          "d": "/",
          "a": "/assistant",
          "m": "/memory",
          "p": "/planner",
          "l": "/logs",
          "k": "/knowledge",
          "s": "/settings",
          "c": "/documents"
        };

        if (routes[key]) {
          router.push(routes[key]);
          setKeySequence([]);
          clearTimeout(timeoutId);
          return;
        }

        // If another key is pressed, reset sequence
        setKeySequence([]);
        clearTimeout(timeoutId);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timeoutId);
    };
  }, [router, toggleSidebar, commandPaletteOpen, openCommandPalette, closeCommandPalette, keySequence]);

  return null;
}
