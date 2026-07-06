"use client";

import { useState } from "react";
import { SubpagesPills } from "@/components/navigation/subpages-pills";
import { BadgeV2 } from "@/components/ui/badge-v2";

const TABS = [
  { id: "general", label: "Général", icon: "⚙" },
  { id: "modules", label: "Modules", icon: "◆" },
  { id: "llm", label: "LLM", icon: "🧠" },
  { id: "api", label: "API", icon: "🔑" },
];

const MODULES = [
  { name: "Planner", status: "active" as const },
  { name: "Executor", status: "active" as const },
  { name: "Memory", status: "active" as const },
  { name: "Learning", status: "paused" as const },
  { name: "Autonomy", status: "paused" as const },
];

export default function Config() {
  const [tab, setTab] = useState("general");

  return (
    <div className="page-in">
      <SubpagesPills pages={TABS} active={tab} onChange={setTab} />

      {tab === "general" && (
        <div className="config-section">
          <div className="config-row"><span>Nom du système</span><span>ETHAN Cognitive OS</span></div>
          <div className="config-row"><span>Version</span><span>2.1.0</span></div>
          <div className="config-row"><span>Mode</span><span>Production</span></div>
          <div className="config-row"><span>Log level</span><span>Info</span></div>
        </div>
      )}

      {tab === "modules" && (
        <div className="config-modules">
          {MODULES.map((m) => (
            <div key={m.name} className="config-module-row">
              <span>{m.name}</span>
              <BadgeV2 variant={m.status === "active" ? "green" : "gold"}>{m.status}</BadgeV2>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}