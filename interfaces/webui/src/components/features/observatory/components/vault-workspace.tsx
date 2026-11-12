"use client";

/**
 * Observatory — Vault (explorateur + éditeur Markdown).
 *
 * Architecture : le Core sert le contenu (lecture/écriture via les routes
 * Engineering Memory, Archives/ protégé). Le WebUI ne fait qu'afficher et
 * transmettre des intentions — aucune logique métier dans ce composant.
 */

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
	BookOpen,
	FolderTree,
	GitCommitHorizontal,
	Lock,
	Loader2,
	PanelLeftClose,
	PanelLeftOpen,
	Save,
	Search,
	Eye,
	PenLine,
	PanelRightOpen,
	PanelRightClose,
	AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui.store";
import {
	listVaultTree,
	readVaultFile,
	searchVault,
	listVaultBacklinks,
	resolveVaultWikilink,
	writeVaultFile,
} from "@/lib/api/observatory";
import { VaultTree } from "./vault-tree";
import { ObservatoryMarkdown } from "./observatory-markdown";
import { parseFrontmatter } from "./frontmatter";
import { DURATION, EASING, staggerStyle } from "@/lib/motion";

type Mode = "read" | "edit";

export function VaultWorkspace() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	// État de sélection, synchronisé avec ?path= via read/write localStorage-free.
	const [selectedPath, setSelectedPath] = React.useState<string | null>(() => {
		if (typeof window === "undefined") return null;
		return new URLSearchParams(window.location.search).get("path");
	});
	const [filter, setFilter] = React.useState("");
	const [searchQuery, setSearchQuery] = React.useState("");
	const [searchResults, setSearchResults] = React.useState<Array<{ path: string; line: number; snippet: string }>>([]);
	const [searching, setSearching] = React.useState(false);
	const [mode, setMode] = React.useState<Mode>("read");
	const [draft, setDraft] = React.useState("");
	const [dirty, setDirty] = React.useState(false);
	const [explorerWidth, setExplorerWidth] = React.useState(280);
	const [explorerCollapsed, setExplorerCollapsed] = React.useState(false);
	const [backlinksOpen, setBacklinksOpen] = React.useState(true);
	const [pendingNavigation, setPendingNavigation] = React.useState<string | null>(null);

	// Arborescence du vault (le Core décide de l'ordre et de l'organisation).
	const { data: tree, isLoading: treeLoading, error: treeError } = useQuery({
		queryKey: ["vault-tree"],
		queryFn: () => listVaultTree(),
		staleTime: 5 * 60_000,
		refetchOnWindowFocus: false,
	});

	// Contenu du fichier sélectionné.
	const { data: file, isLoading: fileLoading, error: fileError } = useQuery({
		queryKey: ["vault-file", selectedPath],
		queryFn: () => readVaultFile(selectedPath as string),
		enabled: !!selectedPath,
		staleTime: 30_000,
	});

	// Backlinks du document courant.
	const { data: backlinksData, isFetching: backlinksLoading, isError: backlinksError } = useQuery({
		queryKey: ["vault-backlinks", selectedPath],
		queryFn: () => listVaultBacklinks(selectedPath as string),
		enabled: !!selectedPath,
		staleTime: 60_000,
	});

	// Brouillon réinitialisé quand le fichier chargé change (pattern « adjust
	// state during render » : pas de setState dans un effet).
	const [lastLoadedKey, setLastLoadedKey] = React.useState<string | null>(null);
	const fileKey = file ? `${file.path}:${file.modified_at ?? file.content.length}` : null;
	if (file && fileKey !== lastLoadedKey) {
		setLastLoadedKey(fileKey);
		setDraft(file.content);
		setDirty(false);
	}

	const isArchive = React.useMemo(
		() => !!selectedPath && (selectedPath === "Archives" || selectedPath.startsWith("Archives/")),
		[selectedPath],
	);
	const canEdit = !!file && !isArchive && file.markdown;

	const saveMutation = useMutation({
		mutationFn: ({ path, content }: { path: string; content: string }) => writeVaultFile(path, content),
		onSuccess: (saved) => {
			addToast({ type: "success", message: `Document enregistré : ${saved.path}` });
			setDirty(false);
			queryClient.setQueryData(["vault-file", saved.path], saved);
			queryClient.invalidateQueries({ queryKey: ["vault-file", saved.path] });
		},
		onError: (err) => {
			addToast({ type: "error", message: err instanceof Error ? err.message : "Écriture refusée par le Core" });
		},
	});

	const navigate = React.useCallback((path: string | null) => {
		setSelectedPath(path);
		setMode("read");
		setDirty(false);
		const url = new URL(window.location.href);
		if (path) url.searchParams.set("path", path);
		else url.searchParams.delete("path");
		window.history.replaceState(null, "", url.toString());
	}, []);

	const navigateWithGuard = React.useCallback(
		(path: string | null) => {
			if (dirty) {
				setPendingNavigation(path);
				return;
			}
			navigate(path);
		},
		[dirty, navigate],
	);

	const handleWikilink = React.useCallback(
		async (raw: string) => {
			try {
				const res = await resolveVaultWikilink(raw);
				if (res.resolved) {
					navigateWithGuard(res.resolved);
				} else {
					addToast({ type: "info", message: `Wikilien non résolu : ${raw}` });
				}
			} catch {
				addToast({ type: "error", message: "Résolution du wikilien impossible" });
			}
		},
		[addToast, navigateWithGuard],
	);

	const runSearch = React.useCallback(async () => {
		const q = searchQuery.trim();
		if (!q) return;
		setSearching(true);
		try {
			const res = await searchVault(q, { limit: 30 });
			setSearchResults(res.hits);
		} catch (err) {
			setSearchResults([]);
			addToast({ type: "error", message: err instanceof Error ? err.message : "Recherche impossible" });
		} finally {
			setSearching(false);
		}
	}, [searchQuery, addToast]);

	// Redimensionnement du panneau explorateur par glisser-déposer.
	const dragState = React.useRef<{ startX: number; startWidth: number } | null>(null);
	const onDragStart = React.useCallback(
		(event: React.PointerEvent<HTMLDivElement>) => {
			event.preventDefault();
			dragState.current = { startX: event.clientX, startWidth: explorerWidth };

			const onMove = (ev: PointerEvent) => {
				if (!dragState.current) return;
				const next = dragState.current.startWidth + (ev.clientX - dragState.current.startX);
				setExplorerWidth(Math.min(480, Math.max(180, next)));
			};
			const onUp = () => {
				dragState.current = null;
				window.removeEventListener("pointermove", onMove);
				window.removeEventListener("pointerup", onUp);
			};
			window.addEventListener("pointermove", onMove);
			window.addEventListener("pointerup", onUp);
		},
		[explorerWidth],
	);

	const frontmatter = file?.markdown ? parseFrontmatter(file.content) : { values: [] };
	const backlinks = backlinksData?.backlinks ?? [];

	return (
		<div className="flex h-full min-h-0 flex-col">
			{/* Bandeau de confirmation de navigation quand des modifications sont non sauvegardées */}
			{pendingNavigation !== null && (
				<div className="ethan-slide-down flex items-center gap-3 border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs text-amber-200">
					<AlertTriangle className="h-4 w-4 shrink-0" />
					Modifications non enregistrées. Quitter ce document ?
					<button type="button" className="ml-auto rounded border border-amber-500/40 px-2 py-1 hover:bg-amber-500/10" onClick={() => setPendingNavigation(null)}>
						Rester
					</button>
					<button type="button" className="rounded border border-red-500/40 px-2 py-1 text-red-300 hover:bg-red-500/10" onClick={() => { setPendingNavigation(null); navigate(pendingNavigation); }}>
						Quitter sans sauvegarder
					</button>
				</div>
			)}

			<div className="flex min-h-0 flex-1">
				{/* Explorateur — le repli est un changement d'état réel : on anime
				    l'entrée/sortie en opacité + translation (composited) plutôt que
				    la largeur, qui déclencherait un reflow à chaque frame. */}
				<AnimatePresence initial={false}>
					{!explorerCollapsed && (
					<motion.aside
						key="vault-explorer"
						initial={{ opacity: 0, x: -12 }}
						animate={{ opacity: 1, x: 0 }}
						exit={{ opacity: 0, x: -12 }}
						transition={{ duration: DURATION.fast, ease: EASING.standard }}
						className="flex min-h-0 shrink-0 flex-col border-r border-line-1 bg-bg-1"
						style={{ width: explorerWidth }}
						aria-label="Explorateur du vault"
					>
						<div className="flex items-center gap-2 border-b border-line-1 px-3 py-2">
							<FolderTree className="h-4 w-4 text-primary" />
							<span className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary">Explorer</span>
							<button type="button" className="ml-auto rounded p-1 text-foreground-tertiary hover:bg-bg-2" onClick={() => setExplorerCollapsed(true)} title="Réduire l'explorateur" aria-label="Réduire l'explorateur">
								<PanelLeftClose className="h-4 w-4" />
							</button>
						</div>

						<div className="border-b border-line-1 p-2">
							<div className="relative">
								<Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground-tertiary" />
								<input
									value={filter}
									onChange={(e) => setFilter(e.target.value)}
									placeholder="Filtrer l'arborescence…"
									aria-label="Filtrer les fichiers"
									className="h-8 w-full rounded-md border border-line-1 bg-bg-2 pl-8 pr-2 text-xs text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-1 focus:ring-primary/50"
								/>
							</div>
							{/* Recherche plein texte */}
							<div className="mt-2 flex gap-1.5">
								<input
									value={searchQuery}
									onChange={(e) => setSearchQuery(e.target.value)}
									onKeyDown={(e) => e.key === "Enter" && runSearch()}
									placeholder="Rechercher dans les documents…"
									aria-label="Recherche plein texte dans le vault"
									className="h-8 min-w-0 flex-1 rounded-md border border-line-1 bg-bg-2 pl-2 pr-2 text-xs text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-1 focus:ring-primary/50"
								/>
								<button type="button" onClick={runSearch} disabled={searching || !searchQuery.trim()} className="h-8 rounded-md border border-line-1 bg-bg-2 px-2 text-foreground-secondary transition-colors hover:text-foreground disabled:opacity-50" title="Rechercher" aria-label="Lancer la recherche">
									{searching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
								</button>
							</div>
							{searchResults.length > 0 && (
								<div className="ethan-slide-down mt-2 max-h-40 overflow-y-auto rounded-md border border-line-1 bg-bg-2">
									{searchResults.map((hit, i) => (
										<button key={`${hit.path}:${hit.line}:${i}`} type="button" onClick={() => navigateWithGuard(hit.path)} className="ethan-fade block w-full border-b border-line-1/50 px-2 py-1.5 text-left last:border-b-0 hover:bg-bg-1" style={staggerStyle(i, 18)}>
											<span className="block truncate text-[10px] font-medium text-primary">{hit.path}:{hit.line}</span>
											<span className="block truncate text-[10px] text-foreground-secondary">{hit.snippet}</span>
										</button>
									))}
								</div>
							)}
						</div>

						<div className="min-h-0 flex-1 overflow-y-auto p-1.5">
							{treeLoading && <TreeSkeleton />}
							{treeError && <p className="px-2 py-4 text-xs text-red-400">Arborescence indisponible : {String((treeError as Error).message)}</p>}
							{tree && <VaultTree tree={tree} selectedPath={selectedPath} onSelect={navigateWithGuard} filter={filter} />}
						</div>
					</motion.aside>
					)}
				</AnimatePresence>

				{/* Poignée de redimensionnement */}
				{!explorerCollapsed && (
					<div
						role="separator"
						aria-orientation="vertical"
						aria-label="Redimensionner l'explorateur"
						onPointerDown={onDragStart}
						className="w-1 shrink-0 cursor-col-resize bg-transparent transition-colors hover:bg-primary/40"
					/>
				)}

				{/* Panneau document */}
				<section className="flex min-h-0 min-w-0 flex-1 flex-col">
					{explorerCollapsed && (
						<div className="flex h-9 shrink-0 items-center border-b border-line-1 bg-bg-1 px-3">
							<button type="button" className="rounded p-1 text-foreground-tertiary hover:bg-bg-2" onClick={() => setExplorerCollapsed(false)} title="Ouvrir l'explorateur" aria-label="Ouvrir l'explorateur">
								<PanelLeftOpen className="h-4 w-4" />
							</button>
						</div>
					)}

					{!selectedPath && (
						<div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
							<BookOpen className="h-10 w-10 text-foreground-tertiary" aria-hidden />
							<h2 className="text-base font-semibold text-foreground">Selectionnez un document</h2>
							<p className="max-w-md text-xs text-foreground-tertiary">
								L&apos;arborescence préserve l&apos;organisation d&apos;origine du vault (daena/) — aucun fichier n&apos;est déplacé ni réécrit.
							</p>
						</div>
					)}

					{selectedPath && fileLoading && <div className="flex flex-1 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Chargement du document" /></div>}
					{selectedPath && fileError && (
						<div className="m-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
							Lecture impossible : {String((fileError as Error).message)}
						</div>
					)}

					{file && (
						<>
							{/* Barre de titre du document */}
							<div className="flex h-11 shrink-0 items-center gap-2 border-b border-line-1 bg-bg-1 px-3">
								<div className="min-w-0">
									<p className="truncate text-[13px] font-semibold text-foreground" title={file.path}>{file.name}</p>
									<p className="truncate text-[10px] text-foreground-tertiary">{file.path}</p>
								</div>
								{isArchive && (
									<span className="ml-2 inline-flex items-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-300" title="Les archives brutes sont immutables via l'interface">
										<Lock className="h-3 w-3" /> Archive
									</span>
								)}
								<div className="ml-auto flex items-center gap-1">
									{canEdit && (
										<div role="tablist" aria-label="Mode d'affichage" className="flex rounded-md border border-line-1 bg-bg-2 p-0.5">
											<button role="tab" aria-selected={mode === "read"} type="button" onClick={() => setMode("read")} className={cn("flex items-center gap-1 rounded px-2 py-1 text-[11px]", mode === "read" ? "bg-bg-1 text-primary shadow-sm" : "text-foreground-secondary")}>
												<Eye className="h-3.5 w-3.5" /> Lire
											</button>
											<button role="tab" aria-selected={mode === "edit"} type="button" onClick={() => setMode("edit")} className={cn("flex items-center gap-1 rounded px-2 py-1 text-[11px]", mode === "edit" ? "bg-bg-1 text-primary shadow-sm" : "text-foreground-secondary")}>
												<PenLine className="h-3.5 w-3.5" /> Éditer
											</button>
										</div>
									)}
									{mode === "edit" && dirty && (
										<button type="button" onClick={() => saveMutation.mutate({ path: file.path, content: draft })} disabled={saveMutation.isPending} className="flex items-center gap-1 rounded-md border border-primary/40 bg-primary/15 px-2 py-1 text-[11px] font-medium text-primary hover:bg-primary/25 disabled:opacity-50">
											{saveMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Enregistrer
										</button>
									)}
									<button type="button" onClick={() => setBacklinksOpen((v) => !v)} className="rounded p-1.5 text-foreground-tertiary hover:bg-bg-2 hover:text-foreground" title={backlinksOpen ? "Masquer l'encart latéral" : "Afficher l'encart latéral"} aria-label="Basculer l'encart latéral">
										{backlinksOpen ? <PanelRightClose className="h-4 w-4" /> : <PanelRightOpen className="h-4 w-4" />}
									</button>
								</div>
							</div>

							<div className="flex min-h-0 flex-1">
								{/* Corps : lecture ou édition */}
								<div className="min-h-0 min-w-0 flex-1 overflow-auto">
									{mode === "read" ? (
										file.markdown ? (
											<div className="p-5"><ObservatoryMarkdown content={file.content} onWikilink={handleWikilink} /></div>
										) : (
											<pre className="p-4 font-mono text-xs leading-relaxed text-foreground-secondary">{file.content}</pre>
										)
									) : (
										<textarea
											value={draft}
											onChange={(e) => { setDraft(e.target.value); setDirty(true); }}
											spellCheck={false}
											aria-label="Éditeur Markdown"
											className="h-full min-h-[24rem] w-full resize-none bg-bg-2 p-4 font-mono text-[12.5px] leading-relaxed text-foreground focus:outline-none"
										/>
									)}
								</div>

								{/* Encart : propriétés + backlinks */}
								{backlinksOpen && (
									<aside className="hidden w-72 shrink-0 flex-col border-l border-line-1 bg-bg-1 md:flex" aria-label="Propriétés et renvois du document">
										<div className="border-b border-line-1 p-3">
											<h3 className="text-[10px] font-semibold uppercase tracking-wider text-foreground-tertiary">Propriétés</h3>
											{frontmatter.values.length === 0 ? (
												<p className="mt-1.5 text-[11px] text-foreground-tertiary">Aucune métadonnée YAML.</p>
											) : (
												<dl className="mt-1.5 space-y-1">
													{frontmatter.values.map(({ key, value }) => (
														<div key={key} className="flex items-baseline justify-between gap-2 rounded bg-bg-2 px-2 py-1">
															<dt className="shrink-0 font-mono text-[10px] text-foreground-tertiary">{key}</dt>
															<dd className="truncate text-[11px] text-foreground-secondary" title={value}>{value}</dd>
														</div>
													))}
												</dl>
											)}
										</div>
										<div className="min-h-0 flex-1 overflow-y-auto p-3">
											<h3 className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-foreground-tertiary">
												<GitCommitHorizontal className="h-3.5 w-3.5" /> Référencé par
												{backlinksLoading && <Loader2 className="h-3 w-3 animate-spin" aria-hidden />}
											</h3>
											{backlinksError && <p className="mt-1.5 text-[11px] text-red-400">Backlinks indisponibles.</p>}
											{!backlinksLoading && backlinks.length === 0 && <p className="mt-1.5 text-[11px] text-foreground-tertiary">Aucune référence entrante.</p>}
											<ul className="mt-1.5 space-y-1.5">
												{backlinks.map((link) => (
													<li key={link.path}>
														<button type="button" onClick={() => navigateWithGuard(link.path)} className="w-full rounded-md border border-line-1 bg-bg-2 px-2 py-1.5 text-left transition-colors hover:border-primary/40">
															<span className="block truncate text-[11px] font-medium text-primary">{link.name}</span>
															{link.excerpts.slice(0, 1).map((excerpt, i) => (
																<span key={i} className="mt-0.5 block truncate text-[10px] text-foreground-tertiary">{excerpt}</span>
															))}
														</button>
													</li>
												))}
											</ul>
										</div>
									</aside>
								)}
							</div>

							{/* Pied de page métadonnées */}
							<div className="flex h-8 shrink-0 items-center gap-3 border-t border-line-1 bg-bg-1 px-3 text-[10px] text-foreground-tertiary">
								<span>{file.line_count} lignes</span>
								<span>{(file.size_bytes ?? 0) / 1024 >= 1 ? `${((file.size_bytes ?? 0) / 1024).toFixed(1)} Ko` : `${file.size_bytes ?? 0} o`}</span>
								<span className="truncate">modifié {file.modified_at ? new Date(file.modified_at).toLocaleString() : "—"}</span>
								<span className="ml-auto hidden sm:inline">{file.markdown ? "Markdown" : (file.extension ?? "").toUpperCase()}</span>
							</div>
						</>
					)}
				</section>
			</div>
		</div>
	);
}

function TreeSkeleton() {
	return (
		<div className="space-y-1 p-1">
			{[72, 96, 60, 88, 64, 100, 76].map((w, i) => (
				<div key={i} className="h-5 animate-pulse rounded bg-bg-2" style={{ width: w }} />
			))}
		</div>
	);
}
