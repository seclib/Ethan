"use client";

import * as React from "react";
import { apiFetch } from "@/lib/api/client";

type QuantarLifecycleStatus = {
  status?: string;
  healthy?: boolean;
  container_id?: string | null;
  error?: string | null;
  allowed_actions?: string[];
};

type QuantarStatus = {
  application?: string;
  available?: boolean;
  runtime?: string;
  message?: string;
  error?: string | null;
};

type QuantarConfig = {
  available?: boolean;
  config?: Record<string, unknown>;
  secrets_exposed?: boolean;
};

export default function QuantarPage() {
  const [status, setStatus] = React.useState<QuantarStatus | null>(null);
  const [lifecycle, setLifecycle] = React.useState<QuantarLifecycleStatus | null>(null);
  const [config, setConfig] = React.useState<QuantarConfig | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [actionPending, setActionPending] = React.useState(false);
  const [actionResult, setActionResult] = React.useState<string | null>(null);

  const reload = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusResponse, configResponse, lifecycleResponse] = await Promise.all([
        apiFetch<QuantarStatus>("/v1/quantar/status"),
        apiFetch<QuantarConfig>("/v1/quantar/config"),
        apiFetch<QuantarLifecycleStatus>("/v1/quantar/lifecycle/status").catch(() => null),
      ]);
      setStatus(statusResponse);
      setConfig(configResponse);
      setLifecycle(lifecycleResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quantar API unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    reload();
  }, [reload]);

  async function runLifecycle(action: "start" | "stop") {
    setActionPending(true);
    setActionResult(null);
    setError(null);
    try {
      const response = await apiFetch<{ status?: string; error?: string | null }>(
        action === "start" ? "/v1/quantar/lifecycle/start" : "/v1/quantar/lifecycle/stop",
        { method: "POST" },
      );
      setActionResult(`${action === "start" ? "Start" : "Stop"}: ${response.status ?? "unknown"}`);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quantar lifecycle operation failed");
    } finally {
      setActionPending(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent">
          Q
        </span>
        <div>
          <h1 className="text-lg font-semibold text-foreground">ETHAN Quantar</h1>
          <p className="text-xs text-foreground-tertiary">
            ETHAN · QUANTITATIVE INTELLIGENCE
          </p>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-line-1 bg-bg-1 p-4 text-sm text-foreground-secondary">
          Loading Quantar status and configuration...
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500">
          {error}
        </div>
      )}

      {status && (
        <div className="rounded-xl border border-line-1 bg-bg-1 p-4">
          <h2 className="text-sm font-semibold text-foreground">Status</h2>
          <p className="mt-2 text-xs text-foreground-secondary">
            Available: {status.available ? "yes" : "no"}
          </p>
          <p className="text-xs text-foreground-secondary">Runtime: {status.runtime ?? "unknown"}</p>
          <p className="text-xs text-foreground-secondary">{status.message ?? "No status message"}</p>
        </div>
      )}

      {lifecycle && (
        <div className="rounded-xl border border-line-1 bg-bg-1 p-4">
          <h2 className="text-sm font-semibold text-foreground">Lifecycle</h2>
          <p className="mt-2 text-xs text-foreground-secondary">State: {lifecycle.status ?? "unknown"}</p>
          <p className="text-xs text-foreground-secondary">Healthy: {lifecycle.healthy ? "yes" : "no"}</p>
          <p className="text-xs text-foreground-secondary">Container: {lifecycle.container_id ?? "none"}</p>
          {lifecycle.error && <p className="text-xs text-red-500">{lifecycle.error}</p>}
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              disabled={actionPending}
              onClick={() => runLifecycle("start")}
              className="rounded-lg border border-line-1 px-3 py-1.5 text-xs hover:bg-elevated disabled:opacity-50"
            >
              Start
            </button>
            <button
              type="button"
              disabled={actionPending}
              onClick={() => runLifecycle("stop")}
              className="rounded-lg border border-line-1 px-3 py-1.5 text-xs hover:bg-elevated disabled:opacity-50"
            >
              Stop
            </button>
          </div>
          {actionResult && <p className="mt-2 text-xs text-foreground-tertiary">{actionResult}</p>}
        </div>
      )}

      {config && (
        <div className="rounded-xl border border-line-1 bg-bg-1 p-4">
          <h2 className="text-sm font-semibold text-foreground">Configuration</h2>
          <p className="mt-2 text-xs text-foreground-secondary">
            Secrets exposed: {config.secrets_exposed ? "yes" : "no"}
          </p>
          <pre className="mt-2 max-h-80 overflow-auto rounded-md border border-line-1 bg-bg-2 p-3 text-xs">
            {JSON.stringify(config.config ?? {}, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
