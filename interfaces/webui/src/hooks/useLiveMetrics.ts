"use client";

import { useEffect, useRef, useState } from "react";

interface MetricData {
  timestamp: number;
  value: number | string | object;
}

export function useLiveMetric<T>(
  endpoint: string,
  interval: number = 1000
): { data: T | null; error: Error | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);

  useEffect(() => {
    let mounted = true;
    let retryTimeout: NodeJS.Timeout;

    const connect = () => {
      if (!mounted) return;

      try {
        const eventSource = new EventSource(endpoint);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          retryCountRef.current = 0;
        };

        eventSource.onmessage = (event) => {
          if (!mounted) return;
          try {
            const parsed = JSON.parse(event.data) as T;
            setData(parsed);
            setError(null);
            setLoading(false);
          } catch (e) {
            console.error("Failed to parse metric data:", e);
          }
        };

        eventSource.onerror = () => {
          if (!mounted) return;
          setError(new Error("Connection lost"));
          eventSource.close();
          
          // Retry with exponential backoff
          retryCountRef.current++;
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 30000);
          retryTimeout = setTimeout(connect, delay);
        };
      } catch (e) {
        if (!mounted) return;
        setError(new Error("Failed to connect"));
        setLoading(false);
      }
    };

    connect();

    return () => {
      mounted = false;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (retryTimeout) {
        clearTimeout(retryTimeout);
      }
    };
  }, [endpoint]);

  return { data, error, loading };
}

export function usePollingMetric<T>(
  fetchFn: () => Promise<T>,
  interval: number = 2000
): { data: T | null; error: Error | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;

    const fetchData = async () => {
      try {
        const result = await fetchFn();
        if (mounted) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      } catch (e) {
        if (mounted) {
          setError(e as Error);
          setLoading(false);
        }
      }
    };

    fetchData();
    timeoutId = setInterval(fetchData, interval);

    return () => {
      mounted = false;
      if (timeoutId) {
        clearInterval(timeoutId);
      }
    };
  }, [fetchFn, interval]);

  return { data, error, loading };
}