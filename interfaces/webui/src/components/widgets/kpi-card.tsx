"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  sparklineData?: number[];
  icon?: string;
  onClick?: () => void;
  className?: string;
}

export function KpiCard({
  title,
  value,
  unit,
  trend,
  trendValue,
  sparklineData,
  icon,
  onClick,
  className,
}: KpiCardProps) {
  const trendColors = {
    up: "text-green-500",
    down: "text-red-500",
    neutral: "text-muted-foreground",
  };

  const trendIcons = {
    up: "↑",
    down: "↓",
    neutral: "→",
  };

  return (
    <Card
      className={cn(
        "p-6 transition-all duration-200 hover:shadow-lg",
        onClick && "cursor-pointer hover:border-primary/50",
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="flex items-baseline gap-2 mt-2">
            <p className="text-3xl font-bold">{value}</p>
            {unit && <p className="text-sm text-muted-foreground">{unit}</p>}
          </div>
          {trend && trendValue && (
            <div className={cn("flex items-center gap-1 mt-2 text-sm", trendColors[trend])}>
              <span>{trendIcons[trend]}</span>
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        {icon && <div className="text-3xl">{icon}</div>}
      </div>

      {sparklineData && sparklineData.length > 1 && (
        <div className="mt-4 h-12">
          <Sparkline data={sparklineData} />
        </div>
      )}
    </Card>
  );
}

// Simple sparkline component using SVG
function Sparkline({ data }: { data: number[] }) {
  const width = 200;
  const height = 48;
  const padding = 2;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((value, index) => {
      const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
      const y = height - padding - ((value - min) / range) * (height - 2 * padding);
      return `${x},${y}`;
    })
    .join(" ");

  const lastValue = data[data.length - 1];
  const firstValue = data[0];
  const trend = lastValue > firstValue ? "up" : lastValue < firstValue ? "down" : "neutral";

  const strokeColor = trend === "up" ? "#10b981" : trend === "down" ? "#ef4444" : "#64748b";

  return (
    <svg width={width} height={height} className="w-full h-full">
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        points={points}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}