"use client";

import { useEffect, useState } from "react";
import { api, type Fact } from "@/lib/api";
import { formatDate, statusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, Search } from "lucide-react";

export function FactsPage() {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const load = async (q?: string) => {
    setLoading(true);
    try {
      if (q) {
        setFacts(await api.searchFacts(q));
      } else {
        setFacts(await api.getFacts(100));
      }
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSearch = () => load(query || undefined);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-text">Facts</h1>
        <p className="text-text-dim text-sm mt-1">Base de connaissances atomique</p>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Rechercher un fait..."
          className="flex-1 rounded-lg border border-border bg-surface-2 px-4 py-2 text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
        />
        <button
          onClick={handleSearch}
          className="rounded-lg bg-ethan-600 px-4 py-2 text-white hover:bg-ethan-500 transition-colors"
        >
          <Search size={18} />
        </button>
      </div>

      {loading && facts.length === 0 && (
        <div className="animate-pulse text-text-dim text-center py-8">Chargement...</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {facts.map((fact) => (
          <div
            key={fact.id}
            className="rounded-lg border border-border bg-surface-2 p-3"
          >
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb size={14} className="text-yellow-400 shrink-0" />
              <Badge variant={statusColor(fact.status)}>{fact.status}</Badge>
              <span className="text-xs text-text-dim">{fact.category}</span>
              <span className="text-xs text-text-dim ml-auto">
                {fact.confidence.toFixed(2)}
              </span>
            </div>
            <p className="text-sm text-text">
              <span className="text-ethan-400">{fact.subject}</span>
              <span className="text-text-dim"> {fact.predicate} </span>
              <span className="text-text">{fact.object}</span>
            </p>
            <p className="text-xs text-text-dim mt-1">{formatDate(fact.created_at)}</p>
          </div>
        ))}
        {!loading && facts.length === 0 && (
          <p className="text-text-dim text-center py-8 col-span-2">Aucun fait</p>
        )}
      </div>
    </div>
  );
}