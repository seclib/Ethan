"use client";

/**
 * McpServersWorkspace — gestion des SERVEURS MCP (infrastructure).
 *
 * Séparation : les serveurs vivent ici ; les outils MCP synchronisés
 * apparaissent en lecture dans le catalogue Tools (/tools)。
 *
 * Capacités réellement supportées par le Core (aucun bouton fictif) :
 *   - CRUD serveur (POST/PUT/DELETE /v1/tools/servers)
 *   - Statut réel du serveur (`status` : connected / disconnected / error)
 *   - Synchroniser = Tester la connexion + découvrir les outils
 *     (POST /v1/tools/servers/{id}/sync — vrai round-trip MCP, SDK officiel)
 *   - Arrêt/marche (`enabled` via PUT serveur — pas par /status)
 *   - Tools découverts en lecture (catalogue /v1/tools, filtré mcp_server_id)
 *   - Secrets protégés : le Core ne renvoie jamais tokens/headers
 *     (auth_config.token_set, metadata.header_keys) — l'UI n'affiche
 *     que leur existence, et les champs d'édition ne sont jamais pré-remplis。
 *   - Resources / Prompts MCP : non exposés par le Core aujourd'hui —
 *     mention honnête dans le détail, pas d'onglet factice.

 * L'exécution (connexion, appels) reste dans ETHAN Core/Runtime。
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getMcpServers,
  addMcpServer,
  updateMcpServer,
  deleteMcpServer,
  syncMcpServer,
  toggleMcpServer,
  type McpServer,
  type McpTransport,
  type CreateMcpServerInput,
  type UpdateMcpServerInput,
} from "@/lib/api/mcp";
import { listTools, type CoreTool } from "@/lib/api/tools";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Server,
  Plus,
  Search,
  RefreshCw,
  Trash2,
  Settings,
  ExternalLink,
  Power,
  PowerOff,
  Wrench,
  Loader2,
} from "lucide-react";

type FilterStatus = "all" | "connected" | "disconnected" | "error";

function badgeVariant(status: McpServer["status"]) {
  if (status === "connected") return "success";
  if (status === "error") return "error";
  return "secondary";
}

function transportLabel(t?: McpTransport) {
  if (t === "stdio") return "STDIO";
  if (t === "sse") return "SSE";
  return "HTTP";
}

export function McpServersWorkspace() {
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<FilterStatus>("all");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editingServer, setEditingServer] = React.useState<McpServer | null>(null);
  const [detailServer, setDetailServer] = React.useState<McpServer | null>(null);
  const [confirmServer, setConfirmServer] = React.useState<McpServer | null>(null);

  const { data: servers = [], isLoading, refetch } = useQuery({
    queryKey: ["mcpServers"],
    queryFn: () => getMcpServers(),
    staleTime: 30000,
  });

  // Tools MCP découverts (tous) — pour compter par serveur via metadata.mcp_server_id.

  const { data: tools = [] } = useQuery({
    queryKey: ["tools"],
    queryFn: () => listTools(),
  });

  const toolsByServer = React.useMemo(() => {
    const map: Record<string, CoreTool[]> = {};
    for (const t of tools) {
      const sid = (t as { metadata?: { mcp_server_id?: string } }).metadata?.mcp_server_id;
      if (sid) (map[sid] ??= []).push(t);
    }
    return map;
  }, [tools]);

  const filtered = servers.filter((s) => {
    if (statusFilter !== "all" && s.status !== statusFilter) return false;
    const q = search.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      (s.description || "").toLowerCase().includes(q)
    );
  });

  const handleToggle = async (s: McpServer) => {
    try {
      await toggleMcpServer(s.id, !s.enabled);
      addToast({
        type: "success",
        message: s.enabled ? "Serveur desactive" : "Serveur active",
      });
      await refetch();
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleSync = async (s: McpServer) => {
    try {
      const res = await syncMcpServer(s.id);
      addToast({
        type: res.error ? "warning" : "success",
        message: res.error
          ? (res.tools_discovered > 0
            ? "Synchronisation partielle : " + res.error
            : "Echec connexion : " + res.error)
          : res.tools_discovered > 0
            ? res.tools_discovered + " outil(s) decouvert(s)"
            : "Serveur connecte, aucun outil expose",
      });
      await refetch();
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleDelete = async () => {
    if (!confirmServer) return;
    try {
      await deleteMcpServer(confirmServer.id);
      addToast({ type: "success", message: "Serveur supprime" });
      setConfirmServer(null);
      await refetch();
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : String(err) });
    }
  };

  function renderGrid() {
    if (filtered.length === 0) {
      return (
        <div className="text-center py-12 border border-dashed rounded-lg">
          <Server className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">
            {search || statusFilter !== "all"
              ? "Aucun serveur ne correspond a votre recherche"
              : "Aucun serveur MCP configure"}
          </p>
        </div>
      );
    }
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((server) => (
          <ServerCard
            key={server.id}
            server={server}
            toolCount={toolsByServer[server.id]?.length ?? 0}
            onToggle={() => handleToggle(server)}
            onSync={() => handleSync(server)}
            onEdit={() => {
              setEditingServer(server);
              setDialogOpen(true);
            }}
            onDetail={() => setDetailServer(server)}
            onRemove={() => setConfirmServer(server)}
          />
        ))}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">MCP Servers</h1>
          <p className="text-sm text-muted-foreground">
            {servers.length} serveur{servers.length !== 1 ? "s" : ""} gere{servers.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button variant="primary" onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Ajouter un serveur
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un serveur..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as FilterStatus)}
          className="px-3 py-1 border rounded bg-background text-sm"
        >
          <option value="all">Tous les statuts</option>
          <option value="connected">Connectes</option>
          <option value="disconnected">Deconnectes</option>
          <option value="error">Erreurs</option>
        </select>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {renderGrid()}

      {dialogOpen && (
        <McpServerDialog
          server={editingServer}
          onClose={() => {
            setDialogOpen(false);
            setEditingServer(null);
          }}
          onSaved={async () => {
            setDialogOpen(false);
            setEditingServer(null);
            await refetch();
          }}
        />
      )}

      {detailServer && (
        <McpServerDetail
          server={detailServer}
          toolCount={toolsByServer[detailServer.id]?.length ?? 0}
          onClose={() => setDetailServer(null)}
        />
      )}

      <ConfirmDialog
        open={confirmServer !== null}
        onOpenChange={(o) => { if (!o) setConfirmServer(null); }}
        title="Supprimer le serveur MCP ?"
        message={
          confirmServer
            ? "Supprimer « " + confirmServer.name + " » ? Les outils decouverts seront retires du catalogue Tools."
            : ""
        }
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}

function ServerCard({ server, toolCount, onToggle, onSync, onEdit, onDetail, onRemove }: {
  server: McpServer;
 toolCount: number; onToggle: () => void; onSync: () => void;
  onEdit: () => void; onDetail: () => void; onRemove: () => void;
}) {
  const transport = server.metadata?.transport;
  return (
    <Card className="group">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          {server.name}
          <Badge variant={badgeVariant(server.status)}>
            {server.status === "connected" && "En ligne"}
            {server.status === "disconnected" && "Hors ligne"}
            {server.status === "error" && "Erreur"}
            {(!server.status || server.status === "unknown") && "Statut inconnu"}
          </Badge>
        </CardTitle>
        <CardDescription>{server.description || "Aucune description"}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="secondary">{transportLabel(transport)}</Badge>
          <Badge variant="secondary">{toolCount} outil{toolCount !== 1 ? "s" : ""}</Badge>
          <Badge variant={server.enabled ? "success" : "error"}>
            {server.enabled ? "Actif" : "Inactif"}
          </Badge>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button size="sm" variant="ghost" onClick={onToggle} title={server.enabled ? "Desactiver" : "Activer"}>
          {server.enabled ? <PowerOff className="h-4 w-4" /> : <Power className="h-4 w-4" />}
        </Button>
        <Button size="sm" variant="ghost" onClick={onSync} title="Tester la connexion et découvrir les outils">
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={onEdit} title="Configurer">
          <Settings className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={onDetail} title="Detail">
          <ExternalLink className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" className="text-red/80 hover:text-red" onClick={onRemove} title="Supprimer">
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}

function CenteredSpinner() {
  return (
    <div className="flex items-center justify-center py-6 text-foreground-tertiary">
      <Loader2 className="h-4 w-4 animate-spin" />
    </div>
  );
}

export function McpServerDialog({
  server,
  onClose,
  onSaved,
}: {
  server: McpServer | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const isEdit = !!server;

  const [name, setName] = React.useState(server?.name ?? "");
  const [description, setDescription] = React.useState(server?.description ?? "");
  const [transport, setTransport] = React.useState<McpTransport>(server?.metadata?.transport ?? "http");
  const [url, setUrl] = React.useState(server?.url ?? "");
  const [command, setCommand] = React.useState(server?.metadata?.command ?? "");
  const [args, setArgs] = React.useState((server?.metadata?.args ?? []).join(" "));
  const [headersText, setHeadersText] = React.useState("");
  const [authType, setAuthType] = React.useState<string>(server?.auth_type ?? "none");
  const [token, setToken] = React.useState("");
  const [enabled, setEnabled] = React.useState(server?.enabled ?? true);
  const [saving, setSaving] = React.useState(false);

  const isHttp = transport === "http" || transport === "sse";
  const headerCount = server?.metadata?.header_keys?.length ?? 0;
const tokenSet = server?.auth_config?.token_set ?? false;

  const parseHeaders = (str: string): Record<string, string> => {
    const obj: Record<string, string> = {};
    str.split("\n").map((l) => l.trim()).filter(Boolean).forEach((line) => {
      const idx = line.indexOf(":");
      if (idx > 0) obj[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    });
    return obj;
  };

  const handleSave = async () => {
    if (!name.trim()) return addToast({ type: "error", message: "Le nom est requis" });
    if (isHttp && !isEdit && !url.trim()) return addToast({ type: "error", message: "L'URL est requise" });
    if (transport === "stdio" && !isEdit && !command.trim()) return addToast({ type: "error", message: "La commande est requise" });

    setSaving(true);
    try {
      const payload: UpdateMcpServerInput = {
        name: name.trim(),
        description: description.trim(),
        enabled,
      };
      payload.auth_type = authType as "none" | "bearer" | "api_key";
      if (authType === "none") {
        // Passage à « Aucune » : efface proprement l'authentification existante.
        payload.auth_config = {};
      } else if (token.trim()) {
        payload.auth_config = { token: token.trim() };
      }
      if (headersText.trim()) payload.headers = parseHeaders(headersText);

      if (isEdit) {
        await updateMcpServer(server.id, payload);
        addToast({ type: "success", message: "Serveur mis a jour" });
      } else {
        const create: CreateMcpServerInput = {
          name: name.trim(),
          description: description.trim(),
          enabled,
          transport,
          ...(isHttp
            ? { url: url.trim() }
            : {
                url: "stdio://" + name.trim().toLowerCase(),
                command: command.trim(),
                args: args.trim() ? args.split(" ").filter(Boolean) : undefined,
              }),
        };
        if (authType !== "none") {
          create.auth_type = authType as "bearer" | "api_key";
          if (token.trim()) create.auth_config = { token: token.trim() };
        }
        if (headersText.trim()) create.headers = parseHeaders(headersText);
        await addMcpServer(create);
        addToast({ type: "success", message: "Serveur ajoute" });
      }
      onSaved();
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : String(err) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onClose}
      title={isEdit ? "Modifier le serveur" : "Ajouter un serveur MCP"}
      size="lg"
    >
      <div className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Nom *</label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex: filesystem" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optionnelle" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Transport</label>
          {isEdit ? (
            <p className="rounded-lg border border-line-1 bg-bg-1 px-3 py-2 text-sm text-foreground-secondary">
              {transportLabel(server?.metadata?.transport)} — le transport est structurant ;
              creez un nouveau serveur pour le changer.
            </p>
          ) : (
            <select
              value={transport}
              onChange={(e) => setTransport(e.target.value as McpTransport)}
              className="w-full rounded-lg border border-line-1 bg-bg-1 px-3 py-2 text-sm"
            >
              <option value="http">HTTP</option>
              <option value="sse">SSE</option>
              <option value="stdio">STDIO (commande locale)</option>
            </select>
          )}
        </div>
        {isEdit && isHttp && (
          <div>
            <label className="mb-1 block text-sm font-medium">URL</label>
            <p className="rounded-lg border border-line-1 bg-bg-1 px-3 py-2 font-mono text-sm break-all">
              {server?.url || "—"}
            </p>
          </div>
        )}
        {isEdit && transport === "stdio" && (
          <div>
            <label className="mb-1 block text-sm font-medium">Commande</label>
            <p className="rounded-lg border border-line-1 bg-bg-1 px-3 py-2 font-mono text-sm break-all">
              {server?.metadata?.command || "—"}{" "}{server?.metadata?.args?.join(" ")}
            </p>
          </div>
        )}
        {!isEdit && isHttp && (
          <div>
            <label className="mb-1 block text-sm font-medium">URL *</label>
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="http://localhost:8000/sse" />
          </div>
        )}
        {!isEdit && transport === "stdio" && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium">Commande *</label>
              <Input value={command} onChange={(e) => setCommand(e.target.value)} placeholder="uv run mcp-server-filesystem" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Arguments (separes par un espace)</label>
              <Input value={args} onChange={(e) => setArgs(e.target.value)} placeholder="--root /workspace" />
            </div>
          </>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium">
            En-tetes HTTP {headerCount > 0 ? `(${headerCount} configuree${headerCount !== 1 ? "s" : ""} — valeurs masquees)` : "(optionnel)"}
          </label>
          <Textarea
            value={headersText}
            onChange={(e) => setHeadersText(e.target.value)}
            rows={3}
            placeholder="Cle: Valeur (une par ligne) — les valeurs existantes ne sont pas affichees"
          />
          <p className="mt-1 text-xs text-foreground-tertiary">
            Laissez vide pour conserver les en-tetes existants ; leur valeur n&apos;est
            jamais renvoyee par le Core.
          </p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Authentification</label>
          <select
            value={authType}
            onChange={(e) => setAuthType(e.target.value)}
            className="w-full rounded-lg border border-line-1 bg-bg-1 px-3 py-2 text-sm"
          >
            <option value="none">Aucune</option>
            <option value="bearer">Bearer token</option>
            <option value="api_key">Clef API</option>
          </select>
          {authType !== "none" && (
            <>
              <Input
                className="mt-2"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder={
                  tokenSet
                    ? "Nouveau token (laisser vide = conserver)"
                    : "Token"
                }
              />
              {tokenSet && (
                <p className="mt-1 text-xs text-foreground-tertiary">
                  Token configure (jamais affiche) — laisser vide pour le conserver.
                </p>
              )}
            </>
          )}
        </div>

        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Actif</label>
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} className="h-4 w-4" />
        </div>

        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          <Button variant="primary" onClick={handleSave} disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            {isEdit ? "Enregistrer" : "Creer"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

function McpServerDetail({ server, onClose, toolCount }: {
  server: McpServer;
  toolCount: number;
  onClose: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const [tools, setTools] = React.useState<Array<{ id: string; name: string; description: string }>>([]);
  const [loading, setLoading] = React.useState(true);
  const [syncing, setSyncing] = React.useState(false);
  const transport = server.metadata?.transport;
  const headerKeys = server.metadata?.header_keys ?? [];
  const tokenSet = server.auth_config?.token_set ?? false;

  const fetchTools = React.useCallback(async () => {
    setLoading(true);
    try {
      const all = await listTools();
      setTools(
        all
          .filter((t) => {
            const meta = (t as { metadata?: { mcp_server_id?: string } }).metadata;
            return meta?.mcp_server_id === server.id;
          })
          .map((t) => ({ id: t.id, name: t.name, description: t.description }))
      );
    } catch {
      setTools([]);
    } finally {
      setLoading(false);
    }
  }, [server.id]);

  React.useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await syncMcpServer(server.id);
      addToast({
        type: res.error ? "warning" : "success",
        message: res.error
          ? "Echec connexion : " + res.error
          : res.tools_discovered > 0
            ? res.tools_discovered + " outil(s) decouvert(s)"
            : "Serveur connecte, aucun outil expose",
      });
      await fetchTools();
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : String(err) });
    } finally {
      setSyncing(false);
    }
  };

  return (
    <Dialog open onClose={onClose} title={server.name} size="lg">
      <div className="flex flex-col gap-4">
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-sm">
            <span className="text-foreground-tertiary">Statut :</span>
            <span><Badge variant={badgeVariant(server.status)}>{server.status}</Badge></span>
            <span className="text-foreground-tertiary">Actif :</span>
            <span>{server.enabled ? "Oui" : "Non"}</span>
            <span className="text-foreground-tertiary">Transport :</span>
            <span>{transportLabel(transport)}</span>
            {(server.url || server.metadata?.command) && (
              <>
                <span className="text-foreground-tertiary">{server.url && transport !== "stdio" ? "URL :" : "Commande :"}</span>
                <code className="break-all rounded bg-bg-2 px-2 py-0.5">
                  {transport !== "stdio"
                    ? server.url || "—"
                    : [server.metadata?.command, ...(server.metadata?.args ?? [])].join(" ")}
                </code>
              </>
            )}
            {server.auth_type && server.auth_type !== "none" && (
              <>
                <span className="text-foreground-tertiary">Auth :</span>
                <span>{server.auth_type}{tokenSet ? " (token configure)" : ""}</span>
              </>
            )}
            {headerKeys.length > 0 && (
              <>
                <span className="text-foreground-tertiary">En-tetes ({headerKeys.length}) :</span>
                <div className="flex flex-wrap gap-1">
                  {headerKeys.map((k) => (
                    <Badge key={k} variant="secondary">{k}: ***</Badge>
                  ))}
                </div>
              </>
            )}
            {server.last_connected_at && (
              <>
                <span className="text-foreground-tertiary">Derniere connexion :</span>
                <span>{new Date(server.last_connected_at).toLocaleString("fr-FR")}</span>
              </>
            )}
            {server.description && (
              <>
                <span className="text-foreground-tertiary">Description :</span>
                <span>{server.description}</span>
              </>
            )}
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground-secondary">
              Outils exposes ({toolCount})
            </h3>
            <Button size="sm" variant="secondary" onClick={handleSync} disabled={syncing}>
              {syncing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              <span className="ml-1">{syncing ? "Test connexion..." : "Tester la connexion / decouvrir"}</span>
            </Button>
          </div>
          {loading ? (
            <CenteredSpinner />
          ) : tools.length === 0 ? (
            <p className="rounded-lg border border-dashed border-line-1 px-3 py-6 text-center text-xs text-foreground-tertiary">
              Aucun outil decouvert. Lancez une synchronisation pour tester la
              connexion et interroger le serveur.
            </p>
          ) : (
            <div className="space-y-2">
              {tools.map((tool) => (
                <div key={tool.id} className="flex items-start gap-3 rounded-lg border border-line-1 p-3">
                  <Wrench className="mt-0.5 h-4 w-4 shrink-0 text-foreground-tertiary" />
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm font-medium">{tool.name}</p>
                    {tool.description && (
                      <p className="mt-0.5 text-xs text-foreground-tertiary">{tool.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          <p className="mt-2 text-xs text-foreground-tertiary">
            Ces outils apparaissent aussi dans le catalogue Tools (provider &laquo; MCP &raquo;) et sont
            selectionnables dans la configuration des Agents.
          </p>
        </div>

        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Resources &amp; Prompts</h3>
          <p className="mt-1 text-xs text-foreground-tertiary">
            ETHAN n&apos;expose pas encore les Resources et Prompts MCP de ce
            serveur — seule la decouverte d&apos;outils est supportee par le Core.
          </p>
        </div>

        <div className="flex justify-end border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Fermer</Button>
        </div>
      </div>
    </Dialog>
  );
}