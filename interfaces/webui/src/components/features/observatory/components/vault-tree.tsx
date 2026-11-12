"use client";

/**
 * Observatory — arborescence du vault (lecture seule).
 *
 * Rend l'arbre retourné par GET /v1/memory/vault/tree tel quel : l'ordre
 * (dossiers avant fichiers, alphabétique) et l'organisation viennent du Core,
 * jamais d'un re-tri côté interface (règle : le Core détient la structure).
 */

import * as React from "react";
import { ChevronRight, FileCode2, FileText, FileJson2, FileSpreadsheet, File, FolderOpen, Folder } from "lucide-react";
import { cn } from "@/lib/utils";
import type { VaultNode } from "@/lib/api/observatory";

interface VaultTreeProps {
	tree: VaultNode;
	selectedPath: string | null;
	onSelect: (path: string) => void;
	/** Filtre par fragment (insensible à la casse) ; vide = tout. */
	filter: string;
}

function matchesFilter(node: VaultNode, needle: string): boolean {
	if (!needle) return true;
	const lower = needle.toLowerCase();
	if (node.type === "file") {
		return node.path.toLowerCase().includes(lower);
	}
	// Une entrée de dossier reste visible si elle-même ou un descendant matche.
	return (node.children ?? []).some((child) => matchesFilter(child, needle));
}

export function VaultTree({ tree, selectedPath, onSelect, filter }: VaultTreeProps) {
	const needle = filter.trim().toLowerCase();
	return (
		<div className="text-[13px]" role="tree">
			{(tree.children ?? []).map((child) => (
				<VaultTreeNode
					key={child.path}
					node={child}
					depth={0}
					needle={needle}
					selectedPath={selectedPath}
					onSelect={onSelect}
				/>
			))}
		</div>
	);
}

function VaultTreeNode({
	node,
	depth,
	needle,
	selectedPath,
	onSelect,
}: {
	node: VaultNode;
	depth: number;
	needle: string;
	selectedPath: string | null;
	onSelect: (path: string) => void;
}) {
	const [open, setOpen] = React.useState(depth < 1);

	if (!matchesFilter(node, needle)) return null;

	if (node.type === "file") {
		const active = selectedPath === node.path;
		return (
			<button
				type="button"
				role="treeitem"
				aria-selected={active}
				onClick={() => onSelect(node.path)}
				style={{ paddingLeft: `${8 + depth * 14}px` }}
				className={cn(
					"flex w-full items-center gap-1.5 rounded-md py-1 pr-2 text-left transition-colors",
					active ? "bg-primary/15 text-primary" : "text-foreground-secondary hover:bg-bg-2 hover:text-foreground",
				)}
				title={node.path}
			>
				<FileIcon extension={node.extension ?? ""} />
				<span className="truncate">{node.name}</span>
			</button>
		);
	}

	const children = node.children ?? [];
	const forceOpen = needle.length > 0;
	const isOpen = forceOpen || open;

	return (
		<div role="group">
			<button
				type="button"
				role="treeitem"
				aria-expanded={isOpen}
				aria-selected={false}
				onClick={() => setOpen((v) => !v)}
				style={{ paddingLeft: `${8 + depth * 14}px` }}
				className="flex w-full items-center gap-1 rounded-md py-1 pr-2 text-foreground hover:bg-bg-2 transition-colors"
			>
				<ChevronRight className={cn("h-3.5 w-3.5 shrink-0 text-foreground-tertiary transition-transform", isOpen && "rotate-90")} />
				{isOpen ? <FolderOpen className="h-3.5 w-3.5 shrink-0 text-primary/80" /> : <Folder className="h-3.5 w-3.5 shrink-0 text-foreground-tertiary" />}
				<span className="truncate font-medium">{node.name}</span>
			</button>
			{isOpen &&
				children.map((child) => (
					<VaultTreeNode
						key={child.path}
						node={child}
						depth={depth + 1}
						needle={needle}
						selectedPath={selectedPath}
						onSelect={onSelect}
					/>
				))}
		</div>
	);
}

function FileIcon({ extension }: { extension: string }) {
	const cls = "h-3.5 w-3.5 shrink-0 text-foreground-tertiary";
	switch (extension.toLowerCase()) {
		case ".md":
		case ".markdown":
			return <FileText className={cls} />;
		case ".json":
		case ".ndjson":
			return <FileJson2 className={cls} />;
		case ".csv":
			return <FileSpreadsheet className={cls} />;
		case ".yaml":
		case ".yml":
			return <FileCode2 className={cls} />;
		default:
			return <File className={cls} />;
	}
}
