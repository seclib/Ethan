"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { useActiveModel } from "@/components/features/assistant/hooks/use-active-model";
import { useModels, type PinnedModel } from "@/components/features/providers/hooks/use-models";
import type { ModelInfo } from "@/lib/api/models";

interface ModelSelectorProps {
  variant?: "full" | "compact";
  className?: string;
  /**
   * Ouverture contrôlée optionnelle (pattern semi-controlled) : sans ces props,
   * comportement interne inchangé (sidebar, top-bar). Avec, l'état est possédé
   * par le parent — utilisé par la ChatContextBar pour dérouler le menu modèle.
   */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

/**
 * Sélecteur de modèle inspiré d'Open-WebUI.
 * - full    : dropdown avec recherche, épinglage, capabilities
 * - compact : indicateur inline "🟢 Ollama / qwen2.5-coder"
 * Délègue la sélection effective à useActiveModel (persistance + backend).
 */
export function ModelSelector({
  variant = "full",
  className = "",
  open,
  onOpenChange,
}: ModelSelectorProps) {
  const [search, setSearch] = React.useState("");
  const [internalOpen, setInternalOpen] = React.useState(false);
  const isControlled = open !== undefined && onOpenChange !== undefined;
  const isOpen = isControlled ? open : internalOpen;
  const setOpen = React.useCallback(
    (next: boolean) => {
      if (!isControlled) setInternalOpen(next);
      onOpenChange?.(next);
    },
    [isControlled, onOpenChange],
  );
  const {
    activeProvider,
    selectedModel,
    setProvider,
    setModel,
    enabledProviders,
  } = useActiveModel();
  const { pinned, pinModel, unpinModel, isPinned, searchModels, isLoading: modelsLoading } = useModels();

  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Fermer le dropdown au clic extérieur
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setOpen]);

  const isCompact = variant === "compact";

  const allModels = searchModels(search);
  const pinnedModels = allModels.filter((m) => isPinned(m.provider, m.id));
  const otherModels = allModels.filter((m) => !isPinned(m.provider, m.id));

  /** Regroupement par provider (target Open-WebUI : Ollama / Other Providers…). */
  const groupedByProvider = otherModels.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    (acc[m.provider] ||= []).push(m);
    return acc;
  }, {});
  const providerGroups = Object.entries(groupedByProvider).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );

  const handleSelect = (providerId: string, modelId: string) => {
    setProvider(providerId);
    setModel(modelId);
    setOpen(false);
    setSearch("");
  };

  const handleTogglePin = (providerId: string, modelId: string) => {
    if (isPinned(providerId, modelId)) {
      unpinModel(providerId, modelId);
    } else {
      pinModel(providerId, modelId);
    }
  };

  // ── Navigation clavier (pattern Open-WebUI Selector.svelte : flèches + Enter + Escape) ──
  const flatItems = React.useMemo(
    () => [...pinnedModels, ...otherModels],
    [pinnedModels, otherModels],
  );
  const [arrowIdx, setArrowIdx] = React.useState(0);
  // La saisie ramène la sélection clavier en tête de liste (comportement OWUI).
  React.useEffect(() => {
    setArrowIdx(0);
  }, [search]);

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (flatItems.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setArrowIdx((i) => Math.min(i + 1, flatItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setArrowIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const m = flatItems[arrowIdx];
      if (m && m.is_available !== false) handleSelect(m.provider, m.id);
      return;
    } else {
      return;
    }
    // Scroll de l'item surligné au centre de la liste (comme OWUI).
    requestAnimationFrame(() => {
      dropdownRef.current
        ?.querySelector('[data-arrow-selected="true"]')
        ?.scrollIntoView({ block: "center" });
    });
  };

  // ── Déclencheur (compact cliquable / full borduré) ──────────
  const isConnected = activeProvider?.status === "connected";
  const trigger = isCompact ? (
    <button
      type="button"
      onClick={() => setOpen(!isOpen)}
      title="Changer de modèle"
      aria-haspopup="listbox"
      aria-expanded={isOpen}
      className="flex items-center gap-1.5 rounded-md px-1.5 py-1 text-xs text-foreground-tertiary transition-colors hover:bg-bg-3 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
    >
      <span
        className={`h-2 w-2 shrink-0 rounded-full ${
          isConnected ? "bg-green-500" : "bg-muted-foreground/40"
        }`}
        title={activeProvider?.status || "unknown"}
      />
      <span className="font-medium text-foreground-secondary">
        {activeProvider?.name || "No provider"}
      </span>
      {selectedModel && (
        <>
          <span>/</span>
          <span className="font-mono">{selectedModel}</span>
        </>
      )}
      <ChevronDown
        className={`h-3.5 w-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`}
      />
    </button>
  ) : (
    <button
      type="button"
      onClick={() => setOpen(!isOpen)}
      aria-haspopup="listbox"
      aria-expanded={isOpen}
      className="flex items-center gap-2 rounded-md border border-line-1 bg-bg-2 px-3 py-1.5 text-sm text-foreground hover:bg-bg-3 focus:outline-none focus:ring-2 focus:ring-accent/50"
    >
      <span className="font-medium">
        {activeProvider?.name || "Select provider"}
      </span>
      <span className="text-foreground-tertiary">/</span>
      <span className="font-mono text-foreground-secondary">
        {selectedModel || "model"}
      </span>
      <ChevronDown
        className={`h-4 w-4 text-foreground-tertiary transition-transform ${isOpen ? "rotate-180" : ""}`}
      />
    </button>
  );

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {trigger}

      {/* Dropdown partagé full / compact */}
      {isOpen && (
        <div
          className={`absolute z-popover mt-2 w-80 rounded-md border border-line-1 bg-bg-2 shadow-lg ${
            isCompact ? "right-0" : "left-0"
          }`}
          role="listbox"
        >
          {/* Barre de recherche */}
          <div className="p-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search models..."
              aria-label="Search In Models"
              className="w-full rounded-md border border-line-1 bg-bg-1 px-3 py-1.5 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
              autoFocus
            />
          </div>

          {/* Liste des modèles */}
          <div className="max-h-96 overflow-y-auto p-2">
            {modelsLoading && allModels.length === 0 && (
              <div className="px-2 py-5 text-center text-sm text-foreground-tertiary">
                Chargement des modèles…
              </div>
            )}

            {!modelsLoading && pinnedModels.length > 0 && (
              <div className="mb-2">
                <div className="px-2 py-1 text-xs font-medium text-foreground-tertiary uppercase tracking-wide">
                  Pinned
                </div>
                {pinnedModels.map((model) => (
                  <ModelItem
                    key={`${model.provider}-${model.id}`}
                    model={model}
                    isSelected={activeProvider?.id === model.provider && selectedModel === model.id}
                    isPinned={true}
                    arrowSelected={flatItems[arrowIdx] === model}
                    onSelect={() => handleSelect(model.provider, model.id)}
                    onTogglePin={() => handleTogglePin(model.provider, model.id)}
                  />
                ))}
              </div>
            )}

            {!modelsLoading && providerGroups.length > 0 &&
              providerGroups.map(([provider, models]) => (
                <div key={provider} className="mb-1">
                  <div className="px-2 py-1 text-xs font-medium text-foreground-tertiary uppercase tracking-wide">
                    {provider}
                  </div>
                  {models.map((model) => (
                    <ModelItem
                      key={`${model.provider}-${model.id}`}
                      model={model}
                      isSelected={activeProvider?.id === model.provider && selectedModel === model.id}
                      isPinned={false}
                      arrowSelected={flatItems[arrowIdx] === model}
                      onSelect={() => handleSelect(model.provider, model.id)}
                      onTogglePin={() => handleTogglePin(model.provider, model.id)}
                    />
                  ))}
                </div>
              ))}

            {!modelsLoading && allModels.length === 0 && (
              <div className="px-2 py-5 text-center text-sm text-foreground-tertiary">
                {search ? `Aucun modèle pour « ${search} »` : "Aucun modèle disponible"}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface ModelItemProps {
  model: ModelInfo;
  isSelected: boolean;
  isPinned: boolean;
  /** Item courant de la navigation clavier flèches (pattern Open-WebUI). */
  arrowSelected?: boolean;
  onSelect: () => void;
  onTogglePin: () => void;
}

function ModelItem({ model, isSelected, isPinned, arrowSelected, onSelect, onTogglePin }: ModelItemProps) {
  // Modèle déclaré indisponible par le Core (provider offline, modèle supprimé…) :
  // l'item est grisé et non sélectionnable, mais l'épinglage reste possible.
  const unavailable = model.is_available === false;

  return (
    <div
      role="option"
      aria-selected={isSelected}
      aria-disabled={unavailable}
      tabIndex={unavailable ? -1 : 0}
      data-arrow-selected={arrowSelected ? "true" : undefined}
      onKeyDown={(e) => {
        if (unavailable) return;
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      onClick={() => {
        if (!unavailable) onSelect();
      }}
      title={unavailable ? "Modèle indisponible" : undefined}
      className={`flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors ${
        unavailable
          ? "cursor-not-allowed opacity-50"
          : isSelected
            ? "cursor-pointer bg-accent/20 text-foreground"
            : "cursor-pointer hover:bg-bg-3 text-foreground-secondary"
      } ${arrowSelected ? "ring-1 ring-accent/60" : ""}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">{model.name}</span>
          {model.is_local && (
            <span className="text-xs text-foreground-tertiary">(local)</span>
          )}
          {unavailable && (
            <span className="shrink-0 rounded bg-muted-foreground/20 px-1 py-0.5 text-[10px] font-medium text-foreground-tertiary">
              Indisponible
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-foreground-tertiary">
          <span>{model.provider}</span>
          {model.context_length > 0 && (
            <>
              <span>•</span>
              <span>{model.context_length.toLocaleString()} ctx</span>
            </>
          )}
        </div>
      </div>
      <button
        type="button"
        onClick={(e) => {
          // stopPropagation : épingler ne doit PAS sélectionner le modèle.
          e.stopPropagation();
          onTogglePin();
        }}
        aria-label={isPinned ? "Désépingler le modèle" : "Épingler le modèle"}
        className={`p-1 rounded hover:bg-bg-1 ${
          isPinned ? "text-amber" : "text-foreground-tertiary"
        }`}
        title={isPinned ? "Unpin" : "Pin"}
      >
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
        </svg>
      </button>
    </div>
  );
}
