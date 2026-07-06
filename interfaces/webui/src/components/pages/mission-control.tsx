"use client";

import { useEffect, useState } from "react";
import { KPICard } from "@/components/widgets/kpi-card";
import { useLiveMetrics } from "@/hooks/useLiveMetrics";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useStore } from "@/lib/store";
import { useToast } from "@/components/ui/toast";

type LiveKPI = { label: string; value: string; trend: number; up: boolean; unit: string };
type TimelineEvent = { time: string; source: string; message: string; type: "info" | "success" | "warn" | "error" };
type ProjectCard = { id: string; name: string; progress: number; step: string; total: number };

const INITIAL_KPI: LiveKPI[] = [
  { label: "Kernel", value: "● ONLINE", trend: 99.2, up: true, unit: "% uptime" },
  { label: "Modules", value: "12", trend: 0, up: true, unit: "actifs" },
  { label: "Goals", value: "3", trend: 1, up: true, unit: "actives" },
  { label: "Budget", value: "2.4k", trend: 0, up: false, unit: "tokens" },
];

const TIMELINE_EVENTS: TimelineEvent[] = [
  { time: "14:32", source: "kernel", message: "Plan exécuté avec succès", type: "success" },
  { time: "14:31", source: "module", message: "Memory : 124 faits consolidés", type: "info" },
  { time: "14:30", source: "goal", message: "Nouvel objectif créé : Déployer v2", type: "info" },
  { time: "14:28", source: "system", message: "Budget : 78% consommé", type: "warn" },
  { time: "14:25", source: "error", message: "Timeout sur module learning", type: "error" },
];

const PROJECTS: ProjectCard[] = [
  { id: "p1", name: "Déploiement API", progress: 80, step: "3/5", total: 5 },
  { id: "p2", name: "Analyse marché", progress: 20, step: "1/8", total: 8 },
  { id: "p3", name: "Monitoring", progress: 60, step: "2/3", total: 3 },
];

const TYPE_COLORS: Record<string, string> = {
  info: "var(--accent)",
  success: "var(--green)",
  warn: "var(--gold)",
  error: "var(--red)",
};

export function MissionControlPage() {
  const [kpis, setKpis] = useState<LiveKPI[]>(INITIAL_KPI);

  useLiveMetrics<LiveKPI>("/api/metrics/kpi", kpis, 2000);
  const { data: wsData } = useWebSocket<{ type: string; message: string }>("ws://localhost:8000/ws", "system.events");

  const { toast } = useToast();

  useEffect(() => {
    if (wsData) {
      toast(wsData.type as "info" | "success" | "warning" | "error", wsData.message);
    }
  }, [wsData, toast]);

  return (
    <div className="page-mission-control">
      <div className="mc-kpi-grid">
        {kpis.map((kpi, i) => (
          <KPICard key={i} {...kpi} accent={["blue", "green", "gold", "purple"][i] as any} sparkline={[30, 45, 38, 52, 48, 55]} />
        ))}
      </div>

      <div className="mc-main-grid">
        <div className="mc-timeline">
          <div className="mc-section-title">Timeline des événements</div>
          <div className="mc-timeline-list">
            {TIMELINE_EVENTS.map((ev, i) => (
              <div key={i} className="mc-timeline-item" style={{ borderLeftColor: TYPE_COLORS[ev.type] }}>
                <span className="mc-timeline-time">{ev.time}</span>
                <span className="mc-timeline-source" style={{ color: TYPE_COLORS[ev.type] }}>[{ev.source}]</span>
                <span className="mc-timeline-msg">{ev.message}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mc-projects">
          <div className="mc-section-title">Projets actifs</div>
          <div className="mc-projects-list">
            {PROJECTS.map((p) => (
              <div key={p.id} className="mc-project-card">
                <div className="mc-project-header">
                  <span className="mc-project-name">{p.name}</span>
                  <span className="mc-project-step">Étape {p.step}</span>
                </div>
                <div className="mc-project-bar">
                  <div className="mc-project-bar-fill" style={{ width: `${p.progress}%` }} />
                </div>
                <span className="mc-project-pct">{p.progress}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}