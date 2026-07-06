"use client";

import { useState } from "react";

const SKILLS = [
  { id: "sk_001", name: "docker-build", version: "1.2.0", status: "active", usage: 47, steps: 3, tools: ["docker", "registry"] },
  { id: "sk_002", name: "web-researcher", version: "0.9.1", status: "testing", usage: 12, steps: 5, tools: ["browser"] },
  { id: "sk_003", name: "code-reviewer", version: "2.0.0", status: "active", usage: 89, steps: 4, tools: ["git", "llm"] },
  { id: "sk_004", name: "deploy-k8s", version: "1.0.0", status: "active", usage: 23, steps: 6, tools: ["kubectl", "helm"] },
  { id: "sk_005", name: "data-analyzer", version: "0.5.0", status: "archived", usage: 3, steps: 8, tools: ["python", "pandas"] },
];

const STATUS_COLORS: Record<string, string> = {
  active: "var(--green)",
  testing: "var(--gold)",
  archived: "var(--dim)",
};

export function SkillsLabPage() {
  const [sandboxInput, setSandboxInput] = useState("");
  const [sandboxOutput, setSandboxOutput] = useState("");

  const runSandbox = () => {
    setSandboxOutput(`> Test exécuté sur "${sandboxInput}"\n> Résultat simulé...\n> ✓ OK (0.3s)`);
  };

  return (
    <div className="page-skills">
      <h1 className="page-title">Skills Lab</h1>

      <div className="skills-actions">
        <button className="btn btn-primary">Nouvelle Skill</button>
        <button className="btn btn-secondary">Importer</button>
        <button className="btn btn-secondary">Tester</button>
      </div>

      <div className="skills-filters">
        <span className="filter-chip active">Toutes</span>
        <span className="filter-chip">Actives</span>
        <span className="filter-chip">En test</span>
        <span className="filter-chip">Archivées</span>
        <span className="filter-chip">Presets</span>
      </div>

      <div className="skills-list">
        {SKILLS.map((s) => (
          <div key={s.id} className="skill-card">
            <div className="skill-header">
              <span className="skill-name">{s.name}</span>
              <span className="skill-version">v{s.version}</span>
              <span className="skill-status-badge" style={{ color: STATUS_COLORS[s.status] || "var(--dim)" }}>
                {s.status}
              </span>
            </div>
            <div className="skill-meta">
              <span>Tools: {s.tools.join(", ")}</span>
              <span>Steps: {s.steps}</span>
              <span>Usage: {s.usage}x</span>
            </div>
            <div className="skill-actions">
              <button className="btn btn-ghost">Tester</button>
              <button className="btn btn-ghost">Éditer</button>
              <button className="btn btn-ghost">Désactiver</button>
            </div>
          </div>
        ))}
      </div>

      <div className="skills-sandbox">
        <h2 className="sandbox-title">Sandbox de test</h2>
        <div className="sandbox-input-row">
          <input
            className="sandbox-input"
            placeholder="Paramètres d'entrée..."
            value={sandboxInput}
            onChange={(e) => setSandboxInput(e.target.value)}
          />
          <button className="btn btn-primary" onClick={runSandbox}>Exécuter</button>
        </div>
        {sandboxOutput && (
          <pre className="sandbox-output">{sandboxOutput}</pre>
        )}
      </div>
    </div>
  );
}