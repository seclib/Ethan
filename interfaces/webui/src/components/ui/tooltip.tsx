"use client";

/**
 * ETHAN WebUI — Tooltip (pattern Open-WebUI « Tooltip.svelte »).
 *
 * Implémentation sans dépendance externe, avec positionnement intelligent :
 *  - flip automatique haut ↔ bas quand l'espace manque dans le viewport ;
 *  - clamp horizontal pour que le tooltip ne déborde jamais des bords.
 * (OWUI utilise tippy.js — ajouter une lib nécessiterait un RFC, non justifié
 * ici : l'apparence et le comportement sont couverts par ce composant.)
 * L'attribut aria-label reste posé pour l'accessibilité.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export type TooltipSide = "top" | "bottom";

export interface TooltipProps {
  content: string;
  children: React.ReactElement<{ "aria-label"?: string }>;
  side?: TooltipSide;
  className?: string;
}

export function Tooltip({ content, children, side = "top", className }: TooltipProps) {
  const wrapperRef = React.useRef<HTMLSpanElement>(null);
  const [effectiveSide, setEffectiveSide] = React.useState<TooltipSide>(side);
  const [edgeClamp, setEdgeClamp] = React.useState(0);

  /** Positionnement adaptatif calendrier réel : flip + clamp aux bords.
   *  Mesuré au premier hover/focus via getBoundingClientRect (aucune lib). */
  const reposition = React.useCallback(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const vw = window.innerWidth;
    const tooltipWidth = 200;
    // Flip : si le côté demandé manque d'espace, on bascule.
    if (side === "top" && rect.top < 16 + 8) {
      setEffectiveSide("bottom");
    } else if (side === "bottom" && rect.bottom > window.innerHeight - 16 - 8) {
      setEffectiveSide("top");
    } else {
      setEffectiveSide(side);
    }
    // Clamp horizontal : garde le tooltip dans le viewport.
    const center = rect.left + rect.width / 2;
    const half = tooltipWidth / 2;
    const minX = 8 + half;
    const maxX = vw - 8 - half;
    const clamped = Math.max(minX, Math.min(maxX, center));
    setEdgeClamp(clamped - center);
  }, [side]);

  return (
    <span
      ref={wrapperRef}
      onMouseEnter={reposition}
      onFocus={reposition}
      className={cn("ethan-tooltip group/tooltip relative inline-flex", className)}
    >
      {React.cloneElement(children, { "aria-label": content })}
      <span
        role="tooltip"
        style={{
          transform: `translate(calc(-50% + ${edgeClamp}px))`,
        }}
        className={cn(
          "ethan-tooltip-bubble pointer-events-none absolute left-1/2 z-tooltip hidden whitespace-nowrap rounded-md border border-line-2 bg-bg-3 px-2 py-1 text-[11px] font-medium text-foreground shadow-lg",
          "transition-transform duration-75",
          "group-hover/tooltip:block group-focus-within/tooltip:block",
          effectiveSide === "top" ? "bottom-full mb-1.5" : "top-full mt-1.5",
        )}
      >
        {content}
      </span>
    </span>
  );
}
