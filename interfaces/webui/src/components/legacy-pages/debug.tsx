"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatTime } from "@/lib/utils";
import { Bug, RefreshCw } from "lucide-react";

export function DebugPage() {
  const [logs, setLogs] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { logs } = await api.getLogs();
      setLogs(logs);
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">Debug</h1>
          <p className="text-text-dim text-sm mt-1">Logs système bruts</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-dim hover:text-text transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Rafraîchir
        </button>
      </div>

      <div className="space-y-1 font-mono text-xs">
        {logs.map((log, i) => (
          <pre
            key={i}
            className="rounded px-2 py-1 hover:bg-surface-2 transition-colors overflow-x-auto"
          >
            <span className="text-text-dim">
              {log.timestamp ? formatTime(log.timestamp as string) : "??"}
            </span>{" "}
            <span className="text-ethan-400">[{String(log.level || "INFO")}]</span>{" "}
            <span className="text-text">{String(log.message || log.msg || "") as string}</span>
          </pre>
        ))}
        {!loading && logs.length === 0 && (
          <p className="text-text-dim text-center py-8">Aucun log</p>
        )}
      </div>
    </div>
  );
}