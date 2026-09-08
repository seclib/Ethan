"use client";

/**
 * RagCollectionsView — toutes les RAG Collections, avec pour chacune :
 * configuration réelle (stratégie, embedding), statut d'indexation et
 * réindexation à la demande.
 *
 * Lecture/écriture via les endpoints Core (/v1/knowledge/collections,
 * /v1/rag/config, reindex).  Aucune logique métier locale.
 */

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Database, RefreshCw, Loader2, CheckCircle2, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useUIStore } from "@/store/ui.store";
import { listCollectionTree, reindexCollection, type KnowledgeCollectionTree } from "@/lib/api/knowledge";
import {
  getRagConfig, getRagStrategies, type RagStrategyOption,
} from "@/lib/api/rag";

function flatten(nodes: KnowledgeCollectionTree[]): KnowledgeCollectionTree[] {
  return nodes.flatMap((n) => [n, ...flatten(n.children)]);
}

export function RagCollectionsView() {
  const addToast = useUIStore((s) => s.addToast);
  const queryClient = useQueryClient();
  const [reindexingId, setReindexingId] = React.useState<string | null>(null);

  // ── (SUITE) ────────────────────────────────────────────────────────────
  const { data: tree = [], isLoading } = useQuery<KnowledgeCollectionTree[]>({
    queryKey: ["knowledge-collections-tree"],
    queryFn: () => listCollectionTree(),
  });
  const { data: ragConfig } = useQuery({
    queryKey: ["rag-config"],
    queryFn: () => getRagConfig(),
  });
  const { data: strategiesData } = useQuery({
    queryKey: ["rag-strategies"],
    queryFn: () => getRagStrategies(),
    staleTime: 300_000,
  });
  const strategies: RagStrategyOption[] = strategiesData?.strategies ?? [];
  const collections = flatten(tree);

  const onReindex = async (id: string) => {
    setReindexingId(id);
    try {
      const res = await reindexCollection(id);
      queryClient.invalidateQueries({ queryKey: ["knowledge-collections-tree"] });
      queryClient.invalidateQueries({ queryKey: ["rag-config"] });
      addToast({
        type: res.errors.length ? "warning" : "success",
        message: `Réindexation : ${res.reindexed}/${res.documents} document(s)${res.errors.length ? ` · ${res.errors.length} erreur(s)` : ""}`,
      });
    } catch (err) {
      addToast({ type: "error", message: err instanceof Error ? err.message : "Réindexation échouée" });
    } finally {
      setReindexingId(null);
    }
  };

  if (isLoading) return <div className="py-10 flex justify-center"><Spinner /></div>;

  return (
    <div className="p-2 space-y-4">
      <div className="rounded-lg border border-line-1 bg-bg-1/40 p-3 flex flex-wrap gap-x-6 text-sm">
        <span className="text-foreground-secondary"><span className="font-semibold text-foreground">{ragConfig?.stats.documents ?? 0}</span> documents RAG</span>
        <span className="text-foreground-secondary"><span className="font-semibold text-foreground">{ragConfig?.stats.chunks ?? 0}</span> chunks indexés</span>
        <span className="text-foreground-secondary">
          Embedding : <span className="font-mono text-xs text-foreground">{ragConfig?.stats.embedding_model || (ragConfig?.stats.embedding_mode === "llm" ? "LLM" : "fallback textuel")}</span>
        </span>
        <span className="text-foreground-secondary">
          Stratégie globale : <span className="font-medium text-foreground">{ragConfig?.config.strategy || "auto"}</span>
        </span>
      </div>

      {/* ── (TABLE) ─────────────────────────────────────────────────────── */}
      {collections.length === 0 ? (
        <p className="px-3 py-6 text-sm text-foreground-tertiary">
          Aucune RAG Collection. Créez-en une (nouvelle collection) ou importez du contenu via Web Import.
        </p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wider text-foreground-tertiary border-b border-line-1">
              <th className="py-2 pr-3">Collection</th>
              <th className="py-2 pr-3">Stratégie</th>
              <th className="py-2 pr-3">Statut</th>
              <th className="py-2 pr-3">Config</th>
              <th className="py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line-1">
            {collections.map((c) => (
              <tr key={c.id} className="hover:bg-bg-2/30">
                <td className="py-2 pr-3">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-foreground-tertiary" />
                    <div className="min-w-0">
                      <p className="truncate font-medium text-foreground">{c.name}</p>
                      <p className="truncate text-[11px] text-foreground-tertiary">
                        {c.document_ids.length} doc{c.document_ids.length > 1 ? "s" : ""}{c.description ? ` · ${c.description}` : ""}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="py-2 pr-3">
                  <span className="rounded-full bg-bg-2 px-2 py-0.5 text-[11px] text-foreground-secondary">
                    {c.retrieval_strategy || (ragConfig?.config.strategy ?? "auto")}
                  </span>
                </td>
                <td className="py-2 pr-3">
                  {(c.document_ids.length ?? 0) > 0 ? (
                    <span className="inline-flex items-center gap-1 text-[12px] text-green-600">
                      <CheckCircle2 className="h-3.5 w-3.5" /> indexée
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[12px] text-foreground-tertiary">
                      <AlertTriangle className="h-3.5 w-3.5" /> vide
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3 text-[11px] text-foreground-tertiary">
                  {strategyLabel(c, strategies)}
                </td>
                <td className="py-2 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onReindex(c.id)}
                    disabled={reindexingId === c.id || (c.document_ids.length ?? 0) === 0}
                    title="Ré-indexer les documents (rechunk + ré-embed)"
                  >
                    {reindexingId === c.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                    Réindexer
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="text-[11px] text-foreground-tertiary">
        La réindexation s'applique au modèle d'embedding courant du moteur. Les noms de collections et leur organisation restent libres.
      </p>
    </div>
  );
}

function strategyLabel(
  c: KnowledgeCollectionTree,
  strategies: RagStrategyOption[],
): string {
  const id = c.retrieval_strategy;
  if (id) return strategies.find((s) => s.id === id)?.label ?? id;
  return "héritée (défaut moteur)";
}