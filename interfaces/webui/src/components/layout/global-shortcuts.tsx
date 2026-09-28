"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/store/ui.store";
import { G_SEQUENCE_ROUTES } from "./nav-config";

export function GlobalShortcuts() {
  const router = useRouter();
  const {
    toggleSidebar,
    commandPaletteOpen,
    openCommandPalette,
    closeCommandPalette,
    toggleInspector
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

      // ⌘ + M = Mission workspace (page dédiée — plus d'overlay sur le Chat)
      if (isCmdOrCtrl && key === "m") {
        e.preventDefault();
        router.push("/missions");
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
        // Source unique : G_SEQUENCE_ROUTES (partagée avec l'indicateur
        // ci-dessous et la palette Ctrl+K) — un raccourci annoncé résout.
        const target = G_SEQUENCE_ROUTES[key];

        if (target) {
          router.push(target.route);
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
  }, [router, toggleSidebar, commandPaletteOpen, openCommandPalette, closeCommandPalette, keySequence, toggleInspector]);

  // Indicateur visuel de séquence « g » (correctif audit UX P2-5) : sans lui,
  // l'attente de la seconde touche était invisible et la fonctionnalité
  // indécouvrable. Pure affichage — la logique reste dans le handler clavier.
  if (keySequence[0] === "g") {
    return (
      <div
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-toast flex max-w-[92vw] items-center gap-2 rounded-full border border-line-2 bg-bg-2 px-4 py-1.5 shadow-lg pointer-events-none"
        role="status"
        aria-live="polite"
      >
        <kbd className="text-[10px] font-semibold text-accent-400 bg-elevated rounded px-1.5 py-0.5">G</kbd>
        <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-foreground-tertiary">
          {/* Généré depuis G_SEQUENCE_ROUTES : l'indicateur ne peut pas
              annoncer une séquence que le handler ne résout pas. */}
          {Object.entries(G_SEQUENCE_ROUTES).map(([key, sequence]) => (
            <span key={key} className="whitespace-nowrap">
              {sequence.label}&nbsp;<kbd className="font-mono">{key.toUpperCase()}</kbd>
            </span>
          ))}
        </span>
      </div>
    );
  }

  return null;
}
