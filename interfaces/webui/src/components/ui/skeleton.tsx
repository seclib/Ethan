"use client";

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className = "", style }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={style}
    />
  );
}

export function KPISkeleton() {
  return (
    <div className="kpi-skeleton">
      <Skeleton className="kpi-skeleton-label" />
      <Skeleton className="kpi-skeleton-value" />
      <Skeleton className="kpi-skeleton-trend" />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="card-skeleton">
      <Skeleton className="card-skeleton-header" />
      <Skeleton className="card-skeleton-body" />
      <Skeleton className="card-skeleton-footer" />
    </div>
  );
}