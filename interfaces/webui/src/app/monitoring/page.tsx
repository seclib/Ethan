"use client";

/**
 * Monitoring — visualisation temps réel des métriques système.
 *
 * Consomme la capacité Core-owned :
 *   GET /api/diagnostics/metrics → SystemMetrics.collect()
 *   (CPU, RAM, disque, GPU/VRAM, processus, Docker)
 *
 * Aucune donnée fictive : une section indique `available: false` + `reason`
 * si une métrique est indisponible (pas de psutil, pas de NVML, daemon
 * Docker absent…). Aucun spinner permanent : les sections
 * indisponibles affichent clairement la raison.
 */

import * as React from "react";
import { RefreshCw, Server, Cpu, HardDrive, MemoryStick, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  SystemMetrics,
  ApiError,
  fetchMetrics,
  GRAFANA_URL,
} from "@/lib/api/diagnostics";

const REFRESH_MS = 5_000;

function fmtBytes(n: number): string {
  const GB = 1024 ** 3;
  if (n >= GB) return `${(n / GB).toFixed(1)} Go`;
  const MB = 1024 ** 2;
  if (n >= MB) return `${(n / MB).toFixed(1)} Mo`;
  return `${Math.round(n / 1024)} Ko`;
}

interface MetricCardProps {
  icon: React.ComponentType<{ size?: number; className?: string; style?: React.CSSProperties }>;
  title: string;
  value: string;
  sub?: string;
  available: boolean;
  reason?: string;
}

function MetricCard({ icon: Icon, title, value, sub, available, reason }: MetricCardProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border p-4"
      style={{ border: "1px solid var(--border)", background: "var(--panel)" }}>
      <Icon size={18} style={{ color: "var(--accent)" }} />
      <div className="flex-1">
        <div className="text-xs uppercase" style={{ color: "var(--fg-3)" }}>{title}</div>
        {available ? (
          <>
            <div className="text-lg font-medium" style={{ color: "var(--fg)" }}>{value}</div>
            {sub && <div className="text-xs" style={{ color: "var(--fg-2)" }}>{sub}</div>}
          </>
        ) : (
          <div className="text-xs italic" style={{ color: "var(--fg-2)" }}>
            Indisponible : {reason || "non disponible"}
          </div>
        )}
    </div>
  </div>
  );
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = React.useState<SystemMetrics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    const res = await fetchMetrics();
    if ("ok" in res) {
      setError((res as ApiError).message);
      setMetrics(null);
    } else {
      setMetrics(res as SystemMetrics);
      setError(null);
    }
    setLoading(false);
  }, []);

  React.useEffect(() => {
    void load();
    const t = setInterval(() => void load(), REFRESH_MS);
    return () => clearInterval(t);
  }, [load]);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6" style={{ width: "100%" }}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--fg)" }}>Monitoring</h1>
          <p className="text-sm" style={{ color: "var(--fg-2, rgb(var(--fg-rgb) / 0.6))" }}>
            Métriques système en temps réel — actualisé toute les {REFRESH_MS / 1000}s
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Actualiser
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border p-3 text-sm"
          style={{ borderColor: "var(--red)", background: "var(--red-soft)", color: "var(--fg)" }}>
          Impossible de récupérer les métriques ({error}). Vérifiez que le Core est démarré (&lsaquo;./ethan up&rsaquo;).
        </div>
      )}

      {!metrics && !error && !loading && (
        <div className="rounded-xl border p-6 text-center"
          style={{ border: "1px solid var(--border)", background: "var(--panel)", color: "var(--fg-2)" }}>
          Aucune métrique disponible.
        </div>
      )}

      {metrics && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <MetricCard icon={Cpu} title="Processeur"
            value={metrics.cpu.available ? `${metrics.cpu.percent}%` : "—"}
            sub={metrics.cpu.available ? `${metrics.cpu.cores} cœurs logiques` : undefined}
            available={metrics.cpu.available} reason={metrics.cpu.reason} />
          <MetricCard icon={MemoryStick} title="Mémoire RAM"
            value={metrics.memory.available ? fmtBytes(metrics.memory.used_bytes ?? 0) : "—"}
            sub={metrics.memory.available ? `/ ${fmtBytes(metrics.memory.total_bytes ?? 0)} (${metrics.memory.percent ?? 0}%)` : undefined}
            available={metrics.memory.available} reason={metrics.memory.reason} />
          <MetricCard icon={HardDrive} title="Stockage"
            value={metrics.disk.available ? fmtBytes(metrics.disk.free_bytes ?? 0) : "—"}
            sub={metrics.disk.available ? `(${metrics.disk.percent ?? 0}% utilisés)` : undefined}
            available={metrics.disk.available} reason={metrics.disk.reason} />
          <MetricCard icon={Zap} title="GPU / VRAM"
            value={metrics.gpu.available ? `${metrics.gpu.count} GPU` : "—"}
            sub={metrics.gpu.available
              ? metrics.gpu.gpus?.map((g) => `${g.name} (${g.vram_percent}% VRAM)`).join(", ")
              : undefined}
            available={metrics.gpu.available} reason={metrics.gpu.reason} />
          <MetricCard icon={Server} title="Processus API"
            value={metrics.process.available ? `${metrics.process.cpu_percent ?? 0}% CPU` : "—"}
            sub={metrics.process.available
              ? `PID ${metrics.process.pid ?? "?"} · RSS ${fmtBytes(metrics.process.rss_bytes ?? 0)}`
              : undefined}
            available={metrics.process.available} reason={metrics.process.reason} />
          <MetricCard icon={Server} title="Docker"
            value={metrics.docker.available
              ? `${metrics.docker.containers?.length || 0} conteneur(s)` : "—"}
            available={metrics.docker.available} reason={metrics.docker.reason} />
        </div>
      )}

      {metrics && metrics.docker.available && metrics.docker.containers && (
        <div className="mt-6 overflow-hidden rounded-xl border"
          style={{ border: "1px solid var(--border)", background: "var(--panel)" }}>
          <div className="px-4 py-2 text-xs uppercase" style={{ color: "var(--fg-3)" }}>Conteneurs</div>
          {metrics.docker.containers.map((c) => (
            <div key={c.name}
              className="flex items-center justify-between border-b px-4 py-2 text-sm last:border-b-0"
              style={{ borderColor: "var(--border)" }}>
              <span style={{ color: "var(--fg)" }}>{c.name}</span>
              <span style={{ color: "var(--fg-2)" }}>CPU {c.cpu_percent}% · {c.mem_usage}</span>
            </div>
          ))}
        </div>
      )}

      <p className="mt-5 text-xs" style={{ color: "var(--fg-3, rgb(var(--fg-rgb) / 0.45))" }}>
        Dashboard Grafana temps réel :{" "}
        <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer"
          style={{ color: "var(--accent)", textDecoration: "underline" }}>{GRAFANA_URL}</a>
      </p>
    </div>
  );
}
