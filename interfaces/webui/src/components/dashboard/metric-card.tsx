"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Sparkline } from "@/components/widgets/sparkline";

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

  const statusColors = {
    normal: "border-green-500/30 bg-green-500/5",
    warning: "border-yellow-500/30 bg-yellow-500/5",
    critical: "border-red-500/30 bg-red-500/5",
    loading: "border-blue-500/30 bg-blue-500/5",
    error: "border-red-500/30 bg-red-500/5",
    na: "border-gray-500/30 bg-gray-500/5",
  };

  const statusIcons = {
    normal: "●",
    warning: "⚠",
    critical: "✗",
    loading: "◐",
    error: "✗",
    na: "—",
  };

  const handleClick = () => {
    if (href) {
      router.push(href);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`
        relative rounded-lg border p-4 transition-all duration-300
        hover:shadow-lg hover:scale-[1.02] cursor-pointer
        ${statusColors[status]}
        ${className}
      `}
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
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{value}</span>
            {unit && <span className="text-sm text-gray-400">{unit}</span>}
          </div>
        </div>
        {icon && <div className="text-2xl ml-2">{icon}</div>}
      </div>

      {sparkline && sparkline.length > 1 && (
        <div className="mt-3 h-8">
          <Sparkline data={sparkline} />
        </div>
      )}

      {progress !== undefined && (
        <div className="mt-3 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}

      <div className="absolute top-2 right-2 text-xs">
        {statusIcons[status]}
      </div>
    </div>
  );
}