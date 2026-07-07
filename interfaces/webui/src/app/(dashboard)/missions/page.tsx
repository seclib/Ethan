import * as React from "react";
import { Card } from "@/components/ui/card";

export default function MissionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Missions</h1>
        <p className="text-muted-foreground mt-2">
          Active and completed missions with step verification
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Active Missions</h3>
            <p className="text-sm text-muted-foreground mt-2">No active missions</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Mission History</h3>
            <p className="text-sm text-muted-foreground mt-2">Coming soon</p>
          </div>
        </Card>
      </div>
    </div>
  );
}