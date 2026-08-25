"use client";

/**
 * VirtualList — a dependency-free virtualized list for rendering large datasets
 * without installing `react-window` or `react-virtualized`.
 *
 * Strategy : we render *all* items (simple, works for moderate lists up to ~1000),
 * but use `IntersectionObserver` to apply a fade-in animation on scroll for
 * perceived performance without jank. For truly massive datasets (>5000 items),
 * prefer replacing this with `react-window` later.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

interface VirtualListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
  rowClassName?: string;
  empty?: React.ReactNode;
  loading?: boolean;
  /** Number of items to render per "batch" (for simple chunking). */
  batchSize?: number;
}

export function VirtualList<T>({
  items,
  renderItem,
  className,
  rowClassName,
  empty,
  loading,
  batchSize = 50,
}: VirtualListProps<T>) {
  const [visibleCount, setVisibleCount] = React.useState(batchSize);

  // Simple intersection observer: when the last rendered item enters view,
  // we increase the visible count by batchSize.
  const sentinelRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleCount((prev) =>
            Math.min(prev + batchSize, items.length),
          );
        }
      },
      { root: null, rootMargin: "200px", threshold: 0 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [batchSize, items.length]);

  if (loading && items.length === 0) {
    return (
      <div className={cn("flex items-center justify-center py-8", className)}>
        <div className="text-foreground-tertiary">Loading…</div>
      </div>
    );
  }

  if (items.length === 0 && !loading) {
    return (
      <div className={cn("flex items-center justify-center py-8", className)}>
        {empty ?? <span className="text-foreground-tertiary">No items found.</span>}
      </div>
    );
  }

  return (
    <div className={cn("space-y-1", className)}>
      {items.slice(0, visibleCount).map((item, index) => (
        <div key={index} className={rowClassName}>
          {renderItem(item, index)}
        </div>
      ))}

      {/* Sentinel for lazy loading */}
      {visibleCount < items.length && items.length > batchSize && (
        <div ref={sentinelRef} className="py-4 text-center text-xs text-foreground-tertiary">
          Loading more…
        </div>
      )}
    </div>
  );
}
