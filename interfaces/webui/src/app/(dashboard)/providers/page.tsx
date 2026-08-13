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
import type { Provider, ProviderUpdate } from "@/core/api/providers.types";

const STATUS_VARIANT: Record<string, "success" | "dim" | "error"> = {
  connected: "success",
  disconnected: "dim",
  error: "error",
  unknown: "dim",
};

export default function ProvidersPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [configOpen, setConfigOpen] = React.useState(false);
  const [configuringProvider, setConfiguringProvider] = React.useState<Provider | null>(null);
  const [apiKey, setApiKey] = React.useState("");
  const [baseUrl, setBaseUrl] = React.useState("");

  const handleConfigureClick = (p: Provider) => {
    setConfiguringProvider(p);
    setApiKey("");
    setBaseUrl(p.base_url || "");
    setConfigOpen(true);
  };

  const { data: providers = [], isLoading, error } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => apiClient.getProviders(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) =>
      apiClient.updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider updated successfully" });
      setConfigOpen(false);
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to update provider" });
    },
  });

  const handleSave = () => {
    if (!configuringProvider) return;
    const data: ProviderUpdate = {};
    if (apiKey) data.api_key = apiKey;
    if (baseUrl) data.base_url = baseUrl;
    updateMutation.mutate({ id: configuringProvider.id, data });
  };

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
                <Badge variant={STATUS_VARIANT[p.status] || "dim"} size="sm" dot>{p.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-xs text-foreground-tertiary">
                <p>Type: <span className="text-foreground-secondary">{p.type}</span></p>
                {p.base_url && <p className="font-mono">{p.base_url}</p>}
                {p.default_model && <p>Model: <span className="text-foreground-secondary font-mono">{p.default_model}</span></p>}
                {p.is_default && <p className="text-green-400">Default provider</p>}
              </div>
              <Button
                size="sm"
                variant="secondary"
                className="mt-3"
                onClick={() => handleConfigureClick(p)}
                aria-label={`Configure ${p.name}`}
              >
                Configure
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
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Base URL (Optional)</label>
            <Input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.example.com"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
            <Button variant="ghost" onClick={() => setConfigOpen(false)}>Cancel</Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}