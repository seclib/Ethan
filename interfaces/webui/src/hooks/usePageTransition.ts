"use client";

import { useEffect, useRef } from "react";

export function usePageTransition() {
  const ref = useRef<HTMLDivElement>(null);
  const key = useRef(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Force re-trigger animation on mount / route change
    key.current += 1;
    el.classList.remove("page-in");
    // Trigger reflow
    void el.offsetWidth;
    el.classList.add("page-in");

    return () => {
      if (el) el.classList.remove("page-in");
    };
  }, []);

  return ref;
}