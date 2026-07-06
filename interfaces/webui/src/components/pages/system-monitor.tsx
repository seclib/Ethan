"use client";

import { useWebSocket } from "@/hooks/useWebSocket";

const MODULES = [
  { name: "executive", status: "running", cpu: 2.1, mem: 45 },
  { name: "planner", status: "running", cpu: 1.8, mem: 38 },
  { name: "memory", status: "running", cpu: 3.2, mem: 92 },
  { name: "reflective", status: "idle", cpu: 0.0, mem: 12 },
  { name: "learning", status: "running", cpu: 2.5, mem: 67 },
  { name: "autonomy", status: "running", cpu: 0.8, mem: 28 },
];

const EVENTS = [
  { time: "14:32:01", subject: "ethan.planner.plan.created", level: "info" },
  { time: "14:32:00", subject: "ethan.executor.task.completed", level: "info" },
  { time: "14:31:58", subject: "ethan.memory.store.complete", level: "success" },
  { time: "14:31:55", subject: "ethan.system.error", level: "error" },
  { time: "14:31:50", subject: "ethan.module.learning.heartbeat", level: "info" },
];

export function SystemMonitorPage() {
  const { status } = useWebSocket("ws://localhost:8000/ws", "system.monitor");

  return (
    <div className="page-monitor">
      <h1 className="page-title">System Monitor</h1>

      <div className="monitor-kpis">
        <div className="monitor-kpi">
          <span className="monitor-kpi-label">Kernel</span>
          <span className="monitor-kpi-value" style={{ color: "var(--green)" }}>● ONLINE</span>
          <span className="monitor-kpi-sub">Uptime: 4h23</span>
        </div>
        <div className="monitor-kpi">
          <span className="monitor-kpi-label">Event Bus</span>
          <span className="monitor-kpi-value" style={{ color: status === "open" ? "var(--green)" : "var(--gold)" }}>
            {status === "open" ? "● OK" : "◐ RECONNECT"}
          </span>
          <span className="monitor-kpi-sub">Messages: 1,247/s</span>
        </div>
        <div className="monitor-kpi">
          <span className="monitor-kpi-label">State</span>
          <span className="monitor-kpi-value" style={{ color: "var(--green)" }}>● OK</span>
          <span className="monitor-kpi-sub">Redis + PostgreSQL</span>
        </div>
      </div>

      <div className="monitor-section">
        <h2 className="monitor-section-title">Modules actifs</h2>
        <div className="monitor-modules">
          {MODULES.map((m) => (
            <div key={m.name} className="monitor-module">
              <div className="monitor-module-header">
                <span className="monitor-module-name">{m.name}</span>
                <span className={`monitor-module-status monitor-status-${m.status}`}>
                  ● {m.status.toUpperCase()}
                </span>
              </div>
              <div className="monitor-module-metrics">
                <span>CPU: {m.cpu}%</span>
                <span>Mem: {m.mem}MB</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="monitor-section">
        <h2 className="monitor-section-title">Event Log</h2>
        <div className="monitor-event-log">
          {EVENTS.map((ev, i) => (
            <div key={i} className={`monitor-event monitor-event-${ev.level}`}>
              <span className="monitor-event-time">{ev.time}</span>
              <span className="monitor-event-subject">{ev.subject}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}