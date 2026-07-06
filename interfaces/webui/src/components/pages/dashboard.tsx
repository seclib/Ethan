"use client";

import { useEffect, useState, useCallback } from "react";
import { KPICard } from "@/components/widgets/kpi-card";
import { ProjectCard } from "@/components/widgets/project-card";
import { TasksWidget } from "@/components/widgets/tasks-widget";
import { SourceBars } from "@/components/widgets/analytics-widgets";
import { KPISkeleton, CardSkeleton } from "@/components/ui/skeleton";
import { useLiveMetrics } from "@/hooks/useLiveMetrics";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { useWebSocket } from "@/hooks/useWebSocket";

const INITIAL_KPI = [
  { label: "Requêtes", value: "1 284", trend: 12.3, up: true, unit: "req/h" },
  { label: "Temps", value: "47s", trend: 3.1, up: false, unit: "latence" },
  { label: "Agents", value: "12", trend: 0, up: true, unit: "actifs" },
  { label: "Uptime", value: "99.2", trend: 0.1, up: true, unit: "%" },
  { label: "Événements", value: "3.2k", trend: 8.4, up: true, unit: "+/h" },
];

const PROJECTS = [
  { name: "Agent NLP", status: "active" as const, progress: 80, tasks: { done: 14, total: 21 } },
  { name: "Pipeline ETL", status: "pending" as const, progress: 45, tasks: { done: 5, total: 12 } },
  { name: "API Gateway", status: "completed" as const, progress: 100, tasks: { done: 8, total: 8 } },
];

const TASKS = [
  { id: "1", label: "Déployer v2.1", done: true },
  { id: "2", label: "Tester intégration", done: false },
  { id: "3", label: "Mettre à jour docs", done: false },
];

type LiveKPI = { label: string; value: string; trend: number; up: boolean; unit: string };

type WidgetItem =
  | { type: "kpi"; data: LiveKPI }
  | { type: "project"; data: typeof PROJECTS[0] }
  | { type: "tasks" }
  | { type: "sources" };

const INITIAL_WIDGETS: WidgetItem[] = [
  ...INITIAL_KPI.map((k) => ({ type: "kpi" as const, data: k })),
  { type: "project", data: PROJECTS[0] },
  { type: "project", data: PROJECTS[1] },
  { type: "project", data: PROJECTS[2] },
  { type: "tasks" },
  { type: "sources" },
];

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<LiveKPI[]>(INITIAL_KPI);
  const [widgets, setWidgets] = useLocalStorage<WidgetItem[]>("dashboard:widgets", INITIAL_WIDGETS);
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const [overIdx, setOverIdx] = useState<number | null>(null);

  useLiveMetrics<LiveKPI>("/api/metrics/kpi", kpis, 2000);
  useWebSocket<LiveKPI[]>("ws://localhost:8000/ws", "metrics.kpi");

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 1200);
    return () => clearTimeout(t);
  }, []);

  const onDragStart = useCallback((idx: number) => () => setDragIdx(idx), []);
  const onDragOver = useCallback((idx: number) => () => setOverIdx(idx), []);
  const onDrop = useCallback(
    (targetIdx: number) => () => {
      if (dragIdx === null || dragIdx === targetIdx) return;
      setWidgets((prev) => {
        const next = prev.slice();
        const [moved] = next.splice(dragIdx, 1);
        next.splice(targetIdx, 0, moved);
        return next;
      });
      setDragIdx(null);
      setOverIdx(null);
    },
    [dragIdx]
  );
  const onDragEnd = useCallback(() => {
    setDragIdx(null);
    setOverIdx(null);
  }, []);

  const renderWidget = (item: WidgetItem, idx: number) => {
    const isOver = overIdx === idx;
    const isDragging = dragIdx === idx;
    if (loading && item.type === "kpi") {
      return <KPISkeleton key={idx} />;
    }
    if (loading && item.type === "project") {
      return <CardSkeleton key={idx} />;
    }
    if (item.type === "kpi") {
      return <KPICard key={idx} {...item.data} />;
    }
    if (item.type === "project") {
      return <ProjectCard key={idx} {...item.data} />;
    }
    if (item.type === "tasks") {
      return <TasksWidget key={idx} title="Tâches" tasks={TASKS} />;
    }
    if (item.type === "sources") {
      return (
        <SourceBars
          key={idx}
          title="Sources"
          items={[
            { label: "Web", value: 45 },
            { label: "API", value: 30 },
            { label: "SDK", value: 25 },
          ]}
        />
      );
    }
    return null;
  };

  return (
    <div className="page-in">
      <div className="dashboard-grid">
        {widgets.slice(0, 5).map((item, idx) => {
          const isOver = overIdx === idx;
          const isDragging = dragIdx === idx;
          return (
            <div
              key={idx}
              draggable
              onDragStart={onDragStart(idx)}
              onDragOver={onDragOver(idx)}
              onDrop={onDrop(idx)}
              onDragEnd={onDragEnd}
              style={{
                opacity: isDragging ? 0.4 : 1,
                transform: isOver && dragIdx !== idx ? "scale(1.01)" : undefined,
                transition: "opacity 0.15s, transform 0.15s",
                cursor: "grab",
              }}
            >
              {renderWidget(item, idx)}
            </div>
          );
        })}
      </div>

      <div className="dashboard-grid" style={{ marginTop: 16 }}>
        {widgets.slice(5).map((item, idx) => {
          const realIdx = idx + 5;
          const isOver = overIdx === realIdx;
          const isDragging = dragIdx === realIdx;
          return (
            <div
              key={realIdx}
              draggable
              onDragStart={onDragStart(realIdx)}
              onDragOver={onDragOver(realIdx)}
              onDrop={onDrop(realIdx)}
              onDragEnd={onDragEnd}
              style={{
                opacity: isDragging ? 0.4 : 1,
                transform: isOver && dragIdx !== realIdx ? "scale(1.01)" : undefined,
                transition: "opacity 0.15s, transform 0.15s",
                cursor: "grab",
              }}
            >
              {renderWidget(item, realIdx)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
