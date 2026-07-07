import * as React from "react";
import { Card } from "@/components/ui/card";

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Agents</h1>
        <p className="text-muted-foreground mt-2">
          Manage your AI agents and their capabilities
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <div className="p-6">
            <h3 className="font-semibold">Agent List</h3>
            <p className="text-sm text-muted-foreground mt-2">Coming soon</p>
          </div>
        </Card>
      </div>
    </div>
  );
}