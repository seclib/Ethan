"use client";

import { useUtcClock } from "@/lib/hydration-safe-time";

/**
 * ETHAN WebUI — Bandeau supérieur de l'écran d'authentification.
 *
 * L'horloge UTC utilise `useUtcClock` : le premier rendu est identique côté
 * serveur et côté client (placeholder), l'heure réelle n'apparaît qu'après
 * l'hydratation. Sans cela, l'heure figée au build dans le HTML prérendu de
 * `/login` différait du premier rendu client → React #418.
 */

export function TopBar() {
  const utcTime = useUtcClock();

  return (
    <header className="fixed top-0 left-0 right-0 z-dropdown h-10">
      <div className="h-full flex items-center justify-between px-6 border-b border-white/5 bg-[#07090d]">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[0.2em] text-cyan-400 uppercase select-none">
            Ethan OS
          </span>
          <span className="w-px h-3 bg-white/10" aria-hidden="true" />
          <span className="text-[10px] tracking-[0.15em] text-white/30 uppercase select-none">
            Classified Access
          </span>
        </div>

        {/* Right: UTC Clock */}
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.5)]" />
          <time
            className="text-[11px] font-mono tracking-[0.1em] text-white/40 select-none"
            dateTime={utcTime}
          >
            {utcTime}
          </time>
        </div>
      </div>
    </header>
  );
}
