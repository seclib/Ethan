          "use client";

import * as React from "react";
import { useProviders } from "@/components/features/providers/hooks/use-providers";
import { ProviderFormDialog } from "@/components/features/providers/components/provider-form-dialog";
import { ModelsPopover } from "@/components/features/providers/components/models-popover";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, RefreshCw, TestTube, Globe, Wifi, AlertCircle, LoaderCircle, ChevronDown, Search, Server } from "lucide-react";
import type { Provider, ProviderCreate, ProviderUpdate } from "@/lib/api/providers";

const STATUS_CONFIG = {
  connected: { icon: Wifi, color: "success", label: "Connected" },
  disconnected: { icon: AlertCircle, color: "error", label: "Disconnected" },
  connecting: { icon: LoaderCircle, color: "info", label: "Connecting…" },
  error: { icon: AlertCircle, color: "error", label: "Error" },
  pending: { icon: LoaderCircle, color: "warning", label: "Pending" },
  unknown: { icon: AlertCircle, color: "warning", label: "Unknown" },
} as const;

function cn(...inputs: (string | false | undefined)[]) {
  return inputs.filter(Boolean).join(" ");
}

interface ProviderCardProps {
  provider: Provider;
  onEdit: (p: Provider) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  onToggle: (id: string, enabled: boolean) => void;
  onRefetch: () => void;
}

function ProviderCard({ provider, onEdit, onDelete, onTest, onToggle }: ProviderCardProps) {
  const config = STATUS_CONFIG[provider.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.unknown;
  const StatusIcon = config.icon;

  return (
    <Card variant="outlined" className="group">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {provider.type === "ollama" && <Globe className="h-5 w-5 text-accent" />}
            <CardTitle className="text-lg">{provider.name}</CardTitle>
          </div>
          <Badge variant={provider.is_default ? "solid" : "secondary"}>
            {provider.is_default ? "Défaut" : provider.type}
          </Badge>
        </div>
        <CardDescription>{provider.base_url || provider.id}</CardDescription>
      </CardHeader>
      <CardContent>
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
          <span>{config.label}</span>
        </div>
        {provider.default_model && (
          <p className="mt-2 text-xs text-foreground-tertiary">
            Modèle par défaut :{" "}
            <code className="rounded bg-elevated px-1 py-0.5">{provider.default_model}</code>
          </p>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onToggle(provider.id, !provider.enabled)}>
            {provider.enabled ? "Désactiver" : "Activer"}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onTest(provider.id)} aria-label="Tester la connexion">
            <TestTube className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex gap-2">
          <ModelsPopover providerId={provider.id} />
          <Button variant="ghost" size="sm" onClick={() => onEdit(provider)}>
            Modifier
          </Button>
          {!provider.is_default && (
            <Button variant="ghost" size="sm" onClick={() => onDelete(provider.id)}>
              Supprimer
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}

export function ProvidersWorkspace() {
  const {
    providers,
    isLoading,
    isCreating,
    testConnection,
    toggleEnabled,
    deleteProviderAsync,
    createProviderAsync,
    updateProviderAsync,
    refetch,
  } = useProviders();

  const [editingProvider, setEditingProvider] = React.useState<Provider | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [dialogMode, setDialogMode] = React.useState<"create" | "edit">("create");
  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<"all" | "connected" | "offline">("all");

  const handleCreate = () => {
    setEditingProvider(null);
    setDialogMode("create");
    setDialogOpen(true);
  };

  const handleEdit = (p: Provider) => {
    setEditingProvider(p);
    setDialogMode("edit");
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Supprimer ce provider ? Cette action est irréversible.")) {
      await deleteProviderAsync(id);
    }
  };

  const q = search.trim().toLowerCase();
  const filtered = providers.filter((p) => {
    const matchesSearch =
      !q ||
      p.name.toLowerCase().includes(q) ||
      p.type.toLowerCase().includes(q) ||
      (p.base_url || "").toLowerCase().includes(q);
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "connected" && p.status === "connected") ||
      (statusFilter === "offline" && p.status !== "connected");
    return matchesSearch && matchesStatus;
  });

  const StatusFilterButton = ({ value, label }: { value: "all" | "connected" | "offline"; label: string }) => (
    <Button
      size="sm"
      variant={statusFilter === value ? "default" : "secondary"}
      onClick={() => setStatusFilter(value)}
    >
      {label}
    </Button>
  );

  return (
        <div className="flex h-full min-h-0 flex-col gap-4 p-6 overflow-y-auto">
      <PageHeader
        title="Providers LLM"
        description="Connexions aux moteurs LLM (Ollama, OpenAI, Anthropic…) via le ProviderManager du Core."
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
          <StatusFilterButton value="all" label="Tous" />
          <StatusFilterButton value="connected" label="Connectés" />
          <StatusFilterButton value="offline" label="Hors ligne" />
          <Button variant="ghost" size="sm" onClick={() => refetch()} disabled={isLoading} aria-label="Actualiser">
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {isLoading && providers.length === 0 ? (
        <div className="py-12 text-center text-foreground-tertiary">
          <LoaderCircle className="mx-auto h-8 w-8 animate-spin" />
          <p className="mt-2">Chargement des providers…</p>
        </div>
      ) : filtered.length === 0 ? (
        <p className="py-12 text-center text-foreground-tertiary">
          {providers.length === 0
            ? "Aucun provider configuré. Cliquez sur « Ajouter un provider » pour commencer."
            : "Aucun provider ne correspond à cette recherche."}
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <ProviderCard
              key={p.id}
              provider={p}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onTest={async (id) => { await testConnection(id); refetch(); }}
              onToggle={async (id, enabled) => { await toggleEnabled(id, enabled); refetch(); }}
              onRefetch={refetch}
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
    </div>
  );
}
