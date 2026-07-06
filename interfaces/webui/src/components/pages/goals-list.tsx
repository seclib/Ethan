"use client";

const GOALS = [
  { id: "G-001", title: "Déployer la v2.1 en production", status: "active", priority: "high", steps: 5, done: 3, budget: "1.2k" },
  { id: "G-002", title: "Analyser les concurrents", status: "pending", priority: "medium", steps: 8, done: 0, budget: "3.0k" },
  { id: "G-003", title: "Mettre à jour la documentation API", status: "active", priority: "low", steps: 3, done: 1, budget: "0.5k" },
  { id: "G-004", title: "Optimiser les coûts LLM", status: "active", priority: "high", steps: 4, done: 2, budget: "0.0k" },
  { id: "G-005", title: "Migration PostgreSQL v16", status: "failed", priority: "high", steps: 6, done: 2, budget: "2.1k" },
];

const STATUS_COLORS: Record<string, string> = {
  active: "var(--green)",
  pending: "var(--gold)",
  failed: "var(--red)",
  archived: "var(--dim)",
};

const PRIORITY_LABELS: Record<string, string> = {
  high: "Haute",
  medium: "Moyenne",
  low: "Basse",
};

export function GoalsPage() {
  return (
    <div className="page-goals">
      <div className="goals-header">
        <h1 className="page-title">Goals & Missions</h1>
        <div className="goals-actions">
          <button className="btn btn-primary">Nouveau Goal</button>
          <button className="btn btn-secondary">Nouvelle Mission</button>
        </div>
      </div>

      <div className="goals-filters">
        <span className="filter-chip active">Tous</span>
        <span className="filter-chip">Actifs</span>
        <span className="filter-chip">En attente</span>
        <span className="filter-chip">Échoués</span>
        <span className="filter-chip">Archivés</span>
      </div>

      <div className="goals-list">
        {GOALS.map((g) => (
          <div key={g.id} className={`goal-card goal-${g.status}`}>
            <div className="goal-header">
              <span className="goal-id" style={{ color: STATUS_COLORS[g.status] }}>{g.id}</span>
              <span className={`goal-priority goal-priority-${g.priority}`}>{PRIORITY_LABELS[g.priority]}</span>
              <span className={`goal-status goal-status-${g.status}`}>{g.status}</span>
            </div>
            <div className="goal-title">{g.title}</div>
            <div className="goal-meta">
              <span>Progression : {g.done}/{g.steps} étapes</span>
              <span>Budget : {g.budget} tokens</span>
            </div>
            <div className="goal-bar">
              <div className="goal-bar-fill" style={{ width: `${(g.done / g.steps) * 100}%` }} />
            </div>
            <div className="goal-actions">
              <button className="btn btn-ghost">Voir</button>
              <button className="btn btn-ghost">Pause</button>
              <button className="btn btn-ghost btn-danger">Kill</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}