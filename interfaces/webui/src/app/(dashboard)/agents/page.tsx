"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAgents } from "@/hooks/use-agents";
import { getStatusColor } from "@/lib/utils";

export default function AgentsPage() {
  const { agents, isLoading, error } = useAgents();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground mt-2">Loading agents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-destructive mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Agents</h1>
        <p className="text-muted-foreground mt-2">
          Manage your AI agents and their capabilities
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.id} className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">{agent.name}</h3>
              <Badge variant={getStatusColor(agent.status)}>
                {agent.status}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              {agent.description || "No description"}
            </p>
            <div className="space-y-2">
              <div className="flex flex-wrap gap-1">
                {agent.capabilities.slice(0, 3).map((cap) => (
                  <span
                    key={cap}
                    className="text-xs bg-muted px-2 py-1 rounded"
                  >
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length > 3 && (
                  <span className="text-xs text-muted-foreground">
                    +{agent.capabilities.length - 3} more
                  </span>
                )}
              </div>
            </div>
            <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
              Created: {new Date(agent.created_at).toLocaleDateString()}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}