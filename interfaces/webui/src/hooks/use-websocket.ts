"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnectInterval = 1000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${url}`);
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (e) {
          console.error("[WebSocket] Failed to parse message:", e);
        }
      };

      ws.onerror = (event: Event) => {
        console.error("[WebSocket] Error:", event);
        setError("WebSocket error occurred");
        onError?.(event);
      };

      ws.onclose = () => {
        console.log(`[WebSocket] Disconnected from ${url}`);
        setIsConnected(false);
        onClose?.();

        // Auto-reconnect
        if (reconnectCountRef.current < maxReconnectAttempts) {
          reconnectCountRef.current++;
          const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current - 1); // Exponential backoff
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          setError("Max reconnection attempts reached");
        }
      };
    } catch (e) {
      console.error("[WebSocket] Failed to connect:", e);
      setError("Failed to establish WebSocket connection");
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.error("[WebSocket] Cannot send message, connection not open");
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    send,
    disconnect,
    reconnect: connect,
  };
}