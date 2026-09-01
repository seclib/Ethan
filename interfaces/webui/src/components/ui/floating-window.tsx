"use client";

/**
 * ETHAN WebUI — FloatingWindow (fenêtre superposée).
 *
 * Fenêtre flottante indépendante (z-drawer = 60), draggable + resizable,
 * pour des fonctions secondaires accessibles sans quitter la page courante.
 * Utilisé pour : Mail, Tasks, Compare.
 *
 * Edge-docking (concept Odysseus modalSnap.js) : glisser la fenêtre vers le
 * bord gauche/droit la docke en panel latéral pleine hauteur ; glisser vers
 * le centre la libère. Largeur + côté persistés (localStorage), position et
 * taille flottantes également persistées. Quand la zone de chat devient trop
 * étroite, la sidebar est auto-repliée (Odysseus MIN_CHAT_WIDTH).
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { useOverlayStore } from "@/store/overlay.store";
import { useEdgeDock } from "@/hooks/use-edge-dock";

export interface FloatingWindowProps {
  id: string;
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultWidth?: number;
  defaultHeight?: number;
  defaultX?: number;
  defaultY?: number;
  children: React.ReactNode;
}

export function FloatingWindow({
  id,
  title,
  open,
  onOpenChange,
  defaultWidth = 380,
  defaultHeight = 520,
  defaultX = 40,
  defaultY = 80,
  children,
}: FloatingWindowProps) {
  const [pos, setPos] = React.useState({ x: defaultX, y: defaultY });
  const [size, setSize] = React.useState({ w: defaultWidth, h: defaultHeight });
  const [dragging, setDragging] = React.useState(false);
  const [resizing, setResizing] = React.useState(false);
  const winRef = React.useRef<HTMLDivElement>(null);
  const startRef = React.useRef<{ px: number; py: number; x: number; y: number; w: number; h: number } | null>(null);

  // Edge-docking (concept Odysseus modalSnap.js) : drag vers un bord → dock
  const handleDockChange = React.useCallback(() => { /* état UI local uniquement */ }, []);
  const { docked, handleDockCheck, resetDock } = useEdgeDock({
    id,
    winRef,
    active: open,
    onDockChange: handleDockChange,
  });

  // Fermeture pendant le dock → nettoie classes/variables CSS globales
  React.useEffect(() => {
    if (!open) resetDock();
  }, [open, resetDock]);

  // Persistance position/taille (recommandation audit overlays) — sauvegarde
  // en fin de geste (drag/resize), jamais pendant le déplacement.
  React.useEffect(() => {
    try {
      const raw = localStorage.getItem(`ethan.win:${id}`);
      if (raw) {
        const saved = JSON.parse(raw) as Partial<{ x: number; y: number; w: number; h: number }>;
        if (typeof saved.w === "number" && typeof saved.h === "number") {
          setSize({ w: saved.w, h: saved.h });
        }
        if (typeof saved.x === "number" && typeof saved.y === "number") {
          setPos({
            x: Math.min(Math.max(saved.x, 0), Math.max(window.innerWidth - 120, 0)),
            y: Math.min(Math.max(saved.y, 0), Math.max(window.innerHeight - 80, 0)),
          });
        }
      }
    } catch { /* storage indisponible ou JSON invalide */ }
  }, [id]);

  React.useEffect(() => {
    if (!open || dragging || resizing) return; // fin de geste uniquement
    try {
      localStorage.setItem(`ethan.win:${id}`, JSON.stringify({ ...pos, ...size }));
    } catch { /* storage indisponible */ }
  }, [open, dragging, resizing, id, pos, size]);

  // ESC via la pile globale
  React.useEffect(() => {
    if (!open) return;
    const unregister = useOverlayStore.getState().push({
      id: `floating-${id}`,
      onClose: () => onOpenChange(false),
    });
    return unregister;
  }, [open, id, onOpenChange]);

  const onPointerDown = React.useCallback((e: React.PointerEvent) => {
    if (!winRef.current) return;
    const rect = winRef.current.getBoundingClientRect();
    startRef.current = {
      px: e.clientX,
      py: e.clientY,
      x: rect.left,
      y: rect.top,
      w: rect.width,
      h: rect.height,
    };
    setDragging(true);
    winRef.current.setPointerCapture(e.pointerId);
  }, []);

  const onResizePointerDown = React.useCallback(
    (e: React.PointerEvent) => {
      if (!winRef.current) return;
      const rect = winRef.current.getBoundingClientRect();
      startRef.current = {
        px: e.clientX,
        py: e.clientY,
        x: rect.left,
        y: rect.top,
        w: rect.width,
        h: rect.height,
      };
      setResizing(true);
      winRef.current.setPointerCapture(e.pointerId);
    },
    [],
  );

  const onPointerMove = React.useCallback(
    (e: PointerEvent) => {
      if (!startRef.current) return;
      const dx = e.clientX - startRef.current.px;
      const dy = e.clientY - startRef.current.py;
      if (dragging) {
        if (docked) {
          // Docké : le drag horizontal redimensionne la largeur / undock (hook)
          handleDockCheck(e.clientX);
        } else {
          setPos({ x: startRef.current.x + dx, y: startRef.current.y + dy });
          // Détection edge-dock pendant le drag (concept Odysseus modalSnap)
          handleDockCheck(e.clientX);
        }
      }
      if (resizing) {
        setSize({ w: Math.max(280, startRef.current.w + dx), h: Math.max(200, startRef.current.h + dy) });
      }
    },
    [dragging, resizing, docked, handleDockCheck],
  );

  const onPointerUp = React.useCallback(() => {
    setDragging(false);
    setResizing(false);
    startRef.current = null;
  }, []);

  React.useEffect(() => {
    if (!dragging && !resizing) return;
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };
  }, [dragging, resizing, onPointerMove, onPointerUp]);

  if (!open) return null;

  // Style docké (panel latéral pleine hauteur) vs flottant (position libre).
  // Le hook fournit l'état ; le composant garde le rendu 100% déclaratif React.
  const dockStyle: React.CSSProperties = docked
    ? docked.side === "right"
      ? { top: 0, right: 0, left: "auto", width: docked.w, height: "100dvh" }
      : { top: 0, left: 0, right: "auto", width: docked.w, height: "100dvh" }
    : { left: `${pos.x}px`, top: `${pos.y}px`, width: size.w, height: size.h };

  return (
    <div
      ref={winRef}
      className={cn(
        "fixed z-drawer border border-line-2 bg-panel shadow-xl animate-in fade-in duration-150",
        docked ? "rounded-none" : "rounded-lg zoom-in-95",
      )}
      style={dockStyle}
    >
      {/* Header — draggable (drag vers un bord = dock, concept Odysseus) */}
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-line-1 cursor-move select-none bg-elevated/50"
        onPointerDown={onPointerDown}
      >
        <span className="text-xs font-medium text-foreground-secondary">
          {title}
          {docked && <span className="ml-2 text-foreground-tertiary">· docké {docked.side === "right" ? "à droite" : "à gauche"}</span>}
        </span>
        <button
          onClick={() => onOpenChange(false)}
          className="text-foreground-tertiary hover:text-foreground transition-colors"
          aria-label="Close"
        >
          <X size={14} />
        </button>
      </div>
      {/* Content */}
      <div className="p-3 overflow-y-auto" style={{ height: "calc(100% - 36px)" }}>
        {children}
      </div>
      {/* Resize handle (masqué quand docké — le drag du header redimensionne) */}
      {!docked && (
        <div
          className="absolute right-0 bottom-0 w-4 h-4 cursor-nwse-resize border-l border-t border-line-2"
          onPointerDown={onResizePointerDown}
        />
      )}
    </div>
  );
}