"use client";

import { useEffect, useState } from "react";

export const DEFAULT_LAYOUT = [
  "core",
  "cpu",
  "ram",
  "gpu",
  "providers",
  "tokens",
  "agents",
  "planner",
  "knowledge",
  "memory",
  "mcp",
  "plugins",
  "events",
  "network",
];

const STORAGE_KEY = "dashboard-layout";

export function useDashboardLayout() {
  const [layout, setLayout] = useState<string[]>(DEFAULT_LAYOUT);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as string[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setLayout(parsed);
        }
      }
    } catch (e) {
      console.warn("Failed to load dashboard layout:", e);
    }
    setLoaded(true);
  }, []);

  const updateLayout = (newLayout: string[]) => {
    setLayout(newLayout);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newLayout));
    } catch (e) {
      console.warn("Failed to save dashboard layout:", e);
    }
  };

  const resetLayout = () => {
    updateLayout(DEFAULT_LAYOUT);
  };

  return { layout, updateLayout, resetLayout, loaded };
}