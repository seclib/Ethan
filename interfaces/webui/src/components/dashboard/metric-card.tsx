"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status?: "normal" | "warning" | "critical" | "loading" | "error" | "na";
  icon?: ReactNode;
  sparkline?: number[];
  progress?: number;
  href?: string;
  onClick?: () => void;
  className?: string;
  dragHandleProps?: Record<string, unknown>;
}

const statusToBadge: Record<string, "success" | "warning" | "error" | "info" | "default" | "dim"> = {
  normal: "success",
  warning: "warning",
  critical: "error",
  loading: "info",
  error: "error",
  na: "dim",
};

export function MetricCard({
  title,
  value,
  unit,
  status = "normal",
  icon,
  sparkline,
  progress,
  href,
  onClick,
  className = "",
  dragHandleProps,
}: MetricCardProps) {
  const router = useRouter();

  const handleClick = () => {
    if (href) {
      router.push(href);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className={cn(
        "relative rounded-xl border border-line-2 bg-background p-4 transition-all duration-100",
        "hover:border-line-3 hover:shadow-md cursor-pointer",
        className
      )}
      onClick={handleClick}
      role={href ? "link" : "button"}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick();
      }}
      data-testid="metric-card"
      data-status={status}
      {...dragHandleProps}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-sm text-foreground-secondary mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-foreground">{value}</span>
            {unit && <span className="text-sm text-foreground-tertiary">{unit}</span>}
          </div>
        </div>
        {icon && <div className="text-2xl ml-2">{icon}</div>}
      </div>

      <div className="absolute top-3 right-3">
        <Badge variant={statusToBadge[status] || "dim"} size="sm" dot>
          {status}
        </Badge>
      </div>

      {sparkline && sparkline.length > 1 && (
        <div className="mt-3 h-8" data-testid="sparkline-wrapper">
          {/* Sparkline will be rendered by the existing Sparkline component */}
          <div className="w-full h-full relative overflow-hidden">
            <svg
              viewBox={`0 0 ${sparkline.length - 1} 100`}
              className="w-full h-full"
              preserveAspectRatio="none"
            >
              <polyline
                fill="none"
                stroke="var(--accent-400)"
                strokeWidth="2"
                points={sparkline
                  .map((val, i) => `${i},${100 - val}`)
                  .join(" ")}
              />
            </svg>
          </div>
        </div>
      )}

      {progress !== undefined && (
        <div className="mt-3 h-2 bg-line-1 rounded-full overflow-hidden">
          <div
            className="h-full bg-accent-500 transition-all duration-500 rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}
    </div>
  );
}