"use client";

/**
 * AuditExplorer — consultation du journal d'audit ETHAN.
 *
 * Connexion réelle : GET /internal/audit/search (core/audit/store.py:AuditStore).
 * Politique UX : liste → détail dans une modale (recherche ponctuelle, pas une
 * supervision continue → pas de drawer ni de page dédiée).
 *
 * Contraintes API assumées honnêtement :
 *  - `q` est obligatoire (≥ 1 caractère) → la liste exige une recherche ;
 *  - le serveur plafonne à 20 entrées par recherche → les filtres
 *    (catégorie, décision) et la pagination sont CLIENT-side et annoncés
 *    comme tels. Aucune pagination serveur n'est simulée.
 *
 * AGENTS.md : lecture seule, aucune logique d'audit ici — le Core journalise.
 */

import * as React from "react";
import { Search, ShieldCheck, ChevronLeft, ChevronRight } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import {
  searchAuditEvents,
  type AuditEvent,
} from "@/lib/api/security";

const PAGE_SIZE = 10;

/** Couleur de badge par décision (vocabulaire complet d'AuditDecision). */
function decisionClass(decision: string): string {
  switch (decision) {
    case "allowed":
    case "approved":
      return "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/40";
    case "denied":
    case "rejected":
    case "error":
    case "timeout":
      return "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/40";
    case "pending":
      return "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/40";
    default:
      return "bg-elevated text-foreground-secondary border-line-2";
  }
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export function AuditExplorer() {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<AuditEvent[] | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = React.useState("all");
  const [decisionFilter, setDecisionFilter] = React.useState("all");
  const [page, setPage] = React.useState(0);
  const [selected, setSelected] = React.useState<AuditEvent | null>(null);

  const filtered = React.useMemo(() => {
    if (!results) return [];
    return results.filter(
      (e) =>
        (categoryFilter === "all" || e.category === categoryFilter) &&
        (decisionFilter === "all" || e.decision === decisionFilter),
    );
  }, [results, categoryFilter, decisionFilter]);

  // Options de filtre dérivées du lot reçu : seules les catégories et
  // décisions réellement présentes sont proposées (pas de hard-code).
  const categories = React.useMemo(
    () => [...new Set((results ?? []).map((e) => e.category))].sort(),
    [results],
  );
  const decisions = React.useMemo(
    () => [...new Set((results ?? []).map((e) => e.decision))].sort(),
    [results],
  );

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const rows = filtered.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  // Reset de la pagination dès que les résultats ou filtres changent.
  React.useEffect(() => setPage(0), [categoryFilter, decisionFilter, results]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      setError("Saisissez au moins un caractère à rechercher.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const events = await searchAuditEvents(q);
      setResults(events);
      setCategoryFilter("all");
      setDecisionFilter("all");
    } catch (err) {
      setResults(null);
      setError(
        err instanceof Error
          ? `Recherche impossible : ${err.message}`
          : "Recherche impossible : erreur inconnue.",
      );
    } finally {
      setLoading(false);
    }
  };

  const filtersDisabled = !results || results.length === 0;

  return (
    <section
      className="rounded-lg border p-4"
      style={{ background: "var(--panel)", borderColor: "var(--border)" }}
    >
      <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold">
        <ShieldCheck size={15} /> Journal d&apos;audit
      </h2>
      <p className="mb-3 text-xs opacity-60">
        Consultation lecture seule — append-only, écrit par le Core. Le serveur
        limite chaque recherche à 20 résultats ; filtres et pagination sont
        appliqués localement sur ce lot.
      </p>

      {/* Recherche */}
      <form onSubmit={handleSearch} className="mb-3 flex gap-2" role="search">
        <div className="relative flex-1">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 opacity-40"
          />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher (action, acteur, source, détails…)"
            aria-label="Recherche dans le journal d'audit"
            className="w-full rounded-md border bg-transparent py-1.5 pl-8 pr-3 text-sm outline-none focus:ring-1 focus:ring-accent-400"
            style={{ borderColor: "var(--border)" }}
          />
        </div>
        <Button type="submit" size="sm" disabled={loading}>
          {loading ? <Spinner className="h-3.5 w-3.5" /> : "Rechercher"}
        </Button>
      </form>

      {/* Filtres (client-side, sur le lot serveur) */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select
          aria-label="Filtrer par catégorie"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          disabled={filtersDisabled}
          className="rounded-md border bg-transparent px-2 py-1 text-xs disabled:opacity-40"
          style={{ borderColor: "var(--border)" }}
        >
          <option value="all">Catégorie : toutes</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          aria-label="Filtrer par décision"
          value={decisionFilter}
          onChange={(e) => setDecisionFilter(e.target.value)}
          disabled={filtersDisabled}
          className="rounded-md border bg-transparent px-2 py-1 text-xs disabled:opacity-40"
          style={{ borderColor: "var(--border)" }}
        >
          <option value="all">Décision : toutes</option>
          {decisions.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        {results && (
          <span className="ml-auto text-[11px] opacity-60">
            {filtered.length} / {results.length} événement(s)
            {results.length >= 20 && " — lot serveur saturé (20 max)"}
          </span>
        )}
      </div>

      {/* États : erreur, avant recherche, vide */}
      {error && (
        <p className="rounded-md border border-red-500/40 bg-red-500/5 px-3 py-2 text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      {!error && !results && !loading && (
        <p className="py-6 text-center text-xs opacity-50">
          Saisissez une recherche pour consulter le journal d&apos;audit.
        </p>
      )}

      {results && filtered.length === 0 && (
        <p className="py-6 text-center text-xs opacity-50">
          Aucun événement d&apos;audit ne correspond
          {categoryFilter !== "all" || decisionFilter !== "all"
            ? " à ces critères sur ce lot."
            : "."}
        </p>
      )}

      <AuditResults
        rows={rows}
        filteredCount={filtered.length}
        pageCount={pageCount}
        page={safePage}
        onPageChange={setPage}
        onSelect={setSelected}
      />

      {/* Détail d'un événement (modale, politique UX liste → détail) */}
      <Dialog
        open={selected !== null}
        onClose={() => setSelected(null)}
        title="Événement d'audit"
      >
        {selected && <AuditEventDetails event={selected} />}
      </Dialog>
    </section>
  );
}

/** Liste paginée des résultats (10/page, pagination locale). */
function AuditResults({
  rows,
  filteredCount,
  pageCount,
  page,
  onPageChange,
  onSelect,
}: {
  rows: AuditEvent[];
  filteredCount: number;
  pageCount: number;
  page: number;
  onPageChange: (p: number) => void;
  onSelect: (ev: AuditEvent) => void;
}) {
  if (filteredCount === 0) return null;

  return (
    <>
      <ul className="divide-y" style={{ borderColor: "var(--border)" }}>
        {rows.map((ev) => (
          <li key={ev.id}>
            <button
              type="button"
              onClick={() => onSelect(ev)}
              className="flex w-full items-center gap-3 px-1 py-2 text-left text-xs hover:bg-elevated transition-colors"
            >
              <span className="w-40 shrink-0 opacity-60 tabular-nums">
                {formatDate(ev.timestamp)}
              </span>
              <span
                className={cn(
                  "shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium",
                  decisionClass(ev.decision),
                )}
              >
                {ev.decision}
              </span>
              <span className="shrink-0 rounded bg-elevated px-1.5 py-0.5 text-[10px] opacity-70">
                {ev.category}
              </span>
              <span className="min-w-0 flex-1 truncate font-medium">
                {ev.action || "(sans action)"}
              </span>
              <span className="shrink-0 opacity-60">{ev.actor}</span>
            </button>
          </li>
        ))}
      </ul>

      {pageCount > 1 && (
        <div className="mt-2 flex items-center justify-end gap-2 text-xs">
          <Button
            variant="ghost"
            size="sm"
            disabled={page === 0}
            onClick={() => onPageChange(page - 1)}
            aria-label="Page précédente"
          >
            <ChevronLeft size={14} />
          </Button>
          <span className="tabular-nums opacity-60">
            {page + 1} / {pageCount}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={page >= pageCount - 1}
            onClick={() => onPageChange(page + 1)}
            aria-label="Page suivante"
          >
            <ChevronRight size={14} />
          </Button>
        </div>
      )}
    </>
  );
}

/** Détail complet d'un événement (rendu dans la modale). */
function AuditEventDetails({ event }: { event: AuditEvent }) {
  return (
    <div className="space-y-3 text-xs">
      <div className="grid grid-cols-[100px_1fr] items-start gap-x-3 gap-y-2">
        <span className="opacity-60">ID</span>
        <span className="font-mono">{event.id}</span>
        <span className="opacity-60">Horodatage</span>
        <span>{formatDate(event.timestamp)}</span>
        <span className="opacity-60">Catégorie</span>
        <span>
          <span className="rounded bg-elevated px-1.5 py-0.5">{event.category}</span>
        </span>
        <span className="opacity-60">Décision</span>
        <span>
          <span
            className={cn(
              "rounded border px-1.5 py-0.5 font-medium",
              decisionClass(event.decision),
            )}
          >
            {event.decision}
          </span>
        </span>
        <span className="opacity-60">Action</span>
        <span className="break-words">{event.action || "—"}</span>
        <span className="opacity-60">Acteur</span>
        <span>{event.actor}</span>
        <span className="opacity-60">Source</span>
        <span>{event.source}</span>
        {event.correlation_id && (
          <>
            <span className="opacity-60">Corrélation</span>
            <span className="break-all font-mono">{event.correlation_id}</span>
          </>
        )}
        {event.tags && event.tags.length > 0 && (
          <>
            <span className="opacity-60">Tags</span>
            <span className="flex flex-wrap gap-1">
              {event.tags.map((t) => (
                <span key={t} className="rounded bg-elevated px-1.5 py-0.5">
                  {t}
                </span>
              ))}
            </span>
          </>
        )}
      </div>

      <div>
        <span className="mb-1 block opacity-60">Détails</span>
        <pre className="max-h-48 overflow-auto rounded-md bg-elevated p-2 font-mono text-[10px]">
          {JSON.stringify(event.details ?? {}, null, 2)}
        </pre>
      </div>
    </div>
  );
}