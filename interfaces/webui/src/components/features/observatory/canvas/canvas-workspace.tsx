"use client";

/**
 * Observatory — Canvas (espace de travail visuel).
 *
 * Surface libre pour organiser des documents du vault en cartes reliées.
 * État 100% local (localStorage) : la persistance serveur n'est pas
 * prétendue — les liens entre documents sont de l'aide à la
 * navigation, pas des relations du Knowledge graph.
 */

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
	Plus,
	Trash2,
	Link2,
	X,
	FileText,
	BookOpen,
	Search,
	RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui.store";
import { listVaultTree, type VaultNode } from "@/lib/api/observatory";

interface CanvasCard {
	id: string;
	path: string;
	label: string;
	x: number;
	y: number;
}

interface CanvasEdge {
	id: string;
	source: string;
	target: string;
	label: string;
}

interface CanvasState {
	cards: CanvasCard[];
	edges: CanvasEdge[];
}

const STORAGE_KEY = "ethan.observatory.canvas.v1";
const CARD_W = 220;
const CARD_H = 84;

const emptyState: CanvasState = { cards: [], edges: [] };

function loadState(): CanvasState {
	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (!raw) return emptyState;
		const parsed = JSON.parse(raw) as CanvasState;
		if (Array.isArray(parsed?.cards) && Array.isArray(parsed?.edges)) {
			return { cards: parsed.cards, edges: parsed.edges };
		}
		return emptyState;
	} catch {
		return emptyState;
	}
}

function flattenMarkdownFiles(node: VaultNode): VaultNode[] {
	const out: VaultNode[] = [];
	const walk = (n: VaultNode) => {
		if (n.type === "file") {
			if (n.markdown) out.push(n);
			return;
		}
		for (const child of n.children ?? []) walk(child);
	};
	walk(node);
	return out.sort((a, b) => a.path.localeCompare(b.path));
}

function fileLabel(path: string): string {
	const parts = path.split("/");
	return parts[parts.length - 1]?.replace(/\.(md|markdown)$/i, "") ?? path;
}

