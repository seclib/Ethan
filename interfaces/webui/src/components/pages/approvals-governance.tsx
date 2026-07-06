"use client";

import { useStore } from "@/lib/store";
import type { Approval } from "@/lib/store";

const HISTORY: { id: string; decision: "approved" | "rejected"; description: string; date: string }[] = [
  { id: "a-001", decision: "approved", description: "Déployer staging", date: "14:20" },
  { id: "a-002", decision: "rejected", description: "Publier sur Twitter", date: "13:45" },
  { id: "a-003", decision: "approved", description: "Exécuter script shell", date: "12:30" },
];

export function ApprovalsGovernancePage() {
  const { approvals, addApproval, resolveApproval } = useStore();

  return (
    <div className="page-approvals">
      <h1 className="page-title">Approvals & Governance</h1>

      <div className="approvals-section">
        <h2 className="approvals-section-title">En attente ({approvals.length})</h2>
        {approvals.length === 0 && (
          <div className="approvals-empty">Aucune approbation en attente</div>
        )}
        {approvals.map((a) => (
          <div key={a.id} className="approval-card">
            <div className="approval-header">
              <span className="approval-id">{a.id}</span>
              <span className={`approval-risk approval-risk-${a.risk}`}>{a.risk}</span>
            </div>
            <div className="approval-desc">{a.description}</div>
            <div className="approval-meta">
              <span>Projet: {a.projectId}</span>
              <span>Étape: {a.stepId}</span>
              <span>Budget: {a.budget} tokens</span>
            </div>
            <div className="approval-actions">
              <button className="btn btn-primary" onClick={() => resolveApproval(a.id, true)}>Approuver</button>
              <button className="btn btn-danger" onClick={() => resolveApproval(a.id, false)}>Refuser</button>
            </div>
          </div>
        ))}
      </div>

      <div className="approvals-section">
        <h2 className="approvals-section-title">Historique des décisions</h2>
        <div className="approvals-history">
          {HISTORY.map((h) => (
            <div key={h.id} className={`history-item history-${h.decision}`}>
              <span className="history-icon">{h.decision === "approved" ? "✓" : "✗"}</span>
              <span className="history-desc">{h.description}</span>
              <span className="history-date">{h.date}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="approvals-section">
        <h2 className="approvals-section-title">Configuration</h2>
        <div className="governance-config">
          <div className="config-field">
            <label>Niveau d'autonomie par défaut</label>
            <select className="config-select">
              <option value="0">0 — Répondre seulement</option>
              <option value="1">1 — Suggérer</option>
              <option value="2" selected>2 — Exécuter avec approbation</option>
              <option value="3">3 — Exécution sandboxée</option>
              <option value="4">4 — Modification fichiers</option>
              <option value="5">5 — Publier/payer/contacter</option>
            </select>
          </div>
          <div className="config-field">
            <label>Budget max par mission (tokens)</label>
            <input className="config-input" type="number" defaultValue={2000} />
          </div>
          <div className="config-field config-gates">
            <label>Gates obligatoires</label>
            <label className="config-checkbox">
              <input type="checkbox" defaultChecked /> Filesystem
            </label>
            <label className="config-checkbox">
              <input type="checkbox" defaultChecked /> Network
            </label>
            <label className="config-checkbox">
              <input type="checkbox" /> Execution
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}