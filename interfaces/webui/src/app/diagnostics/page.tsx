"use client";

/**
 * Diagnostics — page Administration ETHAN.
 *
 * Consomme la capacité Core-owned exposée par :
 *   GET /api/diagnostics          → SystemDiagnostics.run()
 *   GET /api/diagnostics/metrics  → SystemMetrics.collect()
 *
 * Le proxy /api/* → FastAPI injecte automatiquement le cookie JWT →
 * Authorization Bearer. Aucune donnée fictive : chaque check interroge
 * le composant réel (ping SQL, Redis, NATS, docker ps, …).
 */

import * as React from "react";
import {
  RefreshCw,
  ChevronDown,
  Server,
  Activity,
  Database,
  Cloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DiagnosticsReport,
  DiagComponent,
  DiagStatus,
  SystemMetrics,
  fetchDiagnostics,
  fetchMetrics,
  statusMeta,
  DIAG_COMPONENT_ORDER,
  GRAFANA_URL,
} from "@/lib/api/diagnostics";

const REFRESH_MS = 30_000;

const STATUS_COLORS: Record<string, string> = {
  ok: "var(--green)",
  warning: "var(--amber)",
  error: "var(--red)",
  unavailable: "var(--fg-2, rgb(var(--fg-rgb) / 0.5))",
};

const EXPANDED_DEFAULT = [
  "postgres",
  "redis",
  "nats",
  "kernel",
  "docker",
  "providers",
  "models",
];

function iconFor(component: string) {
  switch (component) {
    case "postgres":
    case "redis":
    case "nats":
    case "kernel":
    case "docker":
      return Server;
    case "providers":
    case "models":
      return Cloud;
    case "knowledge":
      return Database;
    default:
      return Activity;
  }
}

export default function DiagnosticsPage() {
  const [report, setReport] = React.useState<DiagnosticsReport | null>(null);
  const [metrics, setMetrics] = React.useState<SystemMetrics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    const [diagRes, metricsRes] = await Promise.all([
      fetchDiagnostics(),
      fetchMetrics(),
    ]);

    if (!("ok" in diagRes) && diagRes) {
      setReport(diagRes as DiagnosticsReport);
    } else if ("ok" in diagRes) {
      setReport(null);
      setError(
        (diagRes as { ok: false; message: string }).message ||
          "Erreur lors de la récupération des diagnostics",
      );
    }

    if (!("ok" in metricsRes) && metricsRes) {
      setMetrics(metricsRes as SystemMetrics);
    }
    setLoading(false);
  }, []);

  React.useEffect(() => {
    void load();
    const t = setInterval(() => void load(), REFRESH_MS);
    return () => clearInterval(t);
  }, [load]);

  const allComponents = report
    ? (Object.keys(report.components).sort(
        (a, b) =>
          (DIAG_COMPONENT_ORDER as readonly string[]).indexOf(a) -
          (DIAG_COMPONENT_ORDER as readonly string[]).indexOf(b),
      ) as string[]).filter((k) => k !== "gpu")
    : [];

  const hasGpu = Boolean(report?.components?.gpu) || Boolean(metrics?.gpu);

  const overall = report?.summary?.status ?? "degraded";
  const overallColor =
    overall === "healthy"
      ? "var(--green)"
      : overall === "unhealthy"
        ? "var(--red)"
        : "var(--amber)";

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6" style={{ width: "100%" }}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--fg)" }}>
            Diagnostics
          </h1>
          <p className="text-sm" style={{ color: "var(--fg-2, rgb(var(--fg-rgb) / 0.6))" }}>
            Vérification réelle de l&apos;état d&apos;ETHAN — actualisé toutes les {REFRESH_MS / 1000}s
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Actualiser
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border p-3 text-sm"
          style={{ borderColor: "var(--red)", background: "var(--red-soft)", color: "var(--fg)" }}>
          Impossible de joindre l&apos;API ETHAN ({error}). Vérifiez que le Core est démarré (&lsaquo;./ethan up&rsaquo;).
        </div>
      )}

      {report && (
        <div className="mb-5 flex items-center gap-3 rounded-xl border p-3"
          style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
          <Activity size={16} style={{ color: overallColor }} />
          <span className="text-sm font-medium" style={{ color: "var(--fg)" }}>
            État global : <strong style={{ color: overallColor }}>{overall}</strong>
          </span>
          <span className="text-xs" style={{ color: "var(--fg-3)" }}>
            ({report.summary.counts.ok}/{report.summary.total} OK, {report.summary.counts.warning} avert., {report.summary.counts.error} erreurs, {report.summary.counts.unavailable} indispo.)
          </span>
        </div>
      )}

      {loading && !report && !error && (
        <div className="rounded-xl border p-8 text-center"
          style={{ border: "1px solid var(--border)", background: "var(--panel)", color: "var(--fg-2, rgb(var(--fg-rgb) / 0.6))" }}>
          Diagnostic en cours…
        </div>
      )}

      {report && (
        <>
          <ComponentList
            components={Object.values(report.components).filter(
              (c: DiagComponent) => c.component !== "gpu",
            )}
            order={allComponents}
          />
          {hasGpu && <GpuCard metrics={metrics} report={report} />}
        </>
      )}

      <p className="mt-5 text-xs" style={{ color: "var(--fg-3, rgb(var(--fg-rgb) / 0.45))" }}>
        Moniteur temps réel des conteneurs :{" "}
        <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer"
          style={{ color: "var(--accent)", textDecoration: "underline" }}>
          Grafana ({new URL(GRAFANA_URL).port})
        </a>{" "}
        · Données du Core, jamais simulées.
      </p>
    </div>
  );
}

