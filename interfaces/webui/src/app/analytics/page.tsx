"use client";

/**
 * Page Analytics — dashboard de supervision ETHAN (admin).
 *
 * Affiche UNIQUEMENT les métriques réellement fournies par le Core :
 *   - GET /v1/analytics/summary → { total_tokens, total_cost, event_count }
 *     (calculs effectués par AnalyticsManager, core/metrics/analytics.py)
 *   - GET /v1/evaluations       → définitions + résultats (EvaluationManager,
 *     core/learning/evaluations.py — résultats en dicts libres, affichés bruts)
 *
 * Aucune métrique dérivée n'est calculée côté frontend (pas de moyennes, pas
 * de tendances, pas de séries temporelles : le Core ne les fournit pas).
 * Aucune logique métier ici — la page ne fait que rendre les données.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsSummary, listEvaluations,
  type AnalyticsSummary, type Evaluation,
} from "@/lib/api/analytics";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Spinner } from "@/components/ui/spinner";
import { BarChart3, Coins, RefreshCw, Hash, Activity, FlaskConical, ChevronRight } from "lucide-react";

/** Carte statistique simple (lecture seule — pas de badge dérivé). */
function StatCard({ title, value, unit, icon }: {
  title: string; value: string; unit?: string; icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-line-2 bg-background p-4">
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm text-foreground-secondary">{title}</p>
        <div className="text-foreground-tertiary">{icon}</div>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold text-foreground tabular-nums">{value}</span>
        {unit && <span className="text-sm text-foreground-tertiary">{unit}</span>}
      </div>
    </div>
  );
}

/** Formate un nombre sans en changer la valeur (séparateurs de milliers). */
function formatNumber(n: number): string {
  return n.toLocaleString("fr-FR");
}

/** Formatage du coût — affichage uniquement, pas de calcul. */
function formatCost(cost: number): string {
  return cost.toFixed(4);
}

function SummarySection({ summary, isLoading, error, onRetry }: {
  summary: AnalyticsSummary | undefined;
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}) {
  if (isLoading) {
    return <div className="flex justify-center p-8"><Spinner /></div>;
  }
  if (error) {
    return (
      <div className="rounded-xl border border-line-2 bg-background p-6 text-center">
        <p className="text-sm text-destructive mb-3">
          Impossible de charger le résumé d&apos;usage.
        </p>
        <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
          <RefreshCw size={14} /> Réessayer
        </Button>
      </div>
    );
  }
  if (!summary) return null;

  const empty = summary.event_count === 0;
  return (
    <div>
      <h2 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-3">
        Résumé global
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard
          title="Jetons totaux"
          value={formatNumber(summary.total_tokens)}
          unit="tokens"
          icon={<Hash size={18} />}
        />
        <StatCard
          title="Coût total"
          value={formatCost(summary.total_cost)}
          unit="USD"
          icon={<Coins size={18} />}
        />
        <StatCard
          title="Événements d'usage"
          value={formatNumber(summary.event_count)}
          icon={<Activity size={18} />}
        />
      </div>
      {empty && (
        <p className="mt-3 text-xs text-foreground-tertiary">
          Aucun événement d&apos;usage enregistré — les métriques apparaîtront
          au fil des conversations traitées par le Core.
        </p>
      )}
    </div>
  );
}
/** Nombre de résultats d'une évaluation (dict libre du Core — lecture seule). */
function resultCount(evaluation: Evaluation): number {
  return Array.isArray(evaluation.results) ? evaluation.results.length : 0;
}

