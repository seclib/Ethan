"use client";

/**
 * Approvals — file d'approbations du Human Root of Trust (ADMIN).
 *
 * Affichage seul : liste les demandes en attente (GET /internal/approval/pending)
 * et les résout (POST /internal/approval/resolve). La décision et l'audit
 * vivent dans le Core (ApprovalEngine + HumanRoot).
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPendingApprovals,
  resolveApproval,
  type PendingApproval,
} from "@/lib/api/approvals";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Check, X, RefreshCw } from "lucide-react";

export function ApprovalsQueue() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [reason, setReason] = React.useState("");

  const { data: pending = [], isLoading, error, refetch } = useQuery<PendingApproval[]>({
    queryKey: ["approvals-pending"],
    queryFn: listPendingApprovals,
    retry: false,
    refetchInterval: 15000,
  });

  const resolveMutation = useMutation({
    mutationFn: (input: { request_id: string; approved: boolean; reason?: string }) =>
      resolveApproval(input),
    onSuccess: (_, v) => {
      addToast({
        type: "success",
        message: v.approved ? "Demande approuvée" : "Demande rejetée",
      });
      queryClient.invalidateQueries({ queryKey: ["approvals-pending"] });
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur" }),
  });

  return (
    <section
      className="rounded-lg border p-4"
      style={{ background: "var(--panel)", borderColor: "var(--border)" }}
    >
      <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold">
        <ShieldCheck size={15} /> Human Root of Trust — Approbations
      </h2>
      <p className="mb-3 text-xs opacity-60">
        Actions sensibles en attente d&apos;aval humain. La décision est auditée dans le Core.
      </p>

      <div className="mb-3 flex items-center gap-2">
        <Button size="sm" variant="ghost" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw size={13} /> Actualiser
        </Button>
        {isLoading && <span className="text-xs opacity-50">Chargement…</span>}
      </div>

      {error && (
        <p className="text-xs opacity-60">
          Indisponible — API hors ligne ou rôle non administrateur.
        </p>
      )}

      {!error && !isLoading && pending.length === 0 && (
        <p className="text-xs opacity-50">Aucune demande en attente.</p>
      )}

      <div className="flex flex-col gap-2">
        {pending.map((item) => (
          <div
            key={item.request_id}
            className="rounded-md border p-3"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="text-sm font-medium">{item.title}</div>
            <div className="mt-0.5 text-[11px] opacity-60">
              {item.category}
              {item.source ? ` · ${item.source}` : ""}
              {item.source_id ? ` · ${item.source_id}` : ""}
            </div>
            {item.description && (
              <p className="mt-1 text-xs opacity-80">{item.description}</p>
            )}
            <div className="mt-2 flex items-center gap-2">
              <input
                className="min-w-0 flex-1 rounded-md border px-2 py-1 text-xs"
                placeholder="Motif (optionnel)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              <Button
                size="sm"
                disabled={resolveMutation.isPending}
                onClick={() =>
                  resolveMutation.mutate({
                    request_id: item.request_id,
                    approved: true,
                    reason: reason || undefined,
                  })
                }
              >
                <Check size={13} /> Approuver
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={resolveMutation.isPending}
                onClick={() =>
                  resolveMutation.mutate({
                    request_id: item.request_id,
                    approved: false,
                    reason: reason || undefined,
                  })
                }
              >
                <X size={13} /> Rejeter
              </Button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