function ComponentList({ components, order }: { components: DiagComponent[]; order: string[] }) {
  if (components.length === 0) return null;
  const sorted = [...components].sort(
    (a, b) =>
      (order as readonly string[]).indexOf(a.component) -
      (order as readonly string[]).indexOf(b.component),
  );
  return (
    <div className="mb-4 overflow-hidden rounded-xl border"
      style={{ border: "1px solid var(--border)", background: "var(--panel)" }}>
      {sorted.map((c) => (
        <ComponentRow key={c.component} c={c} />
      ))}
    </div>
  );
}

function ComponentRow({ c }: { c: DiagComponent }) {
  const meta = statusMeta(c.status as DiagStatus);
  const Icon = iconFor(c.component);
  return (
        <details className="group border-b px-4 py-3 last:border-b-0"
      style={{ borderColor: "var(--border)" }}
      {...{ defaultOpen: EXPANDED_DEFAULT.includes(c.component) }}>
      <summary className="flex cursor-pointer items-center gap-3 text-sm">
        <Icon size={14} style={{ color: "var(--accent)" }} />
        <span style={{ color: "var(--fg)" }}>{c.component}</span>
        <span className="ml-auto flex items-center gap-1.5 text-xs font-medium"
          style={{ color: STATUS_COLORS[c.status] }}>
          <span className="inline-block size-1.5 rounded-full" style={{ background: STATUS_COLORS[c.status] }} />
          {meta.label}
        </span>
        <ChevronDown size={12} className="transition-transform group-open:rotate-180"
          style={{ color: "var(--fg-3)" }} />
      </summary>
      <div className="mt-2 text-xs" style={{ color: "var(--fg-2)" }}>
        <p className="mb-1">{c.message}</p>
        {c.detail && <p className="font-mono opacity-70">{c.detail}</p>}
        {c.duration_ms > 0 && <p className="mt-1 opacity-60">Durée du check : {c.duration_ms} ms</p>}
      </div>
    </details>
  );
}

function GpuCard({ metrics, report }: { metrics: SystemMetrics | null; report: DiagnosticsReport | null }) {
  const rawGpu = metrics?.gpu ?? report?.components?.gpu;
  if (!rawGpu) return null;
  const gpu = rawGpu as {
    available: boolean;
    reason?: string;
    gpus?: Array<{
      name: string; vram_total_gb: number; vram_used_gb: number;
      vram_percent?: number; gpu_percent?: number; temperature_c?: number | null;
    }>;
  };
  const { label, color: dotColor } = statusMeta(
    gpu.available ? "ok" : "unavailable",
  );
  return (
    <details className="mb-4 overflow-hidden rounded-xl border"
      style={{ border: "1px solid var(--border)", background: "var(--panel)" }}
      {...{ defaultOpen: true }}>
      <summary className="flex cursor-pointer items-center gap-3 px-4 py-3 text-sm">
        <Cloud size={14} style={{ color: "var(--accent)" }} />
        <span style={{ color: "var(--fg)" }}>GPU / VRAM</span>
        <span className="ml-auto flex items-center gap-1.5 text-xs font-medium" style={{ color: dotColor }}>
          <span className="inline-block size-1.5 rounded-full" style={{ background: dotColor }} />
          {label}
        </span>
        <ChevronDown size={12} className="transition-transform group-open:rotate-180" style={{ color: "var(--fg-3)" }} />
      </summary>
      <div className="px-4 pb-3 text-xs" style={{ color: "var(--fg-2)" }}>
        {gpu.available && gpu.gpus?.length ? (
          <div className="space-y-1">
            {gpu.gpus.map((g) => (
              <div key={g.name}>
                <span className="font-medium" style={{ color: "var(--fg)" }}>{g.name}</span>{" "}— VRAM {g.vram_used_gb.toFixed(1)}/{g.vram_total_gb.toFixed(1)} Go ({g.vram_percent}%) · util. {g.gpu_percent}%
                {g.temperature_c != null && ` · ${g.temperature_c}°C`}
              </div>
            ))}
          </div>
        ) : (
          <p className="italic opacity-70">{gpu.reason || "Indisponible"}</p>
        )}
      </div>
    </details>
  );
}
