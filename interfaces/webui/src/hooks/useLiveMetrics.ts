"use client";

import { useEffect, useRef, useState } from "react";

export function useLiveMetrics<T>(url: string, initial: T[], intervalMs = 2000) {
  const [data, setData] = useState<T[]>(initial);
  const [connected, setConnected] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function connect() {
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const reader = res.body?.getReader();
        if (!reader) throw new Error("No stream");
        const decoder = new TextDecoder();
        let buffer = "";

        while (!cancelled) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const evt = JSON.parse(line) as T;
              setData((prev) => {
                const next = [...prev, evt];
                return next.length > 200 ? next.slice(-200) : next;
              });
              if (!connected) setConnected(true);
            } catch {
              // ignore parse errors
            }
          }
        }
      } catch {
        // retry after delay
        timerRef.current = window.setTimeout(() => connect(), 3000);
      }
    }

    connect();

    // fallback poll if no SSE
    timerRef.current = window.setInterval(() => {
      fetch(url)
        .then((r) => r.json())
        .then((json) => {
          if (Array.isArray(json)) setData(json);
        })
        .catch(() => {});
    }, intervalMs);

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [url, intervalMs, connected]);

  return { data, connected };
}