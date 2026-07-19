"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useKnowledge } from "@/features/knowledge/hooks/use-knowledge";

export default function KnowledgePage() {
  const { nodes, selectNode } = useKnowledge();
  const [search, setSearch] = React.useState("");

  const filtered = nodes.filter((n: any) => n.label.toLowerCase().includes(search.toLowerCase()));


  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Knowledge</h1>
        <p className="text-foreground-secondary mt-2">Knowledge graph explorer</p>
      </div>

      <div className="flex gap-2">
        <Input placeholder="Search nodes..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((node) => (
          <Card key={node.id} hoverable onClick={() => selectNode(node)}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {node.label}
                <Badge variant="info" size="sm">{node.type}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground-tertiary">{node.connections.length} connections</p>
            </CardContent>
          </Card>
        ))}
        {filtered.length === 0 && (
          <p className="text-foreground-tertiary col-span-full text-center py-8">No knowledge nodes found</p>
        )}
      </div>
    </div>
  );
}