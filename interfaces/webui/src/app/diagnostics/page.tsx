"use client";

/**
 * Diagnostics — page Administration (Open-WebUI style).
 * Interroge la capacité ETHAN réelle : GET /api/health/detailed
 * (proxy catch-all → API FastAPI /health/detailed, JWT injecté).
 * Aucune logique métier : pure affichage de santé des services.
 */

import * as React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HealthReport {
  [component: string]: string;
}

const REFRESH_MS = 30_000;

export default function DiagnosticsPage() {
  const [report, setReport] = React.useState<HealthReport | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/health/detailed", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setReport((await res.json()) as HealthReport);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
    const t = setInterval(() => void load(), REFRESH_MS);
    return () => clearInterval(t);
  }, [load]);

  const entries = Object.entries(report ?? {});
  const allOk = entries.length > 0 && entries.every(([, v]) => v.startsWith("connected"));

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6" style={{ width: "100%" }}>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--fg)" }}>Diagnostics</h1>
          <p className="text-sm" style={{ color: "var(--fg-2, rgb(var(--fg-rgb) / 0.6))" }}>
            Santé des services ETHAN — actualisé toutes les 30 s
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Actualiser
        </Button>
      </div>

      {error && (
        <div
          className="mb-3 rounded-xl border p-3 text-sm"
          style={{ borderColor: "var(--red)", background: "var(--red-soft)", color: "var(--fg)" }}
        >
          Impossible de joindre l&apos;API ETHAN ({error}). Vérifiez que le Core est démarré (./ethan up).
        </div>
      )}

      <div className="overflow-hidden rounded-xl" style={{ border: "1px solid var(--border)", background: "var(--panel)" }}>
        {entries.map(([name, status]) => {
          const ok = status.startsWith("connected");
          return (
            <div
              key={name}
              className="flex items-center justify-between border-b px-4 py-3 last:border-b-0"
              style={{ borderColor: "var(--border)" }}
            >
              <span className="text-sm" style={{ color: "var(--fg)" }}>{name}</span>
              <span className="flex items-center gap-2 text-xs" style={{ color: ok ? "var(--green)" : "var(--red)" }}>
                <span
                  className="inline-block size-2 rounded-full"
                  style={{ background: ok ? "var(--green)" : "var(--red)" }}
                />
                {ok ? "connecté" : status}
              </span>
            </div>
          );
        })}
        {!report && !error && (
          <div className="px-4 py-6 text-center text-sm" style={{ color: "var(--fg-2, rgb(var(--fg-rgb) / 0.6))" }}>
            Chargement…
          </div>
        )}
      </div>

      <p className="mt-3 text-xs" style={{ color: "var(--fg-3, rgb(var(--fg-rgb) / 0.45))" }}>
        État global : {allOk ? "tous les services sont connectés" : "au moins un service signale un problème"} ·
        Monitoring temps réel : Grafana (:3002)
      </p>
    </div>
  );
}
