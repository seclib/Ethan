"use client";

import * as React from "react";
import type { ChartData, ChartPoint } from "./types";

const PALETTE = ["#22d3ee", "#60a5fa", "#84cc16", "#f59e0b", "#f87171", "#a78bfa"];

function BarChart({ data }: { data: ChartPoint[] }) {
  const max = Math.max(...data.map((d) => Math.abs(d.value)), 1);
  const height = 180;
  const barWidth = Math.max(12, Math.floor(320 / data.length));
  const gap = 8;
  const width = data.length * (barWidth + gap) + gap;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full max-w-full" role="img">
      {data.map((d, i) => {
        const barHeight = (Math.abs(d.value) / max) * (height - 40);
        const x = gap + i * (barWidth + gap);
        const y = height - barHeight - 22;
        return (
          <g key={`${d.label}-${i}`}>
            <rect x={x} y={y} width={barWidth} height={barHeight} rx={2} fill={PALETTE[i % PALETTE.length]} />
            <text x={x + barWidth / 2} y={height - 8} textAnchor="middle" fontSize="9" fill="currentColor" className="text-foreground-secondary">{d.label}</text>
            <text x={x + barWidth / 2} y={Math.max(10, y - 4)} textAnchor="middle" fontSize="9" fill="currentColor" className="text-foreground">{d.value}</text>
          </g>
        );
      })}
    </svg>
  );
}

function LineChart({ data }: { data: ChartPoint[] }) {
  const width = Math.max(320, data.length * 36);
  const height = 190;
  const max = Math.max(...data.map((d) => d.value), 1);
  const min = Math.min(...data.map((d) => d.value), 0);
  const range = Math.max(max - min, 1);
  const points = data.map((d, i) => {
    const x = 24 + (i / Math.max(data.length - 1, 1)) * (width - 48);
    const y = height - 24 - ((d.value - min) / range) * (height - 48);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full max-w-full" role="img">
      <line x1={24} y1={height - 24} x2={width - 24} y2={height - 24} stroke="currentColor" opacity="0.2" />
      <polyline fill="none" stroke="#22d3ee" strokeWidth="2" points={points} />
      {data.map((d, i) => {
        const x = 24 + (i / Math.max(data.length - 1, 1)) * (width - 48);
        const y = height - 24 - ((d.value - min) / range) * (height - 48);
        return <circle key={`${d.label}-${i}`} cx={x} cy={y} r={3} fill="#22d3ee" />;
      })}
    </svg>
  );
}

function PieChart({ data }: { data: ChartPoint[] }) {
  const total = data.reduce((acc, d) => acc + Math.abs(d.value), 0) || 1;
  const radius = 70;
  const cx = 90;
  const cy = 90;
  const slices = data.reduce<{ start: number; end: number }[]>((acc, d) => {
    const previous = acc.length ? acc[acc.length - 1].end : -Math.PI / 2;
    const delta = (Math.abs(d.value) / total) * Math.PI * 2;
    acc.push({ start: previous, end: previous + delta });
    return acc;
  }, []);
  return (
    <svg viewBox="0 0 260 180" className="h-auto w-full max-w-[260px]" role="img">
      {slices.map((slice, i) => {
        const d = data[i];
        const { start, end } = slice;
        const delta = end - start;
        const x1 = cx + Math.cos(start) * radius;
        const y1 = cy + Math.sin(start) * radius;
        const x2 = cx + Math.cos(end) * radius;
        const y2 = cy + Math.sin(end) * radius;
        const largeArc = delta > Math.PI ? 1 : 0;
        return (
          <path
            key={`${d.label}-${i}`}
            d={`M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`}
            fill={PALETTE[i % PALETTE.length]}
            stroke="var(--bg-1)"
            strokeWidth={1}
          />
        );
      })}
      {data.map((d, i) => {
        const y = 20 + i * 16;
        return (
          <g key={`legend-${i}`}>
            <rect x={185} y={y - 8} width={8} height={8} fill={PALETTE[i % PALETTE.length]} rx={1} />
            <text x={198} y={y} fontSize="9" fill="currentColor" className="text-foreground-secondary">{d.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

export function ChartView({ data }: { data: ChartData }) {
  return (
    <div className="my-2 rounded-md border border-line-1 bg-surface-secondary px-3 py-2">
      {data.title && <p className="mb-2 text-sm font-semibold text-foreground">{data.title}</p>}
      {data.chartType === "bar" && <BarChart data={data.data} />}
      {data.chartType === "line" && <LineChart data={data.data} />}
      {data.chartType === "pie" && <PieChart data={data.data} />}
    </div>
  );
}
