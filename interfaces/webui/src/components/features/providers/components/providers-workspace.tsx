"use client";

/**
 * ProvidersWorkspace — cockpit moderne d'organisation des providers LLM.
 *
 * Inspiré d'Open-WebUI (cartes, status badges) et AnythingLLM (mode
 * sélection, actions contextuelles). Toute la logique reste dans le Core
 * (ProviderManager) : ce composant affiche et envoie des intentions.
 */

import * as React from "react";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import { ProviderFormDialog } from "@/components/features/providers/components/provider-form-dialog";
import { ModelsPopover } from "@/components/features/providers/components/models-popover";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Plus, RefreshCw, TestTube, Globe, Wifi, AlertCircle, LoaderCircle,
  Search, Server, MoreVertical,
} from "lucide-react";
import type { Provider, ProviderCreate, ProviderUpdate } from "@/lib/api/providers";

const STATUS_CONFIG = {
  connected: { icon: Wifi, color: "success", label: "Connecté" },
  disconnected: { icon: AlertCircle, color: "error", label: "Hors ligne" },
  connecting: { icon: LoaderCircle, color: "info", label: "Connexion…" },
  error: { icon: AlertCircle, color: "error", label: "Erreur" },
  pending: { icon: LoaderCircle, color: "warning", label: "En attente" },
  unknown: { icon: AlertCircle, color: "warning", label: "Inconnu" },
} as const;

const TYPE_ICONS: Record<string, React.ElementType> = {
  ollama: Globe,
  lmstudio: Server,
  vllm: Server,
  openai: Globe,
  anthropic: Globe,
  azure: Globe,
  gemini: Globe,
  openrouter: Globe,
  llamacpp: Globe,
  openai_compatible: Globe,
};

function cn(...inputs: (string | false | undefined)[]) {
  return inputs.filter(Boolean).join(" ");
}

interface ProviderCardProps {
  provider: Provider;
  selected: boolean;
  onSelect: (p: Provider) => void;
  onEdit: (p: Provider) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  onToggle: (id: string, enabled: boolean) => void;
  isTesting: boolean;
}

function ProviderCard({ provider, selected, onSelect, onEdit, onDelete, onTest, onToggle, isTesting }: ProviderCardProps) {
  const config = STATUS_CONFIG[provider.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.unknown;
  const StatusIcon = config.icon;
  const TypeIcon = TYPE_ICONS[provider.type] ?? Server;
  const modelCount = provider.models?.length ?? 0;

  return (
    <Card
      variant="outlined"
      className={cn(
        "group cursor-pointer transition-all",
        selected && "ring-2 ring-primary",
        !provider.enabled && "opacity-60",
      )}
      onClick={() => onSelect(provider)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <TypeIcon className="h-5 w-5 text-accent" />
            <div>
              <CardTitle className="text-lg">{provider.name}</CardTitle>
              <CardDescription className="mt-0.5">
                {provider.base_url || provider.id}
                {provider.type && <span className="text-xs uppercase"> · {provider.type}</span>}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {provider.is_default && <Badge variant="solid">Défaut</Badge>}
            {!provider.enabled && <Badge variant="dim">Inactif</Badge>}
            <button
              className="rounded p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-muted"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(provider);
              }}
              aria-label="Plus d'actions"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm">
          <StatusIcon
            className={cn(
              "h-4 w-4",
              config.color === "success" && "text-green",
              config.color === "error" && "text-red",
              config.color === "warning" && "text-amber",
              config.color === "info" && "text-accent",
            )}
          />
          <span className="font-medium">{config.label}</span>
        </div>

        {modelCount > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-1">
                <Badge variant="dim" size="sm">
                  {modelCount} modèle{modelCount > 1 ? "s" : ""}
                </Badge>
                {provider.default_model && (
                  <span className="text-xs text-foreground-tertiary">
                    Par défaut : {provider.default_model}
                  </span>
                )}
              </div>
            </div>
            <ModelsPopover providerId={provider.id} />
          </div>
        )}

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={isTesting}
            onClick={(e) => {
              e.stopPropagation();
              onTest(provider.id);
            }}
          >
            {isTesting ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <TestTube className="h-4 w-4" />
            )}
            Tester la connexion
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(provider.id, !provider.enabled);
            }}
          >
            {provider.enabled ? "Désactiver" : "Activer"}
          </Button>
        </div>
      </CardContent>

      <CardFooter className="flex justify-end gap-2 border-t border-line-1 pt-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(provider.id);
          }}
        >
          Supprimer
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(provider);
          }}
        >
          Configurer
        </Button>
      </CardFooter>

      {selected && (
        <div className="absolute inset-0 pointer-events-none rounded-lg ring-2 ring-primary" />
      )}
    </Card>
  );
}

interface StatusFilterButtonProps {
  value: string;
  label: string;
  active?: boolean;
  onClick: () => void;
}

