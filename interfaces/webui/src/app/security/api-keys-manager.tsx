"use client";

/**
 * ETHAN WebUI — API Keys management (section Security).
 *
 * Interface de gestion des clés API ETHAN, branchée UNIQUEMENT sur le
 * backend réel /v1/api-keys :créé en phase API Keys.
 *   - liste des clés sans secret :jamais de key_hash, jamais de plaintext
 *   - création → le secret en clair n'est affiché QU'UNE SEULE FOIS, :à la
 *     fermeture de la fenêtre il est purgé du state local
 *   - nom + scopes :métadonnées réellement supportées par le Core
 *   - statut actif / révoqué
 *   - révocation avec confirmation :action sensible
 *
 * L'expiration n'est PAS affichée : le Core :create_key: ne l'expose pas
 * :politique « pas de capacité fantôme »: — aucun champ inventé.
 *
 * Aucune logique métier : délégation totale au Core :core/auth/api_keys.py:.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listApiKeys, createApiKey, revokeApiKey,
  type ApiKeyRecord, type ApiKeyCreateResult,
} from "@/lib/api/security";
import { useUIStore } from "@/store/ui.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { KeyRound, Plus, Trash2, Copy, Check, Loader2 } from "lucide-react";

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function ApiKeysManager() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);

  const { data: keys = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["api-keys"],
    queryFn: listApiKeys,
    retry: false,
  });

  // ── Création ──
  const [createOpen, setCreateOpen] = React.useState(false);
  const [createName, setCreateName] = React.useState("");
  const [createScopes, setCreateScopes] = React.useState("");
  const [createdKey, setCreatedKey] = React.useState<ApiKeyCreateResult | null>(null);
  const [copied, setCopied] = React.useState(false);

  const createMutation = useMutation({
    mutationFn: () => createApiKey({ name: createName.trim(), scopes: createScopes.split(",").map((s) => s.trim()).filter(Boolean) }),
    onSuccess: (result) => {
      setCreateOpen(false);
      setCreateName("");
      setCreateScopes("");
      setCreatedKey(result);
      setCopied(false);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur création" }),
  });

  // ── Révocation :avec confirmation: ──
  const [revokeTarget, setRevokeTarget] = React.useState<ApiKeyRecord | null>(null);
  const revokeMutation = useMutation({
    mutationFn: (id: string) => revokeApiKey(id),
    onSuccess: () => {
      addToast({ type: "success", message: "Clé API révoquée" });
      setRevokeTarget(null);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (e) => addToast({ type: "error", message: e instanceof Error ? e.message : "Erreur révocation" }),
  });

  const handleCopy = async () => {
    if (!createdKey?.key) return;
    try {
      await navigator.clipboard.writeText(createdKey.key);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      addToast({ type: "error", message: "Impossible de copier — copiez la clé manuellement." });
    }
  };

  return (
    <section className="rounded-lg border p-4" style={{ background: "var(--panel)", borderColor: "var(--border)" }}>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <KeyRound size={16} className="text-accent" />
          <h2 className="text-sm font-semibold">API Keys</h2>
        </div>
        <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
          <Plus size={14} className="mr-1" /> Créer une clé
        </Button>
      </div>

      <p className="mb-3 text-[11px] opacity-60">
        Clés d&apos;accès API ETHAN. Le secret complet n&apos;est affiché qu&apos;à la création.
        Actions sensibles journalisées dans l&apos;audit :catégorie SECURITY:.
      </p>

      {isLoading && (
        <div className="flex items-center justify-center p-6 text-xs opacity-60">
          <Loader2 size={14} className="mr-2 animate-spin" /> Chargement…
        </div>
      )}

      {isError && (
        <div className="flex items-center justify-between rounded-md border border-destructive/40 p-3 text-xs">
          <span className="text-destructive">Impossible de charger les clés API.</span>
          <Button size="sm" variant="outline" onClick={() => refetch()}>Réessayer</Button>
        </div>
      )}

      {!isLoading && !isError && keys.length === 0 && (
        <p className="rounded-md p-3 text-xs opacity-60" style={{ background: "var(--muted)" }}>
          Aucune clé API. Créez une clé pour permettre l&apos;accès programmatique.
        </p>
      )}

      {!isLoading && !isError && keys.length > 0 && (
        <div className="overflow-hidden rounded-md border" style={{ borderColor: "var(--border)" }}>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide opacity-50" style={{ background: "var(--muted)" }}>
                <th className="px-3 py-2 font-medium">Nom</th>
                <th className="px-3 py-2 font-medium">Scopes</th>
                <th className="px-3 py-2 font-medium">Statut</th>
                <th className="px-3 py-2 font-medium">Créée le</th>
                <th className="px-3 py-2 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td className="px-3 py-2 font-medium">{k.name}</td>
                  <td className="px-3 py-2 opacity-70">{k.scopes.length > 0 ? k.scopes.join(", ") : "—"}</td>
                  <td className="px-3 py-2">
                    <span className="rounded-full px-2 py-0.5 text-[11px]" style={{ background: k.active ? "var(--green-soft)" : "var(--muted)", color: k.active ? "var(--green)" : "inherit" }}>
                      {k.active ? "Active" : "Révoquée"}
                    </span>
                  </td>
                  <td className="px-3 py-2 opacity-70">{formatDate(k.created_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" disabled={!k.active} onClick={() => setRevokeTarget(k)} title={k.active ? "Révoquer la clé" : "Déjà révoquée"}>
                      <Trash2 size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Dialog de création ── */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Créer une clé API" size="sm">
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium" htmlFor="api-key-name">Nom</label>
            <Input id="api-key-name" placeholder="ex. CI, automation, cli" value={createName} onChange={(e) => setCreateName(e.target.value)} className="w-full" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium" htmlFor="api-key-scopes">Scopes <span className="opacity-50">:optionnel, séparés par des virgules:</span></label>
            <Input id="api-key-scopes" placeholder="ex. read, write" value={createScopes} onChange={(e) => setCreateScopes(e.target.value)} className="w-full" />
          </div>
          <p className="text-[11px] opacity-60">Le secret complet sera affiché une seule fois après la création.</p>
          <div className="flex justify-end gap-2 pt-1">
            <Button size="sm" variant="ghost" onClick={() => setCreateOpen(false)}>Annuler</Button>
            <Button size="sm" disabled={!createName.trim() || createMutation.isPending} onClick={() => createMutation.mutate()}>
              {createMutation.isPending ? "Création…" : "Créer"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* ── Affichage UNIQUE du secret :jamais réaffiché ensuite: ── */}
      <Dialog open={createdKey !== null} onClose={() => setCreatedKey(null)} title="Clé API créée — à copier maintenant" size="sm">
        <div className="space-y-4">
          <div className="rounded-md border border-destructive/40 p-3 text-xs" style={{ background: "var(--muted)" }}>
            <strong className="text-destructive">Cette clé ne sera plus jamais affichée.</strong> Si vous la perdez, vous devrez la révoquer et en créer une nouvelle.
          </div>
          <div className="flex items-center gap-2">
            <code className="min-w-0 flex-1 select-all rounded-md border px-3 py-2 text-xs break-all" style={{ background: "var(--muted)", borderColor: "var(--border)" }}>
              {createdKey?.key}
            </code>
            <Button size="sm" variant="outline" onClick={handleCopy} title="Copier la clé">{copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}</Button>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button size="sm" variant="ghost" onClick={() => setCreatedKey(null)}>Fermer</Button>
          </div>
        </div>
      </Dialog>

      {/* ── Confirmation de révocation ── */}
      <ConfirmDialog
        open={revokeTarget !== null}
        onOpenChange={(open) => { if (!open) setRevokeTarget(null); }}
        title="Révoquer la clé API"
        message={`La clé « ${revokeTarget?.name ?? ""} » sera immédiatement désactivée. Cette action est irréversible.`}
        confirmLabel="Révoquer"
        destructive
        onConfirm={() => revokeTarget && revokeMutation.mutate(revokeTarget.id)}
      />
    </section>
  );
}
