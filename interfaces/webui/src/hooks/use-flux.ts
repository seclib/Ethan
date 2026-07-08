"use client";

import { useCallback, useEffect } from "react";
import { useFluxStore } from "@/stores/flux.store";
import { fluxService } from "@/services/flux.service";
import { useWebSocket } from "./use-websocket";

export function useFlux() {
  const { events, isConnected, isLoading, error, addEvent, setEvents, setConnected, setLoading, setError } = useFluxStore();

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fluxService.getEvents();
      setEvents(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch events");
    } finally {
      setLoading(false);
    }
  }, [setEvents, setLoading, setError]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // WebSocket connection for real-time events
  const handleWebSocketMessage = useCallback((data: any) => {
    if (data.type && data.payload) {
      const newEvent: any = {
        id: data.payload.id || `event-${Date.now()}`,
        type: data.type,
        source: data.source || "unknown",
        payload: data.payload,
        timestamp: data.timestamp || new Date().toISOString(),
      };
      addEvent(newEvent);
    }
  }, [addEvent]);

  const { isConnected: wsConnected, error: wsError } = useWebSocket({
    url: typeof window !== "undefined" ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1/events/ws` : "",
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      console.log("[useFlux] WebSocket connected");
      setConnected(true);
    },
    onClose: () => {
      console.log("[useFlux] WebSocket disconnected");
      setConnected(false);
    },
    onError: (err) => console.error("[useFlux] WebSocket error:", err),
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
  });

  return { 
    events, 
    isLoading, 
    error: error || wsError, 
    isConnected: wsConnected || isConnected, 
    refetch: fetchEvents 
  };
}