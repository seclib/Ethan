"use client";

import * as React from "react";
import { ChevronDown, Server } from "lucide-react";
import { useActiveModel } from "@/components/features/assistant/hooks/use-active-model";
import type { Provider } from "@/lib/api/providers";

/**
 * Sélecteur de provider du header chat — ([Agent ▼] [Model ▼] [Provider ▼]).
 *
 * Règle AGENTS.md : aucune logique métier ici. Le composant délègue à
 * useActiveModel, qui :
 *  - liste les providers du ProviderManager Core (GET /providers) ;
 *  - propage la sélection au backend (PUT /providers/{id}/default) ;
 *  - réaligne le modèle actif sur le default_model du provider choisi.
 * Le payload chat porte ensuite provider_id + model (page.tsx → runStream).
 */
export function ProviderSelector() {
  const {
    providers,
    enabledProviders,
    selectedProviderId,
    activeProvider,
    setProvider,
    isPending,
  } = useActiveModel();
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (id: string) => {
    setProvider(id);
    setIsOpen(false);
  };

  const label = activeProvider?.name || selectedProviderId || "Provider";

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className="flex h-8 items-center gap-1.5 rounded-lg border border-line-1 bg-bg-1 px-2.5 text-xs font-medium text-foreground-secondary transition-colors hover:bg-bg-3 hover:text-foreground"
        title="Moteur actif (provider du Core)"
      >
        <Server size={13} className="text-accent" />
        <span className="max-w-[140px] truncate">{label}</span>
        {isPending ? (
          <span
            className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-amber"
            title="Synchronisation avec le Core…"
          />
        ) : (
          <ChevronDown size={13} className={`shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`} />
        )}
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-label="Sélection du provider"
          className="absolute right-0 top-full z-popover mt-1 max-h-72 min-w-[220px] overflow-y-auto rounded-xl border border-line-1 bg-bg-1 p-1 shadow-xl"
        >
          {providers.length === 0 && (
            <div className="px-3 py-4 text-center text-xs text-foreground-tertiary">
              Aucun provider configuré — voir Settings › Providers.
            </div>
          )}
          {enabledProviders.map((p: Provider) => {
            const isSelected = p.id === selectedProviderId;
            return (
              <div
                key={p.id}
                role="option"
                aria-selected={isSelected}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleSelect(p.id);
                  }
                }}
                onClick={() => handleSelect(p.id)}
                className={`flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                  isSelected
                    ? "bg-accent/20 text-foreground"
                    : "text-foreground-secondary hover:bg-bg-3"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{p.name}</span>
                    {!p.enabled && (
                      <span className="shrink-0 rounded bg-muted-foreground/20 px-1 py-0.5 text-[10px] text-foreground-tertiary">
                        désactivé
                      </span>
                    )}
                  </div>
                  {p.default_model && (
                    <span className="block truncate font-mono text-[10px] text-foreground-tertiary">
                      {p.default_model}
                    </span>
                  )}
                </div>
                {p.is_default && (
                  <span className="shrink-0 rounded-full bg-accent/15 px-1.5 py-0.5 text-[10px] text-accent">
                    défaut
                  </span>
                )}
                {isSelected && (
                  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0 text-accent">
                    <path
                      fillRule="evenodd"
                      d="M16.7 5.3a1 1 0 010 1.4l-7.5 7.5a1 1 0 01-1.4 0L3.3 9.7a1 1 0 111.4-1.4l3.8 3.8 6.8-6.8a1 1 0 011.4 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
