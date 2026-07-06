"use client";

import { useEffect, useState } from "react";
import { api, type ApprovalRequest } from "@/lib/api";
import { formatTime } from "@/lib/utils";
import { CheckSquare, Check, X, Clock } from "lucide-react";

export function ApprovalPage() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setRequests(await api.getPendingApprovals());
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const resolve = async (id: string, approved: boolean) => {
    setResolving(id);
    try {
      await api.resolveApproval(id, approved, "Résolu depuis le dashboard");
      setRequests((prev) => prev.filter((r) => r.request_id !== id));
    } catch {}
    setResolving(null);
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-text">Approbations</h1>
        <p className="text-text-dim text-sm mt-1">
          {requests.length} demande{requests.length > 1 ? "s" : ""} en attente
        </p>
      </div>

      {loading && requests.length === 0 && (
        <div className="animate-pulse text-text-dim text-center py-8">Chargement...</div>
      )}

      <div className="space-y-3">
        {requests.map((req) => (
          <div
            key={req.request_id}
            className="rounded-lg border border-border bg-surface-2 p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="font-medium text-text">{req.title}</h3>
                <p className="text-sm text-text-dim mt-1">{req.description}</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-text-dim shrink-0">
                <Clock size={12} />
                {req.timeout_seconds}s
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-text-dim mb-3">
              <span className="rounded bg-surface-3 px-2 py-0.5">{req.category}</span>
              <span>{req.source}</span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => resolve(req.request_id, true)}
                disabled={resolving === req.request_id}
                className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-500 disabled:opacity-50 transition-colors"
              >
                <Check size={14} />
                Approuver
              </button>
              <button
                onClick={() => resolve(req.request_id, false)}
                disabled={resolving === req.request_id}
                className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-500 disabled:opacity-50 transition-colors"
              >
                <X size={14} />
                Rejeter
              </button>
            </div>
          </div>
        ))}
        {!loading && requests.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-text-dim">
            <CheckSquare size={40} className="mb-3 opacity-50" />
            <p>Aucune approbation en attente</p>
          </div>
        )}
      </div>
    </div>
  );
}