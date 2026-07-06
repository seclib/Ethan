"use client";

import { useEffect, useCallback } from "react";
import { useStore } from "@/lib/store";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";

export function KeyboardListener() {
  const setPage = useStore((s) => s.setPage);
  const toggleSidebar = useStore((s) => s.toggleSidebar);

  const handleNavigate = useCallback(
    (page: Parameters<typeof setPage>[0]) => {
      setPage(page);
    },
    [setPage]
  );

  useKeyboardShortcuts(handleNavigate);

  useEffect(() => {
    const handler = () => toggleSidebar();
    window.addEventListener("ethan:toggle-sidebar", handler);
    return () => window.removeEventListener("ethan:toggle-sidebar", handler);
  }, [toggleSidebar]);

  return null;
}