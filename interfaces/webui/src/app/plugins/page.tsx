"use client";

/**
 * Page Plugins — catalogue moderne de type « app store » (UX inspirée des
 * principes ChatGPT Plugins, identité ETHAN conservée).
 *
 * Toutes les opérations passent par les routes /v1/plugins de l'API ETHAN
 * (interfaces/api/routers/v1.py), qui délèguent au PluginRegistry du Core
 * (core/plugins). Aucune logique métier ici :
 *   - Discover : catalogue Core (manifests), états arbitrés par le Core ;
 *   - Installed : plugins installés (install → enable/disable, connect) ;
 *   - My Plugins : plugins custom/legacy hors catalogue ;
 *   - fiche détaillée : Overview / Capacités / Permissions / Configuration ;
 *   - connexion : AUCUN secret dans le frontend (secret manager côté Core).
 *
 * Lisibilité : surfaces opaques (règle audit transparence) — aucun
 * glassmorphism ni fond translucide.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPlugins, installPlugin, enablePlugin, disablePlugin, connectPlugin, disconnectPlugin,
  type PluginInfo, type PluginCategory,
} from "@/lib/api/plugins";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import {
  Puzzle, Plus, Power, Search, Check, Github, Globe, BookOpen, Code2,
  ImagePlus, FileText, Mail, FolderKanban, Clock, MessageSquare, FolderOpen,
  Wrench, Shield, Settings2, Link2, Unlink,
} from "lucide-react";

// Mapping manifest.icon (nom déclaré par le Core) → composant lucide.
const ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  Github, Globe, BookOpen, Code2, ImagePlus, FileText, Mail,
  FolderKanban, Clock, MessageSquare, FolderOpen, Puzzle,
};

function PluginIcon({ icon, className }: { icon: string; className?: string }) {
  const Icon = ICONS[icon] ?? Puzzle;
  return <Icon size={20} className={className} />;
}

type Tab = "discover" | "installed" | "my";

/** Bouton d'action unique, dérivé de l'état Core — jamais contradictoire. */
function actionFor(plugin: PluginInfo): {
  label: string; kind: "install" | "enable" | "enabled" | "connect";
} {
  if (!plugin.installed) return { label: "Installer", kind: "install" };
  if (plugin.status === "active") {
    return plugin.connected
      ? { label: "Activé", kind: "enabled" }
      : { label: "Connecter", kind: "connect" };
  }
  return { label: "Activer", kind: "enable" };
}

