"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Provider {
  id: string;
  name: string;
  type: string;
  status: "connected" | "disconnected" | "error";
}

export default function ProvidersPage() {
  const [providers] = React.useState<Provider[]>([
    { id: "openai", name: "OpenAI", type: "LLM", status: "connected" },
    { id: "anthropic", name: "Anthropic", type: "LLM", status: "connected" },
    { id: "huggingface", name: "HuggingFace", type: "LLM", status: "disconnected" },
    { id: "pinecone", name: "Pinecone", type: "VectorDB", status: "connected" },
  ]);

  const statusColor = { connected: "success", disconnected: "dim", error: "error" } as const;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Providers</h1>
        <p className="text-foreground-secondary mt-2">External service providers configuration</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {providers.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{p.name}</CardTitle>
                <Badge variant={statusColor[p.status]} size="sm" dot>{p.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-foreground-tertiary mb-3">Type: {p.type}</p>
              <Button size="sm" variant="secondary">Configure</Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}