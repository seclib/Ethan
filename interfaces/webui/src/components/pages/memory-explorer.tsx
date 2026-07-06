"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";

const FACTS = [
  { id: "fct_001", subject: "fatsio", predicate: "utilise", object: "Python 3.11 pour ML", category: "preference", confidence: 0.92, status: "active" },
  { id: "fct_002", subject: "fatsio", predicate: "travaille sur", object: "Déploiement API v2.1", category: "project", confidence: 0.85, status: "active" },
  { id: "fct_003", subject: "fatsio", predicate: "vise", object: "Marathon sub-3h", category: "goal", confidence: 0.78, status: "active" },
  { id: "fct_004", subject: "ethan", predicate: "a comme backend", object: "Anthropic Claude", category: "system", confidence: 1.0, status: "active" },
  { id: "fct_005", subject: "fatsio", predicate: "préfère", object: "Thème sombre", category: "preference", confidence: 0.95, status: "active" },
];

const CATEGORY_COLORS: Record<string, string> = {
  preference: "var(--green)",
  project: "var(--accent)",
  goal: "var(--gold)",
  system: "var(--purple)",
  identity: "var(--blue)",
};

export function MemoryExplorerPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<string | null>(null);
  const { openInspector } = useStore();

  const filtered = FACTS.filter((f) => {
    if (filter && f.category !== filter) return false;
    if (!query) return true;
    const q = query.toLowerCase();
    return f.subject.includes(q) || f.predicate.includes(q) || f.object.includes(q);
  });

  return (
    <div className="page-memory">
      <h1 className="page-title">Memory Explorer</h1>

      <div className="memory-toolbar">
        <input
          className="memory-search"
          placeholder="Rechercher des faits..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="memory-filters">
          {["preference", "project", "goal", "system", "identity"].map((cat) => (
            <button
              key={cat}
              className={`filter-chip ${filter === cat ? "active" : ""}`}
              style={{ borderColor: CATEGORY_COLORS[cat] || "var(--dim)" }}
              onClick={() => setFilter(filter === cat ? null : cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="memory-grid">
        {filtered.map((fact) => (
          <div
            key={fact.id}
            className="memory-card"
            onClick={() => openInspector("fact", fact.id, fact)}
          >
            <div className="memory-card-header" style={{ borderLeft: `3px solid ${CATEGORY_COLORS[fact.category] || "var(--dim)"}` }}>
              <span className="memory-card-category">{fact.category}</span>
              <span className="memory-card-confidence">{(fact.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="memory-card-body">
              <span className="memory-card-subject">{fact.subject}</span>
              <span className="memory-card-predicate">{fact.predicate}</span>
              <span className="memory-card-object">{fact.object}</span>
            </div>
            <div className="memory-card-footer">
              <span className="memory-card-id">{fact.id}</span>
              <span className={`memory-card-status memory-status-${fact.status}`}>{fact.status}</span>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="memory-empty">Aucun fait trouvé</div>
      )}
    </div>
  );
}