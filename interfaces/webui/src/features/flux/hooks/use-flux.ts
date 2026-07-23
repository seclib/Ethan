"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fluxService } from "@/features/flux/services/flux.service";
import { useWebSocket } from "@/core/providers/websocket-provider";
import type { FluxEvent } from "@/types";

export function useFlux() {
  const queryClient = useQueryClient();
  const { status, lastEvent, subscribe, unsubscribe } = useWebSocket();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fluxEvents"],
    queryFn: () => fluxService.getEvents(),
  });

  const events = (data || []) as FluxEvent[];

  useEffect(() => {
    // Subscribe to flux events when hook is active
    subscribe("flux");
    return () => unsubscribe("flux");
  }, [subscribe, unsubscribe]);

  useEffect(() => {
    if (lastEvent && lastEvent.type !== "ping" && lastEvent.type !== "pong") {
      const newEvent: FluxEvent = {
        id: lastEvent.payload?.id || `event-${Date.now()}`,
        type: lastEvent.type,
        source: lastEvent.source || "unknown",
        payload: lastEvent.payload || {},
        timestamp: lastEvent.timestamp || new Date().toISOString(),
      };
      
      // Push new event into React Query cache (max 500 items)
      queryClient.setQueryData(["fluxEvents"], (oldData: any) => {
        const oldEvents = Array.isArray(oldData) ? oldData : [];
        return [newEvent, ...oldEvents].slice(0, 500);
      });
    }
  }, [lastEvent, queryClient]);

  return { 
    events, 
    isLoading, 
    error: error instanceof Error ? error.message : null, 
    isConnected: status === "connected", 
    refetch 
  };
}