"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { FluxEvent } from "@/types";

interface EventStreamProps {
  events: FluxEvent[];
  maxHeight?: number;
  showFilters?: boolean;
  onPause?: () => void;
  onResume?: () => void;
  onExport?: () => void;
  className?: string;
}

export function EventStream({
  events,
  maxHeight = 400,
  showFilters = true,
  onPause,
  onResume,
  onExport,
  className,
}: EventStreamProps) {
  const [filter, setFilter] = React.useState<string>("all");
  const [isPaused, setIsPaused] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");

  const filteredEvents = events.filter((event) => {
    const matchesFilter = filter === "all" || event.type === filter;
    const matchesSearch = !searchQuery || 
      event.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.source.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const eventTypes = Array.from(new Set(events.map((e) => e.type)));

  const getSeverityColor = (type: string): "success" | "warning" | "error" | "info" | "dim" => {
    if (type.includes("error") || type.includes("failed")) return "error";
    if (type.includes("warning") || type.includes("pending")) return "warning";
    if (type.includes("success") || type.includes("completed")) return "success";
    return "info";
  };

  return (
    <Card className={cn("p-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Event Stream</h3>
          <p className="text-sm text-muted-foreground">
            {filteredEvents.length} events {isPaused && "(paused)"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const nextPaused = !isPaused;
              setIsPaused(nextPaused);
              if (nextPaused && onResume) onResume();
              if (!nextPaused && onPause) onPause();
            }}
            className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent/10 transition-colors"
          >
            {isPaused ? "▶ Resume" : "⏸ Pause"}
          </button>
          {onExport && (
            <button
              onClick={onExport}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent/10 transition-colors"
            >
              📥 Export
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex items-center gap-2 mb-4">
          <input
            type="text"
            placeholder="Search events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm"
          />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded-md border bg-background px-3 py-1.5 text-sm"
          >
            <option value="all">All Types</option>
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Event List */}
      <div
        className="space-y-2 overflow-y-auto"
        style={{ maxHeight: `${maxHeight}px` }}
      >
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-muted-foreground">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-60"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-accent/80"></span>
            </span>
            <p className="text-xs">No events to display</p>
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div
              key={event.id}
              className="flex items-start gap-3 p-3 rounded-lg border hover:bg-accent/5 transition-colors"
            >
              {/* Severity indicator */}
              <div className="h-2 w-2 rounded-full mt-1.5 flex-shrink-0" style={{
                backgroundColor: event.type.includes("error") ? "#ef4444" :
                               event.type.includes("warning") ? "#f59e0b" :
                               event.type.includes("success") ? "#10b981" : "#3b82f6"
              }} />

              {/* Event content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-xs text-muted-foreground">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                  <Badge variant={getSeverityColor(event.type)} className="text-xs">
                    {event.type}
                  </Badge>
                </div>
                <p className="text-sm">
                  <span className="font-medium">from {event.source}</span>
                </p>
                {event.payload && Object.keys(event.payload).length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                      View payload
                    </summary>
                    <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                      {JSON.stringify(event.payload, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}