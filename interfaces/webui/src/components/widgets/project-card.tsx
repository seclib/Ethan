"use client";

interface ProjectCardProps {
  name: string;
  status: "active" | "pending" | "completed" | "failed";
  progress: number;
  tasks: { done: number; total: number };
  description?: string;
  accent?: "blue" | "green" | "gold" | "red" | "purple";
}

const STATUS_MAP = {
  active: { label: "Active", color: "var(--green)" },
  pending: { label: "En attente", color: "var(--fg-3)" },
  completed: { label: "Terminé", color: "var(--accent)" },
  failed: { label: "Échec", color: "var(--red)" },
};

export function ProjectCard({ name, status, progress, tasks, description, accent = "blue" }: ProjectCardProps) {
  const st = STATUS_MAP[status];
  return (
    <div className="project-card" data-accent={accent}>
      <div className="project-header">
        <span className="project-name">{name}</span>
        <span className="project-status" style={{ color: st.color }}>{st.label}</span>
      </div>
      {description && <div className="project-desc">{description}</div>}
      <div className="project-progress">
        <div className="project-progress-bar">
          <div className="project-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <span className="project-progress-label">{progress}%</span>
      </div>
      <div className="project-tasks">
        <span className="project-tasks-done">{tasks.done}</span>
        <span className="project-tasks-sep">/</span>
        <span className="project-tasks-total">{tasks.total}</span>
        <span className="project-tasks-lbl">tâches</span>
      </div>
    </div>
  );
}