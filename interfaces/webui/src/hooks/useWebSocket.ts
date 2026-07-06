"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type WSMessage = {
  topic: string;
  data: unknown;
};

export function useWebSocket<T = unknown>(url: string, topic: string) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const reconnectDelay = useRef(1000);

  const connect = useCallback(() => {
    if (typeof window === "undefined" || !window.WebSocket) return;
    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("open");
      reconnectDelay.current = 1000;
      ws.send(JSON.stringify({ type: "subscribe", topic }));
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WSMessage;
        if (msg.topic === topic) setData(msg.data as T);
      } catch {
        // ignore malformed
      }
    };

    ws.onclose = () => {
      setStatus("closed");
      reconnectTimer.current = window.setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url, topic]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, status, reconnect: connect };
}