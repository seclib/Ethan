"use client";

import { useEffect, useState } from "react";
import { api, type Event } from "@/lib/api";
import { formatTime } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Radio, RefreshCw } from "lucide-react";

export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const { events } = await api.getEvents(100);
      setEvents(events);
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const filtered = filter
    ? events.filter((e) =>
        [e.type, e.source, e.id].some((v) =>
          v.toLowerCase().includes(filter.toLowerCase())
        )
      )
    : events;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text">Event Stream</h1>
          <p className="text-text-dim text-sm mt-1">{events.length} événements</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-dim hover:text-text transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Rafraîchir
        </button>
      </div>

      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filtrer par type, source ou ID..."
        aria-label="Filtrer les événements"
        className="w-full rounded-lg border border-border bg-surface-2 px-4 py-2 text-text placeholder-text-dim focus:outline-none focus:border-ethan-500"
      />

      <div className="space-y-2">
        {loading && events.length === 0 && (
          <>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </>
        )}
        {filtered.map((evt) => (
          <details
            key={evt.id}
            className="rounded-lg border border-border bg-surface-2 overflow-hidden"
          >
            <summary className="flex items-center gap-3 px-4 py-2 cursor-pointer hover:bg-surface-3/50 transition-colors">
              <Radio size={14} className="text-ethan-400 shrink-0" />
              <Badge variant="info">{evt.type}</Badge>
              <span className="text-sm text-text-dim">{evt.source}</span>
              <span className="text-xs text-text-dim ml-auto">
                {formatTime(evt.timestamp)}
              </span>
            </summary>
            <div className="px-4 pb-3">
              <pre className="text-xs font-mono text-text bg-surface p-2 rounded overflow-x-auto">
                {JSON.stringify(evt.data, null, 2)}
              </pre>
            </div>
          </details>
        ))}
        {!loading && filtered.length === 0 && (
          <p className="text-text-dim text-center py-8">Aucun événement</p>
        )}
      </div>
    </div>
  );
}