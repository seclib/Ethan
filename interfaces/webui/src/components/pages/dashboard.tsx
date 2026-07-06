"use client";

import { useEffect, useState, useRef } from "react";
import { KPICard } from "@/components/widgets/kpi-card";
import { useLiveMetrics } from "@/hooks/useLiveMetrics";

// ───────── Types ─────────
interface CoreStatus {
  status: "online" | "degraded" | "offline";
  uptime: string;
  mode: string;
  version: string;
  pid: number;
}

interface PlannerStatus {
  objective: string;
  tasksDone: number;
  tasksTotal: number;
  nextStep: string;
  eta: string;
}

interface ProviderEntry {
  name: string;
  connected: boolean;
  latencyMs: number;
}

interface ModelEntry {
  name: string;
  loaded: boolean;
  sizeGb: string;
}

interface AgentEntry {
  name: string;
  status: "run" | "idle" | "sleep" | "error";
}

interface MemStats {
  entries: number;
  triplets: number;
  sessions: number;
  lastWrite: string;
}

interface ResStats {
  gpuName: string;
  gpuUtil: number;
  gpuTemp: number;
  gpuPower: number;
  vramUsed: number;
  vramTotal: number;
  cpuUtil: number;
  cpuCores: number;
  cpuLoad: number;
  ramUsed: number;
  ramTotal: number;
  stoUsed: number;
  stoTotal: number;
}

interface SysEvent {
  time: string;
  level: "info" | "ok" | "warn" | "error";
  subject: string;
}

// ───────── Mock Data ─────────
const MOCK_CORE: CoreStatus = {
  status: "online",
  uptime: "14h 22m",
  mode: "auto",
  version: "2.4.1",
  pid: 12847,
};

const MOCK_PLANNER: PlannerStatus = {
  objective: "Optimiser pipeline RAG",
  tasksDone: 3,
  tasksTotal: 8,
  nextStep: "embed.chunk → memory.store",
  eta: "14:23",
};

const MOCK_PROVIDERS: ProviderEntry[] = [
  { name: "Ollama", connected: true, latencyMs: 1.2 },
  { name: "OpenAI", connected: true, latencyMs: 230 },
  { name: "OpenRouter", connected: false, latencyMs: 0 },
  { name: "Anthropic", connected: false, latencyMs: 0 },
];

const MOCK_MODELS: ModelEntry[] = [
  { name: "gemma3:4b", loaded: true, sizeGb: "2.5" },
  { name: "llama3:8b", loaded: false, sizeGb: "4.7" },
  { name: "qwen2.5:7b", loaded: false, sizeGb: "4.1" },
  { name: "nomic-embed", loaded: false, sizeGb: "0.3" },
];

const MOCK_AGENTS: AgentEntry[] = [
  { name: "planner", status: "run" },
  { name: "executor", status: "run" },
  { name: "memory", status: "idle" },
  { name: "learning", status: "sleep" },
  { name: "reflective", status: "sleep" },
  { name: "autonomy", status: "sleep" },
];

const MOCK_MEM: MemStats = {
  entries: 2418,
  triplets: 1872,
  sessions: 47,
  lastWrite: "il y a 3s",
};

const MOCK_RES: ResStats = {
  gpuName: "NVIDIA RTX 4090",
  gpuUtil: 78,
  gpuTemp: 45,
  gpuPower: 320,
  vramUsed: 18.2,
  vramTotal: 24,
  cpuUtil: 62,
  cpuCores: 8,
  cpuLoad: 3.2,
  ramUsed: 5.8,
  ramTotal: 16,
  stoUsed: 28,
  stoTotal: 256,
};

// ───────── Sub-components ─────────

function CoreWidget({ data }: { data: CoreStatus }) {
  const statusColor = data.status === "online" ? "var(--green)" : data.status === "degraded" ? "var(--gold)" : "var(--red)";
  return (
    <div className="card-db">
      <div className="card-db-title">CORE</div>
      <div className="card-db-body" style={{ gap: 6 }}>
        <div className="flex items-center gap-2">
          <span className="status-dot-lg" style={{ background: statusColor, boxShadow: `0 0 8px ${statusColor}` }} />
          <span className="mono-sm" style={{ color: statusColor, fontWeight: 600 }}>{data.status.toUpperCase()}</span>
        </div>
        <div className="prop-row"><span className="prop-label">Uptime</span><span className="prop-val">{data.uptime}</span></div>
        <div className="prop-row"><span className="prop-label">Mode</span><span className="prop-val">{data.mode}</span></div>
        <div className="prop-row"><span className="prop-label">Version</span><span className="prop-val">{data.version}</span></div>
        <div className="prop-row"><span className="prop-label">PID</span><span className="prop-val mono-sm">{data.pid}</span></div>
        <div className="flex gap-2" style={{ marginTop: 6 }}>
          <button className="btn btn-ghost btn-xs">Relancer</button>
          <button className="btn btn-ghost btn-xs">Logs</button>
        </div>
      </div>
    </div>
  );
}

