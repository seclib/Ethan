"use client";

import { useEffect, useRef, useState } from "react";

export function useMetricHistory<T>(
  endpoint: string,
  maxPoints: number = 30,
  pollInterval?: number
): { data: T[]; timestamps: number[] } {
  const [data, setData] = useState<T[]>([]);
  const [timestamps, setTimestamps] = useState<number[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let mounted = true;
    let pollTimer: NodeJS.Timeout;

    const connectSSE = () => {
      if (!mounted) return;
      
      try {
        const eventSource = new EventSource(endpoint);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          if (!mounted) return;
          try {
            const parsed = JSON.parse(event.data) as { timestamp: number; value: T };
            setData((prev) => [...prev.slice(-maxPoints + 1), parsed.value]);
            setTimestamps((prev) => [...prev.slice(-maxPoints + 1), parsed.timestamp]);
          } catch (e) {
            console.error("Failed to parse metric data:", e);
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          if (pollInterval) {
            pollTimer = setInterval(fetchPoll, pollInterval);
          }
        };
      } catch (e) {
        console.error("Failed to connect SSE:", e);
      }
    };

    const fetchPoll = async () => {
      try {
        const restEndpoint = endpoint.replace("/stream", "");
        const res = await fetch(restEndpoint);
        if (!res.ok) return;
        const json = await res.json();
        if (mounted && json.timestamp && json.value !== undefined) {
          setData((prev) => [...prev.slice(-maxPoints + 1), json.value as T]);
          setTimestamps((prev) => [...prev.slice(-maxPoints + 1), json.timestamp]);
        }
      } catch (e) {
        console.error("Polling failed:", e);
      }
    };

    connectSSE();

    return () => {
      mounted = false;
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, [endpoint, maxPoints, pollInterval]);

  return { data, timestamps };
}