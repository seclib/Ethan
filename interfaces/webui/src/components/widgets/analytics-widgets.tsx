"use client";

/* ───────── Top Content ───────── */

interface TopContentItem {
  label: string;
  value: number;
  unit?: string;
}

interface TopContentProps {
  items: TopContentItem[];
  title?: string;
}

export function TopContent({ items, title = "Top Contenu" }: TopContentProps) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="analytics-card">
      <div className="analytics-title">{title}</div>
      <div className="analytics-list">
        {items.map((item, i) => (
          <div key={i} className="analytics-row">
            <span className="analytics-rank">{String(i + 1).padStart(2, "0")}</span>
            <span className="analytics-label">{item.label}</span>
            <div className="analytics-bar-track">
              <div className="analytics-bar-fill" style={{ width: `${(item.value / max) * 100}%` }} />
            </div>
            <span className="analytics-value">
              {item.value}
              {item.unit && <span className="analytics-unit">{item.unit}</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───────── Source Bars ───────── */

interface SourceItem {
  label: string;
  value: number;
  color?: string;
}

interface SourceBarsProps {
  items: SourceItem[];
  title?: string;
}

const COLORS = ["var(--accent)", "var(--green)", "var(--gold)", "var(--purple)", "var(--red)", "var(--fg-3)"];

export function SourceBars({ items, title = "Sources" }: SourceBarsProps) {
  const total = items.reduce((s, i) => s + i.value, 1);
  return (
    <div className="analytics-card">
      <div className="analytics-title">{title}</div>
      <div className="source-stacked">
        {items.map((item, i) => (
          <div
            key={i}
            className="source-segment"
            style={{
              width: `${(item.value / total) * 100}%`,
              background: item.color || COLORS[i % COLORS.length],
            }}
            title={`${item.label}: ${item.value}`}
          />
        ))}
      </div>
      <div className="source-legend">
        {items.map((item, i) => (
          <div key={i} className="source-legend-item">
            <span
              className="source-legend-dot"
              style={{ background: item.color || COLORS[i % COLORS.length] }}
            />
            <span className="source-legend-label">{item.label}</span>
            <span className="source-legend-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───────── Mini Stats Row ───────── */

interface MiniStat {
  label: string;
  value: string;
  accent?: string;
}

export function MiniStats({ items }: { items: MiniStat[] }) {
  return (
    <div className="mini-stats">
      {items.map((item, i) => (
        <div key={i} className="mini-stat-item">
          <span className="mini-stat-value" style={item.accent ? { color: item.accent } : undefined}>
            {item.value}
          </span>
          <span className="mini-stat-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}