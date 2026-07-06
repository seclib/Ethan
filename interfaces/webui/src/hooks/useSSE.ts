"use client";

import { useEffect, useRef, useState } from "react";

export function useSSE<T>(url: string, onMessage: (data: T) => void) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setConnected(true);
      setError(null);
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        onMessage(data);
      } catch {}
    };

    es.onerror = () => {
      setConnected(false);
      setError("Connexion perdue");
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [url]);

  return { connected, error };
}