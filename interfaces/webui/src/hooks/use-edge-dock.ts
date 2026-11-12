"use client";

/**
 * ETHAN WebUI — useEdgeDock (hook)
 *
 * Ajoute le comportement *edge-docking* inspiré de Odysseus `modalSnap.js` :
 * glisser la fenêtre vers le bord droit ou gauche → dock en tant que panel latéral;
 * glisser hors du bord → restaure la position/taille précédente.
 *
 * Concepts Odysseus intégrés :
 *  - SNAP_PX / UNSNAP_PX   : bande de capture pour le dock / undock
 *  - --right-dock-w / --left-dock-w : variables CSS pour la largeur
 *  - auto-collapse sidebar : si la zone de chat < MIN_CHAT_WIDTH (Odysseus)
 *  - persistance localStorage : largeur + side de dock mémorisés
 *
 * Conforme AGENTS.md : ce hook ne contient AUCUNE logique métier ETHAN.
 * Il ne fait que du positionnement/UI — l'état métier reste dans Core.
 */

import * as React from "react";
import { useUIStore } from "@/store/ui.store";

const SNAP_PX = 60;
const UNSNAP_PX = 80;
const MIN_CHAT_WIDTH = 480;
const MIN_DOCK_WIDTH = 320;
const MAX_DOCK_WIDTH = 640;

const DOCK_WIDTH_KEY = "ethan.dock-width:";
const DOCK_STATE_KEY = "ethan.dock-state:";

type DockSide = "left" | "right";

interface EdgeDockOptions {
  id: string;
  /** Ref de l'élément fenêtre — `RefObject<T | null>` (typage React 19). */
  winRef: React.RefObject<HTMLDivElement | null>;
  active: boolean;
  onDockChange: (docked: boolean, side?: DockSide) => void;
}

export function useEdgeDock(opts: EdgeDockOptions) {
  const { id, winRef, active, onDockChange } = opts;

  const [docked, setDocked] = React.useState<{ side: DockSide; w: number } | null>(null);
  const [dockWidth, setDockWidth] = React.useState(() => {
    // Garde SSR : le hook peut être évalué pendant le prerender Next.js
    if (typeof window === "undefined") return 480;
    const saved = Number(localStorage.getItem(DOCK_WIDTH_KEY + id));
    return Number.isFinite(saved) && saved >= MIN_DOCK_WIDTH && saved <= MAX_DOCK_WIDTH
      ? saved
      : Math.round(window.innerWidth * 0.38);
  });

  const setSidebarExpanded = useUIStore((s) => s.setSidebarExpanded);

  // Stable : ne dépend que de valeurs stables (zustand setter, id)
  const applyDock = React.useCallback(
    (side: DockSide, w: number) => {
    // Le positionnement est rendu par le composant (style React) — le hook
    // gère uniquement l'état global : classes, variables CSS, persistance.
    document.body.classList.add(side === "right" ? "right-dock-active" : "left-dock-active");
    document.documentElement.style.setProperty(
      side === "right" ? "--right-dock-w" : "--left-dock-w", `${w}px`,
    );
    try {
      localStorage.setItem(DOCK_WIDTH_KEY + id, String(w));
      localStorage.setItem(DOCK_STATE_KEY + id, side);
    } catch (_) { /* storage indisponible */ }

    // Auto-collapse sidebar si zone de chat trop petite (concept Odysseus MIN_CHAT_WIDTH)
    const { sidebarExpanded } = useUIStore.getState();
    if (sidebarExpanded && window.innerWidth - w < MIN_CHAT_WIDTH) {
      setSidebarExpanded(false);
    }
    },
    [id, setSidebarExpanded],
  );

  function clearDock() {
    document.body.classList.remove("right-dock-active", "left-dock-active");
    document.documentElement.style.removeProperty("--right-dock-w");
    document.documentElement.style.removeProperty("--left-dock-w");
    try { localStorage.removeItem(DOCK_STATE_KEY + id); } catch (_) { /* ignore */ }
  }

  function checkDock(cx: number): DockSide | null {
    if (!winRef.current) return null;
    const vw = window.innerWidth;
    // Bande de capture plus large pour UNdock (évite le flicker au bord)
    const snap = docked ? UNSNAP_PX : SNAP_PX;
    return cx >= vw - snap ? "right" : cx <= snap ? "left" : null;
  }

  function handleDockCheck(cx: number): DockSide | null {
    if (!active) return docked ? docked.side : null;

    const side = checkDock(cx);

    if (side && !docked) {
      // Entering dock — le composant conserve pos/size pour un éventuel undock
      const w = Math.min(MAX_DOCK_WIDTH, Math.max(MIN_DOCK_WIDTH, dockWidth));
      setDocked({ side, w });
      applyDock(side, w);
      onDockChange(true, side);
      return side;
    }

    if (!side && docked) {
      // Exiting dock — le composant restaure pos/size via son propre état
      clearDock();
      setDocked(null);
      onDockChange(false);
      return null;
    }

    // Drag horizontal pendant le dock → redimensionne la largeur (Odysseus _setWidth)
    if (docked && side === docked.side) {
      const raw =
        docked.side === "right"
          ? window.innerWidth - cx
          : cx - 48 /* largeur sidebar repliée */;
      const w = Math.min(MAX_DOCK_WIDTH, Math.max(MIN_DOCK_WIDTH, raw));
      setDockWidth(w);
      setDocked({ side: docked.side, w });
      document.documentElement.style.setProperty(
        docked.side === "right" ? "--right-dock-w" : "--left-dock-w", `${w}px`,
      );
    }

    return docked ? docked.side : null;
  }

  // Restore dock state on (re)open — Odysseus _getRememberedDock
  React.useEffect(() => {
    if (!active || !winRef.current || docked) return;
    try {
      const sideStr = localStorage.getItem(DOCK_STATE_KEY + id);
      if (sideStr === "left" || sideStr === "right") {
        applyDock(sideStr, dockWidth);
        setDocked({ side: sideStr, w: dockWidth });
        onDockChange(true, sideStr);
      }
    } catch (_) { /* ignore */ }
  }, [active, id, dockWidth, docked, onDockChange, applyDock, winRef]);

  // Reset complet — appelé par le composant à la fermeture de la fenêtre
  function resetDock() {
    clearDock();
    setDocked(null);
    onDockChange(false);
  }

  return {
    docked,
    dockWidth,
    setDockWidth: (w: number) => {
      const clamped = Math.min(MAX_DOCK_WIDTH, Math.max(MIN_DOCK_WIDTH, w));
      setDockWidth(clamped);
    },
    handleDockCheck,
    clearDock,
    resetDock,
  };
}
