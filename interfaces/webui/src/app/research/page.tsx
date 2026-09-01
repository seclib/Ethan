"use client";

/**
 * Page Deep Research — recherche multi-étapes sourcée (RFC-0002).
 * Orchestration dans ETHAN Core (LLM par défaut + tool web_search) ;
 * la page soumet la requête et rend le rapport.
 */

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { runResearch, type ResearchResult } from "@/lib/api/extensions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Telescope, Loader2 } from "lucide-react";

export default function ResearchPage() {
  const [query, setQuery] = React.useState("");
  const [depth, setDepth] = React.useState(2);
  const [result, setResult] = React.useState<ResearchResult | null>(null);

  const research = useMutation({
    mutationFn: () => runResearch(query.trim(), depth),
    onSuccess: setResult,
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !research.isPending) research.mutate();
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)" }}>
        <h1 style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 18, color: "var(--fg)" }}>
          <Telescope size={18} /> Deep Research
        </h1>
        <p style={{ fontSize: 12, opacity: 0.7 }}>
          Recherche approfondie : plan → recherche web → synthèse sourcée.
        </p>
      </header>

      <form onSubmit={submit} style={{ display: "flex", gap: 8, padding: "16px 24px" }}>
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Votre question de recherche…"
          style={{ flex: 1 }}
        />
        <select
          value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
          className="h-10 rounded-[var(--radius-sm)] border border-line-2 bg-background px-3 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
          style={{ width: 130 }}
          aria-label="Profondeur"
        >
          <option value={1}>Rapide</option>
          <option value={2}>Standard</option>
          <option value={3}>Approfondie</option>
          <option value={4}>Exhaustive</option>
        </select>
        <Button type="submit" disabled={!query.trim() || research.isPending} style={{ gap: 6 }}>
          {research.isPending ? <Loader2 className="animate-spin" size={14} /> : null}
          Lancer
        </Button>
      </form>

      <div className="custom-scrollbar" style={{ flex: 1, overflowY: "auto", padding: "0 24px 24px" }}>
        {research.isError && (
          <p style={{ color: "var(--red)", fontSize: 13 }}>
            Échec : {(research.error as Error)?.message ?? "erreur inconnue"}
          </p>
        )}

        {result && (
          <>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "12px 0 20px" }}>
              {result.steps.map((s) => (
                <span key={s.step} style={{ fontSize: 11, border: "1px solid var(--border)", borderRadius: 999, padding: "3px 10px" }}>
                  Étape {s.step} · « {s.query} » · {s.sources_found} source(s)
                </span>
              ))}
            </div>
            <article
              className="panel markdown-body"
              style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 20, maxWidth: 860, fontSize: 13.5, lineHeight: 1.65, whiteSpace: "pre-wrap", fontFamily: "inherit" }}
            >
              {result.report}
            </article>
            {result.sources.length > 0 && (
              <section style={{ marginTop: 20, maxWidth: 860 }}>
                <h3 style={{ fontSize: 13, opacity: 0.7 }}>Sources ({result.sources.length})</h3>
                <ul style={{ fontSize: 12, lineHeight: 1.7 }}>
                  {result.sources.map((s, i) => (
                    <li key={i}>
                      {s.url ? <a href={s.url} target="_blank" rel="noreferrer" style={{ color: "var(--accent)" }}>{s.title || s.url}</a> : s.title}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}