function StatusFilterButton({ value, label, active, onClick }: StatusFilterButtonProps) {
  return (
    <Button
      variant={active ? "default" : "outline"}
      size="sm"
      className="text-xs"
      onClick={onClick}
    >
      {label}
    </Button>
  );
}

export function ProvidersWorkspace() {
  const {
    providers, isLoading, error, refetch,
    isCreating, isTesting, testConnection, toggleEnabled,
    deleteProviderAsync, createProviderAsync, updateProviderAsync,
  } = useProviders();
  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<"all" | "connected" | "offline">("all");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [dialogMode, setDialogMode] = React.useState<"create" | "edit">("create");
  const [editingProvider, setEditingProvider] = React.useState<Provider | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(null);

  const displayedProviders = React.useMemo(() => {
    if (error) return [];
    return providers.filter((p) => {
      const matchesSearch =
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.type.toLowerCase().includes(search.toLowerCase()) ||
        (p.base_url || "").toLowerCase().includes(search.toLowerCase());
      if (!matchesSearch) return false;
      if (statusFilter === "connected") return p.status === "connected";
      if (statusFilter === "offline") return p.status !== "connected";
      return true;
    });
  }, [providers, search, statusFilter, error]);

  const handleCreate = () => {
    setDialogMode("create");
    setEditingProvider(null);
    setDialogOpen(true);
  };

  const handleEdit = (p: Provider) => {
    setDialogMode("edit");
    setEditingProvider(p);
    setDialogOpen(true);
  };

  const handleDelete = async () => {
    if (pendingDeleteId) {
      await deleteProviderAsync(pendingDeleteId);
      refetch();
      setPendingDeleteId(null);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Providers"
        description="Fournisseurs de modèles LLM — état en temps réel."
        icon={<Server className="h-5 w-5" />}
        count={providers.length}
        actions={
          <Button variant="default" size="sm" onClick={handleCreate} disabled={isCreating}>
            <Plus className="h-4 w-4" />
            Ajouter un provider
          </Button>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Rechercher un provider (nom, type, URL)…"
            className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
          />
        </div>
        <div className="flex items-center gap-2">
          <StatusFilterButton
            value="all"
            label="Tous"
            active={statusFilter === "all"}
            onClick={() => setStatusFilter("all")}
          />
          <StatusFilterButton
            value="connected"
            label="Connectés"
            active={statusFilter === "connected"}
            onClick={() => setStatusFilter("connected")}
          />
          <StatusFilterButton
            value="offline"
            label="Hors ligne"
            active={statusFilter === "offline"}
            onClick={() => setStatusFilter("offline")}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
            aria-label="Actualiser"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {isLoading && providers.length === 0 ? (
        <div className="py-12 text-center text-foreground-tertiary">
          <LoaderCircle className="mx-auto h-8 w-8 animate-spin" />
          <p className="mt-2">Chargement des providers…</p>
        </div>
      ) : error ? (
        <div className="py-12 text-center text-foreground-tertiary">
          <AlertCircle className="mx-auto h-8 w-8" />
          <p className="mt-2">Erreur : {error}</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Réessayer
          </Button>
        </div>
      ) : displayedProviders.length === 0 ? (
        <p className="py-12 text-center text-foreground-tertiary">
          {providers.length === 0
            ? "Aucun provider configuré. Cliquez sur « Ajouter un provider » pour commencer."
            : "Aucun provider ne correspond à cette recherche."}
        </p>
      ) : (
        <div className="grid gap-4 py-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {displayedProviders.map((p) => (
            <ProviderCard
              key={p.id}
              provider={p}
              selected={selectedId === p.id}
              onSelect={(prov) => setSelectedId(prov.id)}
              onEdit={handleEdit}
              onDelete={() => setPendingDeleteId(p.id)}
              onTest={async (id) => {
                await testConnection(id);
                refetch();
              }}
              onToggle={async (id, enabled) => {
                await toggleEnabled(id, enabled);
                refetch();
              }}
              isTesting={isTesting}
            />
          ))}
        </div>
      )}

      <ProviderFormDialog
        open={dialogOpen}
        mode={dialogMode}
        provider={editingProvider}
        onClose={() => setDialogOpen(false)}
        onSubmit={async (data) => {
          if (dialogMode === "create") {
            await createProviderAsync(data as unknown as ProviderCreate);
          } else if (editingProvider) {
            await updateProviderAsync(editingProvider.id, data as unknown as ProviderUpdate);
          }
          refetch();
        }}
      />

      <ConfirmDialog
        open={pendingDeleteId !== null}
        onOpenChange={(o) => {
          if (!o) setPendingDeleteId(null);
        }}
        title="Supprimer le provider"
        message={pendingDeleteId ? "Supprimer ce provider ? Cette action est irréversible." : "Cette action est irréversible."}
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}
