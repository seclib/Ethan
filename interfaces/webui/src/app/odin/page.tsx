"use client";

/**
 * Page Odin — pilotage de l'application plugin.
 * Toutes les operations passent par /v1/plugins/odin.
 * Aucune commande Docker construite cote frontend.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getOdinStatus,
  startOdin,
  stopOdin,
  restartOdin,
  installOdin,
  uninstallOdin,
  getOdinLogs,
  getOdinHealth,
  type OdinStatus,
  type OdinLogs,
  type OdinHealth,
} from "@/lib/api/plugins";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  Globe, Play, Square, RefreshCw, ExternalLink, Terminal, Activity, Clock, Trash2
} from "lucide-react";

function statusLabel(status: OdinStatus["status"]): string {
  if (status === "running") return "opérationnel";
  if (status === "degraded") return "dégradé";
  if (status === "starting") return "demarrage";
  if (status === "stopping") return "arret en cours";
  if (status === "error") return "erreur";
  if (status === "unknown") return "inconnu";
  if (status === "not_installed") return "non installé";
  return "installé, arrêté";
}

function StatusPill({ status }: { status: OdinStatus }) {
  const color =
    status.status === "running"
      ? "border-green-500/50 text-green-500 bg-green-500/10"
      : status.status === "error"
        ? "border-red-500/50 text-red-500 bg-red-500/10"
        : status.status === "degraded" || status.status === "unknown"
          ? "border-amber-500/50 text-amber-600 bg-amber-500/10"
        : "border-line-2 text-foreground-tertiary bg-elevated";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${color}`}>
      {statusLabel(status.status)}
      {status.healthy && status.status === "running" ? " - sain" : ""}
    </span>
  );
}

const TAIL_OPTIONS = [50, 100, 200, 500] as const;

export default function OdinPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [logsTail, setLogsTail] = React.useState(100);
  const [logsAutoRefresh, setLogsAutoRefresh] = React.useState(false);
  const [logs, setLogs] = React.useState<string>("");
  const [health, setHealth] = React.useState<OdinHealth | null>(null);
  const [logsHealthRefetch, setLogsHealthRefetch] = React.useState(0);
  const { data, isLoading, error } = useQuery({
    queryKey: ["odin", "status"],
    queryFn: getOdinStatus,
    refetchInterval: 5000,
    retry: false,
  });
  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["odin", "status"] });
  const mutation = useMutation({
    mutationFn: async (kind: "start" | "stop" | "restart" | "install" | "uninstall") => {
      if (kind === "start") return startOdin();
      if (kind === "stop") return stopOdin();
      if (kind === "restart") return restartOdin();
      if (kind === "install") return installOdin();
      return uninstallOdin();
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["odin", "status"], updated);
      addToast({ type: "success", message: "Operation effectuee." });
      invalidate();
    },
    onError: (e: unknown) => {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" });
      invalidate();
    },
  });

  // Logs — fetch on demand / periodic when auto-refresh enabled
  const fetchLogs = React.useCallback(async () => {
    try {
      const res: OdinLogs = await getOdinLogs(logsTail);
      if (res.status === "ok") {
        setLogs(res.logs || "");
      } else {
        setLogs(`Erreur lors de la lecture des logs : ${res.error ?? "inconnue"}\n`);
      }
    } catch (e) {
      setLogs(
        `Erreur de connexion aux logs : ${e instanceof Error ? e.message : "inconnue"}\n`,
      );
    }
  }, [logsTail]);

  // Health — fetch on mount + periodically refetched
  const fetchHealth = React.useCallback(async () => {
    try {
      const res: OdinHealth = await getOdinHealth();
      setHealth(res);
    } catch (e) {
      setHealth(null);
    }
  }, []);

  React.useEffect(() => {
    fetchHealth();
  }, [fetchHealth, logsHealthRefetch]);

  React.useEffect(() => {
    if (!logsAutoRefresh) return;
    const id = setInterval(() => {
      fetchLogs();
      setLogsHealthRefetch((n) => n + 1);
    }, 3000);
    return () => clearInterval(id);
  }, [logsAutoRefresh, fetchLogs]);

  const handleRefreshLogs = () => {
    fetchLogs();
    setLogsHealthRefetch((n) => n + 1);
  };

  const allowed = new Set(data?.allowed_actions ?? []);
  const busy =
    mutation.isPending ||
    data?.status === "starting" ||
    data?.status === "stopping";
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <Globe size={20} />
          </span>
          <div>
            <h1 className="text-lg font-semibold text-foreground">Odin</h1>
            <p className="text-xs text-foreground-tertiary">
              Console geospatiale 3D — conteneur local pilote via l&apos;API ETHAN.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ["odin", "status"] });
              fetchHealth();
              fetchLogs();
            }}
          >
            <RefreshCw size={13} /> Actualiser
          </Button>
          {data && allowed.has("open") && (
            <a href={data.url} target="_blank" rel="noreferrer">
              <Button size="sm" variant="outline" onClick={(e) => e.stopPropagation()}>
                <ExternalLink size={13} /> Ouvrir l&apos;application
              </Button>
            </a>
          )}
        </div>
      </div>
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-foreground-secondary">
          <Spinner /> Chargement…
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500">
          API injoignable : {error instanceof Error ? error.message : "Erreur"}.
        </div>
      )}
      {data && (
        <>
          <div className="flex flex-col gap-4 rounded-xl border border-line-1 bg-bg-1 p-4">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <StatusPill status={data} />
                <span className="text-[11px] text-foreground-tertiary">
                  {data.host}:{data.port}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-foreground-tertiary">
                <Clock size={12} />
                {data.updated_at}
              </div>
            </div>
            {data.error && (
              <div className="rounded-md border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-500">
                {data.error}
              </div>
            )}
            {data.details?.container_info && (
              <div className="grid grid-cols-1 gap-1 rounded-md border border-line-1 bg-bg-2 px-3 py-2 text-xs sm:grid-cols-3">
                <span>Service : {String(data.details.container_info.Service ?? "odin")}</span>
                <span>Conteneur : {String(data.details.container_info.Name ?? data.container_id ?? "—")}</span>
                <span>Image : {String(data.details.container_info.Image ?? "build local")}</span>
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-2">
              {allowed.has("install") && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => mutation.mutate("install")}
                  disabled={busy}
                >
                  <Globe size={13} /> Installer
                </Button>
              )}

              {/* Start button */}
              {allowed.has("start") && (
                <Button
                  size="sm"
                  onClick={() => mutation.mutate("start")}
                  disabled={busy}
                >
                  <Play size={13} /> Demarrer
                </Button>
              )}

              {/* Stop button */}
              {allowed.has("stop") && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => mutation.mutate("stop")}
                >
                  <Square size={13} /> Arreter
                </Button>
              )}

              {/* Restart button */}
              {allowed.has("restart") && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => mutation.mutate("restart")}
                >
                  <RefreshCw size={13} /> Redemarrer
                </Button>
              )}

              {allowed.has("uninstall") && (
                <Button
                  size="sm"
                  variant="destructive"
                  disabled={busy}
                  onClick={() => {
                    if (window.confirm("Désinstaller Odin ? Les conteneurs et ressources Compose seront retirés. Les volumes, fichiers .env, secrets et données du projet seront conservés.")) mutation.mutate("uninstall");
                  }}
                >
                  <Trash2 size={13} /> Désinstaller
                </Button>
              )}

              {busy && <Spinner className="h-4 w-4" />}
            </div>
          </div>

          {/* Health Detail Panel */}
          <details className="rounded-xl border border-line-1 bg-bg-1 p-4">
            <summary className="flex items-center justify-between cursor-pointer font-medium text-foreground">
              <div className="flex items-center gap-2">
                <Activity size={14} />
                <span>Etat de sante detaille</span>
              </div>
              {health ? (
                <span className={`text-xs font-medium ${
                  health.healthy ? "text-green-600" : "text-amber-600"
                }`}>
                  {health.status}
                </span>
              ) : (
                <span className="text-xs text-foreground-tertiary">—</span>
              )}
            </summary>
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Sonde HTTP</span>
                <span className={`font-medium ${health?.tcp_probe ? "text-green-600" : "text-red-500"}`}>
                  {health?.tcp_probe ? "reachable" : "unreachable"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Conteneur</span>
                <span className="font-medium text-foreground-secondary">
                  {health?.container_state ?? "—"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Santé Docker</span>
                <span className="font-medium text-foreground-secondary">
                  {health?.container_health ?? "non déclarée"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Host</span>
                <span className="font-mono text-[10px] text-foreground-secondary">
                  {health?.host ?? "—"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Port</span>
                <span className="font-mono text-[10px] text-foreground-secondary">
                  {health?.port ?? "—"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">URL</span>
                <span className="font-mono text-[10px] text-foreground-secondary break-all">
                  {health?.url ?? "—"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-foreground-tertiary">Derniere verification</span>
                <span className="font-mono text-[10px] text-foreground-secondary">
                  {health?.checked_at ?? "—"}
                </span>
              </div>
            </div>
          </details>

          {/* Logs Panel */}
          <details className="rounded-xl border border-line-1 bg-bg-1 p-4 open">
            <summary className="flex items-center justify-between cursor-pointer font-medium text-foreground mb-1">
              <div className="flex items-center gap-2">
                <Terminal size={14} />
                <span>Logs du conteneur</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1 text-xs text-foreground-tertiary cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={logsAutoRefresh}
                    onChange={(e) => setLogsAutoRefresh(e.target.checked)}
                    className="rounded bg-elevated border-line-2 text-accent focus:ring-accent"
                  />
                  Auto-refresh
                </label>
                <select
                  value={logsTail}
                  onChange={(e) => setLogsTail(Number(e.target.value))}
                  className="rounded border-line-2 bg-elevated text-[10px] text-foreground-secondary focus:border-accent h-6 w-16"
                >
                  {TAIL_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {t} lignes
                    </option>
                  ))}
                </select>
                <Button size="sm" variant="outline" onClick={handleRefreshLogs}>
                  <RefreshCw size={12} />
                </Button>
              </div>
            </summary>
            <div className="mt-2 rounded border border-line-1 bg-bg-2 p-3 font-mono text-[11px] text-foreground-secondary overflow-auto max-h-96 leading-relaxed whitespace-pre">
              {logs ||
                (logsAutoRefresh ? "Chargement des logs…" : "Cliquez sur Actualiser pour charger les logs.")}
            </div>
          </details>
        </>
      )}
    </div>
  );
}