function StatusPill({ plugin }: { plugin: PluginInfo }) {
  const active = plugin.status === "active";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        active
          ? "border-green-500/50 text-green-500 bg-green-500/10"
          : "border-line-2 text-foreground-tertiary bg-elevated"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${active ? "bg-green-500" : "bg-foreground-tertiary"}`} />
      {active ? "actif" : plugin.installed ? "inactif" : "disponible"}
      {plugin.connected && <Check size={10} className="text-green-500" />}
    </span>
  );
}

// ── Carte plugin (surface opaque, hiérarchie claire) ─────────────────
function PluginCard({
  plugin, onOpen, onAction, pending,
}: {
  plugin: PluginInfo;
  onOpen: (id: string) => void;
  onAction: (plugin: PluginInfo) => void;
  pending: boolean;
}) {
  const action = actionFor(plugin);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(plugin.id)}
      onKeyDown={(e) => { if (e.key === "Enter") onOpen(plugin.id); }}
      className="group flex cursor-pointer flex-col gap-3 rounded-xl border border-line-1 bg-bg-1 p-4 transition-colors hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <PluginIcon icon={plugin.icon} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{plugin.name}</p>
            <p className="text-[11px] text-foreground-tertiary">
              v{plugin.version} · {plugin.categories.slice(0, 2).join(", ")}
            </p>
          </div>
        </div>
        <StatusPill plugin={plugin} />
      </div>

      <p className="line-clamp-2 min-h-[2.5rem] text-xs leading-relaxed text-foreground-secondary">
        {plugin.description}
      </p>

      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-foreground-tertiary">
        {plugin.capabilities.slice(0, 3).map((cap) => (
          <span key={cap} className="rounded bg-elevated px-1.5 py-0.5">{cap}</span>
        ))}
        {plugin.tools.length > 0 && (
          <span className="inline-flex items-center gap-0.5"><Wrench size={9} /> {plugin.tools.length}</span>
        )}
        {plugin.mcp.length > 0 && (
          <span className="inline-flex items-center gap-0.5">MCP · {plugin.mcp.length}</span>
        )}
      </div>

      <div className="flex justify-end">
        {action.kind === "enabled" ? (
          <Button variant="outline" size="sm" disabled className="pointer-events-none">
            <Check size={13} /> Activé
          </Button>
        ) : (
          <Button
            variant={action.kind === "connect" ? "outline" : "default"}
            size="sm"
            disabled={pending}
            onClick={(e) => { e.stopPropagation(); onAction(plugin); }}
          >
            {action.kind === "install" && <Plus size={13} />}
            {action.kind === "enable" && <Power size={13} />}
            {action.kind === "connect" && <Link2 size={13} />}
            {action.label}
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Page principale ──────────────────────────────────────────────────
export default function PluginsPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const [tab, setTab] = React.useState<Tab>("discover");
  const [search, setSearch] = React.useState("");
  const [category, setCategory] = React.useState<string>("all");
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const [connectTarget, setConnectTarget] = React.useState<PluginInfo | null>(null);
  const [disableTarget, setDisableTarget] = React.useState<PluginInfo | null>(null);

  const { data: plugins = [], isLoading, error } = useQuery({
    queryKey: ["plugins"],
    queryFn: async () => {
      // Détail du premier plugin pour valider que la vue fusionnée est servie.
      const list = await listPlugins();
      return list;
    },
    retry: false,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ["plugins", "categories"],
    queryFn: async () => (await import("@/lib/api/plugins")).getPluginCategories().then((r) => r.categories),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["plugins"] });
  const toastErr = (e: unknown) =>
    addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" });

  // Actions Core (install / enable / disable / connect / disconnect).
  const actionMutation = useMutation({
    mutationFn: async ({ plugin, kind }: { plugin: PluginInfo; kind: string }) => {
      switch (kind) {
        case "install": return installPlugin({ id: plugin.id });
        case "enable": return enablePlugin(plugin.id);
        case "disable": return disablePlugin(plugin.id);
        case "disconnect": return disconnectPlugin(plugin.id);
        case "connect": return connectPlugin(plugin.id);
        default: throw new Error(`Action inconnue: ${kind}`);
      }
    },
    onSuccess: (updated, vars) => {
      const verb: Record<string, string> = {
        install: "installé (inactif — activez-le pour l'utiliser)",
        enable: "activé",
        disable: "désactivé",
        connect: "connecté",
        disconnect: "déconnecté",
      };
      addToast({ type: "success", message: `${updated.name} ${verb[vars.kind] ?? "mis à jour"}` });
      invalidate();
    },
    onError: toastErr,
  });

  // Fiche détaillée : permissions + capacités réelles du Core.
  const { data: permissions, error: permError } = useQuery({
    queryKey: ["plugins", detailId, "permissions"],
    queryFn: async () => {
      const { getPluginPermissions } = await import("@/lib/api/plugins");
      return getPluginPermissions(detailId!);
    },
    enabled: !!detailId,
  });
  const { data: capabilities } = useQuery({
    queryKey: ["plugins", detailId, "capabilities"],
    queryFn: async () => {
      const { getPluginCapabilities } = await import("@/lib/api/plugins");
      return getPluginCapabilities(detailId!);
    },
    enabled: !!detailId,
  });
  const { data: detail } = useQuery({
    queryKey: ["plugins", detailId],
    queryFn: async () => {
      const { getPlugin } = await import("@/lib/api/plugins");
      return getPlugin(detailId!);
    },
    enabled: !!detailId,
  });

  // Filtrage local (recherche + catégorie) sur la vue Core — l'UI ne décide
  // rien de métier, elle ne fait que présenter.
  const filtered = plugins.filter((p) => {
    if (tab === "installed" && !p.installed) return false;
    if (tab === "my" && p.source !== "custom") return false;
    if (tab === "discover" && p.installed) return false;
    if (category !== "all" && !p.categories.includes(category)) return false;
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      p.description.toLowerCase().includes(q) ||
      p.capabilities.some((c) => c.toLowerCase().includes(q))
    );
  });
  const featured = filtered.filter((p) => p.featured);
  const rest = filtered.filter((p) => !p.featured);

  const handleAction = (plugin: PluginInfo) => {
    const action = actionFor(plugin);
    if (action.kind === "connect") { setConnectTarget(plugin); return; }
    if (action.kind === "enabled") return;
    actionMutation.mutate({ plugin, kind: action.kind });
  };

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Spinner /></div>;
  }
  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-sm text-destructive">
        Impossible de charger les plugins : {error instanceof Error ? error.message : "erreur"}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
              <Puzzle size={18} />
            </span>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Plugins</h1>
              <p className="text-xs text-foreground-tertiary">
                Catalogue, permissions et connexions — arbitrés par ETHAN Core
              </p>
            </div>
          </div>
          <div className="relative w-full max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search plugins..."
              className="pl-8"
              aria-label="Rechercher un plugin"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-5 flex gap-1 rounded-lg border border-line-1 bg-bg-1 p-1">
          {(["discover", "installed", "my"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              aria-pressed={tab === t}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                tab === t ? "bg-accent text-white" : "text-foreground-secondary hover:bg-elevated"
              }`}
            >
              {t === "discover" ? "Discover" : t === "installed" ? "Installed" : "My Plugins"}
            </button>
          ))}
        </div>

        {/* Catégories dynamiques (du Core) */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {[{ id: "all", label: "All", count: String(plugins.length) }, ...categories].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              aria-pressed={category === cat.id}
              className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                category === cat.id
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-line-2 text-foreground-tertiary hover:border-line-1 hover:text-foreground-secondary"
              }`}
            >
              {cat.label} {cat.count && <span className="opacity-60">{cat.count}</span>}
            </button>
          ))}
        </div>

        {/* Grille */}
        <div className="mt-6">
          {tab === "discover" && featured.length > 0 && (
            <>
              <h2 className="mb-3 text-sm font-semibold text-foreground">Featured</h2>
              <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {featured.map((p) => (
                  <PluginCard key={p.id} plugin={p} onOpen={setDetailId}
                    onAction={handleAction} pending={actionMutation.isPending} />
                ))}
              </div>
            </>
          )}
          {rest.length > 0 && (
            <>
              {tab === "discover" && featured.length > 0 && (
                <h2 className="mb-3 text-sm font-semibold text-foreground">All plugins</h2>
              )}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {rest.map((p) => (
                  <PluginCard key={p.id} plugin={p} onOpen={setDetailId}
                    onAction={handleAction} pending={actionMutation.isPending} />
                ))}
              </div>
            </>
          )}
          {filtered.length === 0 && (
            <div className="rounded-xl border border-line-1 bg-bg-1 px-4 py-10 text-center">
              <p className="text-sm text-foreground-secondary">Aucun plugin trouvé</p>
              <p className="mt-1 text-xs text-foreground-tertiary">
                {search ? `Aucun résultat pour « ${search} »` : "Changez de tab ou de catégorie"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Fiche détaillée */}
      <Dialog open={!!detailId} onClose={() => setDetailId(null)} title={detail?.name ?? "Plugin"}>
        {detail ? (
          <div className="space-y-5">
            {/* Overview */}
            <div className="flex items-start gap-3">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                <PluginIcon icon={detail.icon} />
              </span>
              <div className="min-w-0">
                <p className="text-sm text-foreground-secondary">{detail.description}</p>
                <p className="mt-1 text-[11px] text-foreground-tertiary">
                  v{detail.version} · {detail.author} · {detail.source === "custom" ? "custom" : "catalogue ETHAN"}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <StatusPill plugin={detail} />
              {detail.mcp.length > 0 && (
                <span className="rounded-full border border-line-2 px-2 py-0.5 text-[10px] text-foreground-tertiary">
                  MCP · {detail.mcp.join(", ")}
                </span>
              )}
              {detail.skills.length > 0 && (
                <span className="rounded-full border border-line-2 px-2 py-0.5 text-[10px] text-foreground-tertiary">
                  Skills · {detail.skills.join(", ")}
                </span>
              )}
            </div>

            {/* Action unique selon état */}
            {(() => {
              const action = actionFor(detail);
              return (
                <div className="flex justify-end gap-2">
                  {action.kind === "enabled" ? (
                    <>
                      <Button variant="outline" size="sm" disabled={actionMutation.isPending}
                        onClick={() => actionMutation.mutate({ plugin: detail, kind: "disable" })}>
                        <Power size={13} /> Désactiver
                      </Button>
                      {detail.connected && (
                        <Button variant="outline" size="sm" disabled={actionMutation.isPending}
                          onClick={() => actionMutation.mutate({ plugin: detail, kind: "disconnect" })}>
                          <Unlink size={13} /> Déconnecter
                        </Button>
                      )}
                    </>
                  ) : (
                    <Button size="sm" disabled={actionMutation.isPending} onClick={() => handleAction(detail)}>
                      {action.kind === "install" && <Plus size={13} />}
                      {action.kind === "enable" && <Power size={13} />}
                      {action.kind === "connect" && <Link2 size={13} />}
                      {action.label}
                    </Button>
                  )}
                </div>
              );
            })()}

            {/* Capacités */}
            <div>
              <p className="mb-2 text-[11px] uppercase tracking-wider text-foreground-tertiary">Capacités</p>
              <div className="flex flex-wrap gap-1.5">
                {(capabilities?.capabilities ?? detail.capabilities).map((cap) => (
                  <span key={cap} className="inline-flex items-center gap-1 rounded bg-green-500/10 px-2 py-0.5 text-[11px] text-green-500">
                    <Check size={10} /> {cap}
                  </span>
                ))}
              </div>
              {capabilities?.tools && capabilities.tools.length > 0 && (
                <div className="mt-2 space-y-1">
                  {capabilities.tools.map((tool) => (
                    <div key={tool.id} className="flex items-center justify-between rounded-md border border-line-1 px-2.5 py-1.5 text-xs">
                      <span className="inline-flex items-center gap-1.5 text-foreground">
                        <Wrench size={11} className="text-foreground-tertiary" /> {tool.name}
                      </span>
                      <span className={`text-[10px] ${tool.available ? "text-green-500" : "text-foreground-tertiary"}`}>
                        {tool.available ? `disponible · risque ${tool.risk_level ?? "low"}` : "indisponible"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Permissions (du manifest Core — jamais inventées côté UI) */}
            <div>
              <p className="mb-2 inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-foreground-tertiary">
                <Shield size={11} /> Permissions
              </p>
              {permError ? (
                <p className="text-xs text-destructive">Permissions indisponibles</p>
              ) : permissions ? (
                <>
                  <div className="flex flex-wrap gap-1.5">
                    {permissions.declared.map((perm) => (
                      <span key={perm} className="rounded bg-elevated px-2 py-0.5 text-[11px] text-foreground-secondary">{perm}</span>
                    ))}
                    {permissions.declared.length === 0 && (
                      <span className="text-[11px] text-foreground-tertiary">Aucune permission spéciale</span>
                    )}
                  </div>
                  {permissions.effective_from_tools.length > 0 && (
                    <p className="mt-1.5 text-[10px] text-foreground-tertiary">
                      Requises par les outils référencés : {permissions.effective_from_tools.join(", ")}
                    </p>
                  )}
                </>
              ) : (
                <Spinner />
              )}
            </div>

            {/* Configuration + authentification (secrets hors frontend) */}
            {(detail.configuration.length > 0 || detail.authentication.type !== "none") && (
              <div>
                <p className="mb-2 inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-foreground-tertiary">
                  <Settings2 size={11} /> Configuration &amp; connexion
                </p>
                {detail.configuration.map((field) => (
                  <div key={field.key} className="mb-1.5 flex items-center justify-between rounded-md border border-line-1 px-2.5 py-1.5 text-xs">
                    <span className="text-foreground">{field.label}</span>
                    <span className="font-mono text-[10px] text-foreground-tertiary">
                      {detail.configuration ? (field.secret ? "• secret manager" : (detail as PluginInfo & { configuration?: unknown })) && "—" : "—"}
                    </span>
                  </div>
                ))}
                {detail.authentication.type !== "none" && (
                  <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-2.5 py-2 text-[11px] text-amber-500">
                    Authentification {detail.authentication.type} — scopes : {detail.authentication.scopes.join(", ") || "—"}
                    <br />
                    Secrets attendus via secret manager : {detail.authentication.env_vars.join(", ")}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex justify-center py-6"><Spinner /></div>
        )}
      </Dialog>

      {/* Connexion — notice secret manager, aucun champ de secret ici */}
      <Dialog
        open={!!connectTarget}
        onClose={() => setConnectTarget(null)}
        title={`Connecter — ${connectTarget?.name ?? ""}`}
      >
        <div className="space-y-3 text-sm text-foreground-secondary">
          <p>Ce plugin nécessite un accès à :</p>
          <ul className="list-inside list-disc space-y-0.5 text-xs">
            {(connectTarget?.permissions ?? []).map((perm) => (
              <li key={perm}>{perm}</li>
            ))}
          </ul>
          {connectTarget?.authentication.type !== "none" && (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-[11px] text-amber-500">
              Les secrets ({connectTarget?.authentication.env_vars.join(", ")}) doivent être fournis
              via la couche secret manager (variables d&apos;environnement ou Vault).
              Aucun secret ne transite par le navigateur.
            </div>
          )}
          {connectTarget?.configuration.map((field) => (
            <div key={field.key}>
              <label className="mb-1 block text-[11px] uppercase tracking-wider text-foreground-tertiary">
                {field.label}{field.required ? " *" : ""}
              </label>
              <p className="text-[11px] text-foreground-tertiary">{field.description}</p>
              <ConnectFieldInput
                pluginId={connectTarget.id}
                fieldKey={field.key}
                onDone={() => { setConnectTarget(null); invalidate(); }}
                onError={toastErr}
              />
            </div>
          ))}
          {connectTarget?.configuration.length === 0 && (
            <ConnectFieldInput
              pluginId={connectTarget.id}
              fieldKey=""
              onDone={() => { setConnectTarget(null); invalidate(); }}
              onError={toastErr}
            />
          )}
        </div>
      </Dialog>

      {/* Confirmation désactivation */}
      <Dialog
        open={!!disableTarget}
        onClose={() => setDisableTarget(null)}
        title="Désactiver le plugin"
      >
        <p className="text-sm text-foreground-secondary">
          Désactiver <span className="font-semibold">{disableTarget?.name}</span> ?
          Ses capacités ne seront plus disponibles pour ETHAN.
        </p>
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" size="sm" onClick={() => setDisableTarget(null)}>Annuler</Button>
          <Button variant="destructive" size="sm" disabled={actionMutation.isPending}
            onClick={() => {
              if (disableTarget) actionMutation.mutate({ plugin: disableTarget, kind: "disable" });
              setDisableTarget(null);
            }}>
            Désactiver
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

/**
 * Champ de connexion : appelle POST /plugins/{id}/connect via le Core.
 * Un seul champ à la fois pour rester simple — le Core valide l'ensemble.
 */
function ConnectFieldInput({
  pluginId, fieldKey, onDone, onError,
}: {
  pluginId: string;
  fieldKey: string;
  onDone: () => void;
  onError: (e: unknown) => void;
}) {
  const [value, setValue] = React.useState("");
  const connect = useMutation({
    mutationFn: async () => {
      const { connectPlugin } = await import("@/lib/api/plugins");
      return connectPlugin(pluginId, fieldKey ? { [fieldKey]: value.trim() } : undefined);
    },
    onSuccess: onDone,
    onError,
  });
  return (
    <div className="mt-1.5 flex gap-2">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={fieldKey || "Confirmer la connexion"}
        disabled={connect.isPending}
      />
      <Button size="sm" disabled={connect.isPending || (fieldKey ? !value.trim() : false)}
        onClick={() => connect.mutate()}>
        Connecter
      </Button>
    </div>
  );
}
