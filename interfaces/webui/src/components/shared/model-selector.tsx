"use client";

import * as React from "react";
import { useActiveModel } from "@/features/assistant/hooks/use-active-model";
import { useModels, type PinnedModel } from "@/features/providers/hooks/use-models";
import type { ProviderModel } from "@/core/api/providers.types";

interface ModelSelectorProps {
  variant?: "full" | "compact";
  className?: string;
}

/**
 * Sélecteur de modèle inspiré d'Open-WebUI.
 * - full    : dropdown avec recherche, épinglage, capabilities
 * - compact : indicateur inline "🟢 Ollama / qwen2.5-coder"
 * Délègue la sélection effective à useActiveModel (persistance + backend).
 */
export function ModelSelector({ variant = "full", className = "" }: ModelSelectorProps) {
  const [search, setSearch] = React.useState("");
  const [isOpen, setIsOpen] = React.useState(false);
  const {
    activeProvider,
    selectedModel,
    setProvider,
    setModel,
    enabledProviders,
  } = useActiveModel();
  const { pinned, pinModel, unpinModel, isPinned, searchModels } = useModels();

  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Fermer le dropdown au clic extérieur
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (variant === "compact") {
    const isConnected = activeProvider?.status === "connected";
    return (
      <div className={`flex items-center gap-2 text-xs text-foreground-tertiary ${className}`}>
        <span className={isConnected ? "text-green-400" : "text-foreground-tertiary"}>
          {isConnected ? "🟢" : "⚪"}
        </span>
        <span className="font-medium text-foreground-secondary">
          {activeProvider?.name || "No provider"}
        </span>
        {selectedModel && (
          <>
            <span className="text-foreground-tertiary">/</span>
            <span className="font-mono text-foreground-tertiary">{selectedModel}</span>
          </>
        )}
      </div>
    );
  }

  const allModels = searchModels(search);
  const pinnedModels = allModels.filter((m) => isPinned(m.providerId, m.id));
  const otherModels = allModels.filter((m) => !isPinned(m.providerId, m.id));

  const handleSelect = (providerId: string, modelId: string) => {
    setProvider(providerId);
    setModel(modelId);
    setIsOpen(false);
    setSearch("");
  };

  const handleTogglePin = (e: React.MouseEvent, providerId: string, modelId: string) => {
    e.stopPropagation();
    if (isPinned(providerId, modelId)) {
      unpinModel(providerId, modelId);
    } else {
      pinModel(providerId, modelId);
    }
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Bouton principal */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-md border border-line-1 bg-bg-2 px-3 py-1.5 text-sm text-foreground hover:bg-bg-3 focus:outline-none focus:ring-2 focus:ring-accent/50"
      >
        <span className="font-medium">
          {activeProvider?.name || "Select provider"}
        </span>
        <span className="text-foreground-tertiary">/</span>
        <span className="font-mono text-foreground-secondary">
          {selectedModel || "model"}
        </span>
        <svg
          className={`h-4 w-4 text-foreground-tertiary transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-2 w-80 rounded-md border border-line-1 bg-bg-2 shadow-lg">
          {/* Barre de recherche */}
          <div className="p-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search models..."
              className="w-full rounded-md border border-line-1 bg-bg-1 px-3 py-1.5 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
              autoFocus
            />
          </div>

          {/* Liste des modèles */}
          <div className="max-h-96 overflow-y-auto p-2">
            {pinnedModels.length > 0 && (
              <div className="mb-2">
                <div className="px-2 py-1 text-xs font-medium text-foreground-tertiary uppercase tracking-wide">
                  Pinned
                </div>
                {pinnedModels.map((model) => (
                  <ModelItem
                    key={`${model.providerId}-${model.id}`}
                    model={model}
                    isSelected={activeProvider?.id === model.providerId && selectedModel === model.id}
                    isPinned={true}
                    onSelect={() => handleSelect(model.providerId, model.id)}
                    onTogglePin={() => handleTogglePin(null as unknown as React.MouseEvent, model.providerId, model.id)}
                  />
                ))}
              </div>
            )}

            {otherModels.length > 0 && (
              <div>
                {pinnedModels.length > 0 && (
                  <div className="px-2 py-1 text-xs font-medium text-foreground-tertiary uppercase tracking-wide">
                    All Models
                  </div>
                )}
                {otherModels.map((model) => (
                  <ModelItem
                    key={`${model.providerId}-${model.id}`}
                    model={model}
                    isSelected={activeProvider?.id === model.providerId && selectedModel === model.id}
                    isPinned={false}
                    onSelect={() => handleSelect(model.providerId, model.id)}
                    onTogglePin={() => handleTogglePin(null as unknown as React.MouseEvent, model.providerId, model.id)}
                  />
                ))}
              </div>
            )}

            {allModels.length === 0 && (
              <div className="px-2 py-4 text-center text-sm text-foreground-tertiary">
                {search ? "No models found" : "No models available"}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface ModelItemProps {
  model: ProviderModel & { providerId: string; providerName: string };
  isSelected: boolean;
  isPinned: boolean;
  onSelect: () => void;
  onTogglePin: () => void;
}

function ModelItem({ model, isSelected, isPinned, onSelect, onTogglePin }: ModelItemProps) {
  return (
    <div
      onClick={onSelect}
      className={`flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer transition-colors ${
        isSelected
          ? "bg-accent/20 text-foreground"
          : "hover:bg-bg-3 text-foreground-secondary"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">{model.name}</span>
          {model.is_local && (
            <span className="text-xs text-foreground-tertiary">(local)</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-foreground-tertiary">
          <span>{model.providerName}</span>
          {model.context_length > 0 && (
            <>
              <span>•</span>
              <span>{model.context_length.toLocaleString()} ctx</span>
            </>
          )}
        </div>
      </div>
      <button
        onClick={onTogglePin}
        className={`p-1 rounded hover:bg-bg-1 ${
          isPinned ? "text-yellow-400" : "text-foreground-tertiary"
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
