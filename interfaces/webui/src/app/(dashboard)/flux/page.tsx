"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useFlux } from "@/hooks/use-flux";
import type { FluxEvent } from "@/types";

export default function FluxPage() {
  const { events, isLoading, error, isConnected } = useFlux();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Event Flux</h1>
          <p className="text-muted-foreground mt-2">Loading events...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Event Flux</h1>
          <p className="text-destructive mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Event Flux</h1>
        <p className="text-muted-foreground mt-2">
          Real-time event stream from the kernel
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-6">
          <h3 className="font-semibold">Events Today</h3>
          <p className="text-2xl font-bold mt-2">{events.length}</p>
          <p className="text-sm text-muted-foreground">In this session</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Status</h3>
          <p className="text-2xl font-bold mt-2">
            {isConnected ? "● Connected" : "○ Disconnected"}
          </p>
          <p className="text-sm text-muted-foreground">WebSocket status</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Last Event</h3>
          <p className="text-2xl font-bold mt-2">
            {events.length > 0 ? new Date(events[0].timestamp).toLocaleTimeString() : "—"}
          </p>
          <p className="text-sm text-muted-foreground">Most recent</p>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Live Event Stream</h3>
          {events.length === 0 ? (
            <p className="text-sm text-muted-foreground">Waiting for events...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {events.slice(0, 50).map((event: FluxEvent) => (
                <div
                  key={event.id}
                  className="flex items-start justify-between p-2 rounded border text-sm"
                >
                  <div className="flex-1">
                    <span className="font-mono text-xs text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="ml-2 font-medium">{event.type}</span>
                    <span className="ml-2 text-muted-foreground">from {event.source}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}