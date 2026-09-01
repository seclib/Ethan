"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/store/ui.store";

export function GlobalShortcuts() {
  const router = useRouter();
  const { 
    toggleSidebar, 
    commandPaletteOpen, 
    openCommandPalette, 
    closeCommandPalette,
    toggleInspector,
    toggleMissionControl
  } = useUIStore();
  
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

                  // Detect platform : `navigator.platform` is deprecated/undefined in modern
      // browsers, so we fall back to userAgent sniffing (Mac/Windows/Linux).
      const userAgent = typeof navigator !== "undefined" ? navigator.userAgent : "";
      const isMac = /Mac|iPhone|iPad|iPod/.test(userAgent);
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

      // ⌘ + J = Toggle Inspector
      if (isCmdOrCtrl && key === "j") {
        e.preventDefault();
        toggleInspector();
        return;
      }

      // ⌘ + M = Toggle Mission Control
      if (isCmdOrCtrl && key === "m") {
        e.preventDefault();
        toggleMissionControl();
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
          "d": "/workspace",
          "a": "/",
          "m": "/missions",
          "k": "/knowledge",
          "e": "/agents",
          "t": "/tools",
          "s": "/settings",
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
  }, [router, toggleSidebar, commandPaletteOpen, openCommandPalette, closeCommandPalette, keySequence, toggleInspector, toggleMissionControl]);

  // Indicateur visuel de séquence « g » (correctif audit UX P2-5) : sans lui,
  // l'attente de la seconde touche était invisible et la fonctionnalité
  // indécouvrable. Pure affichage — la logique reste dans le handler clavier.
  if (keySequence[0] === "g") {
    return (
      <div
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast flex items-center gap-2 rounded-full border border-line-2 bg-bg-2 px-4 py-1.5 shadow-lg pointer-events-none"
        role="status"
        aria-live="polite"
      >
        <kbd className="text-[10px] font-semibold text-accent-400 bg-elevated rounded px-1.5 py-0.5">G</kbd>
        <span className="text-[11px] text-foreground-tertiary">
          Assistant&nbsp;<kbd className="font-mono">A</kbd> · Workspace&nbsp;<kbd className="font-mono">D</kbd> · Missions&nbsp;<kbd className="font-mono">M</kbd> · Knowledge&nbsp;<kbd className="font-mono">K</kbd> · Agents&nbsp;<kbd className="font-mono">E</kbd> · Tools&nbsp;<kbd className="font-mono">T</kbd> · Settings&nbsp;<kbd className="font-mono">S</kbd>
        </span>
      </div>
    );
  }

  return null;
}
