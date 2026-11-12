"use client";

import * as React from "react";
import type { StatusVariant } from "./types";

const STATUS_STYLES: Record<StatusVariant, string> = {
  success: "text-green border-green/30 bg-green-soft",
  warning: "text-gold border-gold/30 bg-gold-soft",
  error: "text-red border-red/30 bg-red-soft",
  pending: "text-foreground-secondary border-line-1 bg-surface-secondary",
  running: "text-accent border-accent/30 bg-accent-soft",
  completed: "text-green border-green/30 bg-green-soft",
  disabled: "text-foreground-tertiary border-line-1 bg-bg-1",
  unknown: "text-foreground-secondary border-line-1 bg-surface-secondary",
};

export function StatusBadge({ status, label }: { status: StatusVariant; label?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium border ${STATUS_STYLES[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {label ?? status}
    </span>
  );
}
