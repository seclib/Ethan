"use client";

import * as React from "react";
import Link from "next/link";
import { useUIStore } from "@/store/ui.store";
import { useI18n } from "@/lib/i18n";
import { NAV_ITEMS_FLAT } from "@/components/layout/nav-config";

/**
 * Command palette minimale déclenchée par Ctrl+K.
 *
 * Affiche les destinations issues de la taxinomie unique NAV_ITEMS_FLAT
 * (même source que la sidebar et l'en-tête — pas de second système de
 * navigation), filtre selon la requête, navigue via Next.js Link, ferme la
 * palette et réinitialise la recherche après sélection.
 */
export function CommandPalette() {
  const open = useUIStore((state) => state.commandPaletteOpen);
  const openCommandPalette = useUIStore((state) => state.openCommandPalette);
  const closeCommandPalette = useUIStore((state) => state.closeCommandPalette);
  const { t } = useI18n();
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = React.useState("");

  /** Ferme la palette et réinitialise la recherche (fermeture = reset). */
  const closeAndReset = React.useCallback(() => {
    closeCommandPalette();
    setQuery("");
  }, [closeCommandPalette]);

  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        openCommandPalette();
      }
      if (event.key === "Escape" && open) {
        closeAndReset();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, openCommandPalette, closeAndReset]);

  React.useEffect(() => {
    if (open) {
      // Attendre le rendu du DOM avant de focaliser.
      const timer = window.setTimeout(() => inputRef.current?.focus(), 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [open]);

  if (!open) {
    return null;
  }

  const q = query.toLowerCase();
  const results = NAV_ITEMS_FLAT.filter(
    (item) =>
      item.label.toLowerCase().includes(q) || item.href.toLowerCase().includes(q),
  );

  const handleSelect = (href: string) => {
    closeAndReset();
  };

  return (
    <div
      className="fixed inset-0 z-[90] flex items-start justify-center bg-black/40 p-4 pt-[12vh]"
      onClick={closeAndReset}
    >
      <div
        className="w-full max-w-xl rounded-xl border border-line-2 bg-panel shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <input
          ref={inputRef}
          placeholder="Type a command or search..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="h-12 w-full border-0 bg-transparent px-4 text-sm outline-none"
          type="text"
        />
        {results.length > 0 ? (
          <ul role="list" className="mt-2 divide-y divide-line-2">
            {results.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => handleSelect(item.href)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-foreground hover:bg-accent transition-colors"
                >
                  {t(item.label)}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 px-4 py-3 text-sm text-foreground-tertiary">
            Aucun résultat
          </p>
        )}
      </div>
    </div>
  );
}
