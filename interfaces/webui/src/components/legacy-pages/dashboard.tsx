"use client";

import { DashboardGrid } from "@/components/dashboard/dashboard-grid";

export function DashboardPage() {
  return (
    <div className="page-in" style={{ display: "flex", flexDirection: "column", gap: 18, padding: "24px 0" }}>
      <DashboardGrid />
    </div>
  );
}