"use client";

/**
 * ConsolidateDialogs — opérations de consolidation de dossiers.
 *
 * Dialogues passifs : toute la logique (validations, rapport, purge des
 * associations) appartient au Core via /v1/folders/{merge,copy-resources,
 * move-resources}.  L'interface collecte les intentions et AFFICHE le
 * rapport d'opération retourné — les partiels sont visibles, jamais masqués.
 */

import * as React from "react";
import { FolderInput, FolderOutput, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import type { FolderOperationReport, FolderTree } from "@/lib/api/folders";

const INDENT = 12;

/** Aplatit l'arborescence pour une liste de sélection (avec indentation). */
function flatten(tree: FolderTree[]): { id: string; name: string; depth: number }[] {
	const flat: { id: string; name: string; depth: number }[] = [];
	const walk = (nodes: FolderTree[], depth: number) => {
		for (const n of nodes) {
			flat.push({ id: n.id, name: n.name, depth });
			walk(n.children, depth + 1);
		}
	};
	walk(tree, 0);
	return flat;
}

export function OperationReportView({ report }: { report: FolderOperationReport }) {
	return (
		<div
			role="status"
			className={`rounded-lg border px-3 py-2 text-xs ${
				report.status === "failed"
					? "border-destructive/40 bg-destructive/10"
					: report.status === "partially_completed"
						? "border-warning/40 bg-warning/10"
						: "border-emerald-500/40 bg-emerald-500/10"
			}`}
		>
			<p className="font-medium">
				{report.status} · opération {report.operation_id}
			</p>
			<p className="mt-0.5 text-muted-foreground">
				{report.attached} ajouté(s), {report.moved} déplacé(s), {report.skipped} déjà
				présent(s)
				{report.removed_sources?.length
					? `, ${report.removed_sources.length} dossier(s) source(s) supprimé(s)`
					: ""}
			</p>
			{report.errors.length > 0 && (
				<ul className="mt-1 list-disc pl-4 text-destructive">
					{report.errors.map((e) => (
						<li key={e}>{e}</li>
					))}
				</ul>
			)}
		</div>
	);
}

function FolderRadioList({
	tree,
	selectedId,
	onSelect,
	disabledIds,
}: {
	tree: FolderTree[];
	selectedId: string;
	onSelect: (id: string) => void;
	disabledIds?: Set<string>;
}) {
	const flat = flatten(tree);
	return (
		<ul className="max-h-56 overflow-y-auto rounded-lg border">
			{flat.map((f) => (
				<li key={f.id}>
					<label
						className={`flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-muted ${
							disabledIds?.has(f.id) ? "opacity-40" : ""
						}`}
						style={{ paddingLeft: 12 + f.depth * INDENT }}
					>
						<input
							type="radio"
							name="consolidation-target"
							disabled={disabledIds?.has(f.id)}
							checked={selectedId === f.id}
							onChange={() => onSelect(f.id)}
						/>
						<FolderOutput size={14} className="shrink-0 text-muted-foreground" />
						<span className="truncate">{f.name}</span>
					</label>
				</li>
			))}
		</ul>
	);
}

/** Fusion : sources multiples → cible unique (+ suppression explicite des sources). */
export function MergeFoldersDialog({
	tree,
	onMerge,
	onClose,
}: {
	tree: FolderTree[];
	onMerge: (folderIds: string[], targetId: string, removeSources: boolean) => void;
	onClose: () => void;
}) {
	const flat = flatten(tree);
	const [sources, setSources] = React.useState<Set<string>>(new Set());
	const [targetId, setTargetId] = React.useState("");
	const [removeSources, setRemoveSources] = React.useState(false);

	const toggleSource = (id: string) =>
		setSources((prev) => {
			const next = new Set(prev);
			if (next.has(id)) next.delete(id);
			else next.add(id);
			return next;
		});

	const submit = () => {
		onMerge([...sources], targetId, removeSources);
		onClose();
	};

	return (
		<Dialog open onOpenChange={(o) => !o && onClose()} title="Fusionner des dossiers">
			<div className="space-y-4">
				<div>
					<p className="mb-1 flex items-center gap-1.5 text-sm font-medium">
						<FolderInput size={14} /> Dossiers sources
					</p>
					<ul className="max-h-48 overflow-y-auto rounded-lg border">
						{flat.map((f) => (
							<li key={f.id}>
								<label
									className="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-muted"
									style={{ paddingLeft: 12 + f.depth * INDENT }}
								>
									<input
										type="checkbox"
										checked={sources.has(f.id)}
										onChange={() => toggleSource(f.id)}
										aria-label={`Sélectionner ${f.name}`}
									/>
									<Layers size={14} className="shrink-0 text-muted-foreground" />
									<span className="truncate">{f.name}</span>
								</label>
							</li>
						))}
					</ul>
				</div>

				<div>
					<p className="mb-1 text-sm font-medium">Dossier de destination</p>
					<FolderRadioList
						tree={tree}
						selectedId={targetId}
						onSelect={setTargetId}
						disabledIds={sources}
					/>
				</div>

				<label className="flex items-start gap-2 text-sm">
					<input
						type="checkbox"
						className="mt-1"
						checked={removeSources}
						onChange={(e) => setRemoveSources(e.target.checked)}
					/>
					<span>
						Supprimer les dossiers sources après le transfert
						<span className="block text-xs text-muted-foreground">
							Les ressources sont conservées — seuls les dossiers vides disparaissent.
						</span>
					</span>
				</label>

				<div className="flex justify-end gap-2 pt-2">
					<Button variant="ghost" onClick={onClose}>
						Annuler
					</Button>
					<Button
						variant="primary"
						disabled={sources.size === 0 || !targetId}
						onClick={submit}
					>
						Fusionner ({sources.size} → 1)
					</Button>
				</div>
			</div>
		</Dialog>
	);
}
/** Destination unique pour une sélection multi-ressources (copy ou move). */
export function DestinationPickDialog({
	tree,
	mode,
	itemCount,
	report,
	onConfirm,
	onClose,
}: {
	tree: FolderTree[];
	mode: "copy" | "move";
	itemCount: number;
	report: FolderOperationReport | null;
	onConfirm: (targetId: string) => void;
	onClose: () => void;
}) {
	const [targetId, setTargetId] = React.useState("");

	return (
		<Dialog
			open
			onOpenChange={(o) => !o && onClose()}
			title={
				mode === "copy"
					? `Copier ${itemCount} ressource(s) vers…`
					: `Déplacer ${itemCount} ressource(s) vers…`
			}
		>
			<div className="space-y-4">
				<FolderRadioList tree={tree} selectedId={targetId} onSelect={setTargetId} />
				{report && <OperationReportView report={report} />}
				<div className="flex justify-end gap-2 pt-2">
					<Button variant="ghost" onClick={onClose}>
						Fermer
					</Button>
					{!report && (
						<Button
							variant="primary"
							disabled={!targetId}
							onClick={() => onConfirm(targetId)}
						>
							{mode === "copy" ? "Copier ici" : "Déplacer ici"}
						</Button>
					)}
				</div>
			</div>
		</Dialog>
	);
}
