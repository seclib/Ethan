"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

interface WebSocketContextType {
  status: WebSocketStatus;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  lastEvent: any | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<any | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");

    try {
      const token = localStorage.getItem("ethan_token");
      const url = token ? `${WS_URL}?token=${token}` : WS_URL;
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setStatus("connected");
        // Resubscribe to all channels
        subscriptionsRef.current.forEach((channel) => {
          ws.send(JSON.stringify({ type: "subscribe", channel }));
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastEvent(data);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        setStatus("disconnected");
        wsRef.current = null;
        // Auto-reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        setStatus("error");
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setStatus("error");
      // Retry connection after 10 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 10000);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    subscriptionsRef.current.clear();
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  };

  const subscribe = (channel: string) => {
    subscriptionsRef.current.add(channel);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "subscribe", channel }));
    }
  };

  const unsubscribe = (channel: string) => {
    subscriptionsRef.current.delete(channel);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "unsubscribe", channel }));
    }
  };

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        status,
        subscribe,
        unsubscribe,
        lastEvent,
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