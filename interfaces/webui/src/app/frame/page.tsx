"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getFrameStatus,
  startFrame,
  stopFrame,
  restartFrame,
  installFrame,
  uninstallFrame,
  getFrameLogs,
  getFrameHealth,
  type FrameStatus,
  type FrameLogs,
  type FrameHealth,
} from "@/lib/api/frame";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Play, Square, RefreshCw, ExternalLink, Terminal, Activity } from "lucide-react";

function statusLabel(status: FrameStatus["status"]): string {
  if (status === "running") return "operationnel";
  if (status === "degraded") return "degrade";
  if (status === "starting") return "demarrage";
  if (status === "stopping") return "arret en cours";
  if (status === "error") return "erreur";
  if (status === "unknown") return "inconnu";
  if (status === "not_installed") return "non installe";
  return "installe, arrete";
}

function StatusPill({ status }: { status: FrameStatus }) {
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

export default function FramePage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [logsTail, setLogsTail] = React.useState(100);
  const [logs, setLogs] = React.useState("");
  const [health, setHealth] = React.useState<FrameHealth | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["frame", "status"],
    queryFn: getFrameStatus,
    refetchInterval: 5000,
    retry: false,
  });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["frame", "status"] });

  const mutation = useMutation({
    mutationFn: async (kind: "start" | "stop" | "restart" | "install" | "uninstall") => {
      if (kind === "start") return startFrame();
      if (kind === "stop") return stopFrame();
      if (kind === "restart") return restartFrame();
      if (kind === "install") return installFrame();
      return uninstallFrame();
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["frame", "status"], updated);
      addToast({ type: "success", message: "Operation effectuee." });
      invalidate();
    },
    onError: (e: unknown) => {
      addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" });
      invalidate();
    },
  });

  const fetchLogs = React.useCallback(async () => {
    try {
      const res: FrameLogs = await getFrameLogs(logsTail);
      if (res.ok) setLogs(res.logs || "");
      else setLogs(`Erreur de lecture des logs : ${res.error ?? "inconnue"}\n`);
    } catch (e) {
      setLogs(`Erreur de connexion aux logs : ${e instanceof Error ? e.message : "inconnue"}\n`);
    }
  }, [logsTail]);

  const fetchHealth = React.useCallback(async () => {
    try {
      setHealth(await getFrameHealth());
    } catch {
      setHealth(null);
    }
  }, []);

  React.useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const openStudio = () => {
    if (data?.status === "running") {
      window.open(data.url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Frames — Studio</h1>
          <p className="text-sm text-muted-foreground">
            Application independante basee sur Frames. Controle lifecycle et logs uniquement.
          </p>
        </div>
        {data ? <StatusPill status={data} /> : null}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Spinner className="h-4 w-4" /> Chargement...
        </div>
      )}
      {error && (
        <p className="mb-3 text-sm text-red-500">
          {error instanceof Error ? error.message : "Erreur de communication avec Frames."}
        </p>
      )}

      {data && (
        <div className="mb-4 flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" disabled={!data.allowed_actions.includes("start") || mutation.isPending} onClick={() => mutation.mutate("start")}>
            <Play className="h-3.5 w-3.5" />
            <span className="ml-1">Start</span>
          </Button>
          <Button size="sm" variant="secondary" disabled={!data.allowed_actions.includes("stop") || mutation.isPending} onClick={() => mutation.mutate("stop")}>
            <Square className="h-3.5 w-3.5" />
            <span className="ml-1">Stop</span>
          </Button>
          <Button size="sm" variant="secondary" disabled={!data.allowed_actions.includes("restart") || mutation.isPending} onClick={() => mutation.mutate("restart")}>
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="ml-1">Restart</span>
          </Button>
          <Button size="sm" variant="secondary" disabled={!data.allowed_actions.includes("uninstall") || mutation.isPending} onClick={() => mutation.mutate("uninstall")}>
            Supprimer conteneur
          </Button>
          <Button size="sm" variant="primary" disabled={!data.allowed_actions.includes("open")} onClick={openStudio}>
            <ExternalLink className="h-3.5 w-3.5" />
            <span className="ml-1">Ouvrir Frames Studio</span>
          </Button>
        </div>
      )}

      {data && (
        <div className="mb-4 rounded-lg border border-line-1 bg-bg-1 p-3 text-xs text-foreground-secondary">
          <p>URL studio : {data.url}</p>
          <p>Port : {data.port}</p>
          {data.error ? <p className="text-red-500">Erreur : {data.error}</p> : null}
        </div>
      )}

      <div className="mb-3 flex items-center gap-2">
        <select
          value={logsTail}
          onChange={(e) => setLogsTail(Number(e.target.value))}
          className="rounded-lg border border-line-1 bg-bg-1 px-2 py-1.5 text-xs"
        >
          {TAIL_OPTIONS.map((n) => (
            <option key={n} value={n}>Tail {n}</option>
          ))}
        </select>
        <Button size="sm" variant="secondary" onClick={() => { fetchLogs(); fetchHealth(); }}>
          <Terminal className="h-3.5 w-3.5" />
          <span className="ml-1">Logs</span>
        </Button>
        <Button size="sm" variant="secondary" onClick={fetchHealth}>
          <Activity className="h-3.5 w-3.5" />
          <span className="ml-1">Health</span>
        </Button>
      </div>

      <textarea
        readOnly
        value={logs}
        className="mb-3 min-h-[180px] w-full rounded-lg border border-line-1 bg-bg-1 p-3 font-mono text-xs text-foreground"
      />

      {health && (
        <pre className="max-h-[160px] overflow-auto rounded-lg border border-line-1 bg-bg-1 p-3 text-xs text-foreground-secondary">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
    </div>
  );
}