/** Section évaluations : liste, détail en Dialog (politique UX liste → détail). */
function EvaluationsSection({ evaluations, isLoading, error, onRetry }: {
  evaluations: Evaluation[] | undefined;
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}) {
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const detail = evaluations?.find((e) => e.id === detailId) ?? null;

  return (
    <div>
      <h2 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-3">
        Évaluations
      </h2>

      {isLoading && <div className="flex justify-center p-8"><Spinner /></div>}

      {error ? (
        <div className="rounded-xl border border-line-2 bg-background p-6 text-center">
          <p className="text-sm text-destructive mb-3">
            Impossible de charger les évaluations.
          </p>
          <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw size={14} /> Réessayer
          </Button>
        </div>
      ) : null}

      {evaluations && evaluations.length === 0 && (
        <div className="rounded-xl border border-dashed border-line-2 bg-background p-8 text-center">
          <FlaskConical size={28} className="mx-auto mb-3 text-foreground-tertiary" />
          <p className="text-sm text-foreground-secondary mb-1">Aucune évaluation définie</p>
          <p className="text-xs text-foreground-tertiary">
            Les évaluations sont créées par le Core (Learning Engine) — elles
            apparaîtront ici une fois définies.
          </p>
        </div>
      )}

      {evaluations && evaluations.length > 0 && (
        <div className="rounded-xl border border-line-2 bg-background divide-y divide-line-1 overflow-hidden">
          {evaluations.map((evaluation) => (
            <button
              key={evaluation.id}
              onClick={() => setDetailId(evaluation.id)}
              className="w-full text-left px-4 py-3 hover:bg-bg-3 transition-colors flex items-center gap-3"
            >
              <FlaskConical size={16} className="text-foreground-tertiary shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{evaluation.name}</p>
                {evaluation.description && (
                  <p className="text-xs text-foreground-tertiary truncate">{evaluation.description}</p>
                )}
              </div>
              <span className="shrink-0 text-xs text-foreground-tertiary tabular-nums">
                {resultCount(evaluation)} résultat{resultCount(evaluation) > 1 ? "s" : ""}
              </span>
              <ChevronRight size={14} className="text-foreground-tertiary shrink-0" />
            </button>
          ))}
        </div>
      )}

      {/* Détail — Dialog (politique UX ETHAN : liste → détail en modal) */}
      <Dialog
        open={detail !== null}
        onClose={() => setDetailId(null)}
        title={detail ? `Évaluation — ${detail.name}` : "Évaluation"}
        size="xl"
      >
        {detail && (
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            <div>
              <p className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-1">Cible</p>
              <p className="text-sm text-foreground font-mono">{detail.target}</p>
            </div>

            {detail.description && (
              <div>
                <p className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-1">Description</p>
                <p className="text-sm text-foreground-secondary">{detail.description}</p>
              </div>
            )}

            {Array.isArray(detail.criteria) && detail.criteria.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-1">
                  Critères ({detail.criteria.length})
                </p>
                <pre className="text-[10px] font-mono bg-bg-2 p-3 rounded-md overflow-x-auto text-foreground-secondary border border-line-1">
                  {JSON.stringify(detail.criteria, null, 2)}
                </pre>
              </div>
            )}

            <div>
              <p className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-1">
                Résultats ({resultCount(detail)})
              </p>
              {resultCount(detail) === 0 ? (
                <p className="text-sm text-foreground-tertiary">
                  Aucun résultat enregistré pour cette évaluation.
                </p>
              ) : (
                <div className="space-y-2">
                  {detail.results.map((result, i) => (
                    <pre
                      key={i}
                      className="text-[10px] font-mono bg-bg-2 p-3 rounded-md overflow-x-auto text-foreground-secondary border border-line-1"
                    >
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

/** Page Analytics — dashboard admin lecture seule, données 100 % Core. */
export default function AnalyticsPage() {
  const summaryQuery = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: getAnalyticsSummary,
  });
  const evaluationsQuery = useQuery({
    queryKey: ["evaluations"],
    queryFn: listEvaluations,
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
            <BarChart3 size={22} /> Analytics
          </h1>
          <p className="text-sm text-foreground-tertiary">
            Supervision de l&apos;usage et résultats d&apos;évaluation — données calculées par le Core.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => { summaryQuery.refetch(); evaluationsQuery.refetch(); }}
          className="gap-2"
        >
          <RefreshCw size={14} /> Actualiser
        </Button>
      </div>

      <SummarySection
        summary={summaryQuery.data}
        isLoading={summaryQuery.isLoading}
        error={summaryQuery.error}
        onRetry={() => summaryQuery.refetch()}
      />

      <EvaluationsSection
        evaluations={evaluationsQuery.data}
        isLoading={evaluationsQuery.isLoading}
        error={evaluationsQuery.error}
        onRetry={() => evaluationsQuery.refetch()}
      />
    </div>
  );
}
