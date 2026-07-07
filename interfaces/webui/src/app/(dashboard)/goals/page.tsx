import * as React from "react";
import { Card } from "@/components/ui/card";

export default function GoalsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Goals</h1>
        <p className="text-muted-foreground mt-2">
          Active goals and task decomposition
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Active Goals</h3>
            <p className="text-2xl font-bold mt-2">0</p>
            <p className="text-sm text-muted-foreground">No active goals</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Pending Tasks</h3>
            <p className="text-2xl font-bold mt-2">0</p>
            <p className="text-sm text-muted-foreground">No pending tasks</p>
          </div>
        </Card>
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Completed</h3>
            <p className="text-2xl font-bold mt-2">0</p>
            <p className="text-sm text-muted-foreground">No completed goals</p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Goal List</h3>
          <p className="text-sm text-muted-foreground">No goals yet</p>
        </div>
      </Card>
    </div>
  );
}