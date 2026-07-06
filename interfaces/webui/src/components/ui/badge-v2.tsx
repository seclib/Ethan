"use client";

interface BadgeV2Props {
  variant?: "accent" | "gold" | "green" | "red" | "purple" | "solid" | "risk-low" | "risk-medium" | "risk-high" | "skills" | "maintenance";
  dot?: boolean;
  children: React.ReactNode;
}

const VARIANT_MAP: Record<string, string> = {
  accent: "badge--accent",
  gold: "badge--gold",
  green: "badge--green",
  red: "badge--red",
  purple: "badge--purple",
  solid: "badge--solid",
  "risk-low": "badge--risk-low",
  "risk-medium": "badge--risk-medium",
  "risk-high": "badge--risk-high",
  skills: "badge--skills",
  maintenance: "badge--maintenance",
};

const DOT_COLORS: Record<string, string> = {
  accent: "var(--accent)",
  gold: "var(--gold)",
  green: "var(--green)",
  red: "var(--red)",
  purple: "var(--purple)",
  solid: "var(--accent)",
  "risk-low": "var(--green)",
  "risk-medium": "var(--amber)",
  "risk-high": "var(--red)",
  skills: "var(--purple)",
  maintenance: "var(--fg-3)",
};

export function BadgeV2({ variant = "accent", dot, children }: BadgeV2Props) {
  const cls = VARIANT_MAP[variant] || "badge--accent";
  return (
    <span className={`badge ${cls}`}>
      {dot && (
        <span
          className="badge-dot"
          style={{ background: DOT_COLORS[variant] || "var(--accent)" }}
        />
      )}
      {children}
    </span>
  );
}