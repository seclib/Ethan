"use client";

import { useEffect, useRef, useState } from "react";

export function useThrottle<T>(value: T, delay = 1000): T {
  const [throttled, setThrottled] = useState(value);
  const lastTime = useRef<number>(Date.now());

  useEffect(() => {
    const now = Date.now();
    if (now - lastTime.current >= delay) {
      setThrottled(value);
      lastTime.current = now;
    } else {
      const timer = setTimeout(() => {
        setThrottled(value);
        lastTime.current = Date.now();
      }, delay - (now - lastTime.current));
      return () => clearTimeout(timer);
    }
  }, [value, delay]);

  return throttled;
}
