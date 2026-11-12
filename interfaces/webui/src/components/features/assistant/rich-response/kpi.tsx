"use client";

import * as React from "react";
import type { KpiData } from "./types";
import { StatusBadge } from "./status-badge";

export function KpiGrid({ data }: { data: KpiData }) {
  return (
    <div className="my-2">
      {data.title && <p className="mb-2 text-sm font-semibold text-foreground">{data.title}</p>}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {data.items.map((item) => (
          <div key={item.label} className="rounded-md border border-line-1 bg-surface-secondary px-3 py-2">
            <p className="text-xs text-foreground-secondary">{item.label}</p>
            <p className="mt-0.5 text-lg font-semibold text-foreground">{item.value}</p>
            {(item.trend || item.status) && (
              <div className="mt-1 flex items-center gap-2 text-xs text-foreground-tertiary">
                {item.trend && <span>{item.trend}</span>}
                {item.status && <StatusBadge status={item.status} label={item.status} />}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
