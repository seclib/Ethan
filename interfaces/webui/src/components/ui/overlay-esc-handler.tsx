"use client";

import { useEffect } from "react";
import { useOverlayStore } from "@/store/overlay.store";

/**
 * Handler global ESC — pile centralisée (recommandation audit overlay).
 *
 * UN SEUL écouteur, monté une fois dans le RootLayout : il ferme uniquement
 * la couche la plus haute de la pile. Les couches inférieures ne sont
 * jamais fermées tant qu'une couche est au-dessus d'elles (comportement de
 * l'arbitre ESC d'Odysseus, sans la complexité de son DOM impératif).
 *
 * Si la pile est vide, le handler ne fait rien : les gestionnaires locaux
 * (palette Ctrl+K, etc.) gardent la main sur leur propre Escape.
 */
export function OverlayEscHandler() {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      const { stack, closeTop } = useOverlayStore.getState();
      if (stack.length === 0) return;
      e.preventDefault();
      e.stopPropagation();
      closeTop();
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, []);
  return null;
}