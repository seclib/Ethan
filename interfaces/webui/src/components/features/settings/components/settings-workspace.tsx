"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  testProviderConnection,
  setDefaultProvider,
  type Provider,
  type ProviderCreate,
  type ProviderUpdate,
} from "@/lib/api/providers";
import { useSettings } from "@/components/features/settings/hooks/use-settings";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import {
  Settings,
  Palette,
  Database,
  Wrench,
  Bot,
  Shield,
  Plus,
  Search,
  Trash2,
  Edit3,
  Play,
  Loader2,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Save,
} from "lucide-react";

type Section = "general" | "appearance" | "models_providers" | "knowledge" | "tools_mcp" | "agents" | "advanced";

const SECTIONS: { id: Section; label: string; icon: React.ReactNode }[] = [
  { id: "general", label: "General", icon: <Settings className="h-4 w-4" /> },
  { id: "appearance", label: "Appearance", icon: <Palette className="h-4 w-4" /> },
  { id: "models_providers", label: "Models & Providers", icon: <Database className="h-4 w-4" /> },
  { id: "knowledge", label: "Knowledge", icon: <Database className="h-4 w-4" /> },
  { id: "tools_mcp", label: "Tools / MCP", icon: <Wrench className="h-4 w-4" /> },
  { id: "agents", label: "Agents", icon: <Bot className="h-4 w-4" /> },
  { id: "advanced", label: "Advanced", icon: <Shield className="h-4 w-4" /> },
];

