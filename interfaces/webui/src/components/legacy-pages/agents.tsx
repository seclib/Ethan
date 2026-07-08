"use client";

import { BadgeV2 } from "@/components/ui/badge-v2";

const MOCK_AGENTS = [
  { name: "Planner", status: "active", uptime: "2h", tasks: 3, caps: "goal.decompose, plan.create" },
  { name: "Executor", status: "active", uptime: "2h", tasks: 0, caps: "task.assign, task.run" },
  { name: "Memory", status: "idle", uptime: "45m", stores: 1284, caps: "store, recall, context" },
  { name: "Learning", status: "active", uptime: "1h", cycles: 47, caps: "pattern.extract, optimize" },
  { name: "Autonomy", status: "paused", uptime: "0m", goals: 0, caps: "goal.initiate, self.direct" },
  { name: "Reflective", status: "active", uptime: "2h", evals: 12, caps: "outcome.evaluate, self.assess" },
];

export function AgentsPage() {
  return (
    <div className="page-in">
      <div className="agent-grid">
        {MOCK_AGENTS.map((a) => (
          <div key={a.name} className="agent-card" data-status={a.status}>
            <div className="agent-card-header">
              <span className="agent-name">{a.name}</span>
              <BadgeV2 variant={a.status === "active" ? "green" : a.status === "idle" ? "maintenance" : "gold"}>
                {a.status}
              </BadgeV2>
            </div>
            <div className="agent-metrics">
              <span>Uptime: {a.uptime}</span>
              {"tasks" in a && <span>Tâches: {a.tasks}</span>}
              {"stores" in a && <span>Entrées: {a.stores}</span>}
              {"cycles" in a && <span>Cycles: {a.cycles}</span>}
              {"goals" in a && <span>Objectifs: {a.goals}</span>}
              {"evals" in a && <span>Évals: {a.evals}</span>}
            </div>
            <div className="agent-caps">{a.caps}</div>
          </div>
        ))}
      </div>
    </div>
  );
}