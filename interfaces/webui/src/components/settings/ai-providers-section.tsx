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
import type { Provider, ProviderCreate, ProviderType, TestConnectionResult } from "@/core/api/providers.types";

const PROVIDER_TYPES: { value: ProviderType; label: string }[] = [
  { value: "ollama", label: "Ollama" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "vllm", label: "vLLM" },
  { value: "openai-compatible", label: "Custom API" },
];

const STATUS_VARIANT: Record<string, "success" | "dim" | "error"> = {
  connected: "success",
  disconnected: "dim",
  error: "error",
  unknown: "dim",
};

/**
 * AIProvidersSection — sous-section Settings → AI Providers.
 *
 * Consomme les routes /api/providers/* exposées par le ProviderManager backend.
 * Réutilise apiClient + les composants UI ETHAN (Card, Button, Input, Dialog,
 * Badge) — aucune duplication de logique.
 */
export function AIProvidersSection() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [addOpen, setAddOpen] = React.useState(false);
  const [testingId, setTestingId] = React.useState<string | null>(null);
  const [testResult, setTestResult] = React.useState<Record<string, TestConnectionResult>>({});

  // ── Query: liste des providers ────────────────────────────────────────
  const { data: providers = [], isLoading, error } = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: () => apiClient.getProviders(),
  });

  // ── Mutation: créer un provider ───────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: (data: ProviderCreate) => apiClient.createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider added successfully" });
      setAddOpen(false);
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to add provider" });
    },
  });

  // ── Mutation: définir le provider par défaut ──────────────────────────
  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => apiClient.setDefaultProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Default provider updated" });
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to set default" });
    },
  });

  // ── Mutation: supprimer un provider ───────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      addToast({ type: "success", message: "Provider removed" });
    },
    onError: (err) => {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Failed to remove provider" });
    },
  });

  // ── Test de connexion ─────────────────────────────────────────────────
  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await apiClient.testProviderConnection(id);
      setTestResult((prev) => ({ ...prev, [id]: result }));
      addToast({
        type: result.connected ? "success" : "error",
        message: result.connected ? "Connection successful" : result.message || "Connection failed",
      });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Test failed" });
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">AI Providers</h2>
          <p className="text-sm text-foreground-tertiary mt-1">
            Configure and manage your LLM engines
          </p>
        </div>
        <Button size="sm" variant="primary" onClick={() => setAddOpen(true)}>
          + Add Provider
        </Button>
      </div>

      {isLoading && <p className="text-foreground-tertiary text-sm">Loading providers...</p>}
      {error && <p className="text-red/80 text-sm">Error: {error.message}</p>}

      {/* ── Liste des providers ─────────────────────────────────────────── */}
      <div className="grid gap-3 md:grid-cols-2">
        {providers.map((p) => {
          const result = testResult[p.id];
          const status = result?.connected ? "connected" : p.status;
          return (
            <Card key={p.id} variant="outlined" hoverable>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">
                      {status === "connected" ? "✓" : status === "error" ? "✗" : "○"}
                    </span>
                    <CardTitle className="text-sm">{p.name}</CardTitle>
                    {p.is_default && <Badge variant="success" size="sm">Default</Badge>}
                  </div>
                  <Badge variant={STATUS_VARIANT[status] || "dim"} size="sm" dot>
                    {status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-xs text-foreground-tertiary">
                  {p.base_url && <p className="font-mono">{p.base_url}</p>}
                  <p>Type: <span className="text-foreground-secondary">{p.type}</span></p>
                  {p.default_model && <p>Model: <span className="text-foreground-secondary font-mono">{p.default_model}</span></p>}
                  {!p.enabled && <p className="text-foreground-tertiary italic">Disabled</p>}
                </div>
                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleTest(p.id)}
                    disabled={testingId === p.id}
                    aria-label={`Test ${p.name}`}
                  >
                    {testingId === p.id ? "Testing..." : "Test"}
                  </Button>
                  {!p.is_default && p.enabled && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setDefaultMutation.mutate(p.id)}
                      disabled={setDefaultMutation.isPending}
                    >
                      Set Default
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteMutation.mutate(p.id)}
                    disabled={deleteMutation.isPending}
                    className="text-red/70 hover:text-red"
                  >
                    Remove
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* ── Dialog: Ajouter un provider ─────────────────────────────────── */}
      <AddProviderDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        isPending={createMutation.isPending}
      />
    </div>
  );
}

// ── Sous-composant: Formulaire d'ajout ───────────────────────────────────

interface AddProviderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProviderCreate) => void;
  isPending: boolean;
}

function AddProviderDialog({ open, onOpenChange, onSubmit, isPending }: AddProviderDialogProps) {
  const [name, setName] = React.useState("");
  const [type, setType] = React.useState<ProviderType>("ollama");
  const [baseUrl, setBaseUrl] = React.useState("");
  const [apiKey, setApiKey] = React.useState("");
  const [defaultModel, setDefaultModel] = React.useState("");

  const reset = () => {
    setName("");
    setType("ollama");
    setBaseUrl("");
    setApiKey("");
    setDefaultModel("");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      type,
      base_url: baseUrl,
      api_key: apiKey || undefined,
      default_model: defaultModel,
      enabled: true,
    });
    reset();
  };

  const isLocal = type === "ollama" || type === "vllm" || type === "openai-compatible";

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Add AI Provider">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Provider name</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="my-ollama"
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as ProviderType)}
            className="flex h-10 w-full rounded-md border border-line-1 bg-bg-2 px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/50"
          >
            {PROVIDER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {isLocal && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Endpoint</label>
            <Input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:11434"
            />
          </div>
        )}

        {(type === "openai" || type === "anthropic" || type === "openai-compatible") && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">API Key</label>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
            />
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Default Model</label>
          <Input
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            placeholder="qwen2.5-coder"
          />
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t border-line-1 mt-4">
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={isPending}>
            {isPending ? "Saving..." : "Save"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}