export function SettingsWorkspace() {
  const { settings, isLoading, error, update, isUpdating } = useSettings();
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [activeSection, setActiveSection] = React.useState<Section>("models_providers");
  const [search, setSearch] = React.useState("");
  const [selectedProviderId, setSelectedProviderId] = React.useState<string | null>(null);

  const [addProviderOpen, setAddProviderOpen] = React.useState(false);
  const [editProviderOpen, setEditProviderOpen] = React.useState(false);
  const [newProvider, setNewProvider] = React.useState<Partial<ProviderCreate>>({});
  const [editProvider, setEditProvider] = React.useState<Provider | null>(null);

  const [testingId, setTestingId] = React.useState<string | null>(null);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = React.useState<string | null>(null);

  const { data: providers = [], isLoading: providersLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: () => listProviders(),
  });

  const selectedProvider = providers.find((p) => p.id === selectedProviderId) || null;
  const filteredProviders = providers.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    ((p as any).display_name || "").toLowerCase().includes(search.toLowerCase())
  );

  const createMutation = useMutation({
    mutationFn: (data: ProviderCreate) => createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider créé" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec création" }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) => updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider mis à jour" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec mise à jour" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider supprimé" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec suppression" }),
  });

  const defaultMutation = useMutation({
    mutationFn: (id: string) => setDefaultProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider défini comme défaut" });
    },
    onError: (err) => addToast({ type: "error", message: err instanceof Error ? err.message : "Échec" }),
  });

  const handleAddProvider = async () => {
    if (!newProvider.name || !newProvider.type) return;
    await createMutation.mutateAsync(newProvider as ProviderCreate);
    setNewProvider({});
    setAddProviderOpen(false);
  };

  const handleEditProvider = async () => {
    if (!editProvider) return;
    await updateMutation.mutateAsync({
      id: editProvider.id,
        data: {
        base_url: editProvider.base_url,
        default_model: editProvider.default_model,
        display_name: (editProvider as any).display_name,
        enabled: editProvider.enabled,
      },
    });
    setEditProviderOpen(false);
    setEditProvider(null);
  };

  const handleToggleProvider = async (provider: Provider) => {
    await updateMutation.mutateAsync({
      id: provider.id,
      data: { enabled: !provider.enabled },
    });
  };

  const handleTestConnection = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testProviderConnection(id);
      addToast({
        type: result.connected ? "success" : "error",
        message: result.message || (result.connected ? "Connexion OK" : "Connexion échouée"),
      });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Test échoué" });
    } finally {
      setTestingId(null);
    }
  };

  const handleDeleteProvider = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
      if (selectedProviderId === id) setSelectedProviderId(null);
    } finally {
      setDeletingId(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    setSettingDefaultId(id);
    try {
      await defaultMutation.mutateAsync(id);
    } finally {
      setSettingDefaultId(null);
    }
  };

  const handleSaveSection = async (sectionKey: string) => {
    if (!settings) return;
    const result = await update({ [sectionKey]: (settings as any)[sectionKey] } as any);
    if (result.error) addToast({ type: "error", message: result.error });
  };

  return (
    <div className="flex h-full min-h-0">
      {/* Left panel: section navigation */}
      <div className="flex w-64 shrink-0 flex-col border-r border-line-1" style={{ background: "var(--panel)" }}>
        <div className="border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Settings</h2>
        </div>
        <nav className="sidebar-inner custom-scrollbar" style={{ padding: "8px" }}>
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => { setActiveSection(section.id); setSelectedProviderId(null); }}
              className={cn("list-item w-full", activeSection === section.id && "active")}
              style={{ width: "100%", border: "none", background: "transparent", textAlign: "left" }}
            >
              {section.icon}
              <span>{section.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Right panel: section content */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {activeSection === "models_providers" && (
          <ProvidersSection
            providers={filteredProviders}
            selectedProvider={selectedProvider}
            isLoading={providersLoading}
            search={search}
            onSearchChange={setSearch}
            onAdd={() => setAddProviderOpen(true)}
            onSelect={setSelectedProviderId}
            onEdit={(p) => { setEditProvider(p); setEditProviderOpen(true); }}
            onDelete={handleDeleteProvider}
            onToggle={handleToggleProvider}
            onTest={handleTestConnection}
            onSetDefault={handleSetDefault}
            testingId={testingId}
            deletingId={deletingId}
            settingDefaultId={settingDefaultId}
          />
        )}

        {activeSection === "general" && (
          <GenericSection
            title="General"
            description="Thème, langue, notifications"
            settings={settings}
            sectionKey="system"
            onSave={() => handleSaveSection("system")}
            isSaving={isUpdating}
          />
        )}

        {activeSection === "appearance" && (
          <GenericSection
            title="Appearance"
            description="Personnalisation de l'interface"
            settings={settings}
            sectionKey="ui"
            onSave={() => handleSaveSection("ui")}
            isSaving={isUpdating}
          />
        )}

        {activeSection === "knowledge" && (
          <InfoSection
            title="Knowledge"
            description="Gérez la configuration RAG, la mémoire et les documents depuis le workspace Knowledge."
            actionLabel="Ouvrir Knowledge"
            onAction={() => { window.location.href = "/knowledge"; }}
          />
        )}

        {activeSection === "tools_mcp" && (
          <InfoSection
            title="Tools / MCP"
            description="Gérez les outils et serveurs MCP depuis le workspace Tools."
            actionLabel="Ouvrir Tools"
            onAction={() => { window.location.href = "/tools"; }}
          />
        )}

        {activeSection === "agents" && (
          <InfoSection
            title="Agents"
            description="Gérez vos agents depuis le workspace Agents."
            actionLabel="Ouvrir Agents"
            onAction={() => { window.location.href = "/agents"; }}
          />
        )}

        {activeSection === "advanced" && (
          <GenericSection
            title="Advanced"
            description="Paramètres avancés du système"
            settings={settings}
            sectionKey="advanced"
            onSave={() => handleSaveSection("advanced")}
            isSaving={isUpdating}
          />
        )}
      </div>

      {/* Add provider dialog */}
      <Dialog open={addProviderOpen} onOpenChange={setAddProviderOpen} title="Nouveau provider">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={newProvider.name || ""} onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })} placeholder="e.g. Ollama" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Type</label>
            <Input value={newProvider.type || ""} onChange={(e) => setNewProvider({ ...newProvider, type: e.target.value })} placeholder="e.g. ollama" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">URL de base</label>
            <Input value={newProvider.base_url || ""} onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })} placeholder="e.g. http://localhost:11434" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Modèle par défaut</label>
            <Input value={newProvider.default_model || ""} onChange={(e) => setNewProvider({ ...newProvider, default_model: e.target.value })} placeholder="e.g. qwen2.5-coder" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Clé API</label>
            <Input type="password" value={newProvider.api_key || ""} onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })} placeholder="Optionnelle" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setAddProviderOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleAddProvider} disabled={!newProvider.name || !newProvider.type}>Créer</Button>
          </div>
        </div>
      </Dialog>

      {/* Edit provider dialog */}
      <Dialog open={editProviderOpen} onOpenChange={setEditProviderOpen} title="Configurer le provider">
        {editProvider && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Nom</label>
              <Input value={editProvider.name} onChange={(e) => setEditProvider({ ...editProvider, name: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Type</label>
              <Input value={editProvider.type} onChange={(e) => setEditProvider({ ...editProvider, type: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">URL de base</label>
              <Input value={editProvider.base_url || ""} onChange={(e) => setEditProvider({ ...editProvider, base_url: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Modèle par défaut</label>
              <Input value={editProvider.default_model || ""} onChange={(e) => setEditProvider({ ...editProvider, default_model: e.target.value })} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Clé API</label>
              <Input type="password" value={(editProvider as any).api_key || ""} onChange={(e) => setEditProvider({ ...editProvider, api_key: e.target.value } as any)} />
            </div>
            <label className="flex items-center gap-2 text-sm text-foreground-secondary">
              <input
                type="checkbox"
                checked={editProvider.enabled}
                onChange={(e) => setEditProvider({ ...editProvider, enabled: e.target.checked })}
                className="accent-accent"
              />
              Actif
            </label>
            <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
              <Button variant="ghost" onClick={() => setEditProviderOpen(false)}>Annuler</Button>
              <Button variant="primary" onClick={handleEditProvider}>Enregistrer</Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────────── */

function ProvidersSection({
  providers,
  selectedProvider,
  isLoading,
  search,
  onSearchChange,
  onAdd,
  onSelect,
  onEdit,
  onDelete,
  onToggle,
  onTest,
  onSetDefault,
  testingId,
  deletingId,
  settingDefaultId,
}: {
  providers: Provider[];
  selectedProvider: Provider | null;
  isLoading: boolean;
  search: string;
  onSearchChange: (v: string) => void;
  onAdd: () => void;
  onSelect: (id: string | null) => void;
  onEdit: (p: Provider) => void;
  onDelete: (id: string) => void;
  onToggle: (p: Provider) => void;
  onTest: (id: string) => void;
  onSetDefault: (id: string) => void;
  testingId: string | null;
  deletingId: string | null;
  settingDefaultId: string | null;
}) {
  return (
    <div className="flex h-full min-h-0">
      {/* Providers list */}
      <div className="flex w-72 shrink-0 flex-col border-r border-line-1 bg-bg-1/40">
        <div className="flex items-center justify-between border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Providers</h2>
          <Button size="sm" variant="primary" onClick={onAdd}>
            <Plus className="h-3.5 w-3.5" />
            <span className="ml-1">Nouveau</span>
          </Button>
        </div>
        <div className="p-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Rechercher un provider..."
              className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {isLoading && (
            <div className="flex items-center justify-center py-8 text-foreground-tertiary">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          )}
          {providers.map((provider) => (
            <div
              key={provider.id}
              onClick={() => onSelect(provider.id)}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
                provider.id === selectedProvider?.id ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
              )}
            >
              <span className={cn(
                "h-2 w-2 shrink-0 rounded-full",
                provider.status === "connected" ? "bg-green-500" : "bg-muted-foreground/30"
              )} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{(provider as any).display_name || provider.name}</p>
                <p className="truncate text-xs text-foreground-tertiary">{provider.type} · {provider.default_model}</p>
              </div>
              {provider.is_default && (
                <span className="text-xs text-accent">★ défaut</span>
              )}
            </div>
          ))}
          {providers.length === 0 && !isLoading && (
            <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">Aucun provider</p>
          )}
        </div>
      </div>

      {/* Provider details */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {!selectedProvider ? (
          <div className="flex h-full flex-col items-center justify-center text-center px-4">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
              <Database className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Sélectionnez un provider</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Configurez vos modèles et providers. Ajoutez un provider pour commencer.
            </p>
            <Button className="mt-4" variant="primary" onClick={onAdd}>
              <Plus className="h-4 w-4" />
              <span className="ml-1">Nouveau provider</span>
            </Button>
          </div>
        ) : (
          <div className="p-6">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-foreground">{(selectedProvider as any).display_name || selectedProvider.name}</h1>
                  <span className="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent">
                    {selectedProvider.type}
                  </span>
                  {selectedProvider.is_default && (
                    <span className="text-xs text-accent">★ défaut</span>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{selectedProvider.base_url}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => onEdit(selectedProvider)}>
                  <Edit3 className="h-3.5 w-3.5" />
                  <span className="ml-1">Configurer</span>
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => onTest(selectedProvider.id)}
                  disabled={testingId === selectedProvider.id}
                >
                  {testingId === selectedProvider.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                  <span className="ml-1">Tester</span>
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red/80 hover:text-red"
                  onClick={() => onDelete(selectedProvider.id)}
                  disabled={deletingId === selectedProvider.id}
                >
                  {deletingId === selectedProvider.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>

            <div className="mb-6 flex items-center gap-3 rounded-lg border border-line-1 bg-bg-1/50 p-3">
              <span className={cn(
                "h-2.5 w-2.5 rounded-full",
                selectedProvider.status === "connected" ? "bg-green-500" : "bg-muted-foreground/30"
              )} />
              <span className="text-sm text-foreground-secondary">
                {selectedProvider.status === "connected" ? "Connecté" : "Déconnecté"}
              </span>
              <span className="flex-1" />
              <button
                onClick={() => onToggle(selectedProvider)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium transition-colors",
                  selectedProvider.enabled
                    ? "bg-accent/10 text-accent hover:bg-accent/20"
                    : "bg-bg-2 text-foreground-tertiary hover:bg-bg-3"
                )}
                title={selectedProvider.enabled ? "Désactiver" : "Activer"}
              >
                {selectedProvider.enabled ? <ToggleRight className="h-3.5 w-3.5" /> : <ToggleLeft className="h-3.5 w-3.5" />}
                {selectedProvider.enabled ? "Actif" : "Inactif"}
              </button>
            </div>

            <div className="mb-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Modèle par défaut</h3>
                <p className="font-mono text-sm text-foreground-secondary">{selectedProvider.default_model || "—"}</p>
              </div>
              <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
                <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Type</h3>
                <p className="text-sm text-foreground-secondary">{selectedProvider.type}</p>
              </div>
            </div>

            {selectedProvider.models && selectedProvider.models.length > 0 && (
              <div>
                <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">
                  Modèles ({selectedProvider.models.length})
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {selectedProvider.models.map((model) => (
                    <span key={model} className="rounded-full bg-bg-2 px-2.5 py-0.5 text-xs text-foreground-secondary">
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 border-t border-line-1 pt-4">
              <Button size="sm" variant="secondary" onClick={() => onSetDefault(selectedProvider.id)} disabled={settingDefaultId === selectedProvider.id}>
                {settingDefaultId === selectedProvider.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                <span className="ml-1">Définir comme défaut</span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function GenericSection({
  title,
  description,
  settings,
  sectionKey,
  onSave,
  isSaving,
}: {
  title: string;
  description: string;
  settings: any;
  sectionKey: string;
  onSave: () => void;
  isSaving: boolean;
}) {
  const sectionData = settings?.[sectionKey] as Record<string, unknown> | undefined;

  if (!settings) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-8 text-foreground-tertiary">
          <Loader2 className="h-4 w-4 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-foreground">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>

      <div className="space-y-4">
        {sectionData && Object.keys(sectionData).length > 0 ? (
          Object.entries(sectionData).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between rounded-lg border border-line-1 bg-bg-1/40 px-4 py-3">
              <span className="text-sm text-foreground-secondary font-mono">{k}</span>
              <span className="text-sm text-foreground-secondary font-mono">{String(v)}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-foreground-tertiary">Aucun paramètre disponible.</p>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <Button variant="primary" onClick={onSave} disabled={isSaving}>
          {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          <span className="ml-1">Enregistrer</span>
        </Button>
      </div>
    </div>
  );
}

function InfoSection({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center px-4">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
        <Settings className="h-6 w-6 text-accent" />
      </div>
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">{description}</p>
      <Button className="mt-4" variant="primary" onClick={onAction}>
        <ExternalLink className="h-4 w-4" />
        <span className="ml-1">{actionLabel}</span>
      </Button>
    </div>
  );
}
