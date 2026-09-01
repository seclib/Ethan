"use client";

/**
 * Page Plugins — administration des plugins ETHAN (admin).
 *
 * Toutes les opérations passent par les routes /v1/plugins de l'API ETHAN
 * (interfaces/api/routers/v1.py), qui délèguent au CoreWebUIStore du Core
 * (core/state/webui_store.py). Aucune logique métier ici.
 *
 * Capacités réellement exposées (périmètre honnête de l'UI) :
 *   - liste + informations détaillées d'un plugin (Dialog)
 *   - installation (statut initial « inactive », arbitré par le Core)
 *   - activation/désactivation (toggle Core, avec confirmation)
 * Pas de suppression ni d'édition : l'API ne les expose pas — l'UI ne
 * doit pas les simuler (règle anti-fantôme).
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPlugins, getPlugin, installPlugin, togglePlugin, type PluginInfo,
} from "@/lib/api/plugins";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { Puzzle, Plus, Power, Info } from "lucide-react";

function StatusPill({ status }: { status: string }) {
  const active = status === "active";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        active
          ? "border-green-500/50 text-green-500 bg-green-500/10"
          : "border-line-2 text-foreground-tertiary bg-elevated"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${active ? "bg-green-500" : "bg-foreground-tertiary"}`} />
      {active ? "actif" : "inactif"}
    </span>
  );
}

export default function PluginsPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: plugins = [], isLoading, error } = useQuery({
    queryKey: ["plugins"],
    queryFn: listPlugins,
    retry: false,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["plugins"] });

  // ── Installation (POST /v1/plugins/install) ──
  const [installOpen, setInstallOpen] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const installMutation = useMutation({
    mutationFn: () => installPlugin({ name: newName.trim() }),
    onSuccess: (p) => {
      addToast({ type: "success", message: `Plugin '${p.name}' installé (inactif — activez-le pour l'utiliser)` });
      setInstallOpen(false); setNewName(""); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Toggle (PUT /v1/plugins/{id}/toggle) avec confirmation ──
  const [toggleTarget, setToggleTarget] = React.useState<PluginInfo | null>(null);
  const toggleMutation = useMutation({
    mutationFn: (id: string) => togglePlugin(id),
    onSuccess: (p) => {
      addToast({ type: "success", message: `Plugin '${p.name}' ${p.status === "active" ? "activé" : "désactivé"}` });
      setToggleTarget(null); invalidate();
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  // ── Détail (GET /v1/plugins/{id}) ──
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const { data: detail, error: detailError } = useQuery({
    queryKey: ["plugins", detailId],
    queryFn: () => getPlugin(detailId!),
    enabled: !!detailId,
    retry: false,
  });

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 p-6">
      {/* En-tête */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-line-2 bg-elevated p-2">
            <Puzzle size={20} className="text-accent-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">Plugins</h1>
            <p className="text-sm text-foreground-tertiary">
              Extensions enregistrées dans le Core. L&apos;installation crée le plugin
              en statut « inactif » ; l&apos;activation est une action séparée.
            </p>
          </div>
        </div>
        <Button size="sm" onClick={() => setInstallOpen(true)}>
          <Plus size={14} /> Installer
        </Button>
      </div>

      {/* Liste */}
      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          Impossible de charger les plugins : {error instanceof Error ? error.message : "erreur inconnue"}
        </div>
      ) : plugins.length === 0 ? (
        <div className="rounded-lg border border-line-2 p-8 text-center text-sm text-foreground-tertiary">
          Aucun plugin enregistré. Utilisez « Installer » pour ajouter le premier.
        </div>
      ) : (
        <ul className="space-y-2">
          {plugins.map((p) => (
            <li
              key={p.id}
              className="flex items-center justify-between gap-4 rounded-lg border border-line-2 bg-bg-2 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-foreground">{p.name}</span>
                  <StatusPill status={p.status} />
                </div>
                <div className="mt-0.5 flex items-center gap-2 font-mono text-[11px] text-foreground-tertiary">
                  <span>{p.id}</span>
                  <span>•</span>
                  <span>v{p.version}</span>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  variant="ghost" size="sm" title="Informations du plugin"
                  onClick={() => setDetailId(p.id)}
                >
                  <Info size={14} />
                </Button>
                <Button
                  variant="outline" size="sm" className="gap-1.5"
                  onClick={() => setToggleTarget(p)}
                >
                  <Power size={14} />
                  {p.status === "active" ? "Désactiver" : "Activer"}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Installation */}
      <Dialog open={installOpen} onClose={() => setInstallOpen(false)} title="Installer un plugin">
        <div className="space-y-3">
          <p className="text-sm text-foreground-secondary">
            Le plugin sera enregistré dans le Core en statut <strong>inactif</strong>.
            Vous devrez l&apos;activer explicitement après installation.
          </p>
          <Input
            placeholder="Nom du plugin (ex. Jira Sync)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && newName.trim() && !installMutation.isPending) installMutation.mutate();
            }}
            autoFocus
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setInstallOpen(false)}>Annuler</Button>
            <Button
              size="sm" disabled={!newName.trim() || installMutation.isPending}
              onClick={() => installMutation.mutate()}
            >
              Installer
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Confirmation toggle */}
      <Dialog
        open={!!toggleTarget}
        onClose={() => setToggleTarget(null)}
        title={toggleTarget?.status === "active" ? "Désactiver le plugin" : "Activer le plugin"}
      >
        <p className="text-sm text-foreground-secondary">
          {toggleTarget?.status === "active" ? (
            <>
              Désactiver <span className="font-semibold">{toggleTarget?.name}</span> ?
              Les capacités qu&apos;il fournit ne seront plus disponibles.
            </>
          ) : (
            <>
              Activer <span className="font-semibold">{toggleTarget?.name}</span> ?
              Ses capacités deviendront disponibles pour ETHAN.
            </>
          )}
        </p>
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" size="sm" onClick={() => setToggleTarget(null)}>Annuler</Button>
          <Button
            variant={toggleTarget?.status === "active" ? "destructive" : "default"}
            size="sm"
            disabled={toggleMutation.isPending}
            onClick={() => toggleTarget && toggleMutation.mutate(toggleTarget.id)}
          >
            Confirmer
          </Button>
        </div>
      </Dialog>

      {/* Détail */}
      <Dialog open={!!detailId} onClose={() => setDetailId(null)} title={`Plugin — ${detail?.name ?? detailId ?? ""}`}>
        {detail ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-[11px] uppercase tracking-wider text-foreground-tertiary">Statut</p>
                <div className="mt-1"><StatusPill status={detail.status} /></div>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-foreground-tertiary">Version</p>
                <p className="mt-1 font-mono text-foreground">v{detail.version}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[11px] uppercase tracking-wider text-foreground-tertiary">Identifiant</p>
                <p className="mt-1 font-mono text-xs text-foreground">{detail.id}</p>
              </div>
            </div>
            <div>
              <p className="mb-1 text-[11px] uppercase tracking-wider text-foreground-tertiary">Données brutes (Core)</p>
              <pre className="overflow-x-auto rounded-md bg-elevated p-3 font-mono text-[10px] text-foreground-tertiary">
                {JSON.stringify(detail, null, 2)}
              </pre>
            </div>
          </div>
        ) : detailError ? (
          <p className="text-sm text-destructive">
            Impossible de charger le détail : {detailError instanceof Error ? detailError.message : "erreur"}
          </p>
        ) : (
          <div className="flex justify-center py-6"><Spinner /></div>
        )}
      </Dialog>
    </div>
  );
}