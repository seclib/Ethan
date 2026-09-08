"use client";

/**
 * ETHAN WebUI — ModelsWorkspace (Provider → Models)
 *
 * UX inspirée d'Open-WebUI / AnythingLLM :
 *   Provider → Modèles disponibles → Sélection du modèle → Configuration.
 *
 * - Un provider se sélectionne à la souris (clic) : ses modèles sont chargés
 *   depuis l'API Core (aucune liste statique, lazy-load par provider).
 * - Un modèle cliqué devient le modèle actif de la session (sélection visible).
 * - Le « modèle actif » persistant = default_model du provider (endpoint réel
 *   PUT /providers/{id} avec default_model).
 * - Paramètres affichés uniquement s'ils sont réellement supportés.
 *
 * Aucune logique métier : tout passe par useModels/useProviders → API Core.
 */

import * as React from "react";
import { useModels } from "@/components/features/providers/hooks/use-models";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
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
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Settings2,
  ArrowLeft,
  X,
} from "lucide-react";
import type { ModelInfo } from "@/lib/api/models";
import type { Provider } from "@/lib/api/providers";
import { cn } from "@/lib/utils";

const CAPABILITIES_COLORS: Record<string, "success" | "info" | "accent" | "purple" | "gold" | "dim"> = {
  chat: "info",
  embedding: "success",
  reasoning: "accent",
  vision: "purple",
  audio: "gold",
};

const STATUS_COLORS: Record<string, "success" | "info" | "accent" | "purple" | "gold" | "warning" | "error" | "dim"> = {
  connected: "success",
  connecting: "info",
  disconnected: "dim",
  error: "error",
  pending: "warning",
  unknown: "dim",
};

const STORAGE_PINNED_PROVIDERS = "ethan.pinned-providers";

