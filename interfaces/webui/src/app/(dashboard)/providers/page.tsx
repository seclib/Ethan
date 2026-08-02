"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/core/api/api-client";
import { useUIStore } from "@/core/store/ui.store";

interface Provider {
  id: string;
  name: string;
  type: string;
  status: "connected" | "disconnected" | "error";
  configured: boolean;
}

export default function ProvidersPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [configOpen, setConfigOpen] = React.useState(false);
  const [configuringProvider, setConfiguringProvider] = React.useState<Provider | null>(null);

  const handleConfigureClick = (p: Provider) => {
    setConfiguringProvider(p);
    setConfigOpen(true);
  };

  const { data: providers = [], isLoading, error } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => apiClient.request<Provider[]>("/api/v1/providers"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Provider> }) =>
      apiClient.request<Provider>(`/api/v1/providers/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider updated successfully" });
      setConfigOpen(false);
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update provider" });
    },
  });

  const statusColor = { connected: "success", disconnected: "dim", error: "error" } as const;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Providers</h1>
        <p className="text-foreground-secondary mt-2">External service providers configuration</p>
      </div>

      {isLoading && <p className="text-foreground-tertiary text-sm">Loading providers...</p>}
      {error && <p className="text-red/80 text-sm">Error: {error.message}</p>}

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
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleConfigureClick(p)}
                aria-label={`Configure ${p.name}`}
              >
                {p.configured ? "Reconfigure" : "Configure"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog 
        open={configOpen} 
        onOpenChange={setConfigOpen} 
        title={`Configure ${configuringProvider?.name}`}
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">API Key</label>
            <Input type="password" placeholder="sk-..." />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Base URL (Optional)</label>
            <Input placeholder="https://api.example.com" />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setConfigOpen(false)}>Cancel</Button>
            <Button 
              variant="primary" 
              onClick={() => configuringProvider && updateMutation.mutate({ 
                id: configuringProvider.id, 
                data: { status: configuringProvider.status === "connected" ? "disconnected" : "connected" } 
              })}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save & Toggle Status"}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}