export function CanvasWorkspace() {
	const router = useRouter();
	const addToast = useUIStore((s) => s.addToast);
	const [state, setState] = React.useState<CanvasState>(emptyState);
	const [hydrated, setHydrated] = React.useState(false);
	const [pickerOpen, setPickerOpen] = React.useState(false);
	const [pickerFilter, setPickerFilter] = React.useState("");
	const [linkMode, setLinkMode] = React.useState(false);
	const [linkSource, setLinkSource] = React.useState<string | null>(null);
	const [dragCard, setDragCard] = React.useState<{ id: string; offsetX: number; offsetY: number } | null>(null);
	const surfaceRef = React.useRef<HTMLDivElement>(null);

	const { data: tree } = useQuery({ queryKey: ["vault-tree-canvas"], queryFn: () => listVaultTree(), staleTime: 5 * 60_000 });

	// Hydratation locale après montage (localStorage n'existe pas au SSR) —
	// séquence volontaire : lire l'état persistant une seule fois au montage.
	React.useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect
		setState(loadState());
		setHydrated(true);
	}, []);
	React.useEffect(() => {
		if (!hydrated) return;
		try {
			window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
		} catch {
			// quota plein : on continue sans persister, sans faire semblant.
		}
	}, [state, hydrated]);

	const candidates = React.useMemo(() => {
		if (!tree) return [];
		const files = flattenMarkdownFiles(tree);
		const needle = pickerFilter.trim().toLowerCase();
		return needle ? files.filter((f) => f.path.toLowerCase().includes(needle)) : files;
	}, [tree, pickerFilter]);

	const addCard = (file: VaultNode) => {
		setState((current) => {
			if (current.cards.some((card) => card.path === file.path)) {
				addToast({ type: "info", message: "Ce document est déjà sur le canvas." });
				return current;
			}
			const jitter = (current.cards.length % 6) * 36;
			return {
				...current,
				cards: [
					...current.cards,
					{
						id: `card-${Date.now()}-${Math.round(Math.random() * 1e6)}`,
						path: file.path,
						label: fileLabel(file.path),
						x: 40 + jitter,
						y: 40 + jitter,
					},
				],
			};
		});
	};

	const removeCard = (id: string) =>
		setState((current) => ({
			cards: current.cards.filter((c) => c.id !== id),
			edges: current.edges.filter((e) => e.source !== id && e.target !== id),
		}));

	const onCardPointerDown = (card: CanvasCard) => (event: React.PointerEvent<HTMLDivElement>) => {
		if (event.button !== 0) return;
		if ((event.target as HTMLElement).closest("[data-no-drag]")) return;
		const rect = surfaceRef.current?.getBoundingClientRect();
		if (!rect) return;
		event.preventDefault();
		setDragCard({
			id: card.id,
			offsetX: event.clientX - (rect.left + card.x),
			offsetY: event.clientY - (rect.top + card.y),
		});
		(event.currentTarget as HTMLDivElement).setPointerCapture?.(event.pointerId);
	};

	const onSurfacePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
		if (!dragCard) return;
		const rect = surfaceRef.current?.getBoundingClientRect();
		if (!rect) return;
		const nextX = event.clientX - rect.left - dragCard.offsetX;
		const nextY = event.clientY - rect.top - dragCard.offsetY;
		setState((current) => ({
			...current,
			cards: current.cards.map((card) =>
				card.id === dragCard.id ? { ...card, x: Math.max(0, nextX), y: Math.max(0, nextY) } : card,
			),
		}));
	};
	const onSurfacePointerUp = () => setDragCard(null);

	const handleCardClick = (cardId: string) => {
		if (!linkMode) return;
		if (linkSource === null) {
			setLinkSource(cardId);
			return;
		}
		if (linkSource === cardId) {
			setLinkSource(null);
			return;
		}
		setState((current) => {
			const exists = current.edges.some(
				(e) => (e.source === linkSource && e.target === cardId) || (e.source === cardId && e.target === linkSource),
			);
			if (exists) return current;
			return {
				...current,
				edges: [...current.edges, { id: `edge-${Date.now()}`, source: linkSource, target: cardId, label: "" }],
			};
		});
		setLinkSource(null);
	};

	const cardById = new Map(state.cards.map((c) => [c.id, c]));

	return (
		<div className="relative flex h-full min-h-0 flex-col bg-bg-1">
			{/* Barre d'outils */}
			<div className="flex flex-wrap items-center gap-2 border-b border-line-1 px-4 py-2">
				<h1 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
					<BookOpen className="h-4 w-4 text-primary" /> Canvas
					<span className="rounded bg-bg-2 px-1.5 py-0.5 text-[10px] text-foreground-tertiary">{state.cards.length} documents · {state.edges.length} liens</span>
				</h1>
				<div className="ml-auto flex items-center gap-1.5">
					<button type="button" onClick={() => setPickerOpen(true)} className="flex items-center gap-1.5 rounded-md border border-line-1 bg-bg-2 px-2.5 py-1.5 text-[11px] font-medium text-foreground-secondary transition-colors hover:text-foreground">
						<Plus className="h-3.5 w-3.5" /> Document
					</button>
					<button
						type="button"
						onClick={() => { setLinkMode((v) => !v); setLinkSource(null); }}
						aria-pressed={linkMode}
						className={cn(
							"flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors",
							linkMode ? "border-primary/50 bg-primary/15 text-primary" : "border-line-1 bg-bg-2 text-foreground-secondary hover:text-foreground",
						)}
					>
						<Link2 className="h-3.5 w-3.5" /> Relier
					</button>
					<button type="button" onClick={() => setState(emptyState)} title="Vider le canvas" aria-label="Vider le canvas" className="rounded-md border border-line-1 bg-bg-2 p-1.5 text-foreground-tertiary transition-colors hover:text-red-400">
						<RotateCcw className="h-4 w-4" />
					</button>
				</div>
			</div>

			{linkMode && (
				<div className="border-b border-primary/30 bg-primary/10 px-4 py-1.5 text-[11px] text-primary">
					{linkSource === null
						? "Mode liaison — cliquez sur le premier document."
						: "Cliquez sur le second document pour créer le lien (le lien est local à ce canvas)."}
				</div>
			)}

			{/* Surface */}
			<div
				ref={surfaceRef}
				className="relative min-h-0 flex-1 overflow-hidden bg-[radial-gradient(circle_at_1px_1px,#1d2333_1px,transparent_0)_0_0/26px_26px,#0b0e14]"
				onPointerMove={onSurfacePointerMove}
				onPointerUp={onSurfacePointerUp}
				onPointerLeave={onSurfacePointerUp}
			>
				{/* Liens */}
				<svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
					{state.edges.map((edge) => {
						const a = cardById.get(edge.source);
						const b = cardById.get(edge.target);
						if (!a || !b) return null;
						return (
							<line
								key={edge.id}
								x1={a.x + CARD_W / 2}
								y1={a.y + CARD_H / 2}
								x2={b.x + CARD_W / 2}
								y2={b.y + CARD_H / 2}
								stroke="#5b8cff"
								strokeOpacity={0.6}
								strokeWidth={1.6}
								strokeDasharray="6 4"
							/>
						);
					})}
				</svg>

				{/* Cartes */}
				{state.cards.map((card) => {
					const isLinkSource = linkMode && linkSource === card.id;
					return (
						<div
							key={card.id}
							style={{ left: card.x, top: card.y, width: CARD_W, height: CARD_H }}
							onPointerDown={onCardPointerDown(card)}
							onClick={() => handleCardClick(card.id)}
							role="button"
							aria-pressed={isLinkSource}
							aria-label={`Carte document ${card.label}`}
							className={cn(
								"absolute flex cursor-grab flex-col justify-between rounded-xl border p-3 shadow-lg transition-shadow",
								"focus:outline-none focus:ring-2 focus:ring-primary/50",
								dragCard?.id === card.id && "cursor-grabbing shadow-2xl",
								isLinkSource ? "border-primary/70 bg-bg-2 ring-2 ring-primary/40" : "border-line-1 bg-bg-2 hover:border-line-2",
							)}
						>
							<div className="flex items-start gap-2">
								<FileText className="mt-0.5 h-4 w-4 shrink-0 text-primary/80" aria-hidden />
								<div className="min-w-0">
									<p className="truncate text-[12px] font-semibold leading-tight text-foreground" title={card.label}>{card.label}</p>
									<p className="mt-0.5 truncate font-mono text-[9px] text-foreground-tertiary" title={card.path}>{card.path}</p>
								</div>
							</div>
							<div className="flex items-center justify-end gap-1" data-no-drag>
								<button
									type="button"
									onClick={() => router.push(`/workspaces/observatory/vault?path=${encodeURIComponent(card.path)}`)}
									className="rounded p-1 text-foreground-tertiary transition-colors hover:text-primary"
									title="Ouvrir dans le Vault"
									aria-label="Ouvrir dans le Vault"
								>
									<BookOpen className="h-3.5 w-3.5" />
								</button>
								<button type="button" onClick={() => removeCard(card.id)} className="rounded p-1 text-foreground-tertiary transition-colors hover:text-red-400" title="Retirer du canvas" aria-label="Retirer du canvas">
									<Trash2 className="h-3.5 w-3.5" />
								</button>
							</div>
						</div>
					);
				})}

				{state.cards.length === 0 && hydrated && (
					<div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center">
						<BookOpen className="h-10 w-10 text-foreground-tertiary" aria-hidden />
						<h2 className="text-base font-semibold text-foreground">Canvas vide</h2>
						<p className="max-w-sm text-xs text-foreground-tertiary">
							Ajoutez des documents du vault, arrangez-les, reliez-les. Cet espace est local à
							votre navigateur — les liens ne modifient aucun fichier.
						</p>
						<button type="button" onClick={() => setPickerOpen(true)} className="mt-2 flex items-center gap-2 rounded-lg border border-primary/40 bg-primary/15 px-4 py-2 text-xs font-medium text-primary hover:bg-primary/25">
							<Plus className="h-4 w-4" /> Ajouter un document
						</button>
					</div>
				)}

				<p className="pointer-events-none absolute bottom-3 left-4 text-[10px] text-foreground-tertiary">
					Arrangement local (navigateur) — aucune relation n&apos;est écrite dans le vault.
				</p>
			</div>

			{/* Sélecteur de document */}
			{pickerOpen && (
				<div className="absolute inset-0 z-30 flex items-center justify-center bg-black/60 p-6" role="dialog" aria-modal="true" aria-label="Choisir un document">
					<div className="flex h-[70vh] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-line-2 bg-bg-2 shadow-2xl">
						<div className="flex items-center gap-2 border-b border-line-1 p-3">
							<Search className="h-4 w-4 text-foreground-tertiary" aria-hidden />
							<input
								autoFocus
								value={pickerFilter}
								onChange={(e) => setPickerFilter(e.target.value)}
								placeholder="Filtrer les documents Markdown…"
								className="h-8 w-full bg-transparent text-sm focus:outline-none"
								aria-label="Filtrer les documents"
							/>
							<button type="button" onClick={() => setPickerOpen(false)} className="rounded p-1 text-foreground-tertiary hover:bg-bg-1" aria-label="Fermer">
								<X className="h-4 w-4" />
							</button>
						</div>
						<div className="min-h-0 flex-1 overflow-y-auto p-2">
							{candidates.slice(0, 200).map((file) => (
								<button
									key={file.path}
									type="button"
									onClick={() => { addCard(file); setPickerOpen(false); }}
									className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-bg-1"
								>
									<FileText className="h-3.5 w-3.5 shrink-0 text-foreground-tertiary" aria-hidden />
									<span className="truncate text-[12px] text-foreground-secondary">{file.path}</span>
								</button>
							))}
							{candidates.length === 0 && <p className="py-8 text-center text-xs text-foreground-tertiary">Aucun document Markdown ne correspond.</p>}
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
