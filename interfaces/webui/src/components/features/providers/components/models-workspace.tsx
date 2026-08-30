"use client";

/**
 * ETHAN WebUI — ModelsWorkspace (card-grid refactor)
 * Catalogue des modèles LLM (discovered + custom). Inspiré d'Open-WebUI :
 * recherche en tête + grille de cartes avec menu contextuel. Réutilise les
 * hooks existants (useModels) — aucune logique Core réinventée.
 */

import * as React from "react";
import { useModels } from "@/components/features/providers/hooks/use-models";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Database,
  LoaderCircle,
  Star,
  StarHalf,
  Search,
  MoreVertical,
} from "lucide-react";
import type { ModelInfo } from "@/lib/api/models";
import { cn } from "@/lib/utils";

const CAPABILITIES_COLORS: Record<string, "success" | "info" | "accent" | "purple" | "gold" | "dim"> = {
  chat: "info",
  embedding: "success",
  reasoning: "accent",
  vision: "purple",
  audio: "gold",
};

const PROVIDER_LABELS: Record<string, string> = {
  ollama: "Ollama",
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
};

export function ModelsWorkspace() {
  const { models, isLoading, searchModels, pinModel, unpinModel, isPinned } = useModels();

  const [searchQuery, setSearchQuery] = React.useState("");
  const [showPinnedOnly, setShowPinnedOnly] = React.useState(false);
  const [menuModel, setMenuModel] = React.useState<ModelInfo | null>(null);
  const [menuPos, setMenuPos] = React.useState<{ x: number; y: number } | null>(null);

  const filtered = React.useMemo(() => {
    let results = searchModels(searchQuery);
    if (showPinnedOnly) {
      results = results.filter((m) => isPinned(m.provider, m.id));
    }
    return results;
  }, [searchQuery, showPinnedOnly, searchModels, isPinned]);

  const handlePin = (m: ModelInfo) => {
    if (isPinned(m.provider, m.id)) unpinModel(m.provider, m.id);
    else pinModel(m.provider, m.id);
  };

  const handleMenu = (e: React.MouseEvent, model: ModelInfo) => {
    e.stopPropagation();
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setMenuPos({ x: r.right - 8, y: Math.min(r.bottom + 8, window.innerHeight - 220) });
    setMenuModel(model);
  };

  React.useEffect(() => {
    if (!menuModel) return;
    const onDoc = () => setMenuModel(null);
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, [menuModel]);

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Models"
        description="Catalogue des modèles LLM — discovered et custom, issus des providers du Core."
        icon={<Database className="h-5 w-5" />}
        count={models.length}
        actions={
          <Button
            size="sm"
            variant={showPinnedOnly ? "default" : "secondary"}
            onClick={() => setShowPinnedOnly(!showPinnedOnly)}
          >
            <Star className="h-4 w-4" />
            {showPinnedOnly ? "Tous" : "Favoris"}
          </Button>
        }
      />
      <div className="flex items-center justify-between border-b border-line-1 px-4 py-2">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher un modèle…"
            className="w-full rounded-lg border border-line-1 bg-bg-1 py-1.5 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto">
        {(isLoading || (models.length === 0 && !isLoading)) && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
              <Database className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">
              {isLoading
                ? "Chargement des modèles…"
                : searchQuery
                  ? "Aucun modèle trouvé"
                  : "Aucun modèle disponible"}
            </h2>
            {!isLoading && (
              <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
                Activez un fournisseur dans <strong>Fournisseurs</strong> pour voir ses modèles.
              </p>
            )}
          </div>
        )}
        {!isLoading && filtered.length === 0 && models.length > 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
              <Database className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">
              {searchQuery ? "Aucun modèle trouvé" : "Aucun modèle disponible"}
            </h2>
            <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
              Activez un fournisseur dans <strong>Fournisseurs</strong> pour voir ses modèles.
            </p>
          </div>
        )}
        {!isLoading && filtered.length > 0 && (
          <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((model) => (
              <ModelCard
                key={`${model.provider}:${model.id}`}
                model={model}
                pinned={isPinned(model.provider, model.id)}
                onPin={handlePin}
                onMenu={handleMenu}
              />
            ))}
          </div>
        )}
      </div>

      {menuModel && menuPos && (
        <div
          className="fixed z-50 min-w-[170px] rounded-lg border border-line-1 bg-bg-1/95 py-1 shadow-lg backdrop-blur-sm"
          style={{ left: menuPos.x, top: menuPos.y }}
        >
          <button
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => { handlePin(menuModel); setMenuModel(null); }}
          >
            {isPinned(menuModel.provider, menuModel.id) ? "Désépingler" : "Épingler"}
          </button>
          <button
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => setMenuModel(null)}
          >
            Voir la fiche
          </button>
        </div>
      )}
    </div>
  );
}

interface ModelCardProps {
  model: ModelInfo;
  pinned: boolean;
  onPin: (m: ModelInfo) => void;
  onMenu: (e: React.MouseEvent, model: ModelInfo) => void;
}

function ModelCard({ model, pinned, onPin, onMenu }: ModelCardProps) {
  const providerLabel = PROVIDER_LABELS[model.provider] || model.provider;
  const caps = model.capabilities || [];

  return (
    <div className="group relative flex flex-col rounded-xl border border-line-1 bg-bg-1/40 p-4 transition-all hover:border-accent/50 hover:shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
            <Database className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{model.name}</p>
            <p className="text-xs text-foreground-tertiary truncate max-w-[180px]">
              {model.is_local ? "Local" : providerLabel}
            </p>
          </div>
        </div>
        <button
          onClick={(e) => onMenu(e, model)}
          className="rounded p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-bg-2"
          aria-label="Plus d'actions"
        >
          <MoreVertical size={14} />
        </button>
      </div>

      <div className="mt-3 flex flex-col gap-2">
        <p className="text-[11px] text-foreground-tertiary">
          {model.model} · {model.context_length?.toLocaleString() ?? "—"} ctx
        </p>
        {caps.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {caps.slice(0, 4).map((cap) => (
              <Badge
                key={cap}
                variant={CAPABILITIES_COLORS[cap] || "dim"}
                size="sm"
              >
                {cap}
              </Badge>
            ))}
            {caps.length > 4 && (
              <Badge variant="dim" size="sm">+{caps.length - 4}</Badge>
            )}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-foreground-tertiary">
        <span className="flex items-center gap-1">
          <StarHalf className="h-3 w-3" />
          Qualité: {Math.round((model.quality_score || 0) * 100)}%
        </span>
        {model.is_available ? (
          <Badge variant="success" size="sm">Disponible</Badge>
        ) : (
          <Badge variant="error" size="sm">Indisponible</Badge>
        )}
      </div>

      <div className="mt-auto pt-2">
        <Button
          size="sm"
          variant="ghost"
          className={cn("h-6 w-6 p-0", pinned ? "opacity-100" : "opacity-0 group-hover:opacity-100")}
          onClick={(e) => { e.stopPropagation(); onPin(model); }}
          title={pinned ? "Désépingler" : "Épingler"}
        >
          <Star className={pinned ? "h-4 w-4 fill-accent text-accent" : "h-4 w-4"} />
        </Button>
      </div>
    </div>
  );
}
