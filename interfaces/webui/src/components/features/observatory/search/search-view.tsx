"use client";

/**
 * Observatory — Search (recherche unifiée).
 *
 * Deux moteurs réels, jamais réimplémentés :
 *  - Plein texte du vault de documents (GET /v1/memory/vault/search, Core)
 *  - Recherche unifiée ETHAN (GET /v1/search?type=knowledge|conversation|library, Core)
 * Aucun résultat n'est inventé : chaque hit pointe vers sa source ou
 * s'affiche tel quel avec ses métadonnées.
 */

import * as React from "react";
import Link from "next/link";
import { Search, FileText, Database, MessagesSquare, Library, Loader2 } from "lucide-react";
import { search, type SearchType, type SearchResult } from "@/lib/api/search";
import { searchVault, type VaultSearchHit } from "@/lib/api/observatory";
import { cn } from "@/lib/utils";

type Mode = "vault" | SearchType;

const MODES: Array<{ id: Mode; label: string; icon: React.ComponentType<{ className?: string }> }> = [
	{ id: "vault", label: "Documents", icon: FileText },
	{ id: "knowledge", label: "Knowledge", icon: Database },
	{ id: "conversation", label: "Conversations", icon: MessagesSquare },
	{ id: "library", label: "Library", icon: Library },
];

const DEBOUNCE_MS = 350;

export function SearchView() {
	const [mode, setMode] = React.useState<Mode>("vault");
	const [query, setQuery] = React.useState("");
	const [loading, setLoading] = React.useState(false);
	const [error, setError] = React.useState<string | null>(null);
	const [vaultHits, setVaultHits] = React.useState<VaultSearchHit[]>([]);
	const [unifiedResults, setUnifiedResults] = React.useState<SearchResult[]>([]);
	const [searched, setSearched] = React.useState(false);

	const run = React.useCallback(async (q: string, currentMode: Mode) => {
		const needle = q.trim();
		if (!needle) return;
		setLoading(true);
		setError(null);
		try {
			if (currentMode === "vault") {
				const res = await searchVault(needle, { limit: 40 });
				setVaultHits(res.hits);
				setUnifiedResults([]);
			} else {
				const res = await search(needle, currentMode, 20);
				setUnifiedResults(res.results ?? []);
				setVaultHits([]);
			}
			setSearched(true);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Recherche impossible");
			setVaultHits([]);
			setUnifiedResults([]);
		} finally {
			setLoading(false);
		}
	}, []);

	// Recherche débouncée.
	React.useEffect(() => {
		if (!query.trim()) return;
		const handle = window.setTimeout(() => run(query, mode), DEBOUNCE_MS);
		return () => window.clearTimeout(handle);
	}, [query, mode, run]);

	const submitImmediate = () => {
		if (query.trim()) run(query, mode);
	};

	return (
		<div className="flex h-full min-h-0 flex-col bg-bg-1">
			<div className="border-b border-line-1 px-5 py-4">
				<h1 className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em] text-foreground-secondary">
					<Search className="h-4 w-4 text-primary" /> Recherche unifiée
				</h1>
				<p className="mt-0.5 text-[11px] text-foreground-tertiary">
					Plein texte du vault documentaire + moteurs ETHAN. Les résultats pointent vers leur source.
				</p>
				<div className="mt-3 flex flex-wrap items-center gap-2">
					<div className="flex min-w-0 flex-1 gap-2">
						<input
							autoFocus
							value={query}
							onChange={(e) => setQuery(e.target.value)}
							onKeyDown={(e) => e.key === "Enter" && submitImmediate()}
							placeholder="Rechercher une décision, un ADR, un composant…"
							aria-label="Requête de recherche"
							className="h-11 w-full rounded-lg border border-line-1 bg-bg-2 px-4 text-sm text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary/40"
						/>
						<button
							type="button"
							onClick={submitImmediate}
							disabled={loading || !query.trim()}
							className="flex h-11 shrink-0 items-center gap-2 rounded-lg border border-primary/40 bg-primary/15 px-4 text-sm font-medium text-primary transition-colors hover:bg-primary/25 disabled:opacity-50"
						>
							{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
							Rechercher
						</button>
					</div>
				</div>
				<div role="tablist" aria-label="Source de recherche" className="mt-3 flex flex-wrap gap-1.5">
					{MODES.map(({ id, label, icon: Icon }) => (
						<button
							key={id}
							role="tab"
							aria-selected={mode === id}
							type="button"
							onClick={() => setMode(id)}
							className={cn(
								"flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-medium transition-colors",
								mode === id
									? "border-primary/50 bg-primary/15 text-primary"
									: "border-line-1 bg-bg-2 text-foreground-secondary hover:text-foreground",
							)}
						>
							<Icon className="h-3.5 w-3.5" /> {label}
						</button>
					))}
				</div>
			</div>

			<div className="min-h-0 flex-1 overflow-y-auto p-5">
				{error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-300">{error}</p>}

				{!searched && !loading && (
					<p className="mx-auto max-w-md py-16 text-center text-xs text-foreground-tertiary">
						Saisissez une requête. Les résultats Documents listent les fichiers du vault
						avec ligne et extrait ; les autres utilisent le moteur de recherche ETHAN.
					</p>
				)}

				{searched && !loading && vaultHits.length === 0 && unifiedResults.length === 0 && !error && (
					<p className="py-10 text-center text-xs text-foreground-tertiary">Aucun résultat.</p>
				)}

				{vaultHits.length > 0 && (
					<ul className="space-y-1.5">
						{vaultHits.map((hit, i) => (
							<li key={`${hit.path}:${hit.line}:${i}`}>
								<Link
									href={`/workspaces/observatory/vault?path=${encodeURIComponent(hit.path)}`}
									className="block rounded-lg border border-line-1 bg-bg-2 px-3 py-2 transition-colors hover:border-primary/40"
								>
									<span className="block truncate font-mono text-[10px] text-primary">{hit.path}:{hit.line}</span>
									<span className="mt-0.5 block truncate text-[12px] text-foreground-secondary">{hit.snippet}</span>
								</Link>
							</li>
						))}
					</ul>
				)}

				{unifiedResults.length > 0 && (
					<ul className="space-y-1.5">
						{unifiedResults.map((result, i) => (
							<li key={`${result.id ?? i}`} className="rounded-lg border border-line-1 bg-bg-2 px-3 py-2">
								<div className="flex flex-wrap items-baseline gap-2">
									<span className="min-w-0 flex-1 truncate text-[12.5px] font-medium text-foreground">{result.title || result.id}</span>
									{typeof result.score === "number" && (
										<span className="shrink-0 font-mono text-[10px] text-foreground-tertiary">score {result.score.toFixed(2)}</span>
									)}
								</div>
								{result.content && <p className="mt-1 line-clamp-2 text-[11px] text-foreground-secondary">{result.content}</p>}
								<p className="mt-1 text-[9.5px] uppercase tracking-wide text-foreground-tertiary">{result.type}{result.source ? ` · ${result.source}` : ""}</p>
							</li>
						))}
					</ul>
				)}
			</div>
		</div>
	);
}