export function ModelsWorkspace() {
  const {
    providers,
    enabledProviders,
    providersLoading,
    providersError,
    selectedProvider,
    setSelectedProvider,
    models,
    modelsLoading,
    modelsError,
    refetchModels,
    selectedModel,
    setSelectedModel,
    pinModel,
    unpinModel,
    isPinned,
    searchModels,
  } = useModels();

  const { updateProviderAsync } = useProviders();

  const [searchQuery, setSearchQuery] = React.useState("");
  const [showPinnedOnly, setShowPinnedOnly] = React.useState(false);
  const [menuModel, setMenuModel] = React.useState<ModelInfo | null>(null);
  const [menuPos, setMenuPos] = React.useState<{ x: number; y: number } | null>(null);
  const [isSettingDefault, setIsSettingDefault] = React.useState(false);

  // Épinglage des providers (préférence UI locale, pas de logique métier)
  const [pinnedProviders, setPinnedProviders] = React.useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set();
    const raw = window.localStorage.getItem(STORAGE_PINNED_PROVIDERS);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  });

  const togglePinnedProvider = (id: string) => {
    setPinnedProviders((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      window.localStorage.setItem(STORAGE_PINNED_PROVIDERS, JSON.stringify([...next]));
      return next;
    });
  };

  // Modèles filtrés (recherche + favoris) — toujours issus du provider sélectionné
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

  // « Modèle actif » réel : default_model du provider (PUT /providers/{id})
  const handleSetActiveModel = async () => {
    if (!selectedModel || !selectedProvider) return;
    setIsSettingDefault(true);
    try {
      await updateProviderAsync(selectedProvider, { default_model: selectedModel.model });
    } finally {
      setIsSettingDefault(false);
    }
  };

  React.useEffect(() => {
    if (!menuModel) return;
    const onDoc = () => setMenuModel(null);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuModel(null);
    };
    const onReflow = () => setMenuModel(null);
    document.addEventListener("click", onDoc);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onReflow, true);
    window.addEventListener("resize", onReflow);
    return () => {
      document.removeEventListener("click", onDoc);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onReflow, true);
      window.removeEventListener("resize", onReflow);
    };
  }, [menuModel]);

  // ── Étape 1 : Provider — aucun provider sélectionné → grille cliquable ──
  if (!selectedProvider) {
    const visibleProviders = showPinnedOnly
      ? enabledProviders.filter((p) => pinnedProviders.has(p.id))
      : enabledProviders;

    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Models"
          description="Sélectionnez un fournisseur pour voir uniquement ses modèles disponibles."
          icon={<Database className="h-5 w-5" />}
          count={visibleProviders.length}
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
        <div className="flex-1 min-h-0 overflow-y-auto">
          {providersLoading && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <LoaderCircle className="mb-4 h-8 w-8 animate-spin text-accent" />
              <p className="text-sm text-foreground-tertiary">Chargement des fournisseurs…</p>
            </div>
          )}
          {!providersLoading && providersError && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <AlertCircle className="mb-4 h-8 w-8 text-red" />
              <p className="text-sm text-red">Erreur : {providersError}</p>
            </div>
          )}
          {!providersLoading && !providersError && visibleProviders.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
                <Database className="h-6 w-6 text-accent" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">
                {showPinnedOnly ? "Aucun fournisseur favori" : "Aucun fournisseur activé"}
              </h2>
              <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
                Activez un fournisseur dans <strong>Fournisseurs</strong> pour voir ses modèles.
              </p>
            </div>
          )}
          {!providersLoading && !providersError && visibleProviders.length > 0 && (
            <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {visibleProviders.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  isPinned={pinnedProviders.has(provider.id)}
                  onPin={togglePinnedProvider}
                  onClick={() => setSelectedProvider(provider.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Étapes 2-4 : Models → Sélection → Configuration ──
  const currentProvider = providers.find((p) => p.id === selectedProvider);
  const providerName = currentProvider?.name || selectedProvider;
  const providerConnected =
    currentProvider?.status === "connected" || currentProvider?.status === "connecting";

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Models"
        description={`Modèles disponibles chez ${providerName}`}
        icon={<Database className="h-5 w-5" />}
        count={filtered.length}
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSelectedProvider(null);
                setSelectedModel(null);
                setSearchQuery("");
              }}
            >
              <ArrowLeft className="h-4 w-4" />
              Fournisseurs
            </Button>
            <Button
              size="sm"
              variant={showPinnedOnly ? "default" : "secondary"}
              onClick={() => setShowPinnedOnly(!showPinnedOnly)}
            >
              <Star className="h-4 w-4" />
              {showPinnedOnly ? "Tous" : "Favoris"}
            </Button>
          </div>
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
        <Button size="sm" variant="ghost" onClick={() => refetchModels()} title="Rafraîchir">
          <RefreshCw className={cn("h-4 w-4", modelsLoading && "animate-spin")} />
        </Button>
      </div>

      {/* Étape 4 : configuration réelle du modèle sélectionné */}
      {selectedModel && (
        <ModelConfigPanel
          model={selectedModel}
          provider={currentProvider}
          isDefault={currentProvider?.default_model === selectedModel.model}
          isSetting={isSettingDefault}
          onSetDefault={handleSetActiveModel}
          onClear={() => setSelectedModel(null)}
        />
      )}

      <div className="flex-1 min-h-0 overflow-y-auto">
        {modelsLoading && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <LoaderCircle className="mb-4 h-8 w-8 animate-spin text-accent" />
            <p className="text-sm text-foreground-tertiary">Chargement des modèles…</p>
          </div>
        )}
        {!modelsLoading && modelsError && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="mb-4 h-8 w-8 text-red" />
            <p className="text-sm text-red">Erreur : {modelsError}</p>
            <Button size="sm" variant="outline" className="mt-3" onClick={() => refetchModels()}>
              Réessayer
            </Button>
          </div>
        )}
        {!modelsLoading && !modelsError && (
          <>
            {!providerConnected && (
              <div className="mx-4 my-3 rounded-lg border border-amber-soft bg-amber-soft/60 px-3 py-2 text-sm text-amber">
                <AlertCircle className="mr-2 inline h-4 w-4" />
                Le fournisseur <strong>{providerName}</strong> n'est pas connecté — les modèles
                listés peuvent être indisponibles.
              </div>
            )}
            {filtered.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
                  <Database className="h-6 w-6 text-accent" />
                </div>
                <h2 className="text-lg font-semibold text-foreground">
                  {searchQuery ? "Aucun modèle trouvé" : "Aucun modèle disponible"}
                </h2>
                <p className="mt-2 max-w-sm text-sm text-foreground-tertiary">
                  {searchQuery
                    ? "Aucun modèle ne correspond à votre recherche."
                    : "Ce fournisseur n'expose aucun modèle pour le moment."}
                </p>
              </div>
            )}
            {filtered.length > 0 && (
              <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {filtered.map((model) => (
                  <ModelCard
                    key={`${model.provider}:${model.id}`}
                    model={model}
                    pinned={isPinned(model.provider, model.id)}
                    isSelected={
                      selectedModel?.id === model.id && selectedModel?.provider === model.provider
                    }
                    onPin={handlePin}
                    onMenu={handleMenu}
                    onClick={() => setSelectedModel(model)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {menuModel && menuPos && (
        <div
          className="fixed z-popover min-w-[170px] rounded-lg border border-line-1 bg-bg-1/95 py-1 shadow-lg backdrop-blur-sm"
          style={{ left: menuPos.x, top: menuPos.y }}
        >
          <button
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => {
              handlePin(menuModel);
              setMenuModel(null);
            }}
          >
            {isPinned(menuModel.provider, menuModel.id) ? "Désépingler" : "Épingler"}
          </button>
          <button
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-bg-2"
            onClick={() => {
              setSelectedModel(menuModel);
              setMenuModel(null);
            }}
          >
            Configurer
          </button>
        </div>
      )}
    </div>
  );
}

// ── Étape 4 : panneau de configuration réelle du modèle sélectionné ──
// N'affiche QUE les données réellement renvoyées par le Core. Aucun champ
// d'inférence éditable : aucun endpoint backend ne les expose pour les
// modèles découverts. La seule action réelle = default_model du provider.
function ModelConfigPanel({
  model,
  provider,
  isDefault,
  isSetting,
  onSetDefault,
  onClear,
}: {
  model: ModelInfo;
  provider: Provider | undefined;
  isDefault: boolean;
  isSetting: boolean;
  onSetDefault: () => void;
  onClear: () => void;
}) {
  const caps = model.capabilities || [];

  return (
    <div className="mx-4 mt-3 rounded-xl border border-line-1 bg-bg-1/60 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10">
            <Settings2 className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{model.name}</p>
            <p className="text-xs text-foreground-tertiary">
              {model.model} · {model.provider}
              {model.is_local ? " · local" : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isDefault ? (
            <Badge variant="accent" size="sm">Modèle actif</Badge>
          ) : (
            provider && (
              <Button size="sm" variant="secondary" disabled={isSetting} onClick={onSetDefault}>
                Définir comme modèle actif
              </Button>
            )
          )}
          <Button size="sm" variant="ghost" onClick={onClear} title="Fermer">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs sm:grid-cols-4">
        <div>
          <p className="text-foreground-tertiary">Source</p>
          <p className="text-foreground">{model.source}</p>
        </div>
        <div>
          <p className="text-foreground-tertiary">Contexte</p>
          <p className="text-foreground">{model.context_length?.toLocaleString() ?? "—"}</p>
        </div>
        <div>
          <p className="text-foreground-tertiary">Qualité</p>
          <p className="text-foreground">{Math.round((model.quality_score || 0) * 100)}%</p>
        </div>
        <div>
          <p className="text-foreground-tertiary">Disponibilité</p>
          <p className="text-foreground">{model.is_available ? "Disponible" : "Indisponible"}</p>
        </div>
      </div>

      {caps.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {caps.map((cap) => (
            <Badge key={cap} variant={CAPABILITIES_COLORS[cap] || "dim"} size="sm">
              {cap}
            </Badge>
          ))}
        </div>
      )}

      <p className="mt-3 text-[11px] text-foreground-tertiary">
        Le « modèle actif » correspond au <code>default_model</code> du fournisseur dans ETHAN
        Core (source de vérité).
      </p>
    </div>
  );
}

// ── Étape 1 : carte provider cliquable ──
interface ProviderCardProps {
  provider: Provider;
  isPinned: boolean;
  onPin: (id: string) => void;
  onClick: () => void;
}

function ProviderCard({ provider, isPinned, onPin, onClick }: ProviderCardProps) {
  const statusVariant = STATUS_COLORS[provider.status] || "dim";
  const modelCount = provider.models?.length || 0;

  return (
    <div
      className={cn(
        "group relative flex cursor-pointer flex-col rounded-xl border border-line-1 bg-bg-1/40 p-4 transition-all hover:border-accent/50 hover:shadow-sm",
        isPinned && "border-accent/40",
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
            <Database className="h-5 w-5 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{provider.name}</p>
            <p className="max-w-[180px] truncate text-xs text-foreground-tertiary">
              {provider.type}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            className={cn(
              "rounded p-1 transition-opacity hover:bg-bg-2",
              isPinned ? "opacity-100" : "opacity-0 group-hover:opacity-100",
            )}
            onClick={(e) => {
              e.stopPropagation();
              onPin(provider.id);
            }}
            title={isPinned ? "Désépingler" : "Épingler"}
          >
            <Star className={cn("h-4 w-4", isPinned && "fill-accent text-accent")} />
          </button>
          <ChevronRight className="h-4 w-4 text-foreground-tertiary opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <Badge variant={statusVariant} size="sm">
          {provider.status || "unknown"}
        </Badge>
        <span className="text-xs text-foreground-tertiary">
          {modelCount} modèle{modelCount > 1 ? "s" : ""}
        </span>
      </div>
      {provider.is_default && (
        <div className="mt-2">
          <Badge variant="accent" size="sm">Fournisseur par défaut</Badge>
        </div>
      )}
    </div>
  );
}

// ── Étapes 2-3 : carte modèle cliquable (sélection = modèle actif de la session) ──
interface ModelCardProps {
  model: ModelInfo;
  pinned: boolean;
  isSelected: boolean;
  onPin: (m: ModelInfo) => void;
  onMenu: (e: React.MouseEvent, model: ModelInfo) => void;
  onClick: () => void;
}

function ModelCard({ model, pinned, isSelected, onPin, onMenu, onClick }: ModelCardProps) {
  const caps = model.capabilities || [];

  return (
    <div
      className={cn(
        "group relative flex cursor-pointer flex-col rounded-xl border bg-bg-1/40 p-4 transition-all",
        isSelected
          ? "border-accent/60 ring-2 ring-accent/30 shadow-md"
          : "border-line-1 hover:border-accent/50 hover:shadow-sm",
      )}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
            <Database className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{model.name}</p>
            <p className="max-w-[180px] truncate text-xs text-foreground-tertiary">{model.model}</p>
          </div>
        </div>
        <button
          onClick={(e) => onMenu(e, model)}
          className="rounded p-1 opacity-0 transition-opacity hover:bg-bg-2 group-hover:opacity-100"
          aria-label="Plus d'actions"
        >
          <MoreVertical size={14} />
        </button>
      </div>

      <div className="mt-3 flex flex-col gap-2">
        <p className="text-[11px] text-foreground-tertiary">
          Contexte : {model.context_length?.toLocaleString() ?? "—"}
        </p>
        {caps.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {caps.slice(0, 4).map((cap) => (
              <Badge key={cap} variant={CAPABILITIES_COLORS[cap] || "dim"} size="sm">
                {cap}
              </Badge>
            ))}
            {caps.length > 4 && <Badge variant="dim" size="sm">+{caps.length - 4}</Badge>}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-foreground-tertiary">
        <span className="flex items-center gap-1">
          <StarHalf className="h-3 w-3" />
          Qualité : {Math.round((model.quality_score || 0) * 100)}%
        </span>
        {model.is_available ? (
          <Badge variant="success" size="sm">Disponible</Badge>
        ) : (
          <Badge variant="error" size="sm">Indisponible</Badge>
        )}
      </div>

      <div className="mt-auto flex justify-end pt-2">
        <Button
          size="sm"
          variant="ghost"
          className={cn("h-6 w-6 p-0", pinned ? "opacity-100" : "opacity-0 group-hover:opacity-100")}
          onClick={(e) => {
            e.stopPropagation();
            onPin(model);
          }}
          title={pinned ? "Désépingler" : "Épingler"}
        >
          <Star className={pinned ? "h-4 w-4 fill-accent text-accent" : "h-4 w-4"} />
        </Button>
      </div>

      {isSelected && (
        <div className="absolute right-2 top-2 rounded-full bg-accent p-0.5">
          <ChevronRight className="h-3 w-3 text-white" />
        </div>
      )}
    </div>
  );
}

