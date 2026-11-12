/**
 * ETHAN WebUI — Approvals client (Human Root of Trust).
 *
 * Expose les 2 routes Core existantes (aucune logique métier ici) :
 *   GET  /internal/approval/pending → approbations en attente
 *   POST /internal/approval/resolve → approve/reject (ADMIN)
 */

import { apiFetch } from "@/lib/api/client";

export interface PendingApproval {
  request_id: string;
  category: string;
  title: string;
  description?: string;
  source?: string;
  source_id?: string;
  created_at?: string;
  timeout_seconds?: number;
}

export async function listPendingApprovals(): Promise<PendingApproval[]> {
  const res = await apiFetch<PendingApproval[] | { items: PendingApproval[] }>(
    "/internal/approval/pending"
  );
  if (Array.isArray(res)) return res;
  if (res && typeof res === "object" && Array.isArray((res as { items?: unknown }).items)) {
    return (res as { items: PendingApproval[] }).items;
  }
  return [];
}

export async function resolveApproval(input: {
  request_id: string;
  approved: boolean;
  reason?: string;
}): Promise<{ resolved: boolean }> {
  return apiFetch<{ resolved: boolean }>("/internal/approval/resolve", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
