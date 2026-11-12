"use client";

/**
 * Observatory — Graph (graphe de connaissances interactif).
 *
 * Données : GET /v1/memory/vault/graph (wikiliens résolus côté Core).
 * Rendu SVG maison, sans dépendance graphe : pan/zoom, glisser-déposer des
 * nœuds, surlignage des voisins, filtre par dossier de premier niveau.
 */

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { GitBranch, Loader2, Search, X, MousePointer2, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { getVaultGraph, type VaultGraphNode } from "@/lib/api/observatory";
import { layoutGraph } from "./layout";

const WIDTH = 900;
const HEIGHT = 620;

function topFolder(path: string): string {
	const idx = path.indexOf("/");
	return idx === -1 ? "(racine)" : path.slice(0, idx);
}

export function GraphView() {
	const router = useRouter();
	const { data, isLoading, isError, error } = useQuery({
		queryKey: ["vault-graph"],
		queryFn: () => getVaultGraph(150),
		staleTime: 5 * 60_000,
	});

	const nodes = React.useMemo(() => data?.nodes ?? [], [data]);
	const edges = React.useMemo(() => data?.edges ?? [], [data]);

	const folders = React.useMemo(
		() => Array.from(new Set(nodes.map((n) => topFolder(n.path)))).sort(),
		[nodes],
	);
	const [activeFolders, setActiveFolders] = React.useState<Set<string>>(new Set());
	const [hoverId, setHoverId] = React.useState<string | null>(null);
	const [selectedId, setSelectedId] = React.useState<string | null>(null);
	const [query, setQuery] = React.useState("");
	const [view, setView] = React.useState({ x: 0, y: 0, scale: 1 });
	const [dragState, setDragState] = React.useState<{ nodeId: string; offsetX: number; offsetY: number } | null>(null);
	const [positions, setPositions] = React.useState<Map<string, { x: number; y: number }> | null>(null);
	const panState = React.useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(null);
	const svgRef = React.useRef<SVGSVGElement>(null);

	// Filtre par dossier : ensemble des nœuds visibles.
	const visibleIds = React.useMemo(() => {
		if (activeFolders.size === 0) return null; // null = pas de filtre
		return new Set(nodes.filter((n) => activeFolders.has(topFolder(n.path))).map((n) => n.id));
	}, [nodes, activeFolders]);

	const layout = React.useMemo(() => {
		const filtered = visibleIds ? nodes.filter((n) => visibleIds.has(n.id)) : nodes;
		const filteredEdges = visibleIds
			? edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
			: edges;
		return layoutGraph(filtered, filteredEdges, WIDTH, HEIGHT);
	}, [nodes, edges, visibleIds]);

	// Positions courantes (positions simulées + déplacements utilisateur).
	const currentPositions = React.useMemo(() => {
		const map = new Map<string, { x: number; y: number }>();
		for (const node of layout.nodes) {
			map.set(node.id, positions?.get(node.id) ?? { x: node.x, y: node.y });
		}
		return map;
	}, [layout.nodes, positions]);

	const neighborIds = React.useMemo(() => {
		if (!hoverId) return new Set<string>();
		const set = new Set<string>([hoverId]);
		for (const edge of edges) {
			if (edge.source === hoverId) set.add(edge.target);
			if (edge.target === hoverId) set.add(edge.source);
		}
		return set;
	}, [hoverId, edges]);

	const normalizedQuery = query.trim().toLowerCase();
	const matchesQuery = (node: VaultGraphNode) =>
		!normalizedQuery || node.label.toLowerCase().includes(normalizedQuery) || node.path.toLowerCase().includes(normalizedQuery);

	const selected = nodes.find((n) => n.id === selectedId) ?? null;

	const handleWheel = React.useCallback((event: WheelEvent) => {
		event.preventDefault();
		const delta = event.deltaY > 0 ? 0.9 : 1.1;
		setView((v) => ({ ...v, scale: Math.min(4, Math.max(0.35, v.scale * delta)) }));
	}, []);

	// React attache les handlers wheel en passive: zoom exige un listener natif non-passif.
	React.useEffect(() => {
		const svg = svgRef.current;
		if (!svg) return;
		svg.addEventListener("wheel", handleWheel, { passive: false });
		return () => svg.removeEventListener("wheel", handleWheel);
	}, [handleWheel]);


	const handlePanStart = (event: React.PointerEvent<SVGSVGElement>) => {
		if (event.button !== 0) return;
		// Le fond uniquement : les nœuds gèrent eux-mêmes le drag.
		if ((event.target as SVGElement).closest("[data-node-id]")) return;
		panState.current = { startX: event.clientX, startY: event.clientY, originX: view.x, originY: view.y };
		(event.target as Element).setPointerCapture?.(event.pointerId);
	};
	const handlePanMove = (event: React.PointerEvent<SVGSVGElement>) => {
		if (dragState) {
			const point = clientToGraph(svgRef.current, event.clientX, event.clientY, view);
			if (point) {
				setPositions((current) => {
					const map = new Map(current ?? new Map<string, { x: number; y: number }>());
					map.set(dragState.nodeId, { x: point.x - dragState.offsetX, y: point.y - dragState.offsetY });
					return map;
				});
			}
			return;
		}
		if (panState.current) {
			const dx = event.clientX - panState.current.startX;
			const dy = event.clientY - panState.current.startY;
			setView((v) => ({ ...v, x: panState.current!.originX + dx, y: panState.current!.originY + dy }));
		}
	};
	const handlePanEnd = () => {
		panState.current = null;
		setDragState(null);
	};

	const nodeDragStart = (node: VaultGraphNode) => (event: React.PointerEvent<SVGGElement>) => {
		event.stopPropagation();
		event.preventDefault();
		const current = currentPositions.get(node.id);
		const point = clientToGraph(svgRef.current, event.clientX, event.clientY, view);
		if (!current || !point) return;
		setDragState({ nodeId: node.id, offsetX: point.x - current.x, offsetY: point.y - current.y });
		(event.currentTarget as SVGGElement).setPointerCapture?.(event.pointerId);
	};

	const toggleFolder = (folder: string) =>
		setActiveFolders((current) => {
			const next = new Set(current);
			if (next.has(folder)) next.delete(folder);
			else next.add(folder);
			return next;
		});

	if (isLoading) {
		return (
			<div className="flex h-full flex-col items-center justify-center gap-3 bg-bg-1">
				<Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Chargement du graphe" />
				<p className="text-xs text-foreground-tertiary">Résolution des wikiliens…</p>
			</div>
		);
	}

	if (isError) {
		return (
			<div className="m-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
				Graphe indisponible : {String((error as Error)?.message)}
			</div>
		);
	}

	return (
		<div className="flex h-full min-h-0 flex-col bg-bg-1">
			{/* Barre d'outils */}
			<div className="flex flex-wrap items-center gap-2 border-b border-line-1 px-4 py-2">
				<div className="flex items-center gap-2 text-foreground-secondary">
					<GitBranch className="h-4 w-4 text-primary" />
					<span className="text-xs font-semibold uppercase tracking-wider">Graphe de documents</span>
					<span className="rounded bg-bg-2 px-1.5 py-0.5 text-[10px] text-foreground-tertiary">
						{layout.nodes.length} nœuds · {edges.length} liens
					</span>
				</div>
				<div className="relative mx-auto w-full max-w-xs">
					<Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground-tertiary" />
					<input
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						placeholder="Filtrer les nœuds…"
						className="h-8 w-full rounded-md border border-line-1 bg-bg-2 pl-8 pr-7 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50"
						aria-label="Filtrer les nœuds"
					/>
					{query && (
						<button type="button" onClick={() => setQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-foreground-tertiary hover:text-foreground" aria-label="Effacer le filtre">
							<X className="h-3.5 w-3.5" />
						</button>
					)}
				</div>
				<div className="flex gap-1 overflow-x-auto">
					{folders.map((folder) => (
						<button
							key={folder}
							type="button"
							onClick={() => toggleFolder(folder)}
							aria-pressed={activeFolders.has(folder)}
							className={cn(
								"rounded-full border px-2.5 py-1 text-[10px] font-medium transition-colors",
								activeFolders.has(folder)
									? "border-primary/50 bg-primary/15 text-primary"
									: "border-line-1 bg-bg-2 text-foreground-secondary hover:text-foreground",
							)}
						>
							{folder}
						</button>
					))}
					{activeFolders.size > 0 && (
						<button type="button" onClick={() => setActiveFolders(new Set())} className="rounded-full border border-line-1 px-2.5 py-1 text-[10px] text-foreground-tertiary hover:text-foreground">
							Tous
						</button>
					)}
				</div>
			</div>

			<div className="relative min-h-0 flex-1">
				<svg
					ref={svgRef}
					viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
					className="h-full w-full touch-none select-none bg-[radial-gradient(circle_at_50%_40%,#10151f_0%,#0b0e14_75%)]"
					role="application"
					aria-label="Graphe interactif des wikiliens du vault"
					onPointerDown={handlePanStart}
					onPointerMove={handlePanMove}
					onPointerUp={handlePanEnd}
					onPointerLeave={handlePanEnd}
				>
					<g transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}>
						{/* Arêtes */}
						{layout.edges.map((edge, i) => {
							const a = currentPositions.get(edge.source);
							const b = currentPositions.get(edge.target);
							if (!a || !b) return null;
							const highlighted = hoverId !== null && (edge.source === hoverId || edge.target === hoverId);
							return (
								<line
									key={i}
									x1={a.x}
									y1={a.y}
									x2={b.x}
									y2={b.y}
									stroke={highlighted ? "#5b8cff" : "#2a3245"}
									strokeWidth={highlighted ? 1.6 : 0.8}
									strokeOpacity={highlighted ? 0.95 : 0.6}
								/>
							);
						})}
						{/* Nœuds */}
						{layout.nodes.map((node) => {
							const pos = currentPositions.get(node.id);
							if (!pos) return null;
							const isSelected = node.id === selectedId;
							const dimmedByHover = hoverId !== null && !neighborIds.has(node.id);
							const dimmedBySearch = normalizedQuery.length > 0 && !matchesQuery(node);
							const dimmed = dimmedByHover || dimmedBySearch;
							return (
								<g
									key={node.id}
									data-node-id={node.id}
									transform={`translate(${pos.x} ${pos.y})`}
									onPointerDown={nodeDragStart(node)}
									onPointerEnter={() => setHoverId(node.id)}
									onPointerLeave={() => setHoverId(null)}
									onClick={() => setSelectedId(node.id)}
									className="cursor-pointer"
									opacity={dimmed ? 0.25 : 1}
								>
									<circle
										r={isSelected ? 7 : 5}
										fill={isSelected ? "#5b8cff" : "#8b93a7"}
										stroke={isSelected ? "#b8ccff" : "#1a2233"}
										strokeWidth={1.5}
									/>
									{(!dimmed || isSelected) && (
										<text
											x={9}
											y={3}
											fontSize={10}
											fill={isSelected ? "#dce6ff" : "#9aa3b8"}
											fontFamily="ui-monospace, monospace"
											className="select-none"
										>
											{node.label.length > 28 ? node.label.slice(0, 28) + "…" : node.label}
										</text>
									)}
								</g>
							);
						})}
					</g>
				</svg>

				{/* Panneau de détail du nœud sélectionné */}
				{selected && (
					<div className="absolute bottom-4 left-4 w-80 max-w-[calc(100%-2rem)] rounded-xl border border-line-1 bg-bg-2/95 p-4 shadow-2xl backdrop-blur">
						<div className="flex items-start justify-between gap-2">
							<div className="min-w-0">
								<p className="break-words text-[13px] font-semibold text-foreground">{selected.label}</p>
								<p className="mt-0.5 break-all font-mono text-[10px] text-foreground-tertiary">{selected.path}</p>
							</div>
							<button type="button" onClick={() => setSelectedId(null)} className="rounded p-1 text-foreground-tertiary hover:bg-bg-1" aria-label="Fermer">
								<X className="h-4 w-4" />
							</button>
						</div>
						<button
							type="button"
							onClick={() => router.push(`/workspaces/observatory/vault?path=${encodeURIComponent(selected.path)}`)}
							className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-primary/40 bg-primary/15 px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/25"
						>
							<ExternalLink className="h-3.5 w-3.5" /> Ouvrir dans le Vault
						</button>
					</div>
				)}

				{/* Légende d'usage */}
				<div className="pointer-events-none absolute right-4 top-3 flex items-center gap-1.5 rounded-md border border-line-1 bg-bg-2/80 px-2 py-1 text-[10px] text-foreground-tertiary backdrop-blur">
					<MousePointer2 className="h-3 w-3" /> Glisser : déplacer · Molette : zoom · Clic : détail
				</div>
			</div>
		</div>
	);
}

function clientToGraph(
	svg: SVGSVGElement | null,
	clientX: number,
	clientY: number,
	view: { x: number; y: number; scale: number },
): { x: number; y: number } | null {
	if (!svg) return null;
	const rect = svg.getBoundingClientRect();
	// viewBox = WIDTH×HEIGHT projeté sur rect — facteur d'échelle homothétique.
	const k = Math.min(rect.width / WIDTH, rect.height / HEIGHT);
	const offsetX = (rect.width - WIDTH * k) / 2;
	const offsetY = (rect.height - HEIGHT * k) / 2;
	const sx = (clientX - rect.left - offsetX) / k;
	const sy = (clientY - rect.top - offsetY) / k;
	return { x: (sx - view.x) / view.scale, y: (sy - view.y) / view.scale };
}
