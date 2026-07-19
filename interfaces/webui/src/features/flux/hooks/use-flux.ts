"use client";

import { useCallback, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fluxService } from "@/features/flux/services/flux.service";
import { useWebSocket } from "@/core/websocket/use-websocket";
import type { FluxEvent } from "@/types";

export function useFlux() {
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fluxEvents"],
    queryFn: () => fluxService.getEvents(),
  });

  const events = data?.data || [];

  // WebSocket connection for real-time events
  const handleWebSocketMessage = useCallback((data: any) => {
    if (data.type && data.payload) {
      const newEvent: FluxEvent = {
        id: data.payload.id || `event-${Date.now()}`,
        type: data.type,
        source: data.source || "unknown",
        payload: data.payload,
        timestamp: data.timestamp || new Date().toISOString(),
      };
      
      // Push new event into React Query cache (max 500 items)
      queryClient.setQueryData(["fluxEvents"], (oldData: any) => {
        const oldEvents = oldData?.data || [];
        return {
          ...oldData,
          data: [newEvent, ...oldEvents].slice(0, 500)
        };
      });
    }
  }, [queryClient]);

  const { error: wsError } = useWebSocket({
    url: typeof window !== "undefined" ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1/events/ws` : "",
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      console.log("[useFlux] WebSocket connected");
      setWsConnected(true);
    },
    onClose: () => {
      console.log("[useFlux] WebSocket disconnected");
      setWsConnected(false);
    },
    onError: (err) => console.error("[useFlux] WebSocket error:", err),
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
  });

  return { 
    events, 
    isLoading, 
    error: error instanceof Error ? error.message : (wsError || null), 
    isConnected: wsConnected, 
    refetch 
  };
}