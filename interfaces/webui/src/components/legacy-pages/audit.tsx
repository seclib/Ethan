"use client";

import { useEffect, useState } from "react";
import { api, type AuditEntry } from "@/lib/api";
import { formatTime, statusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { FileText, Search } from "lucide-react";

export function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const load = async (q?: string) => {
    setLoading(true);
    try {
      if (q) {
        setEntries(await api.searchAudit(q));
      } else {
        setEntries(await api.getAudit(100));
      }
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(() => load(query), 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = () => {
    load(query || undefined);
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-text">Audit</h1>
        <p className="text-text-dim text-sm mt-1">{entries.length} entrées</p>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Rechercher dans l'audit..."
          className="flex-1 rounded-lg border border-border bg-surface-2 px-4 py-2 text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
        />
        <button
          onClick={handleSearch}
          className="rounded-lg bg-ethan-600 px-4 py-2 text-white hover:bg-ethan-500 transition-colors"
        >
          <Search size={18} />
        </button>
      </div>

      {loading && entries.length === 0 && (
        <div className="animate-pulse text-text-dim text-center py-8">Chargement...</div>
      )}

      <div className="space-y-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="rounded-lg border border-border bg-surface-2 p-3"
          >
            <div className="flex items-center gap-2 mb-1">
              <FileText size={14} className="text-ethan-400 shrink-0" />
              <Badge variant={statusColor(entry.decision)}>
                {entry.decision}
              </Badge>
              <span className="text-sm text-text-dim">{entry.category}</span>
              <span className="text-xs text-text-dim ml-auto">
                {formatTime(entry.timestamp)}
              </span>
            </div>
            <p className="text-sm text-text">
              <span className="text-text-dim">{entry.actor}</span> → {entry.action}
            </p>
          </div>
        ))}
        {!loading && entries.length === 0 && (
          <p className="text-text-dim text-center py-8">Aucune entrée</p>
        )}
      </div>
    </div>
  );
}