function PlannerWidget({ data }: { data: PlannerStatus }) {
  const pct = data.tasksTotal > 0 ? Math.round((data.tasksDone / data.tasksTotal) * 100) : 0;
  return (
    <div className="card-db">
      <div className="card-db-title">PLANNER</div>
      <div className="card-db-body" style={{ gap: 8 }}>
        <div className="prop-row"><span className="prop-label">Objectif</span></div>
        <div className="mono-sm" style={{ color: "var(--fg-0)", fontWeight: 500 }}>{data.objective}</div>
        <div>
          <div className="flex justify-between mono-xs" style={{ marginBottom: 4 }}>
            <span style={{ color: "var(--fg-3)" }}>Tâches</span>
            <span style={{ color: "var(--fg-1)" }}>{data.tasksDone}/{data.tasksTotal}</span>
          </div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${pct}%` }} /></div>
        </div>
        <div className="prop-row"><span className="prop-label">Prochaine étape</span><span className="prop-val mono-sm" style={{ color: "var(--accent)" }}>{data.nextStep}</span></div>
        <div className="prop-row"><span className="prop-label">Fin estimée</span><span className="prop-val mono-sm">{data.eta}</span></div>
      </div>
    </div>
  );
}

function ProvidersWidget({ providers, models }: { providers: ProviderEntry[]; models: ModelEntry[] }) {
  return (
    <div className="card-db">
      <div className="card-db-title">PROVIDERS <span className="ml-auto mono-xs" style={{ color: "var(--fg-3)", fontWeight: 400 }}>{providers.filter(p => p.connected).length}/{providers.length}</span></div>
      <div className="card-db-body" style={{ gap: 4 }}>
        {providers.map((p) => (
          <div key={p.name} className="flex items-center justify-between" style={{ padding: "4px 0" }}>
            <div className="flex items-center gap-2">
              <span className="status-dot" style={{ background: p.connected ? "var(--green)" : "var(--fg-4)", boxShadow: p.connected ? "0 0 6px var(--green)" : "none" }} />
              <span className="mono-xs" style={{ color: "var(--fg-1)" }}>{p.name}</span>
            </div>
            <span className="mono-xs" style={{ color: p.connected ? "var(--fg-3)" : "var(--fg-4)" }}>{p.connected ? `${p.latencyMs}ms` : "—"}</span>
          </div>
        ))}
      </div>
      <div className="card-db-sep" />
      <div className="card-db-title" style={{ marginTop: 6 }}>MODÈLES <span className="ml-auto mono-xs" style={{ color: "var(--fg-3)", fontWeight: 400 }}>{models.filter(m => m.loaded).length}/{models.length}</span></div>
      <div className="card-db-body" style={{ gap: 4, marginTop: 6 }}>
        {models.map((m) => (
          <div key={m.name} className="flex items-center justify-between" style={{ padding: "4px 0" }}>
            <div className="flex items-center gap-2">
              <span className="status-dot" style={{ background: m.loaded ? "var(--green)" : "var(--fg-4)" }} />
              <span className="mono-xs" style={{ color: "var(--fg-1)" }}>{m.name}</span>
            </div>
            <span className="mono-xs" style={{ color: "var(--fg-4)" }}>{m.sizeGb} GB</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AgentsWidget({ agents }: { agents: AgentEntry[] }) {
  const statusIcon = (s: string) => {
    if (s === "run") return { dot: "var(--green)", glow: "0 0 6px var(--green)" };
    if (s === "idle") return { dot: "var(--fg-3)", glow: "none" };
    if (s === "sleep") return { dot: "var(--fg-4)", glow: "none" };
    return { dot: "var(--red)", glow: "0 0 6px var(--red)" };
  };
  return (
    <div className="card-db">
      <div className="card-db-title">AGENTS <span className="ml-auto mono-xs" style={{ color: "var(--fg-3)", fontWeight: 400 }}>{agents.filter(a => a.status === "run").length}/{agents.length}</span></div>
      <div className="card-db-body" style={{ gap: 2 }}>
        {agents.map((a) => {
          const s = statusIcon(a.status);
          return (
            <div key={a.name} className="flex items-center gap-2" style={{ padding: "4px 6px", borderRadius: 6, transition: "background 0.15s" }}>
              <span className="status-dot" style={{ background: s.dot, boxShadow: s.glow }} />
              <span className="mono-xs" style={{ color: "var(--fg-1)", flex: 1 }}>{a.name}</span>
              <span className="mono-xs" style={{ color: a.status === "run" ? "var(--green)" : a.status === "idle" ? "var(--fg-3)" : a.status === "error" ? "var(--red)" : "var(--fg-4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{a.status}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MemWidget({ data }: { data: MemStats }) {
  return (
    <div className="card-db">
      <div className="card-db-title">MÉMOIRE</div>
      <div className="card-db-body" style={{ gap: 6 }}>
        <div className="prop-row"><span className="prop-label">Entrées</span><span className="prop-val mono-sm">{data.entries.toLocaleString()}</span></div>
        <div className="prop-row"><span className="prop-label">Triplets</span><span className="prop-val mono-sm">{data.triplets.toLocaleString()}</span></div>
        <div className="prop-row"><span className="prop-label">Sessions</span><span className="prop-val mono-sm">{data.sessions}</span></div>
        <div className="prop-row" style={{ marginTop: 4 }}><span className="prop-label">Dernière écriture</span><span className="prop-val mono-xs" style={{ color: "var(--fg-3)" }}>{data.lastWrite}</span></div>
      </div>
    </div>
  );
}

function ResWidget({ data }: { data: ResStats }) {
  const gpuPct = Math.round((data.vramUsed / data.vramTotal) * 100);
  const ramPct = Math.round((data.ramUsed / data.ramTotal) * 100);
  const stoPct = Math.round((data.stoUsed / data.stoTotal) * 100);
  const barColor = (pct: number) => pct > 85 ? "var(--red)" : pct > 65 ? "var(--gold)" : "var(--accent)";

  return (
    <div className="card-db">
      <div className="card-db-title">RESSOURCES</div>
      <div className="card-db-body" style={{ gap: 10 }}>
        {/* GPU */}
        <div>
          <div className="flex justify-between items-center" style={{ marginBottom: 4 }}>
            <span className="mono-xs" style={{ color: "var(--fg-1)", fontWeight: 500 }}>GPU</span>
            <span className="mono-xs" style={{ color: "var(--fg-3)" }}>{data.gpuUtil}% · {data.gpuTemp}°C · {data.gpuPower}W</span>
          </div>
          <div className="mono-xs" style={{ color: "var(--fg-4)", marginBottom: 4 }}>{data.gpuName}</div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${data.gpuUtil}%`, background: barColor(data.gpuUtil) }} /></div>
          <div className="mono-xs" style={{ color: "var(--fg-3)", marginTop: 2 }}>VRAM {data.vramUsed}/{data.vramTotal} GB ({gpuPct}%)</div>
        </div>
        {/* CPU */}
        <div>
          <div className="flex justify-between mono-xs" style={{ marginBottom: 4 }}>
            <span style={{ color: "var(--fg-1)", fontWeight: 500 }}>CPU</span>
            <span style={{ color: "var(--fg-3)" }}>{data.cpuUtil}% · {data.cpuCores} cœurs</span>
          </div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${data.cpuUtil}%`, background: barColor(data.cpuUtil) }} /></div>
          <div className="mono-xs" style={{ color: "var(--fg-3)", marginTop: 2 }}>load {data.cpuLoad}/{data.cpuCores}</div>
        </div>
        {/* RAM */}
        <div>
          <div className="flex justify-between mono-xs" style={{ marginBottom: 4 }}>
            <span style={{ color: "var(--fg-1)", fontWeight: 500 }}>RAM</span>
            <span style={{ color: "var(--fg-3)" }}>{ramPct}%</span>
          </div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${ramPct}%`, background: barColor(ramPct) }} /></div>
          <div className="mono-xs" style={{ color: "var(--fg-3)", marginTop: 2 }}>{data.ramUsed}/{data.ramTotal} GB</div>
        </div>
        {/* Stockage */}
        <div>
          <div className="flex justify-between mono-xs" style={{ marginBottom: 4 }}>
            <span style={{ color: "var(--fg-1)", fontWeight: 500 }}>STO</span>
            <span style={{ color: "var(--fg-3)" }}>{stoPct}%</span>
          </div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${stoPct}%`, background: barColor(stoPct) }} /></div>
          <div className="mono-xs" style={{ color: "var(--fg-3)", marginTop: 2 }}>{data.stoUsed}/{data.stoTotal} GB</div>
        </div>
      </div>
    </div>
  );
}

function EventsWidget({ events: initial }: { events: SysEvent[] }) {
  const [events, setEvents] = useState(initial);
  const [filter, setFilter] = useState<string | null>(null);

  // Simulate live events
  useEffect(() => {
    const labels = ["planner.task.done", "agent.run.completed", "memory.store", "executor.task.assigned", "provider.ollama.latency", "core.heartbeat"];
    const levels: SysEvent["level"][] = ["info", "ok", "warn", "error"];
    const t = setInterval(() => {
      const ev: SysEvent = {
        time: new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        level: levels[Math.floor(Math.random() * 4)],
        subject: labels[Math.floor(Math.random() * labels.length)],
      };
      setEvents(prev => [ev, ...prev].slice(0, 50));
    }, 4000);
    return () => clearInterval(t);
  }, []);

  const filtered = filter ? events.filter(e => e.subject.includes(filter)) : events;

  const levelIcon: Record<string, string> = { info: "ℹ ", ok: "✓ ", warn: "⚠ ", error: "✗ " };
  const levelColor: Record<string, string> = { info: "var(--fg-1)", ok: "var(--green)", warn: "var(--gold)", error: "var(--red)" };

  return (
    <div className="card-db" style={{ gridColumn: "1 / -1" }}>
      <div className="card-db-title">
        ÉVÉNEMENTS
        <div className="flex gap-3 ml-auto">
          {["", "planner", "agent", "memory", "core"].map((f) => (
            <button key={f} className="filter-chip-xs" data-active={filter === f || (!filter && !f)} onClick={() => setFilter(f || null)}>
              {f || "Tous"}
            </button>
          ))}
        </div>
      </div>
      <div className="card-db-body" style={{ gap: 0, maxHeight: 200, overflowY: "auto" }}>
        {filtered.slice(0, 20).map((ev, i) => (
          <div key={i} className="flex items-center gap-3" style={{ padding: "5px 4px", borderBottom: "0.5px solid var(--line-1)", fontFamily: "ui-monospace, monospace", fontSize: 11 }}>
            <span style={{ color: "var(--fg-4)", minWidth: 58 }}>{ev.time}</span>
            <span style={{ color: levelColor[ev.level], minWidth: 14 }}>{levelIcon[ev.level]}</span>
            <span style={{ color: ev.level === "error" ? "var(--red)" : ev.level === "warn" ? "var(--gold)" : "var(--fg-1)" }}>{ev.subject}</span>
          </div>
        ))}
        {filtered.length === 0 && <div className="mono-xs" style={{ color: "var(--fg-4)", padding: 16, textAlign: "center" }}>Aucun événement</div>}
      </div>
    </div>
  );
}

// ───────── KPI Data ─────────
const KPI_DATA = [
  { label: "Requêtes", value: "1 284", trend: 12.3, up: true, unit: "req/h" },
  { label: "Latence", value: "47ms", trend: 3.1, up: false, unit: "p50" },
  { label: "Agents", value: "4", trend: 0, up: true, unit: "actifs" },
  { label: "Uptime", value: "99.2", trend: 0.1, up: true, unit: "%" },
  { label: "Tokens", value: "142.5k", trend: 5.2, up: true, unit: "auj." },
  { label: "Erreurs", value: "0", trend: 0, up: true, unit: "dernière h" },
];

// ───────── Mock Events ─────────
const MOCK_EVENTS: SysEvent[] = [
  { time: "08:42:13", level: "info", subject: "planner.task.done" },
  { time: "08:42:10", level: "info", subject: "agent.run.completed" },
  { time: "08:42:07", level: "ok", subject: "memory.store" },
  { time: "08:42:04", level: "info", subject: "executor.task.assigned" },
  { time: "08:42:01", level: "warn", subject: "provider.ollama.latency" },
  { time: "08:41:58", level: "ok", subject: "core.heartbeat" },
];

// ───────── Main Page ─────────
export function DashboardPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(t);
  }, []);

  if (loading) {
    return (
      <div className="page-in" style={{ display: "flex", flexDirection: "column", gap: 16, padding: "24px 0" }}>
        {/* Skeleton KPI row */}
        <div className="kpi-row">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="kpi-skeleton" />
          ))}
        </div>
        {/* Skeleton grid */}
        <div className="db-grid">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="card-skeleton" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="page-in" style={{ display: "flex", flexDirection: "column", gap: 18, padding: "24px 0" }}>

      {/* ─── KPI ROW ─── */}
      <div className="kpi-row">
        {KPI_DATA.map((k, i) => (
          <KPICard key={i} {...k} />
        ))}
      </div>

      {/* ─── CORE + PLANNER ─── */}
      <div className="db-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <CoreWidget data={MOCK_CORE} />
        <PlannerWidget data={MOCK_PLANNER} />
      </div>

      {/* ─── PROVIDERS + MODÈLES + AGENTS + MÉMOIRE ─── */}
      <div className="db-grid" style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
        <ProvidersWidget providers={MOCK_PROVIDERS} models={MOCK_MODELS} />
        <AgentsWidget agents={MOCK_AGENTS} />
        <MemWidget data={MOCK_MEM} />
        <ResWidget data={MOCK_RES} />
      </div>

      {/* ─── ÉVÉNEMENTS (full width) ─── */}
      <EventsWidget events={MOCK_EVENTS} />

    </div>
  );
}