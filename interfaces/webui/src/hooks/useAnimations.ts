"use client";

import { useEffect, useState, useCallback, useRef } from "react";

// ───────── Reduced motion detection ─────────

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return reduced;
}

// ───────── Page transition ─────────

type TransitionStatus = "idle" | "entering" | "exiting";

export function usePageTransition(isActive: boolean): TransitionStatus {
  const [status, setStatus] = useState<TransitionStatus>("idle");
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion) {
      setStatus("idle");
      return;
    }

    if (isActive) {
      setStatus("entering");
      const timer = setTimeout(() => setStatus("idle"), 200);
      return () => clearTimeout(timer);
    } else {
      setStatus("exiting");
      const timer = setTimeout(() => setStatus("idle"), 150);
      return () => clearTimeout(timer);
    }
  }, [isActive, reducedMotion]);

  return status;
}

// ───────── Stagger animation ─────────

export function useStagger<T>(
  items: T[],
  delay: number = 30
): { item: T; style: React.CSSProperties }[] {
  const reducedMotion = useReducedMotion();

  return items.map((item, index) => ({
    item,
    style: reducedMotion
      ? {}
      : {
          animationDelay: `${index * delay}ms`,
        },
  }));
}

// ───────── Value update flash ─────────

export function useValueUpdateFlash(isUpdating: boolean): string {
  const reducedMotion = useReducedMotion();

  if (reducedMotion || !isUpdating) return "";

  return "value-updated";
}

// ───────── Toast animation ─────────

export function useToastAnimation(isVisible: boolean): "enter" | "exit" | "idle" {
  const reducedMotion = useReducedMotion();

  if (reducedMotion || !isVisible) return "idle";

  return "enter";
}

// ───────── Drag animation ─────────

export function useDragAnimation(
  isDragging: boolean,
  isDropTarget: boolean
): {
  isDraggingClass: boolean;
  isDropTargetClass: boolean;
  isDroppedClass: boolean;
} {
  const reducedMotion = useReducedMotion();

  return {
    isDraggingClass: !reducedMotion && isDragging,
    isDropTargetClass: !reducedMotion && isDropTarget,
    isDroppedClass: !reducedMotion && !isDragging && !isDropTarget,
  };
}

// ───────── Intersection Observer for scroll animations ─────────

export function useScrollReveal(
  ref: React.RefObject<HTMLElement | null>,
  options?: IntersectionObserverInit
): boolean {
  const [isVisible, setIsVisible] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion) {
      setIsVisible(true);
      return;
    }

    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        ...options,
      }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [ref, reducedMotion, options]);

  return isVisible;
}

// ───────── Counter animation ─────────

export function useAnimatedCounter(
  target: number,
  duration: number = 500
): number {
  const [count, setCount] = useState(0);
  const reducedMotion = useReducedMotion();
  const startTime = useRef(0);

  useEffect(() => {
    if (reducedMotion) {
      setCount(target);
      return;
    }

    startTime.current = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [target, duration, reducedMotion]);

  return count;
}

// ───────── Pulse animation ─────────

export function usePulse(
  isActive: boolean,
  interval: number = 2000
): boolean {
  const [isPulsing, setIsPulsing] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion || !isActive) {
      setIsPulsing(false);
      return;
    }

    const timeout = setTimeout(() => {
      setIsPulsing(true);
      const intervalId = setInterval(() => {
        setIsPulsing((prev) => !prev);
      }, interval);

      return () => clearInterval(intervalId);
    }, 0);

    return () => clearTimeout(timeout);
  }, [isActive, interval, reducedMotion]);

  return isPulsing;
}