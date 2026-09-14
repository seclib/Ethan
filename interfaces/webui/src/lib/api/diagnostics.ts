/**
 * ETHAN WebUI — Diagnostics & Monitoring API service
 *
 * Consomme les capacités Core-owned exposées par :
 *   GET /diagnostics          → SystemDiagnostics.run()
 *   GET /diagnostics/metrics  → SystemMetrics.collect()
 *
 * Le proxy /api/* → FastAPI est assuré par src/app/api/[...path]/route.ts
 * (conversion cookie JWT → Authorization Bearer, SSE, uploads binaires).
 *
 * Aucune logique métier : types + wrappers fetch.
 */

export type DiagStatus = "ok" | "warning" | "error" | "unavailable";

export interface DiagComponent {
  component: string;
  status: DiagStatus;
  message: string;
  detail?: string;
  metadata?: Record<string, unknown>;
  duration_ms: number;
}

export interface DiagSummary {
  total: number;
  counts: Record<string, number>;
  status: "healthy" | "degraded" | "unhealthy";
}

export interface DiagnosticsReport {
  timestamp: string;
  summary: DiagSummary;
  components: Record<string, DiagComponent>;
}

export interface MetricSection {
  available: boolean;
  reason?: string;
  [key: string]: unknown;
}

export interface CpuMetric extends MetricSection {
  percent?: number;
  cores?: number;
  physical_cores?: number;
  per_core?: number[];
  load?: { "1m": number; "5m": number; "15m": number };
}

export interface MemoryMetric extends MetricSection {
  total_bytes?: number;
  used_bytes?: number;
  percent?: number;
  swap_percent?: number;
}

export interface DiskMetric extends MetricSection {
  path?: string;
  total_bytes?: number;
  used_bytes?: number;
  free_bytes?: number;
  percent?: number;
  inode_percent?: number;
}

export interface GpuMetric extends MetricSection {
  count?: number;
  gpus?: Array<{
    index: number;
    name: string;
    vram_total_bytes?: number;
    vram_used_bytes?: number;
    vram_percent?: number;
    gpu_percent?: number;
    temperature_c?: number | null;
  }>;
}

export interface ProcessMetric extends MetricSection {
  pid?: number;
  cpu_percent?: number;
  rss_bytes?: number;
  threads?: number;
  create_time?: number;
}

export interface ContainerStat {
  name: string;
  cpu_percent: string;
  mem_usage: string;
}

export interface DockerMetric extends MetricSection {
  containers?: ContainerStat[];
}

export interface SystemMetrics {
  timestamp: number;
  uptime_seconds: number;
  cpu: CpuMetric;
  memory: MemoryMetric;
  disk: DiskMetric;
  gpu: GpuMetric;
  process: ProcessMetric;
  docker: DockerMetric;
}

export interface ApiError {
  ok: false;
  status: number;
  message: string;
}

/**
 * Requête GET typée via le proxy /api/*.
 * Le proxy injecte le cookie JWT → Authorization Bearer automatiquement.
 */
export async function fetchDiagnostics(
  components?: string[],
): Promise<DiagnosticsReport | ApiError> {
  const qs = new URLSearchParams();
  if (components && components.length > 0) {
    qs.set("components", components.join(","));
  }
  const path = qs.toString() ? `/diagnostics?${qs}` : "/diagnostics";
  const res = await fetch(`/api${path}`, { cache: "no-store" });
  if (!res.ok) {
    return { ok: false, status: res.status, message: `HTTP ${res.status}` };
  }
  return (await res.json()) as DiagnosticsReport;
}

export async function fetchMetrics(): Promise<SystemMetrics | ApiError> {
  const res = await fetch("/api/diagnostics/metrics", { cache: "no-store" });
  if (!res.ok) {
    return { ok: false, status: res.status, message: `HTTP ${res.status}` };
  }
  return (await res.json()) as SystemMetrics;
}

/** Mappe un DiagStatus → label + couleur CSS. */
export function statusMeta(status: DiagStatus): {
  label: string;
  color: string;
} {
  switch (status) {
    case "ok":
      return { label: "OK", color: "var(--green)" };
    case "warning":
      return { label: "AVERTISSEMENT", color: "var(--amber)" };
    case "error":
      return { label: "ERREUR", color: "var(--red)" };
    case "unavailable":
      return { label: "INDISPO.", color: "var(--fg-2, rgb(var(--fg-rgb) / 0.5))" };
    default:
      return { label: status, color: "var(--fg-2, rgb(var(--fg-rgb) / 0.5))" };
  }
}

/** URL externe du dashboard Grafana (osiris-grafana, cf. port_registry.json). */
export const GRAFANA_URL = "http://localhost:3002";

/** Ordre d'affichage stable des composants dans la page Diagnostics. */
export const DIAG_COMPONENT_ORDER = [
  "cpu", "memory", "disk",
  "postgres", "redis", "nats",
  "kernel", "docker",
  "providers", "models",
  "knowledge", "tools", "mcp", "plugins",
  "filesystem",
] as const;
