"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useFlux } from "@/hooks/use-flux";
import type { FluxEvent } from "@/types";

export default function FluxPage() {
  const { events, isLoading, error, isConnected } = useFlux();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Event Flux</h1>
          <p className="text-foreground-secondary mt-2">Loading events...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="text" lines={3} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Event Flux</h1>
          <p className="text-error-600 mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Event Flux</h1>
        <p className="text-foreground-secondary mt-2">
          Real-time event stream from the kernel
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Events Today</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{events.length}</p>
            <p className="text-sm text-foreground-tertiary mt-1">In this session</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">
              {isConnected ? "● Connected" : "○ Disconnected"}
            </p>
            <p className="text-sm text-foreground-tertiary mt-1">WebSocket status</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Last Event</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">
              {events.length > 0 ? new Date(events[0].timestamp).toLocaleTimeString() : "—"}
            </p>
            <p className="text-sm text-foreground-tertiary mt-1">Most recent</p>
          </CardContent>
        </Card>
      </div>

      <Card variant="outlined">
        <CardHeader>
          <CardTitle>Live Event Stream</CardTitle>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <p className="text-sm text-foreground-tertiary">Waiting for events...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {events.slice(0, 50).map((event: FluxEvent) => (
                <div
                  key={event.id}
                  className="flex items-start justify-between p-2 rounded-lg border border-line-1 hover:border-line-2 transition-colors duration-100 text-sm"
                >
                  <div className="flex-1">
                    <span className="font-mono text-xs text-foreground-tertiary">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="ml-2 font-medium text-foreground">{event.type}</span>
                    <span className="ml-2 text-foreground-tertiary">from {event.source}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}