"use client";

import { BadgeV2 } from "@/components/ui/badge-v2";

const MOCK_SKILLS = [
  { name: "docker.build", version: "v2.1", status: "stable", calls: 12 },
  { name: "k8s.deploy", version: "v1.4", status: "stable", calls: 8 },
  { name: "pytest.run", version: "v3.0", status: "beta", calls: 47 },
  { name: "github.pr", version: "v1.2", status: "stable", calls: 23 },
  { name: "slack.notify", version: "v0.9", status: "beta", calls: 5 },
  { name: "notion.read", version: "v2.0", status: "stable", calls: 34 },
];

export default function Skills() {
  return (
    <div className="page-in">
      <div className="skill-grid">
        {MOCK_SKILLS.map((s) => (
          <div key={s.name} className="skill-card">
            <div className="skill-header">
              <span className="skill-name">{s.name}</span>
              <BadgeV2 variant={s.status === "stable" ? "green" : "gold"}>{s.version}</BadgeV2>
            </div>
            <div className="skill-meta">
              <span>{s.calls} appels</span>
              {s.status === "beta" && <BadgeV2 variant="purple">Beta</BadgeV2>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}