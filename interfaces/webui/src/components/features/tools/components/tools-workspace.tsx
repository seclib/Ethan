"use client";

/**
 * ToolsWorkspace — catalogue des capacités ETHAN (builtin / custom / MCP).
 *
 * Séparation : ici les OUTILS ; /mcp gère les SERVEURS MCP.
 * Capacités réellement supportées par le Core (aucun bouton fictif) :
 *   - liste / recherche / filtres provider + catégorie / tags / détail
 *   - création de tool custom persistant (POST /v1/tools)
 *   - suppression custom uniquement (builtins/MCP refusés par le Core)
 *   - association Agents en lecture (Agent.tool_ids — sélection dans /agents)
 *   - PAS de toggle : non supporté — l'activation = sélection dans un Agent.
 * L'exécution reste dans ETHAN Core/Runtime.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  listTools,
  createTool,
  deleteTool,
  type CoreTool,
} from "@/lib/api/tools";
import { listAgents } from "@/lib/api/agents";
import { useUIStore } from "@/store/ui.store";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  Wrench,
  Search,
  Loader2,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Plus,
  Trash2,
  Users,
} from "lucide-react";

const providerLabel: Record<string, string> = {
  builtin: "Builtin",
  custom: "Custom",
  mcp: "MCP",
};

type ProviderFilter = "all" | "builtin" | "custom" | "mcp";

export function ToolsWorkspace() {
  const router = useRouter();
  const addToast = useUIStore((s) => s.addToast);
  const [search, setSearch] = React.useState("");
  const [providerFilter, setProviderFilter] = React.useState<ProviderFilter>("all");
  const [categoryFilter, setCategoryFilter] = React.useState("all");
  const [selectedToolId, setSelectedToolId] = React.useState<string | null>(null);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [pendingDelete, setPendingDelete] = React.useState<CoreTool | null>(null);

  // Ancien onglet #mcp → page dédiée /mcp (compatibilité anciens liens).
  React.useEffect(() => {
    if (window.location.hash === "#mcp") router.replace("/mcp");
  }, [router]);

  const { data: tools = [], isLoading, refetch } = useQuery({
    queryKey: ["tools"],
    queryFn: () => listTools(),
  });

  // Lecture seule : quels Agents référencent chaque tool (association réelle
  // = Agent.tool_ids, sélectionnable dans l'éditeur d'Agent /agents).
  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents(),
  });

  const categories = React.useMemo(
    () =>
      Array.from(new Set(tools.map((t) => t.category).filter(Boolean))).sort(),
    [tools]
  );

  const filteredTools = tools.filter((t) => {
    const q = search.toLowerCase();
    const matches =
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.category.toLowerCase().includes(q) ||
      t.tags.some((tag) => tag.toLowerCase().includes(q));
    if (!matches) return false;
    if (providerFilter !== "all" && t.provider !== providerFilter) return false;
    if (categoryFilter !== "all" && t.category !== categoryFilter) return false;
    return true;
  });

  const selectedTool = tools.find((t) => t.id === selectedToolId) || null;
  const agentsUsingSelected = selectedTool
    ? agents.filter((a) => (a.tool_ids ?? []).includes(selectedTool.id))
    : [];

  const handleDelete = async () => {
    if (!pendingDelete) return;
    try {
      await deleteTool(pendingDelete.id);
      addToast({ type: "success", message: "Tool custom supprime" });
      if (selectedToolId === pendingDelete.id) setSelectedToolId(null);
      setPendingDelete(null);
      await refetch();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Echec suppression",
      });
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Tools"
        description="Capacités disponibles pour ETHAN et ses Agents"
        icon={<Wrench className="h-5 w-5" />}
        count={tools.length}
        actions={
          <>
            <Button size="sm" variant="secondary" onClick={() => router.push("/mcp")}>
              Gérer MCP
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
            <Button size="sm" variant="primary" onClick={() => setCreateOpen(true)}>
              <Plus className="h-3.5 w-3.5" />
              <span className="ml-1">Nouveau tool custom</span>
            </Button>
          </>
        }
      />
      <div className="flex min-h-0 flex-1">
        {/* Left panel : catalogue */}
        <div className="flex w-72 shrink-0 flex-col border-r border-line-1 bg-bg-1/40">
          <div className="border-b border-line-1 px-4 py-3">
            <h2 className="text-sm font-semibold text-foreground">Catalogue</h2>
          </div>
          <div className="space-y-2 p-3">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Nom, description, tag..."
                className="w-full rounded-lg border border-line-1 bg-bg-1 py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={providerFilter}
                onChange={(e) => setProviderFilter(e.target.value as ProviderFilter)}
                className="min-w-0 flex-1 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-xs"
              >
                <option value="all">Tous types</option>
                <option value="builtin">Builtin</option>
                <option value="custom">Custom</option>
                <option value="mcp">MCP</option>
              </select>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="min-w-0 flex-1 rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-xs"
              >
                <option value="all">Toutes catégories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-2">
            {isLoading && <CenteredLoader />}
            {filteredTools.map((tool) => (
              <ToolRow
                key={tool.id}
                tool={tool}
                isActive={selectedToolId === tool.id}
                onClick={() => setSelectedToolId(tool.id)}
              />
            ))}
            {!isLoading && filteredTools.length === 0 && (
              <p className="px-3 py-6 text-center text-xs text-foreground-tertiary">
                Aucun tool ne correspond
              </p>
            )}
          </div>
        </div>

        {/* Right panel : détail */}
        <div className="flex-1 min-w-0 overflow-y-auto">
          {!selectedTool ? (
            <div className="flex h-full flex-col items-center justify-center text-center px-4">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
                <Wrench className="h-6 w-6 text-accent" />
              </div>
              <h2 className="text-lg font-semibold text-foreground">
                Sélectionnez un tool
              </h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Catalogue des capacités : builtin, custom et outils MCP
                synchronisés (gérés depuis la page MCP). L&apos;exécution reste
                dans ETHAN Core/Runtime.
              </p>
            </div>
          ) : (
            <ToolDetails
              tool={selectedTool}
              agentsUsing={agentsUsingSelected}
              canDelete={selectedTool.provider === "custom"}
              onDelete={() => setPendingDelete(selectedTool)}
            />
          )}
        </div>
      </div>

      {createOpen && (
        <ToolDialog
          onClose={() => setCreateOpen(false)}
          onCreated={async () => {
            setCreateOpen(false);
            await refetch();
          }}
        />
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(o) => { if (!o) setPendingDelete(null); }}
        title="Supprimer le tool custom"
        message={
          pendingDelete
            ? "Supprimer « " + pendingDelete.name + " » ? Cette action est irréversible."
            : ""
        }
        confirmLabel="Supprimer"
        destructive
        onConfirm={handleDelete}
      />
    </div>
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
      <span
        className={cn(
          "h-1.5 w-1.5 shrink-0 rounded-full",
          tool.is_available ? "bg-green-500" : "bg-muted-foreground/30"
        )}
      />
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

function ToolDetails({ tool, agentsUsing, canDelete, onDelete }: {
  tool: CoreTool;
  agentsUsing: Array<{ id: string; name: string }>;
  canDelete: boolean;
  onDelete: () => void;
}) {
  const router = useRouter();
  const meta = (tool as { metadata?: Record<string, unknown> }).metadata;
  const mcpServerId = typeof meta?.mcp_server_id === "string" ? meta.mcp_server_id : null;
  const hasParams = Object.keys(tool.parameters ?? {}).length > 0;
  const permissions = tool.required_permissions ?? [];

  return (
    <div className="p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-mono text-xl font-bold text-foreground">{tool.name}</h1>
            <span className="rounded-full bg-accent/10 px-2 py-0.5 text-xs text-accent">
              {providerLabel[tool.provider] || tool.provider}
            </span>
            {tool.risk_level && tool.risk_level !== "low" && (
              <span className="rounded-full bg-amber-soft px-2 py-0.5 text-xs text-amber">
                risque : {tool.risk_level}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{tool.description}</p>
        </div>
        {canDelete ? (
          <Button size="sm" variant="ghost" className="text-red/80 hover:text-red" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" />
            <span className="ml-1">Supprimer</span>
          </Button>
        ) : (
          <span className="shrink-0 text-xs text-foreground-tertiary">
            Lecture seule — géré par le Core{tool.provider === "mcp" ? " (sync /mcp)" : ""}
          </span>
        )}
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Catégorie</h3>
          <p className="text-sm text-foreground-secondary">{tool.category || "—"}</p>
        </div>
        <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Disponible</h3>
          <p className="flex items-center gap-1.5 text-sm">
            {tool.is_available ? (
              <><CheckCircle2 className="h-4 w-4 text-green-500" /> Oui</>
            ) : (
              <><XCircle className="h-4 w-4 text-red-500" /> Non</>
            )}
          </p>
        </div>
        {typeof tool.total_calls === "number" && (
          <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Appels</h3>
            <p className="text-sm text-foreground-secondary">{tool.total_calls}</p>
          </div>
        )}
        {typeof tool.success_count === "number" && (
          <div className="rounded-lg border border-line-1 bg-bg-1/40 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Succès</h3>
            <p className="text-sm text-foreground-secondary">{tool.success_count}</p>
          </div>
        )}
      </div>

      {hasParams && (
        <div className="mb-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Paramètres (schéma)</h3>
          <pre className="max-h-56 overflow-auto rounded-lg border border-line-1 bg-bg-1 p-3 text-xs text-foreground-secondary">
            {JSON.stringify(tool.parameters, null, 2)}
          </pre>
        </div>
      )}

      {permissions.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
            Permissions requises
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {permissions.map((p) => (
              <span key={p} className="rounded-full bg-amber-soft px-2.5 py-0.5 text-xs text-amber">{p}</span>
            ))}
          </div>
          <p className="mt-1 text-xs text-foreground-tertiary">
            Appliquées par le Core au moment de l&apos;exécution.
          </p>
        </div>
      )}

      <div className="mb-6">
        <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
          <Users className="h-3.5 w-3.5" /> Agents utilisant ce tool ({agentsUsing.length})
        </h3>
        {agentsUsing.length === 0 ? (
          <p className="text-sm text-foreground-tertiary">
            Aucun agent ne le référence. Un tool n&apos;est actif pour un Agent que
            s&apos;il est sélectionné dans sa configuration.
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {agentsUsing.map((a) => (
              <span key={a.id} className="rounded-full bg-accent/10 px-2.5 py-0.5 text-xs text-accent">
                {a.name}
              </span>
            ))}
          </div>
        )}
        <Button size="sm" variant="secondary" className="mt-3" onClick={() => router.push("/agents")}>
          Configurer dans Agents
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>

      {tool.provider === "mcp" && (
        <div className="mb-6 rounded-lg border border-line-1 bg-bg-1/40 p-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Source MCP</h3>
          <p className="mb-2 text-sm text-foreground-secondary">
            Cet outil provient d&apos;un serveur MCP (synchronisation et activation
            sur la page MCP).
          </p>
          <Button size="sm" variant="secondary" onClick={() => router.push("/mcp")}>
            Ouvrir MCP
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
          {mcpServerId && (
            <p className="mt-2 font-mono text-xs text-foreground-tertiary">server_id : {mcpServerId}</p>
          )}
        </div>
      )}

      {tool.tags?.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Tags</h3>
          <div className="flex flex-wrap gap-1.5">
            {tool.tags.map((tag) => (
              <span key={tag} className="rounded-full bg-bg-2 px-2.5 py-0.5 text-xs text-foreground-secondary">{tag}</span>
            ))}
          </div>
        </div>
      )}

      {tool.capabilities?.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Capacités</h3>
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

export function ToolDialog({ onClose, onCreated }: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const addToast = useUIStore((s) => s.addToast);
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [category, setCategory] = React.useState("custom");
  const [tags, setTags] = React.useState("");
  const [capabilities, setCapabilities] = React.useState("");
  const [parameters, setParameters] = React.useState("{}");
  const [code, setCode] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  const csv = (v: string) =>
    v.split(",").map((s) => s.trim()).filter(Boolean);

  const paramsError = React.useMemo(() => {
    const trimmed = parameters.trim() || "{}";
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        return "Les paramètres doivent être un objet JSON ({...}).";
      }
      return null;
    } catch {
      return "JSON invalide.";
    }
  }, [parameters]);

  const handleSave = async () => {
    if (!name.trim()) {
      addToast({ type: "error", message: "Le nom est requis" });
      return;
    }
    if (paramsError) {
      addToast({ type: "error", message: paramsError });
      return;
    }
    setSaving(true);
    try {
      await createTool({
        name: name.trim(),
        description: description.trim(),
        category: category.trim() || "custom",
        parameters: JSON.parse(parameters.trim() || "{}") as Record<string, unknown>,
        code,
        capabilities: csv(capabilities),
        tags: csv(tags),
      });
      addToast({ type: "success", message: "Tool custom créé" });
      onCreated();
    } catch (err) {
      addToast({
        type: "error",
        message: err instanceof Error ? err.message : "Échec création",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onClose={onClose} title="Nouveau tool custom" size="lg">
      <div className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium">Nom *</label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex: summarize_text" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Description</label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Ce que fait le tool" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium">Catégorie</label>
            <Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="custom" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Tags (séparés par des virgules)</label>
            <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="texte, nlp" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Capacités (séparées par des virgules)</label>
          <Input value={capabilities} onChange={(e) => setCapabilities(e.target.value)} placeholder="chat, search" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Paramètres (schéma JSON objet)</label>
          <Textarea value={parameters} onChange={(e) => setParameters(e.target.value)} rows={4} placeholder='{"text": {"type": "string"}}' />
          {paramsError && <p className="mt-1 text-xs text-red">{paramsError}</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Code (définition, optionnel)</label>
          <Textarea value={code} onChange={(e) => setCode(e.target.value)} rows={5} placeholder="# Python — définition de référence" />
          <p className="mt-1 text-xs text-foreground-tertiary">
            Stocké comme métadonnée : le Core n&apos;exécute jamais ce code
            directement — l&apos;exécution passe par l&apos;executor/sandbox du
            Core/Runtime.
          </p>
        </div>
        <div className="flex justify-end gap-2 border-t border-line-1 pt-4">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          <Button variant="primary" onClick={handleSave} disabled={saving || !name.trim() || !!paramsError}>
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            Créer
          </Button>
        </div>
      </div>
    </Dialog>
  );
}