"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listTools,
  listToolServers,
  registerToolServer,
  updateToolServer,
  deleteToolServer,
  type CoreTool,
  type ToolServer,
} from "@/lib/api/tools";
import { apiFetch } from "@/lib/api/client";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  Wrench,
  Server,
  Plus,
  Search,
  RefreshCw,
  Trash2,
  Settings2,
  Play,
  Square,
  Loader2,
  CheckCircle2,
  XCircle,
  Globe,
  Power,
} from "lucide-react";

type Section = "available" | "configured" | "mcp";

const providerLabel: Record<string, string> = {
  builtin: "Builtin",
  custom: "Custom",
  mcp: "MCP",
};

export function ToolsWorkspace() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [activeSection, setActiveSection] = React.useState<Section>("available");
  const [search, setSearch] = React.useState("");
  const [selectedToolId, setSelectedToolId] = React.useState<string | null>(null);
  const [selectedServerId, setSelectedServerId] = React.useState<string | null>(null);

  // Dialogs
  const [addServerOpen, setAddServerOpen] = React.useState(false);
  const [newServerName, setNewServerName] = React.useState("");
  const [newServerUrl, setNewServerUrl] = React.useState("");
  const [newServerDesc, setNewServerDesc] = React.useState("");
  const [editServerOpen, setEditServerOpen] = React.useState(false);
  const [editServer, setEditServer] = React.useState<ToolServer | null>(null);

  // Actions
  const [syncingId, setSyncingId] = React.useState<string | null>(null);
  const [togglingId, setTogglingId] = React.useState<string | null>(null);

  // Onglet piloté par le hash URL (#available | #configured | #mcp) :
  // la sidebar v3 peut ouvrir directement « MCP » (/tools#mcp).
  React.useEffect(() => {
    const applyHash = () => {
      const h = window.location.hash.replace("#", "");
      if (h === "mcp" || h === "available" || h === "configured") {
        setActiveSection(h);
        setSelectedToolId(null);
        setSelectedServerId(null);
      }
    };
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, []);

  const { data: tools = [], isLoading: toolsLoading, refetch: refetchTools } = useQuery({
    queryKey: ["tools"],
    queryFn: () => listTools(),
  });

  const { data: servers = [], isLoading: serversLoading, refetch: refetchServers } = useQuery({
    queryKey: ["toolServers"],
    queryFn: () => listToolServers(),
  });

  const filteredTools = tools.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.category.toLowerCase().includes(search.toLowerCase())
  );
  const filteredServers = servers.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  const selectedTool = tools.find((t) => t.id === selectedToolId) || null;
  const selectedServer = servers.find((s) => s.id === selectedServerId) || null;

  const handleAddServer = async () => {
    if (!newServerName.trim() || !newServerUrl.trim()) return;
    try {
      await registerToolServer({
        name: newServerName.trim(),
        url: newServerUrl.trim(),
        description: newServerDesc.trim() || undefined,
        enabled: true,
        auth_type: "none",
      });
      addToast({ type: "success", message: "Serveur MCP ajouté" });
      setNewServerName("");
      setNewServerUrl("");
      setNewServerDesc("");
      setAddServerOpen(false);
      queryClient.invalidateQueries({ queryKey: ["toolServers"] });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec ajout serveur" });
    }
  };

  const handleUpdateServer = async () => {
    if (!editServer) return;
    try {
      await updateToolServer(editServer.id, {
        name: editServer.name,
        url: editServer.url,
        description: editServer.description,
        enabled: editServer.enabled,
      });
      addToast({ type: "success", message: "Serveur MCP mis à jour" });
      setEditServerOpen(false);
      setEditServer(null);
      queryClient.invalidateQueries({ queryKey: ["toolServers"] });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec mise à jour" });
    }
  };

  const handleToggleServer = async (server: ToolServer) => {
    setTogglingId(server.id);
    try {
      await updateToolServer(server.id, { enabled: !server.enabled });
      addToast({ type: "success", message: server.enabled ? "Serveur désactivé" : "Serveur activé" });
      queryClient.invalidateQueries({ queryKey: ["toolServers"] });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec bascule" });
    } finally {
      setTogglingId(null);
    }
  };

  const handleSyncServer = async (id: string) => {
    setSyncingId(id);
    try {
      const result = await apiFetch<{ status: string; tools_discovered: number }>(
        `/v1/tools/servers/${id}/sync`,
        { method: "POST" }
      );
      addToast({ type: "success", message: `${result.tools_discovered} outils découverts` });
      queryClient.invalidateQueries({ queryKey: ["toolServers"] });
      queryClient.invalidateQueries({ queryKey: ["tools"] });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec synchronisation" });
    } finally {
      setSyncingId(null);
    }
  };

  const handleDeleteServer = async (id: string) => {
    try {
      await deleteToolServer(id);
      addToast({ type: "success", message: "Serveur MCP supprimé" });
      if (selectedServerId === id) setSelectedServerId(null);
      queryClient.invalidateQueries({ queryKey: ["toolServers"] });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Échec suppression" });
    }
  };

  const handleTestTool = async (tool: CoreTool) => {
    try {
      await apiFetch(`/v1/tools/${tool.id}/test`, { method: "POST" });
      addToast({ type: "success", message: `Outil ${tool.name} testé avec succès` });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : `Échec test ${tool.name}` });
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Tools & MCP"
        description="Outils du noyau, serveurs MCP et test des capacités"
        icon={<Wrench className="h-5 w-5" />}
        count={tools.length + servers.length}
        actions={
          <Button size="sm" variant="primary" onClick={() => setAddServerOpen(true)}>
            <Plus className="h-3.5 w-3.5" />
            <span className="ml-1">Serveur MCP</span>
          </Button>
        }
      />
      <div className="flex min-h-0 flex-1">
      {/* Left panel */}
      <div className="flex w-72 shrink-0 flex-col border-r border-line-1 bg-bg-1/40">
        <div className="border-b border-line-1 px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">Catalogue</h2>
        </div>

        <div className="p-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher..."
              className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>
        </div>

        {/* Section nav */}
        <div className="px-3 pb-2">
          <SectionTab
            active={activeSection === "available"}
            onClick={() => { setActiveSection("available"); setSelectedToolId(null); setSelectedServerId(null); }}
            count={tools.length}
            icon={<Wrench className="h-3.5 w-3.5" />}
            label="Available"
          />
          <SectionTab
            active={activeSection === "configured"}
            onClick={() => { setActiveSection("configured"); setSelectedToolId(null); setSelectedServerId(null); }}
            count={servers.filter((s) => s.enabled).length}
            icon={<CheckCircle2 className="h-3.5 w-3.5" />}
            label="Configured"
          />
          <SectionTab
            active={activeSection === "mcp"}
            onClick={() => { setActiveSection("mcp"); setSelectedToolId(null); setSelectedServerId(null); }}
            count={servers.length}
            icon={<Server className="h-3.5 w-3.5" />}
            label="MCP"
          />
        </div>

        {/* List content */}
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {activeSection === "available" && (
            <>
              {toolsLoading && <CenteredLoader />}
              {filteredTools.map((tool) => (
                <ToolRow
                  key={tool.id}
                  tool={tool}
                  isActive={selectedToolId === tool.id}
                  onClick={() => { setSelectedToolId(tool.id); setSelectedServerId(null); }}
                />
              ))}
              {filteredTools.length === 0 && !toolsLoading && (
                <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">Aucun outil disponible</p>
              )}
            </>
          )}

          {activeSection === "configured" && (
            <>
              {serversLoading && <CenteredLoader />}
              {filteredServers.filter((s) => s.enabled).map((server) => (
                <ServerRow
                  key={server.id}
                  server={server}
                  isActive={selectedServerId === server.id}
                  onClick={() => { setSelectedServerId(server.id); setSelectedToolId(null); }}
                />
              ))}
              {filteredServers.filter((s) => s.enabled).length === 0 && !serversLoading && (
                <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">Aucun serveur configuré actif</p>
              )}
            </>
          )}

          {activeSection === "mcp" && (
            <>
              {serversLoading && <CenteredLoader />}
              {filteredServers.map((server) => (
                <ServerRow
                  key={server.id}
                  server={server}
                  isActive={selectedServerId === server.id}
                  onClick={() => { setSelectedServerId(server.id); setSelectedToolId(null); }}
                />
              ))}
              {filteredServers.length === 0 && !serversLoading && (
                <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">Aucun serveur MCP</p>
              )}
            </>
          )}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {!selectedTool && !selectedServer ? (
          <div className="flex h-full flex-col items-center justify-center text-center px-4">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
              <Wrench className="h-6 w-6 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Sélectionnez un outil ou serveur MCP</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Gérez les capacités disponibles pour ETHAN : outils, serveurs MCP, intégrations.
            </p>
          </div>
        ) : selectedTool ? (
          <ToolDetails
            tool={selectedTool}
            onTest={() => handleTestTool(selectedTool)}
          />
        ) : selectedServer ? (
          <ServerDetails
            server={selectedServer}
            onToggle={() => handleToggleServer(selectedServer)}
            onSync={() => handleSyncServer(selectedServer.id)}
            onEdit={() => { setEditServer(selectedServer); setEditServerOpen(true); }}
            onDelete={() => handleDeleteServer(selectedServer.id)}
            isSyncing={syncingId === selectedServer.id}
            isToggling={togglingId === selectedServer.id}
          />
        ) : null}
      </div>

      {/* Add MCP server dialog */}
      <Dialog open={addServerOpen} onOpenChange={setAddServerOpen} title="Ajouter un serveur MCP">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Nom</label>
            <Input value={newServerName} onChange={(e) => setNewServerName(e.target.value)} placeholder="e.g. Weather" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">URL</label>
            <Input value={newServerUrl} onChange={(e) => setNewServerUrl(e.target.value)} placeholder="e.g. http://localhost:8000/sse" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Description</label>
            <Input value={newServerDesc} onChange={(e) => setNewServerDesc(e.target.value)} placeholder="Optionnelle" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setAddServerOpen(false)}>Annuler</Button>
            <Button variant="primary" onClick={handleAddServer} disabled={!newServerName.trim() || !newServerUrl.trim()}>
              Ajouter
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Edit MCP server dialog */}
      <Dialog open={editServerOpen} onOpenChange={setEditServerOpen} title="Configurer le serveur MCP">
        {editServer && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Nom</label>
              <Input
                value={editServer.name}
                onChange={(e) => setEditServer({ ...editServer, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">URL</label>
              <Input
                value={editServer.url || ""}
                onChange={(e) => setEditServer({ ...editServer, url: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Description</label>
              <Input
                value={editServer.description || ""}
                onChange={(e) => setEditServer({ ...editServer, description: e.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-foreground-secondary">
              <input
                type="checkbox"
                checked={editServer.enabled}
                onChange={(e) => setEditServer({ ...editServer, enabled: e.target.checked })}
                className="accent-accent"
              />
              Actif
            </label>
            <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
              <Button variant="ghost" onClick={() => setEditServerOpen(false)}>Annuler</Button>
              <Button variant="primary" onClick={handleUpdateServer}>Enregistrer</Button>
            </div>
          </div>
        )}
      </Dialog>
      </div>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────────── */

function SectionTab({ active, onClick, count, icon, label }: {
  active: boolean;
  onClick: () => void;
  count: number;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
        active ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
      )}
    >
      {icon}
      <span className="flex-1 text-left">{label}</span>
      <span className="text-xs text-foreground-tertiary">{count}</span>
    </button>
  );
}

function ToolRow({ tool, isActive, onClick }: {
  tool: CoreTool;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
        isActive ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
      )}
    >
      <Wrench className="h-4 w-4 shrink-0 text-foreground-tertiary" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{tool.name}</p>
        <p className="truncate text-xs text-foreground-tertiary">
          {providerLabel[tool.provider] || tool.provider} · {tool.category}
        </p>
      </div>
      <span className={cn(
        "h-1.5 w-1.5 shrink-0 rounded-full",
        tool.is_available ? "bg-green-500" : "bg-muted-foreground/30"
      )} />
    </div>
  );
}

function ServerRow({ server, isActive, onClick }: {
  server: ToolServer;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 transition-colors",
        isActive ? "bg-bg-3 text-foreground" : "text-foreground-secondary hover:bg-bg-3/60"
      )}
    >
      <Server className="h-4 w-4 shrink-0 text-foreground-tertiary" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{server.name}</p>
        <p className="truncate text-xs text-foreground-tertiary">
          {server.status || "unknown"} · {server.enabled ? "actif" : "inactif"}
        </p>
      </div>
      <span className={cn(
        "h-1.5 w-1.5 shrink-0 rounded-full",
        server.status === "connected" ? "bg-green-500" : "bg-muted-foreground/30"
      )} />
    </div>
  );
}

function CenteredLoader() {
  return (
    <div className="flex items-center justify-center py-8 text-foreground-tertiary">
      <Loader2 className="h-4 w-4 animate-spin" />
    </div>
  );
}

function ToolDetails({ tool, onTest }: {
  tool: CoreTool;
  onTest: () => void;
}) {
  return (
    <div className="p-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-foreground font-mono">{tool.name}</h1>
            <span className="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent">
              {providerLabel[tool.provider] || tool.provider}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{tool.description}</p>
        </div>
        <Button size="sm" variant="secondary" onClick={onTest}>
          <Play className="h-3.5 w-3.5" />
          <span className="ml-1">Tester</span>
        </Button>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Catégorie</h3>
          <p className="text-sm text-foreground-secondary">{tool.category || "—"}</p>
        </div>
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Disponible</h3>
          <p className="flex items-center gap-1.5 text-sm">
            {tool.is_available ? (
              <><CheckCircle2 className="h-4 w-4 text-green-500" /> Oui</>
            ) : (
              <><XCircle className="h-4 w-4 text-red-500" /> Non</>
            )}
          </p>
        </div>
      </div>

      {tool.tags?.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Tags</h3>
          <div className="flex flex-wrap gap-1.5">
            {tool.tags.map((tag) => (
              <span key={tag} className="rounded-full bg-bg-2 px-2.5 py-0.5 text-xs text-foreground-secondary">{tag}</span>
            ))}
          </div>
        </div>
      )}

      {tool.capabilities?.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Capacités</h3>
          <div className="flex flex-wrap gap-1.5">
            {tool.capabilities.map((cap) => (
              <span key={cap} className="rounded-full bg-accent/10 px-2.5 py-0.5 text-xs text-accent">{cap}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ServerDetails({ server, onToggle, onSync, onEdit, onDelete, isSyncing, isToggling }: {
  server: ToolServer;
  onToggle: () => void;
  onSync: () => void;
  onEdit: () => void;
  onDelete: () => void;
  isSyncing: boolean;
  isToggling: boolean;
}) {
  return (
    <div className="p-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-foreground">{server.name}</h1>
            <span className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
              server.status === "connected" ? "bg-green/10 text-green" : "bg-red/10 text-red"
            )}>
              {server.status || "unknown"}
            </span>
            <span className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
              server.enabled ? "bg-accent/10 text-accent" : "bg-bg-2 text-foreground-tertiary"
            )}>
              {server.enabled ? "Actif" : "Inactif"}
            </span>
          </div>
          {server.description && (
            <p className="mt-1 text-sm text-muted-foreground">{server.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={onToggle} disabled={isToggling}>
            {isToggling ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Power className="h-3.5 w-3.5" />}
            <span className="ml-1">{server.enabled ? "Désactiver" : "Activer"}</span>
          </Button>
          <Button size="sm" variant="secondary" onClick={onSync} disabled={isSyncing}>
            {isSyncing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            <span className="ml-1">Synchroniser</span>
          </Button>
          <Button size="sm" variant="secondary" onClick={onEdit}>
            <Settings2 className="h-3.5 w-3.5" />
          </Button>
          <Button size="sm" variant="ghost" className="text-red/80 hover:text-red" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">URL</h3>
          <p className="flex items-center gap-1.5 font-mono text-sm text-foreground-secondary">
            <Globe className="h-3.5 w-3.5 text-foreground-tertiary" />
            {server.url || "—"}
          </p>
        </div>
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold text-foreground-secondary uppercase tracking-wider">Crée</h3>
          <p className="text-sm text-foreground-secondary">
            {server.created_at ? new Date(server.created_at).toLocaleDateString("fr-FR") : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}