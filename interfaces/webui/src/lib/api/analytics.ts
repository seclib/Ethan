/**
 * ETHAN WebUI — Analytics API service
 *
 * Maps the analytics/evaluation dashboard to the real ETHAN API:
 *   GET /v1/analytics/summary  → { total_tokens, total_cost, event_count }
 *   GET /v1/evaluations        → evaluation definitions + results
 *
 * The summary shape is EXACTLY the one returned by AnalyticsManager
 * (core/metrics/analytics.py). The WebUI must not invent additional metrics
 * (no averages, no trends, no per-provider splits — the Core does not
 * provide them). Evaluation results are free-form dicts owned by the Core;
 * they are displayed as-is.
 */

import { apiFetch } from '@/lib/api/client';

export interface AnalyticsSummary {
  total_tokens: number;
  total_cost: number;
  event_count: number;
}

/** Core-owned evaluation definition (core/learning/evaluations.py). */
export interface Evaluation {
  id: string;
  name: string;
  description: string;
  target: string;
  criteria: Record<string, unknown>[];
  /** Free-form result entries appended by the Core (schema owned by Core). */
  results: Record<string, unknown>[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/** Usage summary (totals computed by the Core, not the frontend). */
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>('/v1/analytics/summary');
}

/** List all evaluation definitions with their results. */
export async function listEvaluations(): Promise<Evaluation[]> {
  return apiFetch<Evaluation[]>('/v1/evaluations');
}
