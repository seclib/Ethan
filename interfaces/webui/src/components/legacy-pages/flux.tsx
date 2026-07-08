"use client";

import { useState, useMemo } from "react";
import { SourceBars } from "@/components/widgets/analytics-widgets";
import { VirtualList } from "@/components/flux/virtual-list";

const MOCK_EVENTS = Array.from({ length: 200 }).map((_, i) => {
  const types = ["user.input", "planner.plan", "executor.task", "memory.store", "agent.result"] as const;
  const type = types[i % types.length];
  const msgs: Record<string, string> = {
    "user.input": "Déploie l'agent NLP",
    "planner.plan": "3 tasks created",
    "executor.task": "docker.build started",
    "memory.store": "entry abc123 stored",
    "agent.result": "Déploiement terminé",
  };
  return {
    time: new Date(Date.now() - i * 1000).toISOString().slice(11, 19),
    type,
    msg: msgs[type],
  };
});

export function FluxPage() {
  const [filter, setFilter] = useState<string | null>(null);
  const events = useMemo(() => {
    const base = filter ? MOCK_EVENTS.filter((e) => e.type === filter) : MOCK_EVENTS;
    return base;
  }, [filter]);

  return (
    <div className="page-in">
      <div className="flux-filters">
        {["all", "user.input", "planner.plan", "executor.task", "memory.store", "agent.result"].map((f) => (
          <button
            key={f}
            className="flux-filter-btn"
            data-active={(!filter && f === "all") || filter === f}
            onClick={() => setFilter(f === "all" ? null : f)}
          >
            {f === "all" ? "Tous" : f}
          </button>
        ))}
      </div>

      <VirtualList
        items={events}
        itemHeight={36}
        containerHeight={Math.min(60, Math.max(36, events.length)) * 36}
        renderItem={(ev) => (
          <div className="flux-row">
            <span className="flux-time">{ev.time}</span>
            <span className="flux-type">{ev.type}</span>
            <span className="flux-msg">{ev.msg}</span>
          </div>
        )}
      />

      <div className="flux-stats">
        <SourceBars
          title="Répartition"
          items={[
            { label: "Interface", value: 42 },
            { label: "Agent", value: 28 },
            { label: "Mémoire", value: 18 },
            { label: "Système", value: 12 },
          ]}
        />
      </div>
    </div>
  );
}
