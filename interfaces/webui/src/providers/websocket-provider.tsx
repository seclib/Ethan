"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode, useCallback } from "react";
import { logger } from "@/lib/logger";
import { resolveRealtimeWebSocketUrl } from "@/lib/websocket-url";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error" | "reconnecting";

interface WebSocketContextType {
  status: WebSocketStatus;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  lastEvent: any | null;
  replayedEvents: any[];
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const DEFAULT_REALTIME_WEB_SOCKET_URL = "ws://localhost:8000/v1/ws";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

export function buildWebSocketUrl(
  wsUrl: string | undefined = process.env.NEXT_PUBLIC_WS_URL,
  isProduction: boolean = process.env.NODE_ENV === "production",
  isSecurePage: boolean = typeof window !== "undefined" && window.location.protocol === "https:",
): string {
  const mergedUrl = wsUrl || process.env.NEXT_PUBLIC_WS_URL;
  return resolveRealtimeWebSocketUrl(mergedUrl, isProduction, isSecurePage);
}

const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<any | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptRef = useRef(0);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());
  const eventBufferRef = useRef<any[]>([]);
  const [replayedEvents, setReplayedEvents] = useState<any[]>([]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus(reconnectAttemptRef.current > 0 ? "reconnecting" : "connecting");

    try {
      const isProduction = process.env.NODE_ENV === "production";
      const isSecurePage =
        typeof window !== "undefined" && window.location.protocol === "https:";
      const url = buildWebSocketUrl(WS_URL, isProduction, isSecurePage);

      logger.debug(`WebSocket connecting to ${url}`);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        logger.debug("WebSocket connected");
        setStatus("connected");
        reconnectAttemptRef.current = 0;

        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }));
          }
        }, 30000);

        // Le catalogue de topics métier est volontairement vide pour ce lot.
        // Les souscriptions contrôlées par le client sont refusées par l'API ;
        // on ne doit pas les émettre automatiquement au handshake.

        setReplayedEvents([...eventBufferRef.current]);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") return;
          setLastEvent(data);
          eventBufferRef.current.push(data);
          if (eventBufferRef.current.length > 100) {
            eventBufferRef.current.shift();
          }
        } catch {
          // Ignore malformed messages
        }
      };

      const scheduleReconnect = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const delay = Math.min(
          INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptRef.current),
          MAX_RECONNECT_DELAY
        );

        reconnectAttemptRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onclose = () => {
        logger.debug("WebSocket closed");
        setStatus("disconnected");
        wsRef.current = null;
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setStatus("error");
      };

      wsRef.current = ws;
    } catch (e) {
      setStatus("error");
      const delay = Math.min(
        INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptRef.current),
        MAX_RECONNECT_DELAY
      );
      reconnectAttemptRef.current += 1;

      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    subscriptionsRef.current.clear();
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, []);

  const subscribe = useCallback((channel: string) => {
    // Conserver la compatibilité de l'API React sans émettre de sujet
    // vers FastAPI : le contrôle des abonnements appartient au serveur.
    subscriptionsRef.current.add(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    subscriptionsRef.current.delete(channel);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return (
    <WebSocketContext.Provider
      value={{
        status,
        subscribe,
        unsubscribe,
        lastEvent,
        replayedEvents,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}