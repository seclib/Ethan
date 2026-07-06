"use client";

import { useLocalStorage } from "@/hooks/useLocalStorage";

interface KPICardProps {
  label: string;
  value: string;
  unit?: string;
  trend?: number;
  sparkline?: number[];
  accent?: "blue" | "green" | "gold" | "red" | "purple";
}

const ACCENT_MAP = {
  blue: { bar: "var(--accent)", bg: "var(--accent-soft)" },
  green: { bar: "var(--green)", bg: "var(--green-soft)" },
  gold: { bar: "var(--gold)", bg: "var(--gold-soft)" },
  red: { bar: "var(--red)", bg: "var(--red-soft)" },
  purple: { bar: "var(--purple)", bg: "var(--purple-soft)" },
};

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const w = 120;
  const h = 32;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="kpi-sparkline">
      <polyline fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  );
}

export function KPICard({ label, value, unit, trend, sparkline, accent = "blue" }: KPICardProps) {
  const colors = ACCENT_MAP[accent];
  const [points, setPoints] = useLocalStorage<number[]>(`kpi:sparkline:${label}`, sparkline || []);

  return (
    <div className="kpi-card" style={{ borderColor: colors.bar }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {trend !== undefined && (
        <div className="kpi-trend" data-up={trend >= 0}>
          {trend >= 0 ? "↑" : "↓"} {Math.abs(trend).toFixed(1)}%
        </div>
      )}
      {points.length > 1 && <Sparkline data={points} color={colors.bar} />}
    </div>
  );
}
