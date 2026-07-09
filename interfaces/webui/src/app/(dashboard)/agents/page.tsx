"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgents } from "@/hooks/use-agents";
import { getStatusColor } from "@/lib/utils";

export default function AgentsPage() {
  const { agents, isLoading, error } = useAgents();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Agents</h1>
          <p className="text-foreground-secondary mt-2">Loading agents...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="text" lines={4} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Agents</h1>
          <p className="text-error-600 mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Agents</h1>
          <p className="text-foreground-secondary mt-2">
            Manage your AI agents and their capabilities
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.id} variant="outlined" hoverable>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{agent.name}</CardTitle>
                <Badge variant={getStatusColor(agent.status)} dot>
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground-secondary mb-4">
                {agent.description || "No description"}
              </p>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-1">
                  {agent.capabilities.slice(0, 3).map((cap: string) => (
                    <span
                      key={cap}
                      className="text-xs bg-elevated text-foreground-secondary px-2 py-1 rounded-md"
                    >
                      {cap}
                    </span>
                  ))}
                  {agent.capabilities.length > 3 && (
                    <span className="text-xs text-foreground-tertiary">
                      +{agent.capabilities.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <p className="text-xs text-foreground-tertiary">
                Created: {new Date(agent.created_at).toLocaleDateString()}
              </p>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}